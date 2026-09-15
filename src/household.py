"""INR-native household join ledger. Reads each desk's lots; never writes them.

Hard split: only the Indian book uses the India line.

- India line (12-month clock, INR, demat / rupee) = Indian book only.
- USD line (Irish accumulating USD share class, 24-month foreign clock, alien
  desk, zero FX) = Ireland/global book, including CSUS+VXUA in full.

CSUS, VXUA, CSPX, XUSE, VWRA, VTI, VXUS are not India-line lots. VXUA's India
look-through is Schedule FA / household concentration, not a lot on the India
desk. Per-lot FX source and date are stored so a Rule 115 / TT-rate (G4) change
is a re-run, not a rebuild. Not a filing source of record without a human
signature. No transfer primitive.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from src.books.ledger import Lot as IndiaLot
from src.books.ledger import lot_cost, lot_value

RUPEE = Decimal(1)
USD_CENT = Decimal("0.01")
INR_NATIVE = Decimal(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
VANGUARD_COST_BASIS_PATH = REPO_ROOT / "data" / "private" / "costbasisdownload_2391.csv"
VANGUARD_MARK_DATE = date(2026, 9, 11)

# Working marks. Not Rule 115. Not a tax conclusion.
# USD mark confirmed from the Vanguard taxable cost-basis export, 11 Sep 2026.
USD_BOOK_MARK_USD = Decimal("354097.28")
USD_INR_WORKING = Decimal("95.69")
INR_DESK_DESIGN_INR = Decimal(5000000)
# Dated GL2 vehicle CSUS+VXUA 60/40 (2026-09-14) on the USD line (alien desk,
# FOREIGN_24M, already-held USD, zero FX). CSUS contributes 0 India. VXUA India
# look-through from the same FTSE All-World family: 1.63% / 38.4% × 0.40 ≈ 1.70%.
# Disclosure only — not an India-desk lot, not INR-funded, not the 12-month
# Indian clock, not a Nifty sleeve.
WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_WEIGHT = Decimal("0.0170")
WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_USD = Decimal(6010)
WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_INR = Decimal(575000)
WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_SOURCE = (
    "working GL2 CSUS+VXUA 60/40 USD-line India look-through ~1.70% / ~$6,010 / "
    "₹5.8 lakh; disclosure only (Schedule FA / household concentration); "
    "not an India-desk lot; VXUA holdings not yet published; not a tax conclusion"
)
# Unchosen G13 substitute, not the default. Also USD-line look-through, not desk.
WORKING_VWRA_INDIA_LOOKTHROUGH_WEIGHT = Decimal("0.011")
WORKING_VWRA_INDIA_LOOKTHROUGH_USD = Decimal(3900)
WORKING_VWRA_INDIA_LOOKTHROUGH_INR = Decimal(370000)
WORKING_VWRA_INDIA_LOOKTHROUGH_SOURCE = (
    "working G13 VWRA USD-line India look-through ~1.1% / ~$3,900; "
    "unchosen substitute, not the default; not an India-desk lot"
)

# Ireland/global (and the pre-wrapper US-listed book) run on the USD line.
# None of these may join as Desk.INDIA / HoldingClock.INDIA_12M.
USD_LINE_SYMBOLS: frozenset[str] = frozenset(
    {"CSUS", "VXUA", "CSPX", "XUSE", "VWRA", "VTI", "VXUS"}
)

FX_SOURCE_RULE_115_TT = "rule_115_tt_buying"
FX_SOURCE_WORKING_MARK = "yahoo_usdinr_working"
FX_SOURCE_INR_NATIVE = "inr_native"


class ClockContamination(ValueError):
    """India 12-month and foreign 24-month clocks must not mix."""


class HoldingClock(StrEnum):
    INDIA_12M = "india_12m"
    FOREIGN_24M = "foreign_24m"


class Desk(StrEnum):
    INDIA = "india"
    ALIEN = "alien"


@dataclass(frozen=True)
class ConversionRate:
    inr_per_unit: Decimal
    source: str
    as_of: date
    currency: str

    def __post_init__(self) -> None:
        if self.inr_per_unit <= 0:
            raise ValueError("inr_per_unit must be > 0")
        if self.currency not in {"INR", "USD"}:
            raise ValueError(f"unsupported conversion currency {self.currency}")


@dataclass(frozen=True)
class DualNumber:
    name: str
    rnor: Decimal
    ror: Decimal
    unit: str = "INR"

    @property
    def governs(self) -> Decimal:
        return self.ror


@dataclass(frozen=True)
class FaLine:
    symbol: str
    desk: str
    native_currency: str


@dataclass(frozen=True)
class IndiaExposure:
    """Household India concentration: India-desk lots plus USD-line look-through.

    `india_desk_inr` is the Indian book only. The look-through fields are
    Schedule FA / concentration disclosure. They are not India-line lots.
    """

    india_desk_inr: Decimal
    usd_line_india_lookthrough_usd: Decimal
    usd_line_india_lookthrough_inr: Decimal
    usd_line_india_lookthrough_weight: Decimal
    total_inr: Decimal
    source: str
    tagged_working: bool = True


@dataclass(frozen=True)
class AlienLot:
    lot_id: str
    symbol: str
    acquired: date
    usd_cost: Decimal
    usd_value: Decimal
    fx_cost: ConversionRate
    fx_value: ConversionRate

    def __post_init__(self) -> None:
        if self.fx_cost.currency != "USD" or self.fx_value.currency != "USD":
            raise ValueError("alien lots are USD-native")
        if self.usd_cost < 0 or self.usd_value < 0:
            raise ValueError("usd cost and value must be >= 0")


@dataclass(frozen=True)
class VanguardLot:
    """One row from a Vanguard taxable cost-basis download. Not a filing lot."""

    lot_id: str
    symbol: str
    acquired: date
    quantity: Decimal
    usd_cost: Decimal
    usd_value: Decimal


@dataclass(frozen=True)
class JoinLot:
    lot_id: str
    desk: Desk
    symbol: str
    acquired: date
    native_cost: Decimal
    native_value: Decimal
    native_currency: str
    fx_cost: ConversionRate
    fx_value: ConversionRate
    clock: HoldingClock

    def __post_init__(self) -> None:
        expected = clock_for_desk(self.desk)
        if self.clock is not expected:
            raise ClockContamination(
                f"{self.lot_id}: {self.desk} must use {expected}, not {self.clock}"
            )
        _assert_usd_line_stays_alien(self)
        if self.native_cost < 0 or self.native_value < 0:
            raise ValueError("native cost and value must be >= 0")

    @property
    def cost_inr(self) -> Decimal:
        return self.native_cost * self.fx_cost.inr_per_unit

    @property
    def value_inr(self) -> Decimal:
        return self.native_value * self.fx_value.inr_per_unit


@dataclass(frozen=True)
class HouseholdLedger:
    lots: tuple[JoinLot, ...]
    as_of: date

    def india_lots(self) -> tuple[JoinLot, ...]:
        return tuple(lot for lot in self.lots if lot.desk is Desk.INDIA)

    def alien_lots(self) -> tuple[JoinLot, ...]:
        return tuple(lot for lot in self.lots if lot.desk is Desk.ALIEN)

    def india_cost_inr(self) -> Decimal:
        return sum((lot.cost_inr for lot in self.india_lots()), Decimal(0))

    def india_value_inr(self) -> Decimal:
        return sum((lot.value_inr for lot in self.india_lots()), Decimal(0))

    def alien_cost_usd(self) -> Decimal:
        return sum((lot.native_cost for lot in self.alien_lots()), Decimal(0))

    def alien_value_usd(self) -> Decimal:
        return sum((lot.native_value for lot in self.alien_lots()), Decimal(0))

    def alien_cost_inr(self) -> Decimal:
        return sum((lot.cost_inr for lot in self.alien_lots()), Decimal(0))

    def alien_value_inr(self) -> Decimal:
        return sum((lot.value_inr for lot in self.alien_lots()), Decimal(0))


def clock_for_desk(desk: Desk) -> HoldingClock:
    if desk is Desk.INDIA:
        return HoldingClock.INDIA_12M
    if desk is Desk.ALIEN:
        return HoldingClock.FOREIGN_24M
    raise ValueError(f"unknown desk {desk}")


def _assert_usd_line_stays_alien(lot: JoinLot) -> None:
    usd_line = lot.symbol in USD_LINE_SYMBOLS or lot.native_currency == "USD"
    if not usd_line:
        return
    if lot.desk is Desk.ALIEN and lot.clock is HoldingClock.FOREIGN_24M:
        return
    raise ClockContamination(
        f"{lot.lot_id}: {lot.symbol} is USD-line; only the Indian book uses the "
        f"India line; must use {Desk.ALIEN} / {HoldingClock.FOREIGN_24M}, "
        f"not {lot.desk} / {lot.clock}"
    )


def inr_native_rate(as_of: date) -> ConversionRate:
    return ConversionRate(
        inr_per_unit=INR_NATIVE,
        source=FX_SOURCE_INR_NATIVE,
        as_of=as_of,
        currency="INR",
    )


def usd_rate(inr_per_usd: Decimal, *, source: str, as_of: date) -> ConversionRate:
    return ConversionRate(
        inr_per_unit=inr_per_usd,
        source=source,
        as_of=as_of,
        currency="USD",
    )


def join_india_lot(lot: IndiaLot, *, lot_id: str, as_of: date) -> JoinLot:
    if lot.symbol in USD_LINE_SYMBOLS:
        raise ClockContamination(
            f"{lot_id}: {lot.symbol} is USD-line; only the Indian book uses the India line"
        )
    fx = inr_native_rate(as_of)
    return JoinLot(
        lot_id=lot_id,
        desk=Desk.INDIA,
        symbol=lot.symbol,
        acquired=lot.acquired,
        native_cost=lot_cost(lot),
        native_value=lot_value(lot),
        native_currency="INR",
        fx_cost=fx,
        fx_value=fx,
        clock=HoldingClock.INDIA_12M,
    )


def join_alien_lot(lot: AlienLot) -> JoinLot:
    """USD-line join: Desk.ALIEN / FOREIGN_24M / USD. CSUS+VXUA use this path."""
    return JoinLot(
        lot_id=lot.lot_id,
        desk=Desk.ALIEN,
        symbol=lot.symbol,
        acquired=lot.acquired,
        native_cost=lot.usd_cost,
        native_value=lot.usd_value,
        native_currency="USD",
        fx_cost=lot.fx_cost,
        fx_value=lot.fx_value,
        clock=HoldingClock.FOREIGN_24M,
    )


def from_desks(
    *,
    india: Sequence[IndiaLot],
    alien: Sequence[AlienLot],
    as_of: date,
) -> HouseholdLedger:
    india_joined = tuple(
        join_india_lot(lot, lot_id=f"in-{i}", as_of=as_of) for i, lot in enumerate(india)
    )
    alien_joined = tuple(join_alien_lot(lot) for lot in alien)
    ledger = HouseholdLedger(lots=india_joined + alien_joined, as_of=as_of)
    assert_reproduces_india(ledger, india)
    assert_reproduces_alien(ledger, alien)
    return ledger


def assert_reproduces_india(ledger: HouseholdLedger, india: Sequence[IndiaLot]) -> None:
    desk_cost = sum((lot_cost(lot) for lot in india), Decimal(0))
    desk_value = sum((lot_value(lot) for lot in india), Decimal(0))
    if abs(ledger.india_cost_inr() - desk_cost) > RUPEE:
        raise ValueError("household india cost does not reproduce the desk to ₹1")
    if abs(ledger.india_value_inr() - desk_value) > RUPEE:
        raise ValueError("household india value does not reproduce the desk to ₹1")


def assert_reproduces_alien(ledger: HouseholdLedger, alien: Sequence[AlienLot]) -> None:
    desk_cost = sum((lot.usd_cost for lot in alien), Decimal(0))
    desk_value = sum((lot.usd_value for lot in alien), Decimal(0))
    if abs(ledger.alien_cost_usd() - desk_cost) > USD_CENT:
        raise ValueError("household alien cost does not reproduce the desk to $0.01")
    if abs(ledger.alien_value_usd() - desk_value) > USD_CENT:
        raise ValueError("household alien value does not reproduce the desk to $0.01")


def revalue(lot: JoinLot, *, fx_cost: ConversionRate, fx_value: ConversionRate) -> JoinLot:
    """W1 / G4 answer change is a re-run with a new named basis, not a rebuild."""
    if lot.desk is Desk.INDIA:
        raise ValueError("india lots are INR-native; do not revalue FX")
    return replace(lot, fx_cost=fx_cost, fx_value=fx_value)


def fa_line_register(ledger: HouseholdLedger) -> tuple[FaLine, ...]:
    seen: dict[str, FaLine] = {}
    for lot in ledger.alien_lots():
        seen.setdefault(
            lot.symbol,
            FaLine(symbol=lot.symbol, desk=lot.desk.value, native_currency=lot.native_currency),
        )
    return tuple(seen[symbol] for symbol in sorted(seen))


def fa_line_count(ledger: HouseholdLedger) -> int:
    return len(fa_line_register(ledger))


def total_india_exposure(
    ledger: HouseholdLedger,
    *,
    usd_line_india_lookthrough_usd: Decimal = WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_USD,
    usd_line_india_lookthrough_inr: Decimal = WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_INR,
    usd_line_india_lookthrough_weight: Decimal = WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_WEIGHT,
    source: str = WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_SOURCE,
) -> IndiaExposure:
    """India-desk value plus USD-line look-through. Look-through is not a desk lot."""
    india_desk = ledger.india_value_inr()
    return IndiaExposure(
        india_desk_inr=india_desk,
        usd_line_india_lookthrough_usd=usd_line_india_lookthrough_usd,
        usd_line_india_lookthrough_inr=usd_line_india_lookthrough_inr,
        usd_line_india_lookthrough_weight=usd_line_india_lookthrough_weight,
        total_inr=india_desk + usd_line_india_lookthrough_inr,
        source=source,
        tagged_working=True,
    )


def dual(name: str, *, rnor: Decimal, ror: Decimal, unit: str = "INR") -> DualNumber:
    return DualNumber(name=name, rnor=rnor.quantize(RUPEE), ror=ror.quantize(RUPEE), unit=unit)


def working_mark_rate(*, as_of: date = VANGUARD_MARK_DATE) -> ConversionRate:
    """G4/W1 still open. Named working Yahoo USDINR stand-in already on this ledger."""
    return usd_rate(USD_INR_WORKING, source=FX_SOURCE_WORKING_MARK, as_of=as_of)


def parse_vanguard_cost_basis(text: str) -> tuple[VanguardLot, ...]:
    """Read a Vanguard cost-basis download. Does not write lots or store account numbers."""
    rows = _vanguard_data_rows(text)
    lots: list[VanguardLot] = []
    seen: dict[str, int] = {}
    for row in rows:
        symbol = row["Symbol/CUSIP"].strip()
        acquired = _us_mdy(row["Acquired date"])
        key = f"{symbol.lower()}-{acquired.isoformat()}"
        suffix = seen.get(key, 0)
        seen[key] = suffix + 1
        lots.append(
            VanguardLot(
                lot_id=f"{key}-{suffix}",
                symbol=symbol,
                acquired=acquired,
                quantity=Decimal(row["Quantity"].strip()),
                usd_cost=_usd_money(row["Total cost"]),
                usd_value=_usd_money(_column(row, "Market value")),
            )
        )
    if not lots:
        raise ValueError("vanguard cost-basis download has a header but no lots")
    return tuple(lots)


def load_vanguard_cost_basis(path: Path = VANGUARD_COST_BASIS_PATH) -> tuple[VanguardLot, ...]:
    return parse_vanguard_cost_basis(path.read_text(encoding="utf-8"))


def alien_lots_from_vanguard(
    lots: Sequence[VanguardLot],
    *,
    fx_cost: ConversionRate | None = None,
    fx_value: ConversionRate | None = None,
) -> tuple[AlienLot, ...]:
    cost_fx = fx_cost or working_mark_rate()
    value_fx = fx_value or working_mark_rate()
    return tuple(
        AlienLot(
            lot_id=lot.lot_id,
            symbol=lot.symbol,
            acquired=lot.acquired,
            usd_cost=lot.usd_cost,
            usd_value=lot.usd_value,
            fx_cost=cost_fx,
            fx_value=value_fx,
        )
        for lot in lots
    )


def load_alien_from_vanguard(
    path: Path = VANGUARD_COST_BASIS_PATH,
    *,
    fx_cost: ConversionRate | None = None,
    fx_value: ConversionRate | None = None,
) -> tuple[AlienLot, ...]:
    return alien_lots_from_vanguard(
        load_vanguard_cost_basis(path),
        fx_cost=fx_cost,
        fx_value=fx_value,
    )


def _vanguard_data_rows(text: str) -> tuple[dict[str, str], ...]:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if "Symbol/CUSIP" in line)
    rows = tuple(
        row
        for row in csv.DictReader(lines[start:])
        if row.get("Symbol/CUSIP", "").strip()
    )
    return rows


def _column(row: dict[str, str], prefix: str) -> str:
    for key, value in row.items():
        if key.startswith(prefix):
            return value
    raise KeyError(prefix)


def _us_mdy(raw: str) -> date:
    month, day, year = raw.strip().split("/")
    return date(int(year), int(month), int(day))


def _usd_money(raw: str) -> Decimal:
    text = raw.strip().replace(",", "").replace("$", "")
    if text in {"", "-"}:
        return Decimal("0.00")
    return Decimal(text).quantize(USD_CENT)
