"""Direction-normalized Horizon scores for Precision ranking / diagnostics."""

from __future__ import annotations

import polars as pl


def edge_score_expr(
    score_col: str = "horizon_score",
    direction_col: str = "horizon_direction",
) -> pl.Expr:
    """
    Higher = stronger sleeve conviction.

    Long keeps raw score; Short flips so ascending rank (lowest raw = rank 1)
    also maps to high edge — matching Horizon ``rank_descending`` polarity.
    """
    return (
        pl.when(pl.col(direction_col) == "short")
        .then(-pl.col(score_col))
        .otherwise(pl.col(score_col))
        .alias("edge_score")
    )


def check_rank_edge_polarity(
    df: pl.DataFrame,
    *,
    bar_col: str = "decision_bar",
) -> dict[str, bool | int]:
    """
    Within each ``(bar, direction)`` group, lower rank must have weakly
    higher ``edge_score``. Empty / tiny frames count as OK.
    """
    ok = {
        "rank_polarity_ok": True,
        "rank_polarity_groups": 0,
        "rank_polarity_violations": 0,
    }
    if df.height < 2:
        return ok

    ranked = df.drop_nulls(
        subset=["horizon_rank", "edge_score", "horizon_direction"]
    ).sort([bar_col, "horizon_direction", "horizon_rank"])
    if ranked.height < 2:
        return ok

    keys = [bar_col, "horizon_direction"]
    adjacent = ranked.with_columns(
        prev_rank=pl.col("horizon_rank").shift(1).over(keys),
        prev_edge=pl.col("edge_score").shift(1).over(keys),
    )
    violations = adjacent.filter(
        pl.col("prev_rank").is_not_null()
        & (pl.col("horizon_rank") > pl.col("prev_rank"))
        & (pl.col("edge_score") > pl.col("prev_edge") + 1e-12)
    ).height

    return {
        "rank_polarity_ok": violations == 0,
        "rank_polarity_groups": ranked.select(keys).unique().height,
        "rank_polarity_violations": violations,
    }
