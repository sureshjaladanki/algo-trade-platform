"""Book A $0.5 kill screen: vertical put-spread round-trip on ThetaData FREE.

Not A1. n≈38, MDE 68.1 bps, ratio 0.59 — H3 closes certification. This module
only asks whether the traded spread's own round-trip eats 25% of credit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

from src.costs import (
    WORKING_TABLE,
    ProductBucket,
    SpreadRoundTrip,
    vertical_spread_round_trip,
)
from src.harness import Declaration
from src.theta import OptionQuote, ThetaUnavailable, list_expirations, puts_on_date
from src.yahoo import DailyBar

ROOT = "SPX"
FREE_START = date(2023, 6, 1)
DTE_LOW = 30
DTE_HIGH = 45
DTE_TARGET = 37
DELTA_LOW = 0.20
DELTA_HIGH = 0.25
DELTA_TARGET = 0.225
WIDTH_LOW = 50.0
WIDTH_HIGH = 100.0
PREFERRED_WIDTHS = (50.0, 100.0)
CREDIT_RETAIN_MIN = 0.25
WORKING_RATE = 0.05
WORKING_DIV_YIELD = 0.013
TRADING_DAYS = 365.0
A05_SIGMA = 150.0
A05_HYPOTHESIZED = 116.0
A05_N_PLAN = 38
MIN_STRUCTURES = 8
SIGN_STABLE_MIN = 4


def screen_declaration(n: int = A05_N_PLAN) -> Declaration:
    return Declaration(
        book_id="A",
        spec_id="A.spread-cost-kill",
        n=n,
        sigma=A05_SIGMA,
        hypothesized_effect=A05_HYPOTHESIZED,
        unit="bps_of_sleeve_per_cycle",
    )


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def year_fraction(start: date, end: date) -> float:
    return (end - start).days / TRADING_DAYS


def black_scholes_put(
    spot: float,
    strike: float,
    t: float,
    *,
    rate: float = WORKING_RATE,
    div: float = WORKING_DIV_YIELD,
    vol: float,
) -> float:
    if t <= 0:
        return max(strike - spot, 0.0)
    if vol <= 0:
        fwd = strike * math.exp(-rate * t) - spot * math.exp(-div * t)
        return max(fwd, 0.0)
    sqrt_t = math.sqrt(t)
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * t) / (vol * sqrt_t)
    d2 = d1 - vol * sqrt_t
    return strike * math.exp(-rate * t) * _norm_cdf(-d2) - spot * math.exp(
        -div * t
    ) * _norm_cdf(-d1)


def black_scholes_put_delta(
    spot: float,
    strike: float,
    t: float,
    *,
    rate: float = WORKING_RATE,
    div: float = WORKING_DIV_YIELD,
    vol: float,
) -> float:
    if t <= 0 or vol <= 0:
        return -1.0 if spot < strike else 0.0
    sqrt_t = math.sqrt(t)
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * t) / (vol * sqrt_t)
    return -math.exp(-div * t) * _norm_cdf(-d1)


def implied_vol_put(
    price: float,
    spot: float,
    strike: float,
    t: float,
    *,
    rate: float = WORKING_RATE,
    div: float = WORKING_DIV_YIELD,
) -> float | None:
    if t <= 0 or price <= 0 or spot <= 0 or strike <= 0:
        return None
    intrinsic = max(strike * math.exp(-rate * t) - spot * math.exp(-div * t), 0.0)
    if price < intrinsic * 0.999:
        return None
    lo, hi = 1e-4, 5.0
    vol = 0.2
    for _ in range(40):
        model = black_scholes_put(spot, strike, t, rate=rate, div=div, vol=vol)
        sqrt_t = math.sqrt(t)
        d1 = (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * t) / (
            vol * sqrt_t
        )
        vega = spot * math.exp(-div * t) * _norm_pdf(d1) * sqrt_t
        diff = model - price
        if abs(diff) < 1e-4:
            return vol
        if vega < 1e-8:
            break
        vol = vol - diff / vega
        if vol <= lo or vol >= hi:
            break
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        model = black_scholes_put(spot, strike, t, rate=rate, div=div, vol=mid)
        if model > price:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def put_delta(quote: OptionQuote, spot: float) -> float | None:
    t = year_fraction(quote.trade_date, quote.expiry)
    vol = implied_vol_put(quote.mid, spot, quote.strike, t)
    if vol is None:
        return None
    return black_scholes_put_delta(spot, quote.strike, t, vol=vol)


def is_third_friday(day: date) -> bool:
    return day.weekday() == 4 and 15 <= day.day <= 21


def is_monthly_expiry(day: date) -> bool:
    """SPX monthly listed expiry: third Friday, the Saturday after it (old AM
    Saturday settlement), or the Thursday before it (last trading day)."""
    if not (15 <= day.day <= 22):
        return False
    return day.weekday() in {3, 4, 5}


def monthly_expiries(days: list[date], *, start: date = FREE_START) -> list[date]:
    return [day for day in days if is_third_friday(day) and day >= start + timedelta(days=DTE_LOW)]


def black_scholes_put_vega(
    spot: float,
    strike: float,
    t: float,
    *,
    rate: float = WORKING_RATE,
    div: float = WORKING_DIV_YIELD,
    vol: float,
) -> float:
    """Black–Scholes put vega per 1.00 of volatility (not per vol point)."""
    if t <= 0 or vol <= 0:
        return 0.0
    sqrt_t = math.sqrt(t)
    d1 = (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * t) / (vol * sqrt_t)
    return spot * math.exp(-div * t) * _norm_pdf(d1) * sqrt_t


def put_iv_delta(quote: OptionQuote, spot: float) -> tuple[float, float] | None:
    t = year_fraction(quote.trade_date, quote.expiry)
    vol = implied_vol_put(quote.mid, spot, quote.strike, t)
    if vol is None:
        return None
    return vol, black_scholes_put_delta(spot, quote.strike, t, vol=vol)


def entry_date(
    expiry: date,
    trading_days: list[date],
    *,
    start: date | None = None,
    lo: int = DTE_LOW,
    hi: int = DTE_HIGH,
    target: int = DTE_TARGET,
) -> date | None:
    begin = FREE_START if start is None else start
    candidates = [
        day
        for day in trading_days
        if day >= begin and lo <= (expiry - day).days <= hi
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda day: abs((expiry - day).days - target))


@dataclass(frozen=True)
class SpreadQuote:
    trade_date: date
    expiry: date
    dte: int
    short_strike: float
    long_strike: float
    short_delta: float
    round_trip: SpreadRoundTrip


def _width_rank(width: float) -> tuple[int, float]:
    for i, preferred in enumerate(PREFERRED_WIDTHS):
        if abs(width - preferred) < 0.51:
            return (i, 0.0)
    if WIDTH_LOW <= width <= WIDTH_HIGH:
        return (len(PREFERRED_WIDTHS), abs(width - PREFERRED_WIDTHS[0]))
    return (99, abs(width))


def pick_put_spread(
    quotes: list[OptionQuote],
    spot: float,
) -> SpreadQuote | None:
    puts = [q for q in quotes if q.right == "P"]
    if not puts:
        return None
    scored: list[tuple[float, OptionQuote, float]] = []
    for quote in puts:
        delta = put_delta(quote, spot)
        if delta is None:
            continue
        abs_delta = abs(delta)
        if abs_delta < DELTA_LOW or abs_delta > DELTA_HIGH:
            continue
        scored.append((abs(abs_delta - DELTA_TARGET), quote, delta))
    if not scored:
        return None
    scored.sort(key=lambda row: (row[0], row[1].strike))
    _, short, short_delta = scored[0]
    by_strike = {quote.strike: quote for quote in puts}
    longs: list[tuple[tuple[int, float], OptionQuote]] = []
    for strike, quote in by_strike.items():
        width = short.strike - strike
        if width < WIDTH_LOW or width > WIDTH_HIGH:
            continue
        longs.append((_width_rank(width), quote))
    if not longs:
        return None
    longs.sort(key=lambda row: (row[0], -row[1].strike))
    long = longs[0][1]
    try:
        cost = vertical_spread_round_trip(
            short_bid=short.bid,
            short_ask=short.ask,
            long_bid=long.bid,
            long_ask=long.ask,
        )
    except ValueError:
        return None
    return SpreadQuote(
        trade_date=short.trade_date,
        expiry=short.expiry,
        dte=(short.expiry - short.trade_date).days,
        short_strike=short.strike,
        long_strike=long.strike,
        short_delta=short_delta,
        round_trip=cost,
    )


def spot_on(bars: list[DailyBar], day: date) -> float | None:
    by_date = {bar.date: bar.close for bar in bars}
    if day in by_date:
        return by_date[day]
    prior = [bar.close for bar in bars if bar.date <= day]
    if not prior:
        return None
    return prior[-1]


def construct_spreads(
    *,
    spx: list[DailyBar],
    expiries: list[date],
    chain_loader=puts_on_date,
) -> list[SpreadQuote]:
    days = [bar.date for bar in spx]
    out: list[SpreadQuote] = []
    n_fetched = 0
    for expiry in expiries:
        if not is_third_friday(expiry):
            continue
        trade = entry_date(expiry, days)
        if trade is None:
            continue
        spot = spot_on(spx, trade)
        if spot is None:
            continue
        chain = chain_loader(root=ROOT, expiry=expiry, trade_date=trade)
        n_fetched += 1
        spread = pick_put_spread(chain, spot)
        if spread is not None:
            out.append(spread)
    if n_fetched == 0 and expiries:
        raise ThetaUnavailable("no SPX EOD chains returned")
    return out


@dataclass(frozen=True)
class SpreadScreen:
    n: int
    n_expiries: int
    mean_credit: float
    mean_bid_ask_pct_of_credit: float
    mean_all_in_pct_of_credit: float
    mean_retained: float
    atm_all_in_high: float
    retain_ok: bool
    sparse: bool
    authorize_a1: bool


def run_spread_screen(spreads: list[SpreadQuote], *, n_expiries: int) -> SpreadScreen:
    atm = WORKING_TABLE[ProductBucket.SPX_ATM_30_45].all_in_high
    sparse = len(spreads) < MIN_STRUCTURES or (
        n_expiries > 0 and len(spreads) / n_expiries < 0.5
    )
    if not spreads:
        return SpreadScreen(
            n=0,
            n_expiries=n_expiries,
            mean_credit=0.0,
            mean_bid_ask_pct_of_credit=0.0,
            mean_all_in_pct_of_credit=0.0,
            mean_retained=0.0,
            atm_all_in_high=atm,
            retain_ok=False,
            sparse=True,
            authorize_a1=False,
        )
    mean_credit = sum(s.round_trip.credit for s in spreads) / len(spreads)
    mean_ba = sum(s.round_trip.quoted_pct_of_credit for s in spreads) / len(spreads)
    mean_all_in = sum(s.round_trip.all_in_pct_of_credit for s in spreads) / len(spreads)
    mean_ret = sum(s.round_trip.retained_fraction for s in spreads) / len(spreads)
    retain_ok = mean_ret >= CREDIT_RETAIN_MIN
    return SpreadScreen(
        n=len(spreads),
        n_expiries=n_expiries,
        mean_credit=mean_credit,
        mean_bid_ask_pct_of_credit=mean_ba,
        mean_all_in_pct_of_credit=mean_all_in,
        mean_retained=mean_ret,
        atm_all_in_high=atm,
        retain_ok=retain_ok,
        sparse=sparse,
        authorize_a1=retain_ok and not sparse,
    )


def load_spreads(spx: list[DailyBar]) -> tuple[list[SpreadQuote], int]:
    expiries = [day for day in list_expirations(ROOT) if is_third_friday(day)]
    start = FREE_START
    expiries = [day for day in expiries if day >= start + timedelta(days=DTE_LOW)]
    return construct_spreads(spx=spx, expiries=expiries), len(expiries)
