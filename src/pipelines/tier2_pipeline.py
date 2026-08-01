import polars as pl
from typing import Dict, Any
from src.features.tier2 import calculate_tier2_features
from src.labels.horizon import calculate_horizon_labels
from src.models.tier2_trainer import Tier2Model, get_purged_cv_splits
from src.regime.types import DailyRegime, IntradayRegime

TRADEABLE_DAILY_REGIMES = [
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
]

LONG_FEATURES = [
    "rel_ret_15_vs_nifty", "rel_ret_60_vs_nifty", "stock_r_15", "stock_rv_15",
    "stock_volz_15", "stock_vwap_dist", "sector_rel_strength", "dist_to_prev_day_high",
    "orb_breakout_flag", "rolling_beta_60d", "trend_strength_daily", "pct_from_20d_high",
    "adv_rank_20d", "tod_sin", "tod_cos"
]

SHORT_FEATURES = [
    "rel_ret_15_vs_nifty", "rel_ret_60_vs_nifty", "stock_r_15", "stock_rv_15",
    "stock_volz_15", "stock_vwap_dist", "rolling_beta_60d", "trend_strength_daily",
    "adv_rank_20d", "tod_sin", "tod_cos", "sector_rel_weakness", "dist_to_prev_day_low",
    "orb_breakdown_flag", "pct_from_52w_high", "bounce_risk_zscore", "downside_acceleration"
]

def prepare_tier2_data(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    sector_df: pl.DataFrame,
    daily_stock_df: pl.DataFrame,
    daily_nifty_df: pl.DataFrame,
    regime_df: pl.DataFrame  # Contains daily_regime and intraday_regime
) -> pl.DataFrame:
    """
    Builds features, labels, and merges regimes.
    """
    # 1. Features
    features_df = calculate_tier2_features(
        stock_df, nifty_df, sector_df, daily_stock_df, daily_nifty_df
    )
    
    # 2. Labels
    labels_df = calculate_horizon_labels(stock_df, nifty_df, horizon_bars=4)
    
    # 3. Join
    df = features_df.join(labels_df, on=["symbol", "datetime"], how="inner")
    
    # 4. Join Regimes
    df = df.join(
        regime_df.select(["symbol", "datetime", "daily_regime", "intraday_regime"]),
        on=["symbol", "datetime"], how="inner"
    )
    
    # 5. Filter out 9:15-9:30 for entry
    df = df.filter(pl.col("time_only") > pl.time(9, 30))
    
    # Drop rows with null features or labels
    # We only care about rows where valid_label is True
    df = df.filter(pl.col("valid_label"))
    df = df.drop_nulls(subset=LONG_FEATURES + SHORT_FEATURES + ["fwd_excess_ret"])
    
    return df

def train_tier2_models(df: pl.DataFrame) -> Dict[str, Any]:
    """
    Trains Long and Short models using purged walk-forward CV.
    """
    # Filter for Long
    long_df = df.filter(
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES) &
        (pl.col("intraday_regime") == IntradayRegime.TREND_UP.value)
    )
    
    # Filter for Short
    short_df = df.filter(
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES) &
        (pl.col("intraday_regime") == IntradayRegime.TREND_DOWN.value)
    )
    
    results = {}
    
    # Train Long
    if long_df.height > 0:
        print(f"Training Long model on {long_df.height} samples...")
        splits = get_purged_cv_splits(long_df)
        long_ics = []
        long_models = []
        for train_df, val_df in splits:
            if train_df.height == 0 or val_df.height == 0:
                continue
            model = Tier2Model(direction="long")
            ic = model.train(
                X_train=train_df, y_train=train_df["fwd_excess_ret"],
                X_val=val_df, y_val=val_df["fwd_excess_ret"],
                features=LONG_FEATURES
            )
            long_ics.append(ic)
            long_models.append(model)
        
        results["long_models"] = long_models
        results["long_mean_ic"] = sum(long_ics) / len(long_ics) if long_ics else 0.0
        print(f"Long Mean IC: {results['long_mean_ic']:.4f}")
        
    # Train Short
    if short_df.height > 0:
        print(f"Training Short model on {short_df.height} samples...")
        # For short, target is the same (excess return), but more negative is better.
        # LightGBM will just learn to predict the negative return.
        splits = get_purged_cv_splits(short_df)
        short_ics = []
        short_models = []
        for train_df, val_df in splits:
            if train_df.height == 0 or val_df.height == 0:
                continue
            model = Tier2Model(direction="short")
            ic = model.train(
                X_train=train_df, y_train=train_df["fwd_excess_ret"],
                X_val=val_df, y_val=val_df["fwd_excess_ret"],
                features=SHORT_FEATURES
            )
            short_ics.append(ic)
            short_models.append(model)
            
        results["short_models"] = short_models
        results["short_mean_ic"] = sum(short_ics) / len(short_ics) if short_ics else 0.0
        print(f"Short Mean IC: {results['short_mean_ic']:.4f}")
        
    return results

def predict_tier2(df: pl.DataFrame, long_model: Tier2Model, short_model: Tier2Model) -> pl.DataFrame:
    """
    Inference: Score all eligible names each bar -> top-K long / bottom-K short.
    """
    # Score Long
    long_mask = pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES) & (pl.col("intraday_regime") == IntradayRegime.TREND_UP.value)
    
    # Score Short
    short_mask = pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES) & (pl.col("intraday_regime") == IntradayRegime.TREND_DOWN.value)
    
    # We will score them separately
    long_df = df.filter(long_mask)
    short_df = df.filter(short_mask)
    
    if long_df.height > 0 and long_model is not None:
        long_preds = long_model.predict(long_df)
        long_df = long_df.with_columns(
            tier2_score=pl.Series(long_preds),
            tier2_direction=pl.lit("long")
        )
    else:
        long_df = long_df.with_columns(
            tier2_score=pl.lit(None, dtype=pl.Float64),
            tier2_direction=pl.lit(None, dtype=pl.Utf8)
        )
        
    if short_df.height > 0 and short_model is not None:
        short_preds = short_model.predict(short_df)
        short_df = short_df.with_columns(
            tier2_score=pl.Series(short_preds),
            tier2_direction=pl.lit("short")
        )
    else:
        short_df = short_df.with_columns(
            tier2_score=pl.lit(None, dtype=pl.Float64),
            tier2_direction=pl.lit(None, dtype=pl.Utf8)
        )
        
    # Combine
    scored_df = pl.concat([long_df, short_df], how="diagonal")
    
    # Rank cross-sectionally per datetime
    scored_df = scored_df.with_columns(
        tier2_rank=pl.when(pl.col("tier2_direction") == "long")
        .then(pl.col("tier2_score").rank(descending=True).over("datetime"))
        .when(pl.col("tier2_direction") == "short")
        .then(pl.col("tier2_score").rank(descending=False).over("datetime"))
        .otherwise(None)
    )
    
    return scored_df
