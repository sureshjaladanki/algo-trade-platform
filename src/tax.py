"""Tax treatment. Every after-tax result imports this; none re-implements it.

Working rates follow Blueprint §0.1 (household income $200k–$500k, mid-tax state)
until a later milestone replaces them with a filed return.
"""

from __future__ import annotations

from calendar import monthrange
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

STCG_RATE = 0.40
LTCG_RATE = 0.20
SECTION_1256_LT_WEIGHT = 0.60
SECTION_1256_ST_WEIGHT = 0.40
SECTION_1256_BLEND = SECTION_1256_LT_WEIGHT * LTCG_RATE + SECTION_1256_ST_WEIGHT * STCG_RATE
QD_RATE = 0.20
ORDINARY_DIVIDEND_RATE = STCG_RATE
IRA_RATE = 0.0

HOLDING_PERIOD_LT_DAYS = 365
QD_MIN_HOLDING_DAYS = 61
QD_WINDOW_DAYS = 121
QD_WINDOW_LOOKBACK_DAYS = 60
WASH_SALE_WINDOW_DAYS = 30
HARVEST_QUARANTINE_DAYS = 31
IRA_ANNUAL_CONTRIBUTION = 7_000.0
VTI_EXPENSE_RATIO = 0.0003


class Wrapper(StrEnum):
    TAXABLE = "taxable"
    IRA = "ira"
    ROTH = "roth"


class LotMethod(StrEnum):
    FIFO = "fifo"
    SPECIFIC = "specific"


@dataclass(frozen=True)
class Lot:
    lot_id: str
    taxpayer_id: str
    account_id: str
    wrapper: Wrapper
    symbol: str
    quantity: float
    cost_basis: float
    acquired: date
    is_1256: bool = False


@dataclass(frozen=True)
class Purchase:
    lot_id: str
    taxpayer_id: str
    account_id: str
    wrapper: Wrapper
    symbol: str
    quantity: float
    cost_basis: float
    trade_date: date


@dataclass(frozen=True)
class Realization:
    lot_id: str
    taxpayer_id: str
    symbol: str
    quantity: float
    proceeds: float
    basis: float
    acquired: date
    closed: date
    holding_days: int
    gain: float
    wrapper: Wrapper
    is_1256: bool
    wash_disallowed: float = 0.0
    ira_destroyed: bool = False

    @property
    def recognized_gain(self) -> float:
        if self.ira_destroyed:
            return 0.0
        if self.gain < 0:
            return self.gain + self.wash_disallowed
        return self.gain


@dataclass(frozen=True)
class WashMatch:
    disallowed: float
    ira_destroyed: bool
    replacement_lot_id: str | None
    replacement_basis_add: float


def capital_gain_rate(holding_days: int, *, is_1256: bool = False) -> float:
    if is_1256:
        return SECTION_1256_BLEND
    if holding_days > HOLDING_PERIOD_LT_DAYS:
        return LTCG_RATE
    return STCG_RATE


def tax_on_gain(
    gain: float,
    *,
    holding_days: int,
    wrapper: Wrapper,
    is_1256: bool = False,
) -> float:
    if wrapper is not Wrapper.TAXABLE:
        return 0.0
    return gain * capital_gain_rate(holding_days, is_1256=is_1256)


def section_1256_tax(gain: float, *, wrapper: Wrapper = Wrapper.TAXABLE) -> float:
    return tax_on_gain(gain, holding_days=0, wrapper=wrapper, is_1256=True)


def qualified_dividend_window(ex_date: date) -> tuple[date, date]:
    start = ex_date - timedelta(days=QD_WINDOW_LOOKBACK_DAYS)
    end = start + timedelta(days=QD_WINDOW_DAYS - 1)
    return start, end


def is_qualified_dividend(
    *,
    acquired: date,
    ex_date: date,
    sold: date | None = None,
) -> bool:
    start, end = qualified_dividend_window(ex_date)
    hold_start = max(acquired, start)
    hold_end = min(sold, end) if sold is not None else end
    return (hold_end - hold_start).days >= QD_MIN_HOLDING_DAYS


def dividend_tax(
    amount: float,
    *,
    qualified: bool,
    wrapper: Wrapper,
) -> float:
    if wrapper is not Wrapper.TAXABLE:
        return 0.0
    rate = QD_RATE if qualified else ORDINARY_DIVIDEND_RATE
    return amount * rate


def wash_sale_window(sale_date: date) -> tuple[date, date]:
    return (
        sale_date - timedelta(days=WASH_SALE_WINDOW_DAYS),
        sale_date + timedelta(days=WASH_SALE_WINDOW_DAYS),
    )


def apply_wash_sale(
    *,
    symbol: str,
    quantity_sold: float,
    loss: float,
    sale_date: date,
    taxpayer_id: str,
    sold_lot_id: str,
    purchases: Sequence[Purchase],
) -> WashMatch:
    """IRC 1091 window across joint accounts. IRA replacement destroys the loss (Rev. Rul. 2008-5)."""
    if loss >= 0 or quantity_sold <= 0:
        return WashMatch(0.0, False, None, 0.0)
    window_start, window_end = wash_sale_window(sale_date)
    candidates = [
        p
        for p in purchases
        if p.taxpayer_id == taxpayer_id
        and p.symbol == symbol
        and p.lot_id != sold_lot_id
        and window_start <= p.trade_date <= window_end
    ]
    candidates.sort(key=lambda p: (p.trade_date, p.lot_id))
    remaining = quantity_sold
    disallowed = 0.0
    ira_destroyed = False
    replacement_lot_id: str | None = None
    replacement_basis_add = 0.0
    for purchase in candidates:
        matched = min(remaining, purchase.quantity)
        portion = matched / quantity_sold
        matched_disallowed = -loss * portion
        disallowed += matched_disallowed
        if purchase.wrapper in (Wrapper.IRA, Wrapper.ROTH):
            ira_destroyed = True
        else:
            replacement_lot_id = purchase.lot_id
            replacement_basis_add += matched_disallowed
        remaining -= matched
        if remaining <= 0:
            break
    if remaining == quantity_sold:
        return WashMatch(0.0, False, None, 0.0)
    if ira_destroyed:
        return WashMatch(disallowed, True, None, 0.0)
    return WashMatch(disallowed, False, replacement_lot_id, replacement_basis_add)


def _select_lots(
    open_lots: Sequence[Lot],
    *,
    symbol: str,
    quantity: float,
    method: LotMethod,
    lot_ids: Sequence[str],
) -> list[Lot]:
    eligible = [lot for lot in open_lots if lot.symbol == symbol and lot.quantity > 0]
    if method is LotMethod.SPECIFIC:
        wanted = set(lot_ids)
        eligible = [lot for lot in eligible if lot.lot_id in wanted]
        eligible.sort(key=lambda lot: lot_ids.index(lot.lot_id))
    else:
        eligible.sort(key=lambda lot: (lot.acquired, lot.lot_id))
    selected: list[Lot] = []
    remaining = quantity
    for lot in eligible:
        selected.append(lot)
        remaining -= lot.quantity
        if remaining <= 0:
            return selected
    raise ValueError(f"insufficient quantity to close {quantity} of {symbol}")


def close_lots(
    open_lots: Sequence[Lot],
    *,
    symbol: str,
    quantity: float,
    proceeds: float,
    closed: date,
    method: LotMethod = LotMethod.FIFO,
    lot_ids: Sequence[str] = (),
    purchases: Sequence[Purchase] = (),
) -> tuple[list[Lot], list[Realization]]:
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    selected = _select_lots(
        open_lots, symbol=symbol, quantity=quantity, method=method, lot_ids=lot_ids
    )
    remaining_qty = quantity
    remaining_open = [lot for lot in open_lots if lot.lot_id not in {s.lot_id for s in selected}]
    realizations: list[Realization] = []
    basis_adjustments: dict[str, float] = {}

    for lot in selected:
        take = min(lot.quantity, remaining_qty)
        take_ratio = take / quantity
        take_proceeds = proceeds * take_ratio
        take_basis = lot.cost_basis * (take / lot.quantity)
        gain = take_proceeds - take_basis
        holding_days = (closed - lot.acquired).days
        wash = apply_wash_sale(
            symbol=symbol,
            quantity_sold=take,
            loss=gain,
            sale_date=closed,
            taxpayer_id=lot.taxpayer_id,
            sold_lot_id=lot.lot_id,
            purchases=purchases,
        )
        realizations.append(
            Realization(
                lot_id=lot.lot_id,
                taxpayer_id=lot.taxpayer_id,
                symbol=symbol,
                quantity=take,
                proceeds=take_proceeds,
                basis=take_basis,
                acquired=lot.acquired,
                closed=closed,
                holding_days=holding_days,
                gain=gain,
                wrapper=lot.wrapper,
                is_1256=lot.is_1256,
                wash_disallowed=wash.disallowed,
                ira_destroyed=wash.ira_destroyed,
            )
        )
        if wash.replacement_lot_id is not None and wash.replacement_basis_add:
            basis_adjustments[wash.replacement_lot_id] = (
                basis_adjustments.get(wash.replacement_lot_id, 0.0)
                + wash.replacement_basis_add
            )
        leftover = lot.quantity - take
        if leftover > 0:
            leftover_basis = lot.cost_basis * (leftover / lot.quantity)
            remaining_open.append(replace(lot, quantity=leftover, cost_basis=leftover_basis))
        remaining_qty -= take

    adjusted: list[Lot] = []
    for lot in remaining_open:
        add = basis_adjustments.get(lot.lot_id, 0.0)
        if add:
            adjusted.append(replace(lot, cost_basis=lot.cost_basis + add))
        else:
            adjusted.append(lot)
    return adjusted, realizations


def tax_on_realization(realization: Realization) -> float:
    if realization.wrapper is not Wrapper.TAXABLE:
        return 0.0
    if realization.ira_destroyed:
        return 0.0
    recognized = realization.recognized_gain
    return tax_on_gain(
        recognized,
        holding_days=realization.holding_days,
        wrapper=realization.wrapper,
        is_1256=realization.is_1256,
    )


def mark_1256_year_end(
    open_lots: Sequence[Lot],
    *,
    year: int,
    prices: dict[str, float],
) -> tuple[list[Lot], list[Realization]]:
    """December mark: unrealized 1256 gain/loss is realized at the blend; basis resets to FMV."""
    year_end = date(year, 12, 31)
    kept: list[Lot] = []
    marks: list[Realization] = []
    for lot in open_lots:
        if not lot.is_1256:
            kept.append(lot)
            continue
        price = prices[lot.symbol]
        mark_value = price * lot.quantity
        gain = mark_value - lot.cost_basis
        marks.append(
            Realization(
                lot_id=lot.lot_id,
                taxpayer_id=lot.taxpayer_id,
                symbol=lot.symbol,
                quantity=lot.quantity,
                proceeds=mark_value,
                basis=lot.cost_basis,
                acquired=lot.acquired,
                closed=year_end,
                holding_days=(year_end - lot.acquired).days,
                gain=gain,
                wrapper=lot.wrapper,
                is_1256=True,
            )
        )
        kept.append(replace(lot, cost_basis=mark_value, acquired=year_end))
    return kept, marks


# India listed equity (s.196 / s.198). Book L imports these. Not US STCG_RATE 0.40.
LTCG_EXEMPTION = Decimal(125000)
_INDIA_LISTED_STCG = Decimal("0.20")
_INDIA_LISTED_LTCG = Decimal("0.125")
_INDIA_CESS = Decimal("0.04")
_INDIA_PAISE = Decimal("0.01")
_SURCHARGE_CG_CAP = Decimal("0.15")


def add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    day_num = min(day.day, monthrange(year, month)[1])
    return date(year, month, day_num)


def long_term_holding(acquired: date, as_of: date) -> bool:
    """Listed equity / equity-oriented funds: held ≥ 12 months (s.198 vs s.196)."""
    return as_of >= add_months(acquired, 12)


def _india_money(value: Decimal) -> Decimal:
    return value.quantize(_INDIA_PAISE, rounding=ROUND_HALF_UP)


def _india_with_cess(tax: Decimal, surcharge_rate: Decimal) -> Decimal:
    surcharge_rate = min(surcharge_rate, _SURCHARGE_CG_CAP)
    return _india_money(tax * (Decimal(1) + surcharge_rate) * (Decimal(1) + _INDIA_CESS))


def stcg(gain: Decimal, surcharge_rate: Decimal = Decimal(0)) -> Decimal:
    """s.196: 20% from the first rupee, plus 4% cess. Not US 40% STCG_RATE."""
    if gain <= 0:
        return Decimal("0.00")
    return _india_with_cess(gain * _INDIA_LISTED_STCG, surcharge_rate)


def ltcg(gain: Decimal, exemption_used: Decimal, surcharge_rate: Decimal = Decimal(0)) -> Decimal:
    """s.198: 12.5% on the excess over ₹1,25,000 aggregate per tax year, plus cess."""
    remaining = LTCG_EXEMPTION - exemption_used
    if remaining < 0:
        remaining = Decimal(0)
    taxable = gain - remaining
    if taxable <= 0:
        return Decimal("0.00")
    return _india_with_cess(taxable * _INDIA_LISTED_LTCG, surcharge_rate)


# --- GL1 join surface. INR-measured foreign CG. Not IRA / §1256 / 40–20. ---
# tax takes a residency calendar, not a rate. G4/G5 stay W1; no tax conclusion.

INDIA_FOREIGN_LTCG_RATE = Decimal("0.13")
INDIA_FOREIGN_STCG_RATE = Decimal("0.312")
INDIA_CG_CARRY_YEARS = 8
INDIA_LISTED_LONG_MONTHS = 12
INDIA_FOREIGN_LONG_MONTHS = 24
ALLOWED_FILING_COUNTRIES = frozenset({"IN", "US"})


class ThirdJurisdictionRefused(ValueError):
    """GL-L3: no third-country filing obligation."""


class FxRateBasis(StrEnum):
    RULE_115_TT_BUYING = "rule_115_tt_buying"
    WORKING_YAHOO_USDINR = "yahoo_usdinr_working"


@dataclass(frozen=True)
class ResidencyCalendar:
    rnor_cliff: date


@dataclass(frozen=True)
class RealisedLine:
    desk: str
    gain_inr: Decimal
    long_term: bool
    closed: date
    receipt_in_india: bool = False
    other_asset: bool = True


@dataclass(frozen=True)
class SetOffResult:
    tax: Decimal
    tax_without_cross_book: Decimal
    value_inr: Decimal
    sheltered_inr: Decimal
    carried_stcl: Decimal
    carried_ltcl: Decimal
    carry_through_fy: str
    g5_applied: bool = False


def working_residency_calendar() -> ResidencyCalendar:
    from src.residency import rnor_cliff

    return ResidencyCalendar(rnor_cliff=rnor_cliff())


def rnor_reporting_calendar() -> ResidencyCalendar:
    return ResidencyCalendar(rnor_cliff=date(9999, 12, 31))


def ror_reporting_calendar() -> ResidencyCalendar:
    return ResidencyCalendar(rnor_cliff=date(1, 1, 1))


def indian_fy_label(day: date) -> str:
    start = day.year if day.month >= 4 else day.year - 1
    return f"{start}-{str(start + 1)[2:]}"


def holding_months(*, acquired: date, as_of: date) -> int:
    return (as_of.year - acquired.year) * 12 + (as_of.month - acquired.month)


def foreign_holding_is_long(*, acquired: date, closed: date) -> bool:
    return holding_months(acquired=acquired, as_of=closed) >= INDIA_FOREIGN_LONG_MONTHS


def is_rnor(day: date, calendar: ResidencyCalendar) -> bool:
    return day <= calendar.rnor_cliff


def refuse_third_jurisdiction(countries: Sequence[str]) -> None:
    extra = set(countries) - ALLOWED_FILING_COUNTRIES
    if extra:
        raise ThirdJurisdictionRefused(f"third jurisdiction refused: {sorted(extra)}")


def inr_measured_foreign_gain(
    *,
    usd_cost: Decimal,
    usd_proceeds: Decimal,
    inr_per_usd_cost: Decimal,
    inr_per_usd_proceeds: Decimal,
) -> Decimal:
    if inr_per_usd_cost <= 0 or inr_per_usd_proceeds <= 0:
        raise ValueError("FX rate must be > 0")
    return usd_proceeds * inr_per_usd_proceeds - usd_cost * inr_per_usd_cost


def india_foreign_cg_rate(*, acquired: date, closed: date) -> Decimal:
    if foreign_holding_is_long(acquired=acquired, closed=closed):
        return INDIA_FOREIGN_LTCG_RATE
    return INDIA_FOREIGN_STCG_RATE


def india_tax_on_foreign_gain(
    gain_inr: Decimal,
    *,
    acquired: date,
    closed: date,
    receipt_in_india: bool,
    calendar: ResidencyCalendar,
) -> Decimal:
    """Foreign CG in rupees. Calendar chooses RNOR vs ROR; this does not take a rate."""
    if gain_inr <= 0:
        return Decimal(0)
    if is_rnor(closed, calendar) and not receipt_in_india:
        return Decimal(0)
    return (gain_inr * india_foreign_cg_rate(acquired=acquired, closed=closed)).quantize(
        Decimal(1)
    )


def dual_india_tax_on_foreign_gain(
    gain_inr: Decimal,
    *,
    acquired: date,
    closed: date,
    receipt_in_india: bool,
) -> tuple[Decimal, Decimal]:
    rnor = india_tax_on_foreign_gain(
        gain_inr,
        acquired=acquired,
        closed=closed,
        receipt_in_india=receipt_in_india,
        calendar=rnor_reporting_calendar(),
    )
    ror = india_tax_on_foreign_gain(
        gain_inr,
        acquired=acquired,
        closed=closed,
        receipt_in_india=receipt_in_india,
        calendar=ror_reporting_calendar(),
    )
    return rnor, ror


def _foreign_rate(line: RealisedLine) -> Decimal:
    if line.long_term:
        return INDIA_FOREIGN_LTCG_RATE
    return INDIA_FOREIGN_STCG_RATE


def _tax_foreign_gains(gains: list[RealisedLine]) -> Decimal:
    return sum((line.gain_inr * _foreign_rate(line) for line in gains), Decimal(0)).quantize(
        Decimal(1)
    )


def _absorb(loss: Decimal, gains: list[RealisedLine]) -> tuple[Decimal, Decimal]:
    """Apply a loss (positive rupees of loss) to gains. Returns leftover loss, sheltered."""
    leftover = loss
    sheltered = Decimal(0)
    for i, line in enumerate(gains):
        if leftover <= 0 or line.gain_inr <= 0:
            continue
        take = min(leftover, line.gain_inr)
        gains[i] = replace(line, gain_inr=line.gain_inr - take)
        leftover -= take
        sheltered += take
    return leftover, sheltered


def _can_cross_book(loss: RealisedLine, gain: RealisedLine) -> bool:
    if loss.gain_inr >= 0 or gain.gain_inr <= 0:
        return False
    if loss.long_term and not gain.long_term:
        return False
    # G5 unresolved (W1): other-asset losses do not reduce s.198 listed gains.
    g5_blocked = loss.other_asset and not gain.other_asset
    return not g5_blocked


def carry_through_fy(closed: date) -> str:
    start = closed.year if closed.month >= 4 else closed.year - 1
    last = start + INDIA_CG_CARRY_YEARS
    return f"{last}-{str(last + 1)[2:]}"


def _empty_set_off() -> SetOffResult:
    return SetOffResult(
        tax=Decimal(0),
        tax_without_cross_book=Decimal(0),
        value_inr=Decimal(0),
        sheltered_inr=Decimal(0),
        carried_stcl=Decimal(0),
        carried_ltcl=Decimal(0),
        carry_through_fy="",
        g5_applied=False,
    )


def cross_book_set_off(
    lines: Sequence[RealisedLine],
    *,
    calendar: ResidencyCalendar,
    cross_book: bool = True,
) -> SetOffResult:
    """Set off at ROR with 8-year carry. RNOR: foreign side is zero. G5 not applied."""
    refuse_third_jurisdiction(("IN", "US"))
    if not lines:
        return _empty_set_off()
    closed = max(line.closed for line in lines)
    foreign = [replace(line) for line in lines if line.desk == "alien"]
    india = [replace(line) for line in lines if line.desk == "india"]
    if is_rnor(closed, calendar):
        foreign = [line for line in foreign if line.receipt_in_india]
        if not foreign:
            return _empty_set_off()

    st_gains = [line for line in foreign if line.gain_inr > 0 and not line.long_term]
    lt_gains = [line for line in foreign if line.gain_inr > 0 and line.long_term]
    stcl = sum((-line.gain_inr for line in foreign if line.gain_inr < 0 and not line.long_term), Decimal(0))
    ltcl = sum((-line.gain_inr for line in foreign if line.gain_inr < 0 and line.long_term), Decimal(0))
    stcl, _ = _absorb(stcl, st_gains)
    stcl, _ = _absorb(stcl, lt_gains)
    ltcl, _ = _absorb(ltcl, lt_gains)
    tax_without = _tax_foreign_gains([line for line in st_gains + lt_gains if line.gain_inr > 0])

    sheltered = Decimal(0)
    if cross_book:
        india_stcl = sum(
            (-line.gain_inr for line in india if line.gain_inr < 0 and not line.long_term),
            Decimal(0),
        )
        india_ltcl = sum(
            (-line.gain_inr for line in india if line.gain_inr < 0 and line.long_term),
            Decimal(0),
        )
        dummy_st = RealisedLine("india", Decimal(-1), False, closed, other_asset=False)
        dummy_lt = RealisedLine("india", Decimal(-1), True, closed, other_asset=False)
        if any(_can_cross_book(dummy_st, gain) for gain in st_gains + lt_gains if gain.gain_inr > 0):
            leftover, took_st = _absorb(india_stcl, st_gains)
            leftover, took_st_lt = _absorb(leftover, lt_gains)
            sheltered += took_st + took_st_lt
        if any(_can_cross_book(dummy_lt, gain) for gain in lt_gains if gain.gain_inr > 0):
            _, took_lt = _absorb(india_ltcl, lt_gains)
            sheltered += took_lt

    tax = _tax_foreign_gains([line for line in st_gains + lt_gains if line.gain_inr > 0])
    value = tax_without - tax if cross_book else Decimal(0)
    through = carry_through_fy(closed) if (stcl > 0 or ltcl > 0) else ""
    return SetOffResult(
        tax=tax,
        tax_without_cross_book=tax_without,
        value_inr=value,
        sheltered_inr=sheltered,
        carried_stcl=stcl,
        carried_ltcl=ltcl,
        carry_through_fy=through,
        g5_applied=False,
    )


def prefer_realising_inr_book() -> tuple[str, ...]:
    """Per unit of gain, the USD book costs more at ROR. Sequencing, not a hedge."""
    return ("india", "alien")


def ror_realisation_tax(
    *,
    desk: str,
    native_cost: Decimal,
    native_proceeds: Decimal,
    inr_per_unit_cost: Decimal,
    inr_per_unit_proceeds: Decimal,
    long_term: bool,
) -> Decimal:
    gain = inr_measured_foreign_gain(
        usd_cost=native_cost,
        usd_proceeds=native_proceeds,
        inr_per_usd_cost=inr_per_unit_cost,
        inr_per_usd_proceeds=inr_per_unit_proceeds,
    )
    if gain <= 0:
        return Decimal(0)
    rate = INDIA_FOREIGN_LTCG_RATE if long_term else INDIA_FOREIGN_STCG_RATE
    return gain * rate

