"""Tier 2 Horizon eval — per-bar IC and Top-K vs Rest aggregates."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from src.horizon.eval.constants import MIN_NAMES_PER_BAR
from src.labels.triple_barrier import ARCHIVE_ROUND_TRIP_COST, ROUND_TRIP_COST


def _mean_or_nan(series: pl.Series) -> float:
    m = series.mean()
    return float(m) if m is not None else float("nan")


def per_bar_ic(panel: pl.DataFrame) -> pl.DataFrame:
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


def per_bar_topk_stats(panel: pl.DataFrame, k: int) -> pl.DataFrame:
    """Per-bar Top-K vs Rest spreads + TB rates + rank-tier means."""
    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < max(MIN_NAMES_PER_BAR, k + 1):
            continue
        top = g.filter(pl.col("eval_rank") <= k)
        rest = g.filter(pl.col("eval_rank") > k)
        if rest.height == 0:
            continue

        adj_top = _mean_or_nan(top["adj_excess"])
        adj_rest = _mean_or_nan(rest["adj_excess"])
        spread = adj_top - adj_rest
        cost_spread = (adj_top - ROUND_TRIP_COST) - adj_rest
        archive_cost_spread = (adj_top - ARCHIVE_ROUND_TRIP_COST) - adj_rest

        r12 = g.filter(pl.col("eval_rank") <= 2)
        r3k = g.filter((pl.col("eval_rank") >= 3) & (pl.col("eval_rank") <= k))
        mean_12 = _mean_or_nan(r12["adj_excess"]) if r12.height else float("nan")
        mean_3k = _mean_or_nan(r3k["adj_excess"]) if r3k.height else float("nan")

        tb = g.filter(pl.col("tb_label").is_not_null())
        tb_top = tb.filter(pl.col("eval_rank") <= k)
        tb_rest = tb.filter(pl.col("eval_rank") > k)
        p_top = (
            _mean_or_nan(tb_top["tb_label"] == 1) if tb_top.height else float("nan")
        )
        p_rest = (
            _mean_or_nan(tb_rest["tb_label"] == 1) if tb_rest.height else float("nan")
        )
        p_all = _mean_or_nan(tb["tb_label"] == 1) if tb.height else float("nan")

        if not (
            np.isfinite(spread)
            and np.isfinite(cost_spread)
            and np.isfinite(archive_cost_spread)
        ):
            continue

        rows.append(
            {
                "date": bar,
                "date_only": g["date_only"][0],
                "n_names": g.height,
                "spread": spread,
                "cost_spread": cost_spread,
                "archive_cost_spread": archive_cost_spread,
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
        "archive_cost_spread": pl.Float64,
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
