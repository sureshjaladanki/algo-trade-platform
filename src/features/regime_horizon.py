"""Regime-derived Horizon features computed after Tier 1 cascade join."""

import polars as pl


def calculate_regime_horizon_features(
    df: pl.DataFrame,
    regime_col: str = "intraday_regime",
    symbol_col: str = "symbol",
    date_col: str = "date_only",
) -> pl.DataFrame:
    """
    Bars since post-hysteresis entry into the current intraday regime episode.

    Reset on each regime change within a symbol-session. First bar of an episode = 0.
    Also emits `regime_episode_id`, the within-session episode counter used for
    episode-level sample weighting (and later LambdaRank grouping).
    """
    ordered = df.sort([symbol_col, date_col, "date"])
    return ordered.with_columns(
        _regime_change=(
            pl.col(regime_col) != pl.col(regime_col).shift(1).over([symbol_col, date_col])
        ).fill_null(True),
    ).with_columns(
        regime_episode_id=pl.col("_regime_change")
        .cum_sum()
        .over([symbol_col, date_col])
        .cast(pl.Int32),
    ).with_columns(
        bars_since_regime_flip=(
            pl.col("date")
            .cum_count()
            .over([symbol_col, date_col, "regime_episode_id"])
            - 1
        ).cast(pl.Int32),
    ).drop("_regime_change")
