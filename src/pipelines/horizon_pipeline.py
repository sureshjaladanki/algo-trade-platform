"""Tier 2 Horizon pipeline: features + labels + cascade masks + train / predict."""

from typing import Any, Dict

import polars as pl

from src.features.horizon import calculate_horizon_features
from src.horizon.features_regime import add_bars_since_regime_flip
from src.horizon.horizon_model import (
    LONG_FEATURES,
    SHORT_FEATURES,
    HorizonModel,
    episode_balanced_weights,
    get_purged_cv_splits,
    sleeve_sample_diagnostics,
)
from src.horizon.session import (
    auction_bleed_entry_expr,
    long_entry_ok_expr,
    short_entry_ok_expr,
)
from src.labels.horizon import calculate_horizon_labels
from src.labels.triple_barrier import calculate_triple_barrier_labels
from src.regime.types import DailyRegime, IntradayRegime

TRADEABLE_DAILY_REGIMES = [
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
]


def prepare_horizon_data(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    sector_df: pl.DataFrame | None,
    daily_stock_df: pl.DataFrame,
    daily_nifty_df: pl.DataFrame,
    regime_df: pl.DataFrame,
    daily_regime_features: pl.DataFrame | None = None,
    include_triple_barrier: bool = True,
) -> pl.DataFrame:
    """
    Build horizon features and labels, join Tier 1 regimes, apply entry filters.

    `regime_df` must include post-hysteresis daily_regime and intraday_regime.
    Optional `daily_regime_features` supplies vol_regime_ratio → vix_regime_ratio.
    """
    features_df = calculate_horizon_features(
        stock_df,
        nifty_df,
        sector_df,
        daily_stock_df,
        daily_nifty_df,
        daily_regime_features=daily_regime_features,
    )
    labels_df = calculate_horizon_labels(stock_df, nifty_df, horizon_bars=4)

    df = features_df.join(labels_df, on=["symbol", "datetime"], how="inner")

    regime_cols = ["datetime", "daily_regime", "intraday_regime"]
    if "symbol" in regime_df.columns:
        df = df.join(
            regime_df.select(["symbol", *regime_cols]),
            on=["symbol", "datetime"],
            how="inner",
        )
    else:
        # Index-level Tier 1 regimes broadcast to all names.
        df = df.join(regime_df.select(regime_cols), on="datetime", how="inner")

    df = add_bars_since_regime_flip(df)

    if include_triple_barrier:
        tb_df = calculate_triple_barrier_labels(
            stock_df, nifty_df, daily_stock_df, horizon_bars=4
        )
        df = df.join(tb_df, on=["symbol", "datetime"], how="left")

    # Exclude 09:15 auction-bleed entries (bar-start convention).
    df = df.filter(~auction_bleed_entry_expr("time_only"))
    return df


def train_horizon_models(
    df: pl.DataFrame, cv_kwargs: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Train Long / Short Horizon models on cascade-valid sleeves with purged WF.

    `cv_kwargs` overrides the walk-forward window sizes (see get_purged_cv_splits).
    """
    long_df = df.filter(
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_UP.value)
        & pl.col("valid_label_long")
    )
    short_df = df.filter(
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_DOWN.value)
        & pl.col("valid_label_short")
    )

    long_df = long_df.drop_nulls(subset=LONG_FEATURES + ["fwd_excess_ret"])
    short_df = short_df.drop_nulls(subset=SHORT_FEATURES + ["fwd_excess_ret"])

    results: Dict[str, Any] = {}

    if long_df.height > 0:
        results.update(
            _train_sleeve(
                long_df,
                direction="long",
                features=LONG_FEATURES,
                cv_kwargs=cv_kwargs,
            )
        )

    if short_df.height > 0:
        # Short episodes are scarce: balance at episode level, never by row oversampling.
        results.update(
            _train_sleeve(
                short_df,
                direction="short",
                features=SHORT_FEATURES,
                episode_balanced=True,
                cv_kwargs=cv_kwargs,
            )
        )

    return results


def _train_sleeve(
    sleeve_df: pl.DataFrame,
    direction: str,
    features: list[str],
    episode_balanced: bool = False,
    cv_kwargs: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    diagnostics = sleeve_sample_diagnostics(sleeve_df)
    print(
        f"{direction.capitalize()} sleeve: {diagnostics['bars']} bars, "
        f"{diagnostics['sessions']} sessions, {diagnostics['episodes']} episodes "
        f"(median {diagnostics['median_episode_bars']:.0f} bars/episode)"
    )

    val_ics: list[float] = []
    test_ics: list[float] = []
    models: list[HorizonModel] = []

    for train_df, val_df, test_df in get_purged_cv_splits(sleeve_df, **(cv_kwargs or {})):
        if min(train_df.height, val_df.height, test_df.height) == 0:
            continue
        model = HorizonModel(direction=direction)
        val_ic = model.train(
            X_train=train_df,
            y_train=train_df["fwd_excess_ret"],
            X_val=val_df,
            y_val=val_df["fwd_excess_ret"],
            features=features,
            train_weight=episode_balanced_weights(train_df) if episode_balanced else None,
        )
        test_ic = model.spearman_ic(test_df, test_df["fwd_excess_ret"])
        val_ics.append(val_ic)
        test_ics.append(test_ic)
        models.append(model)

    mean_val = sum(val_ics) / len(val_ics) if val_ics else 0.0
    mean_test = sum(test_ics) / len(test_ics) if test_ics else 0.0
    print(
        f"{direction.capitalize()} Mean Val IC: {mean_val:.4f} | Test IC: {mean_test:.4f}"
    )
    return {
        f"{direction}_models": models,
        f"{direction}_mean_ic": mean_val,
        f"{direction}_mean_test_ic": mean_test,
        f"{direction}_diagnostics": diagnostics,
    }


def predict_horizon(
    df: pl.DataFrame,
    long_model: HorizonModel | None,
    short_model: HorizonModel | None,
) -> pl.DataFrame:
    """
    Score cascade-eligible names each bar; rank Long descending / Short ascending.
    """
    # Inference uses entry cutoffs only (labels need future bars; live scores must not).
    long_mask = (
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_UP.value)
        & long_entry_ok_expr("time_only")
    )
    short_mask = (
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_DOWN.value)
        & short_entry_ok_expr("time_only")
    )

    long_df = df.filter(long_mask)
    short_df = df.filter(short_mask)

    if long_df.height > 0 and long_model is not None:
        long_df = long_df.with_columns(
            horizon_score=pl.Series(long_model.predict(long_df)),
            horizon_direction=pl.lit("long"),
        )
    else:
        long_df = long_df.with_columns(
            horizon_score=pl.lit(None, dtype=pl.Float64),
            horizon_direction=pl.lit(None, dtype=pl.Utf8),
        )

    if short_df.height > 0 and short_model is not None:
        short_df = short_df.with_columns(
            horizon_score=pl.Series(short_model.predict(short_df)),
            horizon_direction=pl.lit("short"),
        )
    else:
        short_df = short_df.with_columns(
            horizon_score=pl.lit(None, dtype=pl.Float64),
            horizon_direction=pl.lit(None, dtype=pl.Utf8),
        )

    scored_df = pl.concat([long_df, short_df], how="diagonal")
    return scored_df.with_columns(
        horizon_rank=pl.when(pl.col("horizon_direction") == "long")
        .then(pl.col("horizon_score").rank(descending=True).over("datetime"))
        .when(pl.col("horizon_direction") == "short")
        .then(pl.col("horizon_score").rank(descending=False).over("datetime"))
        .otherwise(None)
    )
