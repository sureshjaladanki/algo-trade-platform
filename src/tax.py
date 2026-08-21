"""Tax treatment. Every after-tax result imports this; none re-implements it.

Working rates follow Blueprint §0.1 (household income $200k–$500k, mid-tax state)
until a later milestone replaces them with a filed return.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date, timedelta
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
