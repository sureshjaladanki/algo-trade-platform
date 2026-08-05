"""Tier 2 Horizon stock-selection LightGBM models (Long / Short)."""

from typing import List, Tuple

import lightgbm as lgb
import numpy as np
import polars as pl
from scipy.stats import spearmanr
from sklearn.isotonic import IsotonicRegression

# Shared core + Long-only confirmation (~15) + regime pass-throughs.
LONG_FEATURES = [
    "rel_ret_15_vs_nifty",
    "rel_ret_60_vs_nifty",
    "stock_r_15",
    "stock_rv_15",
    "stock_volz_15",
    "stock_vwap_dist",
    "sector_rel_strength",
    "dist_to_prev_day_high",
    "orb_breakout_flag",
    "rolling_beta_60d",
    "trend_strength_daily",
    "pct_from_20d_high",
    "adv_rank_20d",
    "bars_since_regime_flip",
    "tod_sin",
    "tod_cos",
    "vol_regime_ratio",
    "index_vwap_dist",
]

# Shared core + Short asymmetry + regime pass-throughs.
SHORT_FEATURES = [
    "rel_ret_15_vs_nifty",
    "rel_ret_60_vs_nifty",
    "stock_r_15",
    "stock_rv_15",
    "stock_volz_15",
    "stock_vwap_dist",
    "rolling_beta_60d",
    "trend_strength_daily",
    "adv_rank_20d",
    "bars_since_regime_flip",
    "tod_sin",
    "tod_cos",
    "sector_rel_weakness",
    "dist_to_prev_day_low",
    "orb_breakdown_flag",
    "pct_from_52w_high",
    "bounce_risk_zscore",
    "downside_acceleration",
    "vol_regime_ratio",
    "index_vwap_dist",
]

LONG_PARAMS = {
    "objective": "huber",
    "alpha": 0.9,
    "metric": "mae",
    "learning_rate": 0.03,
    "num_leaves": 15,
    "max_depth": 4,
    "min_child_samples": 300,
    "n_estimators": 1000,
    "subsample": 0.75,
    "colsample_bytree": 0.7,
    "reg_alpha": 0.5,
    "reg_lambda": 5.0,
    "random_state": 42,
    "verbose": -1,
}

SHORT_PARAMS = {
    "objective": "huber",
    "alpha": 0.7,
    "metric": "mae",
    "learning_rate": 0.025,
    "num_leaves": 15,
    "max_depth": 3,
    "min_child_samples": 400,
    "n_estimators": 600,
    "subsample": 0.65,
    "colsample_bytree": 0.65,
    "reg_alpha": 1.0,
    "reg_lambda": 8.0,
    "random_state": 42,
    "verbose": -1,
}

# ~21 trading months, 1m val, ~2m test (verdict: 18–24m → 1m → 1–3m).
DEFAULT_TRAIN_DAYS = 420
DEFAULT_VAL_DAYS = 21
DEFAULT_TEST_DAYS = 42
DEFAULT_EMBARGO_DAYS = 1


class HorizonModel:
    """
    Tier 2 Horizon LightGBM ranker for one sleeve (long or short).
    Trains on excess-return vs Nifty; calibrates with isotonic on purged val.
    """

    def __init__(self, direction: str):
        if direction not in ("long", "short"):
            raise ValueError("direction must be 'long' or 'short'")
        self.direction = direction
        self.params = LONG_PARAMS.copy() if direction == "long" else SHORT_PARAMS.copy()
        self.early_stopping_rounds = 50 if direction == "long" else 40
        self.model = lgb.LGBMRegressor(**self.params)
        self.calibrator = IsotonicRegression(out_of_bounds="clip")
        self.is_fitted = False
        self.features: List[str] = []

    def fit(
        self,
        X_train: pl.DataFrame,
        y_train: pl.Series,
        X_val: pl.DataFrame,
        y_val: pl.Series,
        features: List[str],
        train_weight: np.ndarray | None = None,
    ) -> float:
        self.features = list(features)

        X_train_np = X_train.select(features).to_numpy()
        y_train_np = y_train.to_numpy()
        X_val_np = X_val.select(features).to_numpy()
        y_val_np = y_val.to_numpy()

        self.model.fit(
            X_train_np,
            y_train_np,
            sample_weight=train_weight,
            eval_X=X_val_np,
            eval_y=y_val_np,
            callbacks=[
                lgb.early_stopping(
                    stopping_rounds=self.early_stopping_rounds, verbose=False
                )
            ],
        )

        val_preds = self.model.predict(X_val_np)
        self.calibrator.fit(val_preds, y_val_np)
        self.is_fitted = True

        ic, _ = spearmanr(val_preds, y_val_np)
        return float(ic) if ic == ic else 0.0

    def predict(self, X: pl.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")
        X_np = X.select(self.features).to_numpy()
        raw_preds = self.model.predict(X_np)
        return self.calibrator.predict(raw_preds)

    def spearman_ic(self, X: pl.DataFrame, y: pl.Series) -> float:
        preds = self.predict(X)
        ic, _ = spearmanr(preds, y.to_numpy())
        return float(ic) if ic == ic else 0.0


def episode_balanced_weights(df: pl.DataFrame) -> np.ndarray:
    """
    Per-row weights that equalize each regime episode's contribution.

    Long trends produce many more bars per episode than the scarce `TREND_DOWN`
    episodes, so weight rows by 1/(bars in episode) and rescale to mean 1. This
    fixes imbalance at the episode level instead of duplicating rows.
    """
    keys = ["date_only", "regime_episode_id"]
    counts = pl.col("date").len().over(keys)
    weights = (
        df.select((1.0 / counts).alias("w"))
        .with_columns(w=pl.col("w") / pl.col("w").mean())
        .to_series()
        .to_numpy()
    )
    return weights


def sleeve_sample_diagnostics(df: pl.DataFrame) -> dict:
    """Post-filter sample counts — Short hyperparams are retuned against these."""
    if df.height == 0:
        return {"bars": 0, "sessions": 0, "episodes": 0, "median_episode_bars": 0.0}
    keys = ["date_only", "regime_episode_id"]
    per_episode = df.group_by(keys).agg(bars=pl.len())
    return {
        "bars": df.height,
        "sessions": df.select(pl.col("date_only").n_unique()).item(),
        "episodes": per_episode.height,
        "median_episode_bars": float(per_episode["bars"].median()),
    }


def get_purged_cv_splits(
    df: pl.DataFrame,
    n_splits: int = 5,
    embargo_days: int = DEFAULT_EMBARGO_DAYS,
    embargo_bars: int = 4,
    train_days: int = DEFAULT_TRAIN_DAYS,
    val_days: int = DEFAULT_VAL_DAYS,
    test_days: int = DEFAULT_TEST_DAYS,
    calendar_dates: list | None = None,
) -> List[Tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]]:
    """
    Purged walk-forward: train → embargo (≥1 day + horizon) → val → embargo → test.

    Window lengths are counted on `calendar_dates` (market sessions), not on the
    possibly sparse sleeve dates inside `df`. Pass the full train period's
    `date_only` values so DEFAULT_TRAIN_DAYS ≈ 21 calendar trading months even
    when the sleeve only fires on TREND_UP / TREND_DOWN days.

    Embargo ≥ horizon (4 bars) plus ≥ 1 trading day at every train/val and val/test
    boundary. Same-day labels make a full trading-day embargo sufficient; we also
    drop the last `embargo_bars` from the end of each train/val block.
    """
    if calendar_dates is not None:
        dates = sorted(set(calendar_dates))
    else:
        dates = df.select("date_only").unique().sort("date_only").to_series().to_list()
    block = train_days + embargo_days + val_days + embargo_days + test_days
    if len(dates) < block:
        return []

    splits: List[Tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]] = []
    step = max(1, (len(dates) - block) // max(n_splits, 1))

    for i in range(0, len(dates) - block + 1, step):
        train_start = dates[i]
        train_end = dates[i + train_days - 1]

        val_start_idx = i + train_days + embargo_days
        val_start = dates[val_start_idx]
        val_end = dates[val_start_idx + val_days - 1]

        test_start_idx = val_start_idx + val_days + embargo_days
        test_start = dates[test_start_idx]
        test_end = dates[test_start_idx + test_days - 1]

        train_df = df.filter(
            (pl.col("date_only") >= train_start) & (pl.col("date_only") <= train_end)
        )
        val_df = df.filter(
            (pl.col("date_only") >= val_start) & (pl.col("date_only") <= val_end)
        )
        test_df = df.filter(
            (pl.col("date_only") >= test_start) & (pl.col("date_only") <= test_end)
        )

        train_df = _purge_tail_bars(train_df, embargo_bars)
        val_df = _purge_tail_bars(val_df, embargo_bars)

        splits.append((train_df, val_df, test_df))
        if len(splits) == n_splits:
            break

    return splits


def _purge_tail_bars(df: pl.DataFrame, embargo_bars: int) -> pl.DataFrame:
    """Drop the last `embargo_bars` rows of the final session (horizon purge)."""
    if df.height == 0 or embargo_bars <= 0:
        return df
    last_date = df.select(pl.col("date_only").max()).item()
    last_day = df.filter(pl.col("date_only") == last_date).sort("date")
    if last_day.height <= embargo_bars:
        return df.filter(pl.col("date_only") < last_date)
    keep_times = last_day["date"][:-embargo_bars]
    return df.filter(
        (pl.col("date_only") < last_date) | pl.col("date").is_in(keep_times)
    )
