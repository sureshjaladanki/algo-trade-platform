"""Tier 2 Horizon eval — gated metrics (universe, H10, H1–H3, H5)."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from src.horizon.eval.bar_stats import per_bar_ic
from src.horizon.eval.constants import (
    H10_NULL_ABS_MAX,
    MIN_NAMES_PER_BAR,
    MIN_SESSIONS,
    MetricResult,
    k_for,
    min_bars_for,
    session_block_mean_ci,
)


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
    ic_df = per_bar_ic(panel)
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
