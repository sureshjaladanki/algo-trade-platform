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
    "trend_strength",
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


def _session_side_scores(
    daily_classified: pl.DataFrame,
    price_15m: pl.DataFrame,
    side: int,
    last_entry,
    extra_daily_cols: tuple[str, ...] = (),
) -> pl.DataFrame:
    """One row per session: daily_regime, optional daily cols, OpportunityScore."""
    daily_cols = ["daily_regime", *extra_daily_cols]
    daily = daily_classified.select(
        pl.col("date").cast(pl.Date).alias("date_only"),
        *daily_cols,
    )
    bars = (
        price_15m.sort("date")
        .with_columns(
            date_only=pl.col("date").dt.date(),
            time_only=pl.col("date").dt.time(),
        )
        .join(daily, on="date_only", how="inner")
    )
    rows = []
    for key, day_df in bars.group_by(["date_only", *daily_cols]):
        # group_by key is a tuple when multiple columns
        if not isinstance(key, tuple):
            key = (key,)
        date_only, regime, *extras = key
        row = {
            "date_only": date_only,
            "daily_regime": regime,
            "score": _day_opportunity(
                day_df["close"].to_numpy(),
                day_df["time_only"].to_list(),
                side,
                last_entry,
            ),
        }
        for col, val in zip(extra_daily_cols, extras):
            row[col] = val
        rows.append(row)
    return pl.DataFrame(rows)


def _boot_mean_diff(
    a: np.ndarray,
    b: np.ndarray,
    n_boot: int,
    rng: np.random.Generator,
) -> tuple[float, float, float]:
    """Point mean(a)-mean(b) and 95% session-bootstrap CI."""
    n_pair = min(a.size, b.size)
    point = float(a.mean() - b.mean())
    diffs = np.array(
        [
            rng.choice(a, size=n_pair, replace=True).mean()
            - rng.choice(b, size=n_pair, replace=True).mean()
            for _ in range(n_boot)
        ]
    )
    return point, float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))


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
    results: list[MetricResult] = []
    for side_name, side, last_entry in (
        ("long", 1, LONG_LAST_ENTRY),
        ("short", -1, SHORT_LAST_ENTRY),
    ):
        day_scores = _session_side_scores(daily_classified, price_15m, side, last_entry)

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

        if powered:
            sep, ci_lo, ci_hi = _boot_mean_diff(s_vals, h_vals, n_boot, rng)
            gate = mono and ci_lo > 0.0
        else:
            sep = float(means[D2_ORDER[0]] - means[D2_ORDER[2]])
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


def o3_side_trend_diagnostic(
    daily_classified: pl.DataFrame,
    price_15m: pl.DataFrame,
    series_name: str,
    n_boot: int,
    rng: np.random.Generator,
    market_trend_threshold: float = 0.0,
) -> list[MetricResult]:
    """
    O3 diagnostic only — no runtime gate.

    Across all sessions (O1 Daily labels in place), does market_trend sign
    separate side opportunity?
      long  aligned = market_trend >= thr;  Δ = aligned − misaligned
      short aligned = market_trend <= thr;  Δ = aligned − misaligned

    Uses all sessions (not S+A only): tradeable-only is underpowered because
    SUPPORTIVE already requires market_trend >= 0, so trend- cells go thin.

    CI LB > 0 is evidence to consider a later hard gate + contract re-lock,
    not a ship gate by itself.
    """
    results: list[MetricResult] = []

    for side_name, side, last_entry, aligned_ge in (
        ("long", 1, LONG_LAST_ENTRY, True),
        ("short", -1, SHORT_LAST_ENTRY, False),
    ):
        day_scores = _session_side_scores(
            daily_classified,
            price_15m,
            side,
            last_entry,
            extra_daily_cols=("market_trend",),
        )
        trend = pl.col("market_trend")
        if aligned_ge:
            aligned = day_scores.filter(trend >= market_trend_threshold)["score"].to_numpy()
            misaligned = day_scores.filter(trend < market_trend_threshold)["score"].to_numpy()
            a_label, m_label = "trend+", "trend-"
        else:
            aligned = day_scores.filter(trend <= market_trend_threshold)["score"].to_numpy()
            misaligned = day_scores.filter(trend > market_trend_threshold)["score"].to_numpy()
            a_label, m_label = "trend-", "trend+"

        for label, cell in ((a_label, aligned), (m_label, misaligned)):
            results.append(
                MetricResult(
                    f"O3[{series_name}]",
                    f"{side_name}/{label}",
                    float(cell.mean()) if cell.size else None,
                    None,
                    None,
                    int(cell.size),
                    None,
                    "diagnostic" if cell.size >= MIN_SESSIONS else "diagnostic;thin",
                )
            )

        powered = min(aligned.size, misaligned.size) >= MIN_SESSIONS
        if powered:
            sep, ci_lo, ci_hi = _boot_mean_diff(aligned, misaligned, n_boot, rng)
            # Informational only — PASS means CI+ evidence, not a merge lock.
            evidence = ci_lo > 0.0
        else:
            sep = (
                float(aligned.mean() - misaligned.mean())
                if aligned.size and misaligned.size
                else float("nan")
            )
            ci_lo = ci_hi = float("nan")
            evidence = False

        results.append(
            MetricResult(
                f"O3[{series_name}]",
                f"{side_name}/aligned-mis",
                sep,
                ci_lo,
                ci_hi,
                int(min(aligned.size, misaligned.size)),
                evidence,
                "diagnostic;CI+=>consider hard gate" if powered else "diagnostic;thin",
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
    metrics.extend(
        o3_side_trend_diagnostic(daily_classified, market_15m, "index", n_boot, rng)
    )
    if basket_15m is not None:
        metrics.extend(
            d2_opportunity_separation(daily_classified, basket_15m, "ew100", n_boot, rng)
        )
        metrics.extend(
            o3_side_trend_diagnostic(daily_classified, basket_15m, "ew100", n_boot, rng)
        )
    return metrics
