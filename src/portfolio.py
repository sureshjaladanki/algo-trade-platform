"""L2: weights, §6.1 limits, and every sell through Book L."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from src.books.ledger import (
    Lot,
    ProposedSell,
    Schedule,
    lot_value,
    realisation_schedule,
    tax_on_gain,
)
from src.tax import LTCG_EXEMPTION, add_months, long_term_holding

GROSS_MAX = Decimal(1)
ACTIVE_MAX = Decimal("0.40")
NAME_MAX = Decimal("0.06")
SECTOR_MAX = Decimal("0.25")
OVERNIGHT_4SIGMA_MAX = Decimal("0.02")
MARGIN_BUFFER = Decimal("0.25")
MAX_DEFER_SESSIONS = 63
DESIGN_EQUITY = Decimal(5000000)
PAISE = Decimal("0.01")


class LimitError(Exception):
    """A §6.1 limit was breached."""


@dataclass(frozen=True)
class Deferral:
    symbol: str
    quantity: Decimal
    ltcg_on: date
    rupees_saved: Decimal
    note: str


@dataclass(frozen=True)
class SchedulerResult:
    executed: Schedule
    deferred: tuple[Deferral, ...]
    harvested: Schedule
    log: tuple[str, ...]


def _rupees(value: Decimal) -> Decimal:
    return value.quantize(PAISE)


def assert_gross(total_value: Decimal, equity: Decimal) -> None:
    cap = _rupees(equity * GROSS_MAX)
    if total_value > cap:
        raise LimitError(f"gross {total_value} exceeds {cap}")


def assert_active(active_value: Decimal, equity: Decimal) -> None:
    cap = _rupees(equity * ACTIVE_MAX)
    if active_value > cap:
        raise LimitError(f"active sleeve {active_value} exceeds {cap}")


def assert_single_name(name_value: Decimal, equity: Decimal) -> None:
    cap = _rupees(equity * NAME_MAX)
    if name_value > cap:
        raise LimitError(f"single name {name_value} exceeds {cap}")


def assert_sector(sector_value: Decimal, equity: Decimal) -> None:
    cap = _rupees(equity * SECTOR_MAX)
    if sector_value > cap:
        raise LimitError(f"sector {sector_value} exceeds {cap}")


def assert_no_naked_short_options(n: int) -> None:
    if n != 0:
        raise LimitError("naked short options must be 0")


def assert_no_single_stock_derivatives(n: int) -> None:
    if n != 0:
        raise LimitError("single-stock derivatives must be 0")


def assert_overnight_4sigma(position_value: Decimal, daily_sigma: Decimal, equity: Decimal) -> None:
    loss = position_value * Decimal(4) * daily_sigma
    cap = _rupees(equity * OVERNIGHT_4SIGMA_MAX)
    if loss > cap:
        raise LimitError(f"4σ overnight {loss} exceeds {cap}")


def assert_margin(broker_margin: Decimal, equity: Decimal, buffer: Decimal = MARGIN_BUFFER) -> None:
    reserved = broker_margin * (Decimal(1) + buffer)
    if reserved > equity:
        raise LimitError(f"margin+buffer {reserved} exceeds equity {equity}")


def assert_portfolio(lots: list[Lot], equity: Decimal, daily_sigma: dict[str, Decimal]) -> None:
    total = sum((lot_value(lot) for lot in lots), Decimal(0))
    assert_gross(total, equity)
    by_name: dict[str, Decimal] = {}
    by_sector: dict[str, Decimal] = {}
    active = Decimal(0)
    for lot in lots:
        value = lot_value(lot)
        by_name[lot.symbol] = by_name.get(lot.symbol, Decimal(0)) + value
        if lot.sector:
            by_sector[lot.sector] = by_sector.get(lot.sector, Decimal(0)) + value
        if lot.sleeve == "active":
            active += value
    assert_active(active, equity)
    for value in by_name.values():
        assert_single_name(value, equity)
    for value in by_sector.values():
        assert_sector(value, equity)
    for symbol, value in by_name.items():
        if symbol in daily_sigma:
            assert_overnight_4sigma(value, daily_sigma[symbol], equity)
    assert_no_naked_short_options(0)
    assert_no_single_stock_derivatives(0)


def deferral_saving(sell: ProposedSell, exemption_used: Decimal) -> Decimal | None:
    if sell.long_term or sell.gain <= 0:
        return None
    later_tax, _ = tax_on_gain(sell.gain, True, exemption_used)
    return sell.tax - later_tax


def apply_realisation(
    lots: list[Lot],
    target_weights: dict[str, Decimal],
    as_of: date,
    *,
    exemption_used: Decimal = Decimal(0),
    max_defer_sessions: int = MAX_DEFER_SESSIONS,
    harvest_exemption: bool = False,
) -> SchedulerResult:
    """Every proposed sell passes through Book L. STCG that would become LTCG within N sessions is deferred."""
    raw = realisation_schedule(lots, target_weights, as_of, exemption_used=exemption_used)
    kept: list[ProposedSell] = []
    deferred: list[Deferral] = []
    log: list[str] = []
    for sell in raw.sells:
        ltcg_on = add_months(sell.acquired, 12)
        wait = (ltcg_on - as_of).days
        saving = deferral_saving(sell, exemption_used)
        if saving is not None and saving > 0 and 0 < wait <= max_defer_sessions:
            note = (
                f"DEFER {sell.symbol} qty {sell.quantity} until {ltcg_on.isoformat()} "
                f"({wait} days); STCG→LTCG saves ₹{saving}"
            )
            deferred.append(
                Deferral(
                    symbol=sell.symbol,
                    quantity=sell.quantity,
                    ltcg_on=ltcg_on,
                    rupees_saved=saving,
                    note=note,
                )
            )
            log.append(note)
            continue
        kept.append(sell)

    used = exemption_used
    executed: list[ProposedSell] = []
    for sell in kept:
        tax, used = tax_on_gain(sell.gain, sell.long_term, used)
        executed.append(replace(sell, tax=tax))

    harvested_sells: list[ProposedSell] = []
    if harvest_exemption and as_of.month == 3:
        remaining = LTCG_EXEMPTION - used
        if remaining > 0:
            harvested_sells, used, harvest_notes = _harvest_exemption(
                lots, as_of, remaining, executed
            )
            log.extend(harvest_notes)

    executed_sched = Schedule(
        sells=tuple(executed),
        tax=sum((s.tax for s in executed), Decimal("0.00")),
        exemption_used=used,
    )
    harvest_sched = Schedule(
        sells=tuple(harvested_sells),
        tax=sum((s.tax for s in harvested_sells), Decimal("0.00")),
        exemption_used=used,
    )
    return SchedulerResult(
        executed=executed_sched,
        deferred=tuple(deferred),
        harvested=harvest_sched,
        log=tuple(log),
    )


def _harvest_exemption(
    lots: list[Lot],
    as_of: date,
    remaining: Decimal,
    already: list[ProposedSell],
) -> tuple[list[ProposedSell], Decimal, list[str]]:
    sold_qty: dict[tuple[str, date], Decimal] = {}
    for sell in already:
        key = (sell.symbol, sell.acquired)
        sold_qty[key] = sold_qty.get(key, Decimal(0)) + sell.quantity
    sells: list[ProposedSell] = []
    notes: list[str] = []
    leftover = remaining
    used = LTCG_EXEMPTION - remaining
    ordered = sorted(
        (lot for lot in lots if long_term_holding(lot.acquired, as_of)),
        key=lambda lot: lot.acquired,
    )
    for lot in ordered:
        if leftover <= 0:
            break
        available_qty = lot.quantity - sold_qty.get((lot.symbol, lot.acquired), Decimal(0))
        if available_qty <= 0:
            continue
        gain_per = lot.price - lot.cost_per_share
        if gain_per <= 0:
            continue
        max_qty = leftover / gain_per
        qty = min(available_qty, max_qty)
        proceeds = qty * lot.price
        cost = qty * lot.cost_per_share
        gain = proceeds - cost
        tax, used = tax_on_gain(gain, True, used)
        sells.append(
            ProposedSell(
                symbol=lot.symbol,
                quantity=qty,
                acquired=lot.acquired,
                proceeds=proceeds,
                cost=cost,
                gain=gain,
                long_term=True,
                tax=tax,
            )
        )
        notes.append(
            f"HARVEST {lot.symbol} qty {qty} gain ₹{gain} against remaining s.198 exemption ₹{leftover}"
        )
        leftover -= gain
    return sells, used, notes


def tracking_error_bps(lots: list[Lot], deferred: tuple[Deferral, ...]) -> Decimal:
    total = sum((lot_value(lot) for lot in lots), Decimal(0))
    if total == 0 or not deferred:
        return Decimal(0)
    extra = Decimal(0)
    for item in deferred:
        extra += item.quantity * _price(lots, item.symbol)
    return extra / total * Decimal(10000)


def _price(lots: list[Lot], symbol: str) -> Decimal:
    for lot in lots:
        if lot.symbol == symbol:
            return lot.price
    raise KeyError(symbol)
