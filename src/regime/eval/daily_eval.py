"""Daily Regime eval — D1 occupancy, D2 opportunity separation, D5 leakage audit."""

from __future__ import annotations

import numpy as np
import polars as pl

from src.horizon.session import LONG_LAST_ENTRY, SHORT_LAST_ENTRY
from src.labels.triple_barrier import ROUND_TRIP_COST
from src.regime.eval.common import (
    D2_ORDER,
    H_BARS,
    MIN_SESSIONS,
    MetricResult,
    TRADEABLE_DAILY,
)
from src.regime.intraday import NSE_OPEN_BLEED_BAR
from src.regime.types import DailyRegime

DAILY_FEATURE_COLS = (
    "market_trend",
    "vol_regime_ratio",
    "vol_regime_delta",
    "shock",
    "breadth_div",
)


def build_ew_basket_15m(stock_frames: list[pl.DataFrame]) -> pl.DataFrame:
    """Equal-weight close basket from per-symbol 15m frames (PIT by availability)."""
    closes = pl.concat(
        [df.select(["date", "close"]).with_columns(pl.lit(i).alias("_id"))
         for i, df in enumerate(stock_frames)]
    )
    return (
        closes.group_by("date")
        .agg(close=pl.col("close").mean())
        .sort("date")
        .with_columns(open=pl.col("close"), high=pl.col("close"), low=pl.col("close"))
        .select(["date", "open", "high", "low", "close"])
    )


def d5_leakage_audit(daily_features: pl.DataFrame) -> MetricResult:
    """Pre-open feature coverage audit (structural precondition)."""
    n = daily_features.height
    coverage = {
        c: float(daily_features[c].is_not_null().mean()) for c in DAILY_FEATURE_COLS
    }
    ok = min(coverage.values()) >= 0.90
    note = ", ".join(f"{k}={v:.0%}" for k, v in coverage.items())
    return MetricResult("D5", "-", float(ok), None, None, n, ok, note)


def d1_occupancy(daily_classified: pl.DataFrame) -> list[MetricResult]:
    counts = {
        row["daily_regime"]: row["len"]
        for row in daily_classified.group_by("daily_regime").len().iter_rows(named=True)
    }
    total = daily_classified.height
    out = []
    for state in (*D2_ORDER, DailyRegime.NO_TRADE.value):
        n = counts.get(state, 0)
        pct = n / total
        out.append(MetricResult("D1", state, pct, None, None, n, None, f"{pct:.1%}"))
    open_pct = sum(counts.get(s, 0) for s in TRADEABLE_DAILY) / total
    out.append(
        MetricResult("D1", "SUPPORTIVE+AMBIGUOUS", open_pct, None, None, total, None, "coverage")
    )
    return out


def _day_opportunity(closes: np.ndarray, times: list, side: int, last_entry) -> float:
    """Best cost-netted directional window in a session (H<=4, MIS entry cutoff)."""
    best = 0.0
    n = len(closes)
    for i in range(n):
        if times[i] == NSE_OPEN_BLEED_BAR or times[i] > last_entry:
            continue
        entry = closes[i]
        for j in range(i + 1, min(n, i + H_BARS + 1)):
            ret = side * (closes[j] / entry - 1.0) - ROUND_TRIP_COST
            if ret > best:
                best = ret
    return best


def d2_opportunity_separation(
    daily_classified: pl.DataFrame,
    price_15m: pl.DataFrame,
    series_name: str,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    """
    Mean OpportunityScore by DailyRegime x side.

    NO_TRADE reported only (not gated). Gate: S >= A >= H and CI(S-H) LB > 0.
    """
    daily = daily_classified.select(
        pl.col("date").cast(pl.Date).alias("date_only"),
        "daily_regime",
    )
    bars = (
        price_15m.sort("date")
        .with_columns(
            date_only=pl.col("date").dt.date(),
            time_only=pl.col("date").dt.time(),
        )
        .join(daily, on="date_only", how="inner")
    )

    results: list[MetricResult] = []
    for side_name, side, last_entry in (
        ("long", 1, LONG_LAST_ENTRY),
        ("short", -1, SHORT_LAST_ENTRY),
    ):
        rows = [
            {
                "date_only": day,
                "daily_regime": regime,
                "score": _day_opportunity(
                    day_df["close"].to_numpy(),
                    day_df["time_only"].to_list(),
                    side,
                    last_entry,
                ),
            }
            for (day, regime), day_df in bars.group_by(["date_only", "daily_regime"])
        ]
        day_scores = pl.DataFrame(rows)

        means: dict[str, float] = {}
        ns: dict[str, int] = {}
        for state in (*D2_ORDER, DailyRegime.NO_TRADE.value):
            cell = day_scores.filter(pl.col("daily_regime") == state)["score"].to_numpy()
            means[state] = float(cell.mean()) if cell.size else float("nan")
            ns[state] = int(cell.size)
            results.append(
                MetricResult(
                    f"D2[{series_name}]",
                    f"{side_name}/{state}",
                    means[state] if cell.size else None,
                    None,
                    None,
                    ns[state],
                    None,
                    "" if ns[state] >= MIN_SESSIONS else "thin",
                )
            )

        s_vals = day_scores.filter(pl.col("daily_regime") == D2_ORDER[0])["score"].to_numpy()
        a_vals = day_scores.filter(pl.col("daily_regime") == D2_ORDER[1])["score"].to_numpy()
        h_vals = day_scores.filter(pl.col("daily_regime") == D2_ORDER[2])["score"].to_numpy()
        powered = min(s_vals.size, a_vals.size, h_vals.size) >= MIN_SESSIONS
        mono = means[D2_ORDER[0]] >= means[D2_ORDER[1]] >= means[D2_ORDER[2]]
        sep = float(means[D2_ORDER[0]] - means[D2_ORDER[2]])

        if powered:
            n_pair = min(s_vals.size, h_vals.size)
            diffs = np.array(
                [
                    rng.choice(s_vals, size=n_pair, replace=True).mean()
                    - rng.choice(h_vals, size=n_pair, replace=True).mean()
                    for _ in range(n_boot)
                ]
            )
            ci_lo, ci_hi = float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))
            gate = mono and ci_lo > 0.0
        else:
            ci_lo = ci_hi = float("nan")
            gate = False

        results.append(
            MetricResult(
                f"D2[{series_name}]",
                f"{side_name}/S-H",
                sep,
                ci_lo,
                ci_hi,
                int(min(ns[D2_ORDER[0]], ns[D2_ORDER[2]])),
                gate,
                f"mono={mono}",
            )
        )
    return results


def evaluate_daily(
    daily_features: pl.DataFrame,
    daily_classified: pl.DataFrame,
    market_15m: pl.DataFrame,
    basket_15m: pl.DataFrame | None,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    metrics = [d5_leakage_audit(daily_features)]
    metrics.extend(d1_occupancy(daily_classified))
    metrics.extend(
        d2_opportunity_separation(daily_classified, market_15m, "index", n_boot, rng)
    )
    if basket_15m is not None:
        metrics.extend(
            d2_opportunity_separation(daily_classified, basket_15m, "ew100", n_boot, rng)
        )
    return metrics
