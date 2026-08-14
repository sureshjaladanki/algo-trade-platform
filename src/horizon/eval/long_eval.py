"""Long-sleeve Horizon eval — L1 rank-3 floor + L2 emission-threshold report-first."""

from __future__ import annotations

import numpy as np
import polars as pl

from src.horizon.eval.constants import APPLY_L1_LONG, MetricResult, k_for
from src.labels.triple_barrier import ROUND_TRIP_COST

# Report-first L2 floor: emit Top-K only when mean Top-K score ≥ 1× round-trip cost.
L2_SCORE_FLOOR = ROUND_TRIP_COST


def apply_l1_rank3_floor(panel: pl.DataFrame) -> pl.DataFrame:
    """
    Pre-registered L1: set ranks 1–2 eval_score to the rank-3 score, then re-rank.

    Bars with fewer than 3 names are left unchanged.
    """
    rank3 = (
        panel.filter(pl.col("eval_rank") == 3)
        .select("date", pl.col("eval_score").alias("_rank3_score"))
    )
    return (
        panel.join(rank3, on="date", how="left")
        .with_columns(
            eval_score=pl.when(
                pl.col("_rank3_score").is_not_null() & (pl.col("eval_rank") <= 2)
            )
            .then(pl.col("_rank3_score"))
            .otherwise(pl.col("eval_score"))
        )
        .drop("_rank3_score")
        .with_columns(
            eval_rank=pl.col("eval_score")
            .rank(method="ordinal", descending=True)
            .over("date")
        )
    )


def l1_activation_note(direction: str, panel: pl.DataFrame) -> MetricResult:
    """Report whether L1 Long rank-3 floor is active."""
    if direction != "long":
        return MetricResult("L1", direction, None, None, None, panel.height, None, "n/a")
    if not APPLY_L1_LONG:
        return MetricResult(
            "L1", direction, 0.0, None, None, panel.height, None, "off"
        )
    return MetricResult(
        "L1",
        direction,
        1.0,
        None,
        None,
        panel.height,
        None,
        "on rank1-2←rank3_score",
    )


def l2_emission_diagnostics(panel: pl.DataFrame, direction: str) -> list[MetricResult]:
    """
    L2 report-first: Top-K score floor (~1×c) coverage + point H2/H5 on keep vs drop bars.

    Does not change gated K or emit a hard filter. Chartered A+B only if later approved.
    """
    if direction != "long":
        return [
            MetricResult("L2cov", direction, None, None, None, panel.height, None, "n/a")
        ]
    if panel.height == 0:
        return [
            MetricResult("L2cov", direction, None, None, None, 0, None, "empty"),
        ]

    from src.horizon.eval.bar_stats import per_bar_ic, per_bar_topk_stats

    k = k_for(direction)
    per_bar = (
        panel.group_by("date", maintain_order=True)
        .agg(
            date_only=pl.col("date_only").first(),
            topk_mean=pl.col("eval_score")
            .filter(pl.col("eval_rank") <= k)
            .mean(),
            score_k=pl.col("eval_score").filter(pl.col("eval_rank") == k).first(),
            score_k1=pl.col("eval_score")
            .filter(pl.col("eval_rank") == (k + 1))
            .first(),
            n=pl.len(),
        )
        .with_columns(
            gap_k=pl.col("score_k") - pl.col("score_k1"),
            keep=pl.col("topk_mean") >= L2_SCORE_FLOOR,
        )
    )
    n_bars = per_bar.height
    n_keep = int(per_bar.filter(pl.col("keep")).height) if n_bars else 0
    pct_keep = n_keep / n_bars if n_bars else 0.0
    gap_vals = per_bar["gap_k"].drop_nulls()
    gap = float(gap_vals.mean()) if gap_vals.len() else None
    results: list[MetricResult] = [
        MetricResult(
            "L2cov",
            direction,
            pct_keep,
            None,
            None,
            n_bars,
            None,
            f"floor={L2_SCORE_FLOOR:.4f} keep_bars={n_keep}/{n_bars} report-first",
        ),
        MetricResult(
            "L2gap",
            direction,
            gap,
            None,
            None,
            n_bars,
            None,
            f"mean(score_K-score_K+1) K={k}",
        ),
    ]

    keep_dates = per_bar.filter(pl.col("keep"))["date"]
    drop_dates = per_bar.filter(~pl.col("keep"))["date"]
    keep_panel = panel.filter(pl.col("date").is_in(keep_dates))
    drop_panel = panel.filter(pl.col("date").is_in(drop_dates))

    for slice_name, sub in (("keep", keep_panel), ("drop", drop_panel)):
        if sub.height == 0:
            for name in ("L2h1", "L2h2", "L2h5"):
                results.append(
                    MetricResult(
                        name,
                        direction,
                        None,
                        None,
                        None,
                        0,
                        None,
                        f"slice={slice_name} empty",
                    )
                )
            continue
        ic_df = per_bar_ic(sub)
        h1 = float(ic_df["ic"].mean()) if ic_df.height else None
        bar_stats = per_bar_topk_stats(sub, k)
        h2 = float(bar_stats["spread"].mean()) if bar_stats.height else None
        finite_h5 = bar_stats.filter(
            pl.col("h5").is_finite()
            & (pl.col("n_tb_top") > 0)
            & (pl.col("n_tb_rest") > 0)
        )
        h5 = float(finite_h5["h5"].mean()) if finite_h5.height else None
        p_top = (
            float(finite_h5["p_tb_top"].mean()) if finite_h5.height else float("nan")
        )
        note = f"slice={slice_name}"
        if finite_h5.height and np.isfinite(p_top):
            note = f"slice={slice_name} p_top={p_top:.3f}"
        results.append(
            MetricResult("L2h1", direction, h1, None, None, ic_df.height, None, note)
        )
        results.append(
            MetricResult(
                "L2h2", direction, h2, None, None, bar_stats.height, None, note
            )
        )
        results.append(
            MetricResult(
                "L2h5", direction, h5, None, None, finite_h5.height, None, note
            )
        )
    return results
