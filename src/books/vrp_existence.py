"""A1: implied-minus-realized in the traded 20–25Δ / 30–45 DTE bucket.

Tape is OptionsDX SPX EOD 2012–2023 plus ThetaData FREE from 2024 (Cboe cart
> $100). IV and delta are reconstructed from bid/ask mid + Yahoo ^GSPC.
Cost is the A0.5 spread round-trip via `costs.vertical_spread_round_trip`,
converted to vol points with spread vega. ATM bucket is the fallback.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from src.books.vrp import (
    premium_cost_to_vol_points,
    realized_vol_points,
    working_premium_cost,
)
from src.books.vrp_spread import (
    DTE_HIGH,
    DTE_LOW,
    SIGN_STABLE_MIN,
    SpreadQuote,
    black_scholes_put_vega,
    entry_date,
    is_monthly_expiry,
    pick_put_spread,
    put_iv_delta,
    spot_on,
    year_fraction,
)
from src.costs import SPX_MULTIPLIER
from src.harness import Declaration
from src.optionsdx import puts_from_panel
from src.theta import OptionQuote
from src.yahoo import DailyBar

A1_START = date(2012, 1, 1)
THETA_TAIL_START = date(2024, 1, 1)
ChainLoader = Callable[[date, date], list[OptionQuote]]
A1_SIGMA = 150.0
A1_HYPOTHESIZED = 116.0
A1_N_PLAN = 175
COST_MULTIPLE = 2.0
STRESS_YEARS = (2018, 2020, 2024)
SUBPERIODS: tuple[tuple[date, date], ...] = (
    (date(2012, 1, 1), date(2014, 5, 31)),
    (date(2014, 6, 1), date(2016, 10, 31)),
    (date(2016, 11, 1), date(2019, 3, 31)),
    (date(2019, 4, 1), date(2021, 8, 31)),
    (date(2021, 9, 1), date(2026, 12, 31)),
)
DELTA_BINS: tuple[tuple[str, float, float, float], ...] = (
    ("10", 0.075, 0.125, 0.10),
    ("15", 0.125, 0.175, 0.15),
    ("20", 0.175, 0.225, 0.20),
    ("25", 0.225, 0.275, 0.25),
    ("30", 0.275, 0.325, 0.30),
)
TENOR_TARGETS: tuple[tuple[str, int, int, int], ...] = (
    ("0", 0, 0, 1),
    ("7", 7, 5, 9),
    ("14", 14, 12, 16),
    ("30", 30, 28, 32),
    ("45", 45, 42, 47),
)
GATE_TENOR = "30-45"


def screen_declaration(n: int = A1_N_PLAN) -> Declaration:
    return Declaration(
        book_id="A",
        spec_id="A.spx-put-spread-20-25d-30-45dte",
        n=n,
        sigma=A1_SIGMA,
        hypothesized_effect=A1_HYPOTHESIZED,
        unit="bps_of_sleeve_per_cycle",
    )


def subsequent_rv(
    spx: list[DailyBar], start: date, end: date
) -> float | None:
    closes = [bar.close for bar in spx if start <= bar.date <= end]
    if len(closes) < 2:
        return None
    if len(closes) == 2:
        ret = abs(math.log(closes[1] / closes[0]))
        return ret * math.sqrt(252.0) * 100.0
    return realized_vol_points(closes)


def cost_vol_points(
    spread: SpreadQuote,
    short: OptionQuote,
    long: OptionQuote,
    spot: float,
) -> float | None:
    iv_delta = put_iv_delta(short, spot)
    long_iv = put_iv_delta(long, spot)
    if iv_delta is None or long_iv is None:
        return None
    iv_short, _ = iv_delta
    iv_long, _ = long_iv
    t = year_fraction(spread.trade_date, spread.expiry)
    vega = (
        black_scholes_put_vega(spot, short.strike, t, vol=iv_short)
        - black_scholes_put_vega(spot, long.strike, t, vol=iv_long)
    ) / 100.0
    if vega <= 1e-6:
        return None
    return (spread.round_trip.all_in_usd / SPX_MULTIPLIER) / vega


def atm_cost_vol_points(implied: float) -> float:
    return premium_cost_to_vol_points(working_premium_cost("high"), implied)


@dataclass(frozen=True)
class VrpObs:
    trade_date: date
    expiry: date
    dte: int
    delta_bucket: str
    tenor: str
    implied: float
    realized: float
    raw: float
    cost_vol: float
    net: float
    used_spread_cost: bool


def _obs(
    *,
    trade_date: date,
    expiry: date,
    dte: int,
    delta_bucket: str,
    tenor: str,
    implied: float,
    realized: float,
    cost_vol: float,
    used_spread_cost: bool,
) -> VrpObs:
    raw = implied - realized
    return VrpObs(
        trade_date=trade_date,
        expiry=expiry,
        dte=dte,
        delta_bucket=delta_bucket,
        tenor=tenor,
        implied=implied,
        realized=realized,
        raw=raw,
        cost_vol=cost_vol,
        net=raw - cost_vol,
        used_spread_cost=used_spread_cost,
    )


def one_per_month(days: list[date]) -> list[date]:
    rank = {4: 0, 5: 1, 3: 2}
    by_month: dict[tuple[int, int], date] = {}
    for day in days:
        if day.weekday() not in rank:
            continue
        key = (day.year, day.month)
        prior = by_month.get(key)
        if prior is None:
            by_month[key] = day
            continue
        better = (rank[day.weekday()], abs(day.day - 17)) < (
            rank[prior.weekday()],
            abs(prior.day - 17),
        )
        if better:
            by_month[key] = day
    return sorted(by_month.values())


def monthly_expiries(panel) -> list[date]:
    days = [
        day
        for day in panel["expire_date"].unique().to_list()
        if is_monthly_expiry(day) and day >= A1_START
    ]
    return one_per_month(days)


def theta_monthly_expiries(
    expiries: list[date], *, last_bar: date | None = None
) -> list[date]:
    days = [
        day for day in expiries if is_monthly_expiry(day) and day >= THETA_TAIL_START
    ]
    if last_bar is not None:
        days = [day for day in days if day <= last_bar]
    return one_per_month(days)


def quote_dates(panel) -> list[date]:
    return sorted(panel["quote_date"].unique().to_list())


def tenor_entry(
    expiry: date, days: list[date], *, lo: int, hi: int, target: int
) -> date | None:
    return entry_date(expiry, days, start=A1_START, lo=lo, hi=hi, target=target)


def gate_from_chain(
    *,
    chain: list[OptionQuote],
    spx: list[DailyBar],
    expiry: date,
    trade: date,
) -> VrpObs | None:
    spot = spot_on(spx, trade)
    if spot is None:
        return None
    spread = pick_put_spread(chain, spot)
    if spread is None:
        return None
    by_strike = {quote.strike: quote for quote in chain}
    short = by_strike.get(spread.short_strike)
    long = by_strike.get(spread.long_strike)
    if short is None or long is None:
        return None
    solved = put_iv_delta(short, spot)
    if solved is None:
        return None
    iv, _ = solved
    implied = iv * 100.0
    realized = subsequent_rv(spx, trade, expiry)
    if realized is None:
        return None
    cost = cost_vol_points(spread, short, long, spot)
    used_spread = cost is not None
    if cost is None:
        cost = atm_cost_vol_points(implied)
    return _obs(
        trade_date=trade,
        expiry=expiry,
        dte=spread.dte,
        delta_bucket="20-25",
        tenor=GATE_TENOR,
        implied=implied,
        realized=realized,
        cost_vol=cost,
        used_spread_cost=used_spread,
    )


def gate_observation(
    *,
    panel,
    spx: list[DailyBar],
    expiry: date,
    days: list[date],
) -> VrpObs | None:
    trade = tenor_entry(expiry, days, lo=DTE_LOW, hi=DTE_HIGH, target=37)
    if trade is None:
        return None
    chain = puts_from_panel(panel, expiry=expiry, trade_date=trade)
    return gate_from_chain(chain=chain, spx=spx, expiry=expiry, trade=trade)


def collect_observations(panel, spx: list[DailyBar]) -> tuple[list[VrpObs], list[VrpObs]]:
    days = quote_dates(panel)
    expiries = [day for day in monthly_expiries(panel) if day < THETA_TAIL_START]
    gate: list[VrpObs] = []
    grid: list[VrpObs] = []
    for i, expiry in enumerate(expiries, start=1):
        row = gate_observation(panel=panel, spx=spx, expiry=expiry, days=days)
        if row is not None:
            gate.append(row)
        if i % 12 == 0 or i == len(expiries):
            print(f"A1 expiries {i}/{len(expiries)} gate={len(gate)}", flush=True)
        for tenor, target_dte, dte_lo, dte_hi in TENOR_TARGETS:
            trade = tenor_entry(
                expiry, days, lo=dte_lo, hi=dte_hi, target=target_dte
            )
            if trade is None:
                continue
            spot = spot_on(spx, trade)
            if spot is None:
                continue
            chain = puts_from_panel(panel, expiry=expiry, trade_date=trade)
            solved: list[tuple[OptionQuote, float, float]] = []
            for quote in chain:
                pair = put_iv_delta(quote, spot)
                if pair is None:
                    continue
                vol, delta = pair
                solved.append((quote, vol, delta))
            realized = subsequent_rv(spx, trade, expiry)
            if realized is None:
                continue
            dte = (expiry - trade).days
            for bucket, lo, hi, target in DELTA_BINS:
                scored = [
                    (abs(abs(delta) - target), quote, vol, delta)
                    for quote, vol, delta in solved
                    if lo <= abs(delta) < hi
                ]
                if not scored:
                    continue
                scored.sort(key=lambda item: (item[0], item[1].strike))
                _, quote, vol, _ = scored[0]
                implied = vol * 100.0
                grid.append(
                    _obs(
                        trade_date=trade,
                        expiry=expiry,
                        dte=dte,
                        delta_bucket=bucket,
                        tenor=tenor,
                        implied=implied,
                        realized=realized,
                        cost_vol=atm_cost_vol_points(implied),
                        used_spread_cost=False,
                    )
                )
    return gate, grid


def _grid_from_chain(
    *,
    chain: list[OptionQuote],
    spx: list[DailyBar],
    expiry: date,
    trade: date,
    tenor: str,
) -> list[VrpObs]:
    spot = spot_on(spx, trade)
    if spot is None:
        return []
    realized = subsequent_rv(spx, trade, expiry)
    if realized is None:
        return []
    solved: list[tuple[OptionQuote, float, float]] = []
    for quote in chain:
        pair = put_iv_delta(quote, spot)
        if pair is None:
            continue
        vol, delta = pair
        solved.append((quote, vol, delta))
    dte = (expiry - trade).days
    out: list[VrpObs] = []
    for bucket, lo, hi, target in DELTA_BINS:
        scored = [
            (abs(abs(delta) - target), quote, vol, delta)
            for quote, vol, delta in solved
            if lo <= abs(delta) < hi
        ]
        if not scored:
            continue
        scored.sort(key=lambda item: (item[0], item[1].strike))
        _, quote, vol, _ = scored[0]
        implied = vol * 100.0
        out.append(
            _obs(
                trade_date=trade,
                expiry=expiry,
                dte=dte,
                delta_bucket=bucket,
                tenor=tenor,
                implied=implied,
                realized=realized,
                cost_vol=atm_cost_vol_points(implied),
                used_spread_cost=False,
            )
        )
    return out


def collect_theta_tail(
    spx: list[DailyBar],
    *,
    expiries: list[date],
    chain_loader: ChainLoader,
    include_grid: bool = False,
) -> tuple[list[VrpObs], list[VrpObs]]:
    """2024–present monthlies from ThetaData FREE. Completes 2012–present, not a new spec."""
    days = [bar.date for bar in spx]
    last_bar = days[-1] if days else None
    monthlies = theta_monthly_expiries(expiries, last_bar=last_bar)
    gate: list[VrpObs] = []
    grid: list[VrpObs] = []
    for i, expiry in enumerate(monthlies, start=1):
        trade = tenor_entry(expiry, days, lo=DTE_LOW, hi=DTE_HIGH, target=37)
        if trade is not None:
            chain = chain_loader(expiry, trade)
            row = gate_from_chain(chain=chain, spx=spx, expiry=expiry, trade=trade)
            if row is not None:
                gate.append(row)
        if i % 6 == 0 or i == len(monthlies):
            print(f"A1 theta tail {i}/{len(monthlies)} gate={len(gate)}", flush=True)
        if not include_grid:
            continue
        for tenor, target_dte, dte_lo, dte_hi in TENOR_TARGETS:
            trade = tenor_entry(expiry, days, lo=dte_lo, hi=dte_hi, target=target_dte)
            if trade is None:
                continue
            chain = chain_loader(expiry, trade)
            grid.extend(
                _grid_from_chain(
                    chain=chain, spx=spx, expiry=expiry, trade=trade, tenor=tenor
                )
            )
    return gate, grid


def mean_field(rows: list[VrpObs], field: str) -> float:
    if not rows:
        raise ValueError("no observations")
    return sum(getattr(row, field) for row in rows) / len(rows)


def subperiod_means(rows: list[VrpObs], *, field: str) -> list[tuple[date, date, float, int]]:
    out: list[tuple[date, date, float, int]] = []
    for start, stop in SUBPERIODS:
        bucket = [row for row in rows if start <= row.trade_date <= stop]
        if not bucket:
            continue
        out.append((start, stop, mean_field(bucket, field), len(bucket)))
    return out


def sign_stable(rows: list[tuple[date, date, float, int]]) -> bool:
    positive = sum(1 for row in rows if row[2] > 0)
    return positive >= SIGN_STABLE_MIN and len(rows) >= SIGN_STABLE_MIN


def year_mean(rows: list[VrpObs], year: int, *, field: str) -> float | None:
    bucket = [row for row in rows if row.trade_date.year == year]
    if not bucket:
        return None
    return mean_field(bucket, field)


def grid_means(grid: list[VrpObs]) -> list[tuple[str, str, float, int]]:
    keys = {(row.delta_bucket, row.tenor) for row in grid}
    out: list[tuple[str, str, float, int]] = []
    for bucket, tenor in sorted(keys, key=lambda key: (int(key[1]), int(key[0]))):
        cell = [row for row in grid if row.delta_bucket == bucket and row.tenor == tenor]
        out.append((bucket, tenor, mean_field(cell, "raw"), len(cell)))
    return out


@dataclass(frozen=True)
class ExistenceScreen:
    n: int
    n_expiries: int
    mean_raw: float
    mean_cost: float
    mean_net: float
    multiple: float
    n_spread_cost: int
    subperiods_net: list[tuple[date, date, float, int]]
    stress_raw: dict[int, float | None]
    sign_stable_net: bool
    exceed_2x: bool
    passed: bool
    grid: list[tuple[str, str, float, int]]
    first: date | None
    last: date | None


def run_existence_screen(
    gate: list[VrpObs],
    grid: list[VrpObs],
    *,
    n_expiries: int,
) -> ExistenceScreen:
    if not gate:
        return ExistenceScreen(
            n=0,
            n_expiries=n_expiries,
            mean_raw=0.0,
            mean_cost=0.0,
            mean_net=0.0,
            multiple=0.0,
            n_spread_cost=0,
            subperiods_net=[],
            stress_raw={year: None for year in STRESS_YEARS},
            sign_stable_net=False,
            exceed_2x=False,
            passed=False,
            grid=grid_means(grid) if grid else [],
            first=None,
            last=None,
        )
    mean_raw = mean_field(gate, "raw")
    mean_cost = mean_field(gate, "cost_vol")
    mean_net = mean_field(gate, "net")
    multiple = mean_raw / mean_cost if mean_cost > 0 else 0.0
    subs = subperiod_means(gate, field="net")
    stable = sign_stable(subs)
    exceed = multiple >= COST_MULTIPLE
    return ExistenceScreen(
        n=len(gate),
        n_expiries=n_expiries,
        mean_raw=mean_raw,
        mean_cost=mean_cost,
        mean_net=mean_net,
        multiple=multiple,
        n_spread_cost=sum(1 for row in gate if row.used_spread_cost),
        subperiods_net=subs,
        stress_raw={year: year_mean(gate, year, field="raw") for year in STRESS_YEARS},
        sign_stable_net=stable,
        exceed_2x=exceed,
        passed=exceed and stable,
        grid=grid_means(grid),
        first=gate[0].trade_date,
        last=gate[-1].trade_date,
    )
