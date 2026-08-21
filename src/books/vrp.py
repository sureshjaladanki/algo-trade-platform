"""Book A $0 screen: VIX minus subsequent SPX realized vol, PUTW vs after-tax VTI.

Not A1. A pass is permission to buy CBOE SPX EOD, not a certified book.
"""

from __future__ import annotations

import math
import urllib.error
from dataclasses import dataclass
from datetime import date

from src.costs import WORKING_TABLE, ProductBucket, round_trip_pct_of_premium
from src.harness import Declaration
from src.tax import ORDINARY_DIVIDEND_RATE, SECTION_1256_BLEND
from src.vti import (
    IndexPoint,
    after_tax_vti_series,
    annualized_return,
    calendar_year_returns,
)
from src.yahoo import DailyBar, load_or_fetch

RV_WINDOW = 21
TRADING_DAYS = 252
VRP_SIGMA = 10.0
VRP_HYPOTHESIZED = 4.0
STRESS_YEARS = (2018, 2020, 2024)
SUBPERIODS: tuple[tuple[date, date], ...] = (
    (date(2005, 1, 1), date(2008, 12, 31)),
    (date(2009, 1, 1), date(2012, 12, 31)),
    (date(2013, 1, 1), date(2016, 12, 31)),
    (date(2017, 1, 1), date(2020, 12, 31)),
    (date(2021, 1, 1), date(2026, 12, 31)),
)
SIGN_STABLE_MIN = 4
PUTW_INCEPTION = date(2016, 2, 24)


def screen_declaration(n: int) -> Declaration:
    return Declaration(
        book_id="A",
        spec_id="A.public-vix-rv-putw",
        n=n,
        sigma=VRP_SIGMA,
        hypothesized_effect=VRP_HYPOTHESIZED,
        unit="vol_points_per_month",
    )


def log_return(later: float, earlier: float) -> float:
    return math.log(later / earlier)


def realized_vol_points(closes: list[float]) -> float:
    """Close-to-close RV over the supplied window, annualized in vol points."""
    if len(closes) < 2:
        raise ValueError("need at least two closes")
    rets = [
        log_return(closes[i], closes[i - 1]) for i in range(1, len(closes))
    ]
    mean = sum(rets) / len(rets)
    var = sum((ret - mean) ** 2 for ret in rets) / (len(rets) - 1)
    return math.sqrt(var * TRADING_DAYS) * 100.0


def premium_cost_to_vol_points(pct_of_premium: float, implied_vol: float) -> float:
    """ATM elasticity dP/P ≈ dσ/σ, so % of premium maps to vol points as pct × σ / 100.

    `pct_of_premium` is the costs-module figure (1.0 = 1% of premium).
    `implied_vol` is in vol points (20.0, not 0.20).
    """
    return pct_of_premium / 100.0 * implied_vol


def working_premium_cost(kind: str) -> float:
    spec = WORKING_TABLE[ProductBucket.SPX_ATM_30_45]
    if kind == "mid":
        return round_trip_pct_of_premium(ProductBucket.SPX_ATM_30_45)
    if kind == "high":
        return spec.all_in_high
    raise ValueError(kind)


@dataclass(frozen=True)
class VrpPoint:
    date: date
    vix: float
    realized: float
    raw: float
    net_mid: float
    net_high: float


def vrp_points(vix: list[DailyBar], spx: list[DailyBar]) -> list[VrpPoint]:
    spx_by_date = {bar.date: bar.close for bar in spx}
    spx_days = [bar.date for bar in spx]
    index = {day: i for i, day in enumerate(spx_days)}
    mid_pct = working_premium_cost("mid")
    high_pct = working_premium_cost("high")
    out: list[VrpPoint] = []
    for bar in vix:
        if bar.date not in index:
            continue
        start = index[bar.date]
        stop = start + RV_WINDOW + 1
        if stop > len(spx_days):
            continue
        window = [spx_by_date[day] for day in spx_days[start : stop]]
        realized = realized_vol_points(window)
        raw = bar.close - realized
        out.append(
            VrpPoint(
                date=bar.date,
                vix=bar.close,
                realized=realized,
                raw=raw,
                net_mid=raw - premium_cost_to_vol_points(mid_pct, bar.close),
                net_high=raw - premium_cost_to_vol_points(high_pct, bar.close),
            )
        )
    return out


def nonoverlapping(points: list[VrpPoint], step: int = RV_WINDOW) -> list[VrpPoint]:
    return points[::step]


def mean_vrp(points: list[VrpPoint], *, field: str) -> float:
    if not points:
        raise ValueError("no VRP points")
    return sum(getattr(p, field) for p in points) / len(points)


def subperiod_means(
    points: list[VrpPoint], *, field: str
) -> list[tuple[date, date, float, int]]:
    rows: list[tuple[date, date, float, int]] = []
    for start, stop in SUBPERIODS:
        bucket = [p for p in points if start <= p.date <= stop]
        if not bucket:
            continue
        rows.append((start, stop, mean_vrp(bucket, field=field), len(bucket)))
    return rows


def sign_stable(rows: list[tuple[date, date, float, int]]) -> bool:
    positive = sum(1 for row in rows if row[2] > 0)
    return positive >= SIGN_STABLE_MIN and len(rows) >= SIGN_STABLE_MIN


def year_mean(points: list[VrpPoint], year: int, *, field: str) -> float | None:
    bucket = [p for p in points if p.date.year == year]
    if not bucket:
        return None
    return mean_vrp(bucket, field=field)


def max_drawdown(values: list[float]) -> float:
    peak = values[0]
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1.0)
    return worst


def after_tax_ordinary_series(bars: list[DailyBar]) -> list[IndexPoint]:
    from src.vti import total_return_series

    before = dict(total_return_series(bars, dividend_tax_rate=0.0))
    after = dict(total_return_series(bars, dividend_tax_rate=ORDINARY_DIVIDEND_RATE))
    return [
        IndexPoint(date=bar.date, before_tax=before[bar.date], after_tax=after[bar.date])
        for bar in bars
    ]


def marked_cagr(year_returns: dict[int, float], rate: float) -> float:
    if not year_returns:
        raise ValueError("no year returns")
    growth = 1.0
    for ret in year_returns.values():
        growth *= 1.0 + ret * (1.0 - rate)
    return growth ** (1.0 / len(year_returns)) - 1.0


@dataclass(frozen=True)
class PutwReport:
    start: date
    end: date
    putw_before_tax: float
    putw_after_tax_ordinary: float
    vti_after_tax: float
    diy_1256_marked: float
    tax_wedge_bps: float
    putw_max_dd: float
    put_index_max_dd: float | None
    stress_putw: dict[int, float]
    source: str


def putw_report(
    putw: list[DailyBar],
    vti_points: list[IndexPoint],
    put_index: list[DailyBar] | None = None,
) -> PutwReport:
    overlap_start = max(putw[0].date, PUTW_INCEPTION)
    putw_window = [bar for bar in putw if bar.date >= overlap_start]
    putw_points = after_tax_ordinary_series(putw_window)
    vti_by_date = {p.date: p for p in vti_points}
    aligned_vti = [
        vti_by_date[p.date] for p in putw_points if p.date in vti_by_date
    ]
    aligned_putw = [p for p in putw_points if p.date in vti_by_date]
    if len(aligned_putw) < 2 or len(aligned_vti) < 2:
        raise ValueError("PUTW and VTI do not overlap")
    putw_years = calendar_year_returns(aligned_putw, field="before_tax")
    has_divs = any(bar.dividend for bar in putw_window)
    if has_divs:
        ordinary = annualized_return(aligned_putw, field="after_tax")
    else:
        ordinary = marked_cagr(putw_years, ORDINARY_DIVIDEND_RATE)
    diy = marked_cagr(putw_years, SECTION_1256_BLEND)
    stress: dict[int, float] = {}
    for year in STRESS_YEARS:
        year_pts = [p for p in aligned_putw if p.date.year == year]
        if len(year_pts) < 2:
            continue
        stress[year] = year_pts[-1].before_tax / year_pts[0].before_tax - 1.0
    put_dd = None
    if put_index:
        put_dd = max_drawdown([bar.close for bar in put_index])
    return PutwReport(
        start=aligned_putw[0].date,
        end=aligned_putw[-1].date,
        putw_before_tax=annualized_return(aligned_putw, field="before_tax"),
        putw_after_tax_ordinary=ordinary,
        vti_after_tax=annualized_return(aligned_vti, field="after_tax"),
        diy_1256_marked=diy,
        tax_wedge_bps=1e4 * (diy - ordinary),
        putw_max_dd=max_drawdown([p.before_tax for p in aligned_putw]),
        put_index_max_dd=put_dd,
        stress_putw=stress,
        source="PUTW" if has_divs else "^PUT",
    )


@dataclass(frozen=True)
class VrpScreen:
    n: int
    mean_raw: float
    mean_net_mid: float
    mean_net_high: float
    subperiods_high: list[tuple[date, date, float, int]]
    stress_raw: dict[int, float | None]
    sign_stable_high: bool
    buy_cboe: bool
    putw: PutwReport | None


def run_vrp_screen(
    vix: list[DailyBar],
    spx: list[DailyBar],
    *,
    putw: list[DailyBar] | None = None,
    vti_points: list[IndexPoint] | None = None,
    put_index: list[DailyBar] | None = None,
) -> VrpScreen:
    daily = vrp_points(vix, spx)
    sample = nonoverlapping(daily)
    if not sample:
        raise ValueError("no non-overlapping VRP windows")
    highs = subperiod_means(sample, field="net_high")
    stable = sign_stable(highs)
    mean_high = mean_vrp(sample, field="net_high")
    report = None
    packaged = putw if putw and len(putw) >= 50 else put_index
    if packaged and vti_points:
        try:
            report = putw_report(packaged, vti_points, put_index)
        except ValueError:
            report = None
    return VrpScreen(
        n=len(sample),
        mean_raw=mean_vrp(sample, field="raw"),
        mean_net_mid=mean_vrp(sample, field="net_mid"),
        mean_net_high=mean_high,
        subperiods_high=highs,
        stress_raw={year: year_mean(sample, year, field="raw") for year in STRESS_YEARS},
        sign_stable_high=stable,
        buy_cboe=mean_high > 0 and stable,
        putw=report,
    )


def load_public_inputs() -> tuple[
    list[DailyBar],
    list[DailyBar],
    list[DailyBar],
    list[IndexPoint],
    list[DailyBar],
]:
    vix = load_or_fetch("^VIX")
    spx = load_or_fetch("^GSPC")
    putw = load_or_fetch("PUTW", start=PUTW_INCEPTION)
    vti_bars = load_or_fetch("VTI")
    vti_points = after_tax_vti_series(vti_bars)
    try:
        put_index = load_or_fetch("^PUT")
    except (OSError, urllib.error.URLError, TypeError, KeyError, ValueError):
        put_index = []
    return vix, spx, putw, vti_points, put_index
