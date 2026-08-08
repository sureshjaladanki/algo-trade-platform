"""Horizon-scored decision features for Tier 3 Precision registry."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.horizon.session import (
    MIS_FLAT_BY,
    long_entry_ok_expr,
    short_entry_ok_expr,
)
from src.precision.scores import edge_score_expr
from src.precision.session import HORIZON_MINUTES, TOP_K
from src.regime.types import DailyRegime, IntradayRegime

TRADEABLE_DAILY_REGIMES = [
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
]


def calculate_horizon_precision_features(
    horizon_scored: pl.DataFrame,
    top_k: int = TOP_K,
) -> pl.DataFrame:
    """
    Narrow Horizon scores to the Precision universe (top-K / bottom-K + TB gates).

    Phase 1: ``TOP_K=5`` by default (ablate with ``top_k=8``). Conviction
    (edge ≥ bar×sleeve median) is applied later in ``classify_precision`` so
    skipped names still count in the episode base.

    Expects columns from `predict_horizon_gbm` joined with TB geometry.
    ``date`` / ``decision_bar`` are 15m bar-end stamps (actionable clock).
    """
    required = {
        "symbol",
        "date",
        "horizon_rank",
        "horizon_score",
        "horizon_direction",
        "daily_regime",
        "intraday_regime",
        "close",
        "atr_pct",
        "long_tp_w",
        "long_sl_w",
        "short_tp_w",
        "short_sl_w",
        "tb_eligible_long",
        "tb_eligible_short",
    }
    missing = required - set(horizon_scored.columns)
    if missing:
        raise ValueError(f"horizon_scored missing columns: {sorted(missing)}")

    df = horizon_scored.with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
        decision_bar=pl.col("date"),
        decision_close=pl.col("close"),
    )

    long_mask = (
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_UP.value)
        & (pl.col("horizon_direction") == "long")
        & pl.col("tb_eligible_long")
        & long_entry_ok_expr("time_only")
        & (pl.col("horizon_rank") <= top_k)
    )
    short_mask = (
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_DOWN.value)
        & (pl.col("horizon_direction") == "short")
        & pl.col("tb_eligible_short")
        & short_entry_ok_expr("time_only")
        & (pl.col("horizon_rank") <= top_k)
    )

    # Live MIS flatten is wall-clock MIS_FLAT_BY (~15:00), not decision+H alone.
    mis_deadline = (
        pl.col("decision_bar").dt.truncate("1d")
        + dt.timedelta(
            hours=MIS_FLAT_BY.hour,
            minutes=MIS_FLAT_BY.minute,
        )
    )
    registry = (
        df.filter(long_mask | short_mask)
        .with_columns(
            vertical_deadline=pl.min_horizontal(
                pl.col("decision_bar") + dt.timedelta(minutes=HORIZON_MINUTES),
                mis_deadline,
            ),
        )
        .with_columns(edge_score_expr())
    )
    return registry.sort(["decision_bar", "horizon_direction", "horizon_rank"])
