"""Book P — packaged factor vehicle versus self-run replication. No alpha claim."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.costs import BookKind, Product, Venue, round_trip_bps
from src.tax import ltcg, stcg

HOLDING_LTCG_YEARS = Decimal(1)


@dataclass(frozen=True)
class AfterTaxPath:
    terminal: Decimal
    tax: Decimal
    friction: Decimal
    ter_drag: Decimal


def packaged_after_tax(
    start_tri: Decimal,
    end_tri: Decimal,
    ter: Decimal,
    exit_load: Decimal,
    holding_years: Decimal,
    capital: Decimal,
) -> AfterTaxPath:
    """One tax event at redemption, at 13.0% (s.198 + cess) if holding_years ≥ 1."""
    gross = end_tri / start_tri
    net = gross * (Decimal(1) - ter) ** holding_years
    if holding_years * Decimal(365) < Decimal(15):
        net = net * (Decimal(1) - exit_load)
    pretax = capital * net
    gain = pretax - capital
    tax = ltcg(gain, Decimal(0)) if holding_years >= HOLDING_LTCG_YEARS else stcg(gain)
    return AfterTaxPath(
        terminal=pretax - tax,
        tax=tax,
        friction=Decimal("0.00"),
        ter_drag=capital - capital * (Decimal(1) - ter) ** holding_years,
    )


def self_run_friction(turnover_value: Decimal) -> Decimal:
    trip = round_trip_bps(
        product=Product.DELIVERY,
        venue=Venue.NSE,
        buy_value=turnover_value,
        sell_value=turnover_value,
        n_buy_orders=1,
        n_sell_orders=1,
        book=BookKind.CAPITAL_GAINS,
        n_isins_sold=1,
    )
    return trip.rupees


def self_run_after_tax(
    start_tri: Decimal,
    end_tri: Decimal,
    turnover: Decimal,
    holding_years: Decimal,
    capital: Decimal,
) -> AfterTaxPath:
    """Replication that realises `turnover` of the book each year as STCG and pays delivery friction."""
    gross = end_tri / start_tri
    pretax = capital * gross
    annual_gain = capital * (gross ** (Decimal(1) / holding_years) - Decimal(1)) if holding_years else Decimal(0)
    realised = annual_gain * turnover * holding_years
    tax = stcg(realised)
    friction = self_run_friction(capital * turnover) * holding_years
    return AfterTaxPath(
        terminal=pretax - tax - friction,
        tax=tax,
        friction=friction,
        ter_drag=Decimal("0.00"),
    )


def bps_difference(packaged: AfterTaxPath, self_run: AfterTaxPath, capital: Decimal) -> Decimal:
    """Positive ⇒ packaged wins, in bps/yr of starting capital (terminal gap / years is not used; gap / capital)."""
    return (packaged.terminal - self_run.terminal) / capital * Decimal(10000)


@dataclass(frozen=True)
class Verdict:
    kind: str
    packaged_minus_self_bps: Decimal
    note: str


def verdict(packaged_minus_self_bps: Decimal) -> Verdict:
    if packaged_minus_self_bps > Decimal(100):
        return Verdict("packaged", packaged_minus_self_bps, "Book M closes; implement the named fund")
    if packaged_minus_self_bps < Decimal(-100):
        return Verdict("self_run", packaged_minus_self_bps, "Book M may open against h0-prereg-book-m.md")
    return Verdict("tie_buy_fund", packaged_minus_self_bps, "within ±100 bps; buy the fund")
