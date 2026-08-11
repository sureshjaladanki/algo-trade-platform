"""Tier 2 Horizon ranker metrics — H1/H2/H3/H5 gated; H10 precondition; H4/H6 diagnostic."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from src.horizon.eval.common import (
    H10_NULL_ABS_MAX,
    MIN_NAMES_PER_BAR,
    MIN_SESSIONS,
    MetricResult,
    k_for,
    min_bars_for,
    session_block_mean_ci,
    side_sign,
)
from src.horizon.session import long_entry_ok_expr, short_entry_ok_expr
from src.labels.triple_barrier import ROUND_TRIP_COST
from src.regime.types import DailyRegime, IntradayRegime

_TRADEABLE_DAILY = (
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
)

_SLEEVE = {
    "long": {
        "intraday": IntradayRegime.TREND_UP.value,
        "valid_label": "valid_label_long",
        "entry_ok": long_entry_ok_expr,
        "tb_col": "tb_label_long",
    },
    "short": {
        "intraday": IntradayRegime.TREND_DOWN.value,
        "valid_label": "valid_label_short",
        "entry_ok": short_entry_ok_expr,
        "tb_col": "tb_label_short",
    },
}


def _eligible_expr(direction: str) -> pl.Expr:
    """Same sleeve mask as production predict + MIS-safe label + finite score/y."""
    cfg = _SLEEVE[direction]
    return (
        pl.col("daily_regime").is_in(list(_TRADEABLE_DAILY))
        & (pl.col("intraday_regime") == cfg["intraday"])
        & cfg["entry_ok"]("time_only")
        & pl.col(cfg["valid_label"])
        & pl.col("horizon_score").is_finite()
        & pl.col("fwd_excess_ret").is_finite()
    )


def prepare_eval_panel(scored: pl.DataFrame, direction: str) -> pl.DataFrame:
    """
    Cascade-valid scored rows with eval-only sign convention.

    ``eval_score`` is higher = more actionable for both sleeves (Short flips).
    ``adj_excess`` folds Short's "more negative = better" into the same scale.
    Rank is recomputed descending on ``eval_score`` within each bar (matches
    production Long descending / Short ascending after the flip).
    """
    side = side_sign(direction)
    tb_col = _SLEEVE[direction]["tb_col"]

    base = scored
    if "time_only" not in base.columns:
        base = base.with_columns(time_only=pl.col("date").dt.time())

    panel = (
        base.filter(_eligible_expr(direction))
        .with_columns(
            date_only=pl.col("date").dt.date(),
            time_only=pl.col("date").dt.time(),
            eval_score=pl.col("horizon_score") * side,
            adj_excess=pl.col("fwd_excess_ret") * side,
            tb_label=pl.col(tb_col),
            direction=pl.lit(direction),
        )
        .with_columns(
            eval_rank=pl.col("eval_score")
            .rank(method="ordinal", descending=True)
            .over("date")
        )
    )
    return panel


def _per_bar_ic(panel: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < MIN_NAMES_PER_BAR:
            continue
        ic, _ = spearmanr(
            g["eval_score"].to_numpy(),
            g["adj_excess"].to_numpy(),
        )
        if ic != ic:
            continue
        rows.append(
            {
                "date": bar,
                "date_only": g["date_only"][0],
                "ic": float(ic),
                "n_names": g.height,
            }
        )
    return pl.DataFrame(rows) if rows else pl.DataFrame(
        schema={
            "date": pl.Datetime,
            "date_only": pl.Date,
            "ic": pl.Float64,
            "n_names": pl.Int64,
        }
    )


def _per_bar_topk_stats(panel: pl.DataFrame, k: int) -> pl.DataFrame:
    """Per-bar Top-K vs Rest spreads + TB rates + rank-tier means."""
    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < max(MIN_NAMES_PER_BAR, k + 1):
            continue
        top = g.filter(pl.col("eval_rank") <= k)
        rest = g.filter(pl.col("eval_rank") > k)
        if rest.height == 0:
            continue

        adj_top = float(top["adj_excess"].mean())
        adj_rest = float(rest["adj_excess"].mean())
        spread = adj_top - adj_rest
        cost_spread = (adj_top - ROUND_TRIP_COST) - adj_rest

        r12 = g.filter(pl.col("eval_rank") <= 2)
        r3k = g.filter((pl.col("eval_rank") >= 3) & (pl.col("eval_rank") <= k))
        mean_12 = float(r12["adj_excess"].mean()) if r12.height else float("nan")
        mean_3k = float(r3k["adj_excess"].mean()) if r3k.height else float("nan")

        tb = g.filter(pl.col("tb_label").is_not_null())
        tb_top = tb.filter(pl.col("eval_rank") <= k)
        tb_rest = tb.filter(pl.col("eval_rank") > k)
        p_top = (
            float((tb_top["tb_label"] == 1).mean()) if tb_top.height else float("nan")
        )
        p_rest = (
            float((tb_rest["tb_label"] == 1).mean()) if tb_rest.height else float("nan")
        )
        p_all = float((tb["tb_label"] == 1).mean()) if tb.height else float("nan")

        rows.append(
            {
                "date": bar,
                "date_only": g["date_only"][0],
                "n_names": g.height,
                "spread": spread,
                "cost_spread": cost_spread,
                "mean_12": mean_12,
                "mean_3k": mean_3k,
                "mono_diff": mean_12 - mean_3k,
                "p_tb_top": p_top,
                "p_tb_rest": p_rest,
                "p_tb_all": p_all,
                "h5": p_top - p_rest,
                "n_tb_top": tb_top.height,
                "n_tb_rest": tb_rest.height,
            }
        )
    schema = {
        "date": pl.Datetime,
        "date_only": pl.Date,
        "n_names": pl.Int64,
        "spread": pl.Float64,
        "cost_spread": pl.Float64,
        "mean_12": pl.Float64,
        "mean_3k": pl.Float64,
        "mono_diff": pl.Float64,
        "p_tb_top": pl.Float64,
        "p_tb_rest": pl.Float64,
        "p_tb_all": pl.Float64,
        "h5": pl.Float64,
        "n_tb_top": pl.Int64,
        "n_tb_rest": pl.Int64,
    }
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema=schema)


def universe_parity_precondition(panel: pl.DataFrame, direction: str) -> MetricResult:
    """Binary: panel non-empty under the same sleeve mask as production predict."""
    n_bars = panel.select(pl.col("date").n_unique()).item() if panel.height else 0
    n_sessions = (
        panel.select(pl.col("date_only").n_unique()).item() if panel.height else 0
    )
    ok = panel.height > 0 and n_sessions > 0
    return MetricResult(
        "universe",
        direction,
        float(n_bars),
        None,
        None,
        int(panel.height),
        ok,
        f"sessions={n_sessions} bars={n_bars}",
    )


def h10_null_leakage(
    panel: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """
    Within-bar score shuffle → mean IC ≈ 0.

    FAIL if null IC CI lower bound > 0 (spurious skill) or |point| > H10_NULL_ABS_MAX.
    """
    if panel.height == 0:
        return MetricResult("H10", direction, None, None, None, 0, False, "empty")

    null_ics = []
    sessions = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < MIN_NAMES_PER_BAR:
            continue
        scores = g["eval_score"].to_numpy().copy()
        rng.shuffle(scores)
        ic, _ = spearmanr(scores, g["adj_excess"].to_numpy())
        if ic != ic:
            continue
        null_ics.append(float(ic))
        sessions.append(g["date_only"][0])

    n = len(null_ics)
    if n < MIN_SESSIONS:
        return MetricResult("H10", direction, None, None, None, n, False, "thin")

    values = np.asarray(null_ics, dtype=float)
    # Map sessions to integer ids for bootstrap.
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    ok = (ci_lo <= 0.0) and (abs(point) <= H10_NULL_ABS_MAX)
    return MetricResult(
        "H10",
        direction,
        point,
        ci_lo,
        ci_hi,
        n,
        ok,
        f"|null|<={H10_NULL_ABS_MAX}",
    )


def h1_spearman_ic(
    panel: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """Per-bar cross-sectional Spearman IC; session-block CI LB > 0 gates."""
    ic_df = _per_bar_ic(panel)
    n = ic_df.height
    n_sessions = ic_df.select(pl.col("date_only").n_unique()).item() if n else 0
    min_bars = min_bars_for(direction)

    if n < min_bars or n_sessions < MIN_SESSIONS:
        return MetricResult(
            "H1",
            direction,
            None,
            None,
            None,
            n,
            False,
            f"thin bars={n} sess={n_sessions}",
        )

    values = ic_df["ic"].to_numpy()
    sessions = ic_df["date_only"].to_list()
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    return MetricResult(
        "H1",
        direction,
        point,
        ci_lo,
        ci_hi,
        n,
        ci_lo > 0.0,
        f"sess={n_sessions}",
    )


def h2_topk_spread(
    bar_stats: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """Top-K vs Rest raw adj_excess spread; CI LB > 0 gates."""
    n = bar_stats.height
    n_sessions = (
        bar_stats.select(pl.col("date_only").n_unique()).item() if n else 0
    )
    min_bars = min_bars_for(direction)
    k = k_for(direction)

    if n < min_bars or n_sessions < MIN_SESSIONS:
        return MetricResult(
            "H2",
            direction,
            None,
            None,
            None,
            n,
            False,
            f"thin K={k}",
        )

    values = bar_stats["spread"].to_numpy()
    sessions = bar_stats["date_only"].to_list()
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    return MetricResult(
        "H2",
        direction,
        point,
        ci_lo,
        ci_hi,
        n,
        ci_lo > 0.0,
        f"K={k} sess={n_sessions}",
    )


def h3_rank_monotonicity(
    bar_stats: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """
    Rank 1–2 vs 3–K mean adj_excess.

    FAIL only on significant inversion: CI(diff) entirely below 0.
    """
    finite = bar_stats.filter(pl.col("mono_diff").is_finite())
    n = finite.height
    n_sessions = finite.select(pl.col("date_only").n_unique()).item() if n else 0
    min_bars = min_bars_for(direction)
    k = k_for(direction)

    if n < min_bars or n_sessions < MIN_SESSIONS:
        return MetricResult(
            "H3",
            direction,
            None,
            None,
            None,
            n,
            False,
            f"thin K={k}",
        )

    values = finite["mono_diff"].to_numpy()
    sessions = finite["date_only"].to_list()
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    # Significant inversion ⇒ CI entirely negative.
    inverted = ci_hi < 0.0
    mean_12 = float(finite["mean_12"].mean())
    mean_3k = float(finite["mean_3k"].mean())
    return MetricResult(
        "H3",
        direction,
        point,
        ci_lo,
        ci_hi,
        n,
        not inverted,
        f"m12={mean_12:.4f} m3k={mean_3k:.4f}",
    )


def h4_cost_netted_spread(bar_stats: pl.DataFrame, direction: str) -> MetricResult:
    """Diagnostic companion: Top-K cost-netted vs Rest (flat 30 bps)."""
    n = bar_stats.height
    if n == 0:
        return MetricResult("H4", direction, None, None, None, 0, None, "empty")
    point = float(bar_stats["cost_spread"].mean())
    return MetricResult(
        "H4",
        direction,
        point,
        None,
        None,
        n,
        None,
        f"c={ROUND_TRIP_COST:.4f}",
    )


def h5_stock_tb_bridge(
    bar_stats: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    """StockTB+1 Top-K vs Rest (gated) + Top-K vs sleeve-average (diagnostic)."""
    finite = bar_stats.filter(
        pl.col("h5").is_finite()
        & (pl.col("n_tb_top") > 0)
        & (pl.col("n_tb_rest") > 0)
    )
    n = finite.height
    n_sessions = finite.select(pl.col("date_only").n_unique()).item() if n else 0
    min_bars = min_bars_for(direction)
    k = k_for(direction)
    results: list[MetricResult] = []

    if n < min_bars or n_sessions < MIN_SESSIONS:
        results.append(
            MetricResult(
                "H5",
                direction,
                None,
                None,
                None,
                n,
                False,
                f"thin K={k}",
            )
        )
        return results

    values = finite["h5"].to_numpy()
    sessions = finite["date_only"].to_list()
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    p_top = float(finite["p_tb_top"].mean())
    p_rest = float(finite["p_tb_rest"].mean())
    results.append(
        MetricResult(
            "H5",
            direction,
            point,
            ci_lo,
            ci_hi,
            n,
            ci_lo > 0.0,
            f"p_top={p_top:.3f} p_rest={p_rest:.3f} K={k}",
        )
    )

    # Diagnostic: Top-K vs sleeve-average (Gemini marginal-value framing).
    vs_avg = finite.with_columns(
        h5_avg=pl.col("p_tb_top") - pl.col("p_tb_all")
    )
    avg_vals = vs_avg["h5_avg"].to_numpy()
    avg_point = float(avg_vals.mean())
    p_all = float(finite["p_tb_all"].mean())
    results.append(
        MetricResult(
            "H5avg",
            direction,
            avg_point,
            None,
            None,
            n,
            None,
            f"p_top={p_top:.3f} p_all={p_all:.3f}",
        )
    )
    return results


def h6_coverage(panel: pl.DataFrame, direction: str) -> MetricResult:
    """Eligible-name counts / scarcity diagnostic."""
    if panel.height == 0:
        return MetricResult("H6", direction, None, None, None, 0, None, "empty")
    per_bar = panel.group_by("date").agg(n=pl.len())
    median_n = float(per_bar["n"].median())
    n_sessions = panel.select(pl.col("date_only").n_unique()).item()
    n_bars = per_bar.height
    k = k_for(direction)
    thin = int((per_bar["n"] < 15).sum())
    return MetricResult(
        "H6",
        direction,
        median_n,
        None,
        None,
        int(panel.height),
        None,
        f"sess={n_sessions} bars={n_bars} K={k} thin<15={thin}",
    )


def evaluate_direction(
    scored: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    """Run precondition → H1 → H3 → H2 → H5 (+ diagnostics) for one sleeve."""
    panel = prepare_eval_panel(scored, direction)
    metrics: list[MetricResult] = [
        universe_parity_precondition(panel, direction),
        h10_null_leakage(panel, direction, n_boot, rng),
        h6_coverage(panel, direction),
    ]

    preconds_ok = all(m.gate_pass for m in metrics if m.name in ("universe", "H10"))
    if not preconds_ok or panel.height == 0:
        # Still emit thin FAIL placeholders so the report shows the gated set.
        for name in ("H1", "H3", "H2", "H5"):
            metrics.append(
                MetricResult(
                    name,
                    direction,
                    None,
                    None,
                    None,
                    panel.height,
                    False,
                    "precondition-fail",
                )
            )
        return metrics

    metrics.append(h1_spearman_ic(panel, direction, n_boot, rng))

    bar_stats = _per_bar_topk_stats(panel, k_for(direction))
    metrics.append(h3_rank_monotonicity(bar_stats, direction, n_boot, rng))
    metrics.append(h2_topk_spread(bar_stats, direction, n_boot, rng))
    metrics.append(h4_cost_netted_spread(bar_stats, direction))
    metrics.extend(h5_stock_tb_bridge(bar_stats, direction, n_boot, rng))
    return metrics
