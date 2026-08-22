"""A2: defined-risk 20–25Δ put-spread sleeve, after cost and after tax.

Same OptionsDX tape as A1. Rule is pre-registered: 30–45 DTE, 50–100 wide,
close at 50% of credit or at 14 DTE. Sized to 8% of a $250k book's max loss.
Tax is the working 28% Section 1256 blend with a December mark on open cycles.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import polars as pl

from src.books.tax_engine import C1_HURDLE_BPS
from src.books.vrp import after_tax_ordinary_series, marked_cagr, max_drawdown
from src.books.vrp_existence import A1_START, monthly_expiries, quote_dates
from src.books.vrp_spread import (
    DTE_HIGH,
    DTE_LOW,
    SpreadQuote,
    entry_date,
    pick_put_spread,
    spot_on,
)
from src.costs import SPX_MULTIPLIER
from src.harness import Declaration
from src.optionsdx import legs_on_date, puts_from_panel
from src.tax import ORDINARY_DIVIDEND_RATE, SECTION_1256_BLEND
from src.vti import IndexPoint, annualized_return, calendar_year_returns
from src.yahoo import DailyBar

# C1 measured excess, not the 25 bps hurdle. A2's non-dilution gate uses this.
C1_MEASURED_BPS = 35.5
assert C1_MEASURED_BPS >= C1_HURDLE_BPS

BOOK_EQUITY = 250_000.0
SLEEVE_WEIGHT = 0.20
SLEEVE_NOTIONAL = BOOK_EQUITY * SLEEVE_WEIGHT
MAX_LOSS_FRAC = 0.08
CLOSE_CREDIT_FRAC = 0.50
CLOSE_DTE = 14
PUTW_HURDLE_BPS = 75.0
SHARPE_MIN = 0.4
MAX_DD_FRAC = 0.25
BLEND_WEIGHTS = (0.15, 0.20, 0.25)
MONTHS_PER_YEAR = 12.0


def screen_declaration(n: int) -> Declaration:
    return Declaration(
        book_id="A",
        spec_id="A.spx-put-spread-sleeve-a2",
        n=n,
        sigma=150.0,
        hypothesized_effect=116.0,
        unit="bps_of_sleeve_per_cycle",
    )


@dataclass(frozen=True)
class CyclePnl:
    entry: date
    expiry: date
    exit: date
    n_contracts: int
    pnl_usd: float
    max_loss_usd: float
    cash_settled: bool


def _n_contracts(spread: SpreadQuote) -> int:
    width = spread.short_strike - spread.long_strike
    max_loss_pts = width - spread.round_trip.credit
    if max_loss_pts <= 0:
        return 0
    budget = MAX_LOSS_FRAC * BOOK_EQUITY
    n = int(budget / (max_loss_pts * SPX_MULTIPLIER))
    return max(n, 1)


def _expiry_days(panel, expiry: date, start: date) -> list[date]:
    return sorted(
        panel.filter(
            (pl.col("expire_date") == expiry) & (pl.col("quote_date") >= start)
        )["quote_date"]
        .unique()
        .to_list()
    )


def _mid_credit(short_bid: float, short_ask: float, long_bid: float, long_ask: float) -> float:
    return 0.5 * (short_bid + short_ask) - 0.5 * (long_bid + long_ask)


def _settlement_pnl(spread: SpreadQuote, spot: float) -> float:
    short_pay = max(spread.short_strike - spot, 0.0)
    long_pay = max(spread.long_strike - spot, 0.0)
    return spread.round_trip.credit - (short_pay - long_pay)


def simulate_cycle(
    panel,
    spx: list[DailyBar],
    spread: SpreadQuote,
) -> CyclePnl | None:
    n = _n_contracts(spread)
    if n <= 0:
        return None
    width = spread.short_strike - spread.long_strike
    max_loss_usd = (width - spread.round_trip.credit) * SPX_MULTIPLIER * n
    open_cost = spread.round_trip.all_in_usd * n
    days = _expiry_days(panel, spread.expiry, spread.trade_date)
    exit_day = None
    exit_debit = None
    for day in days:
        if day <= spread.trade_date:
            continue
        dte = (spread.expiry - day).days
        legs = legs_on_date(
            panel,
            expiry=spread.expiry,
            trade_date=day,
            short_strike=spread.short_strike,
            long_strike=spread.long_strike,
        )
        if legs is None:
            continue
        short, long = legs
        credit = _mid_credit(short.bid, short.ask, long.bid, long.ask)
        hit_half = credit <= CLOSE_CREDIT_FRAC * spread.round_trip.credit
        hit_dte = dte <= CLOSE_DTE
        if hit_half or hit_dte:
            exit_day = day
            exit_debit = credit
            break
    if exit_day is None or exit_debit is None:
        spot = spot_on(spx, spread.expiry)
        if spot is None:
            return None
        economic = _settlement_pnl(spread, spot)
        cost = 0.5 * open_cost
        pnl = economic * SPX_MULTIPLIER * n - cost
        return CyclePnl(
            entry=spread.trade_date,
            expiry=spread.expiry,
            exit=spread.expiry,
            n_contracts=n,
            pnl_usd=pnl,
            max_loss_usd=max_loss_usd,
            cash_settled=True,
        )
    economic = spread.round_trip.credit - exit_debit
    pnl = economic * SPX_MULTIPLIER * n - open_cost
    return CyclePnl(
        entry=spread.trade_date,
        expiry=spread.expiry,
        exit=exit_day,
        n_contracts=n,
        pnl_usd=pnl,
        max_loss_usd=max_loss_usd,
        cash_settled=False,
    )


def construct_cycles(panel, spx: list[DailyBar]) -> list[tuple[SpreadQuote, CyclePnl]]:
    days = quote_dates(panel)
    out: list[tuple[SpreadQuote, CyclePnl]] = []
    for expiry in monthly_expiries(panel):
        trade = entry_date(expiry, days, start=A1_START, lo=DTE_LOW, hi=DTE_HIGH)
        if trade is None:
            continue
        spot = spot_on(spx, trade)
        if spot is None:
            continue
        chain = puts_from_panel(panel, expiry=expiry, trade_date=trade)
        spread = pick_put_spread(chain, spot)
        if spread is None:
            continue
        cycle = simulate_cycle(panel, spx, spread)
        if cycle is not None:
            out.append((spread, cycle))
    return out


def _monthly_pnl(cycles: list[CyclePnl]) -> dict[tuple[int, int], float]:
    by_month: dict[tuple[int, int], float] = {}
    for cycle in cycles:
        key = (cycle.exit.year, cycle.exit.month)
        by_month[key] = by_month.get(key, 0.0) + cycle.pnl_usd
    return by_month


def _year_pnl(cycles: list[CyclePnl]) -> dict[int, float]:
    """1256: trades that span 31 Dec split P&L by calendar fraction (working mark)."""
    by_year: dict[int, float] = {}
    for cycle in cycles:
        if cycle.entry.year == cycle.exit.year:
            by_year[cycle.exit.year] = by_year.get(cycle.exit.year, 0.0) + cycle.pnl_usd
            continue
        span = max((cycle.exit - cycle.entry).days, 1)
        marked = cycle.pnl_usd * min(
            max((date(cycle.entry.year, 12, 31) - cycle.entry).days / span, 0.0), 1.0
        )
        by_year[cycle.entry.year] = by_year.get(cycle.entry.year, 0.0) + marked
        by_year[cycle.exit.year] = by_year.get(cycle.exit.year, 0.0) + (
            cycle.pnl_usd - marked
        )
    return by_year


def after_tax_cagr(cycles: list[CyclePnl], *, years: float) -> float:
    if years <= 0:
        raise ValueError("years must be > 0")
    wealth = SLEEVE_NOTIONAL
    for year, pnl in sorted(_year_pnl(cycles).items()):
        wealth += pnl * (1.0 - SECTION_1256_BLEND)
    if wealth <= 0:
        return -1.0
    return (wealth / SLEEVE_NOTIONAL) ** (1.0 / years) - 1.0


def sleeve_sharpe(cycles: list[CyclePnl]) -> float:
    monthly = _monthly_pnl(cycles)
    if len(monthly) < 3:
        return 0.0
    rets = [pnl / SLEEVE_NOTIONAL * (1.0 - SECTION_1256_BLEND) for pnl in monthly.values()]
    mean = sum(rets) / len(rets)
    var = sum((ret - mean) ** 2 for ret in rets) / (len(rets) - 1)
    if var <= 0:
        return 0.0
    return mean / (var**0.5) * (MONTHS_PER_YEAR**0.5)


def sleeve_max_dd(cycles: list[CyclePnl]) -> float:
    wealth = SLEEVE_NOTIONAL
    path = [wealth]
    for cycle in cycles:
        wealth += cycle.pnl_usd * (1.0 - SECTION_1256_BLEND)
        path.append(wealth)
    return abs(max_drawdown(path))


def blend_excess_bps(
    *,
    sleeve_cagr: float,
    vti_cagr: float,
    weight: float,
    c1_bps: float = C1_MEASURED_BPS,
) -> float:
    return 1e4 * (weight * (sleeve_cagr - vti_cagr) + (1.0 - weight) * (c1_bps / 1e4))


@dataclass(frozen=True)
class SleeveScreen:
    n: int
    start: date
    end: date
    years: float
    sleeve_after_tax: float
    putw_after_tax: float
    vti_after_tax: float
    vs_putw_bps: float
    sharpe: float
    max_dd: float
    blend_20_bps: float
    blends: dict[float, float]
    beat_putw: bool
    sharpe_ok: bool
    dd_ok: bool
    no_dilute: bool
    passed: bool


def _packaged_after_tax(
    bars: list[DailyBar], vti_points: list[IndexPoint], *, start: date, end: date
) -> tuple[float, float]:
    window = [bar for bar in bars if start <= bar.date <= end]
    points = after_tax_ordinary_series(window)
    vti_by_date = {point.date: point for point in vti_points}
    aligned = [point for point in points if point.date in vti_by_date]
    aligned_vti = [vti_by_date[point.date] for point in aligned]
    if len(aligned) < 2:
        raise ValueError("PUT/VTI do not overlap the sleeve window")
    if any(bar.dividend for bar in window):
        ordinary = annualized_return(aligned, field="after_tax")
    else:
        ordinary = marked_cagr(
            calendar_year_returns(aligned, field="before_tax"), ORDINARY_DIVIDEND_RATE
        )
    return ordinary, annualized_return(aligned_vti, field="after_tax")


def run_sleeve_screen(
    cycles: list[CyclePnl],
    *,
    putw: list[DailyBar],
    vti_points: list[IndexPoint],
    put_index: list[DailyBar] | None = None,
) -> SleeveScreen:
    if len(cycles) < 2:
        raise ValueError("need at least two cycles")
    start = cycles[0].entry
    end = cycles[-1].exit
    years = (end - start).days / 365.25
    sleeve = after_tax_cagr(cycles, years=years)
    packaged = putw if len(putw) >= 2 else (put_index or [])
    if len(packaged) < 2:
        raise ValueError("PUTW/PUT series missing")
    putw_at, vti_at = _packaged_after_tax(packaged, vti_points, start=start, end=end)
    sharpe = sleeve_sharpe(cycles)
    dd = sleeve_max_dd(cycles)
    blends = {
        w: blend_excess_bps(sleeve_cagr=sleeve, vti_cagr=vti_at, weight=w)
        for w in BLEND_WEIGHTS
    }
    vs_putw = 1e4 * (sleeve - putw_at)
    beat = vs_putw >= PUTW_HURDLE_BPS
    sharpe_ok = sharpe >= SHARPE_MIN
    dd_ok = dd <= MAX_DD_FRAC
    no_dilute = blends[SLEEVE_WEIGHT] >= C1_MEASURED_BPS
    return SleeveScreen(
        n=len(cycles),
        start=start,
        end=end,
        years=years,
        sleeve_after_tax=sleeve,
        putw_after_tax=putw_at,
        vti_after_tax=vti_at,
        vs_putw_bps=vs_putw,
        sharpe=sharpe,
        max_dd=dd,
        blend_20_bps=blends[SLEEVE_WEIGHT],
        blends=blends,
        beat_putw=beat,
        sharpe_ok=sharpe_ok,
        dd_ok=dd_ok,
        no_dilute=no_dilute,
        passed=beat and sharpe_ok and dd_ok and no_dilute,
    )
