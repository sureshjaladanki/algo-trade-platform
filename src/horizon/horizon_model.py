import lightgbm as lgb
import polars as pl
import numpy as np
from typing import List, Tuple
from sklearn.isotonic import IsotonicRegression
from scipy.stats import spearmanr

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
    "verbose": -1
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
    "verbose": -1
}

class Tier2Model:
    def __init__(self, direction: str):
        """
        direction: 'long' or 'short'
        """
        self.direction = direction
        self.params = LONG_PARAMS.copy() if direction == "long" else SHORT_PARAMS.copy()
        self.model = None
        self.calibrator = None
        self.features = []
        
    def train(self, X_train: pl.DataFrame, y_train: pl.Series, X_val: pl.DataFrame, y_val: pl.Series, features: List[str]):
        self.features = features
        
        # Convert to numpy
        X_train_np = X_train.select(features).to_numpy()
        y_train_np = y_train.to_numpy()
        X_val_np = X_val.select(features).to_numpy()
        y_val_np = y_val.to_numpy()
        
        # LightGBM datasets
        train_data = lgb.Dataset(X_train_np, label=y_train_np)
        val_data = lgb.Dataset(X_val_np, label=y_val_np, reference=train_data)
        
        # Early stopping
        callbacks = [lgb.early_stopping(stopping_rounds=50, verbose=False)]
        
        # Train
        n_estimators = self.params.pop("n_estimators")
        self.model = lgb.train(
            self.params,
            train_data,
            num_boost_round=n_estimators,
            valid_sets=[val_data],
            callbacks=callbacks
        )
        
        # Calibration on validation set
        val_preds = self.model.predict(X_val_np)
        self.calibrator = IsotonicRegression(out_of_bounds='clip')
        self.calibrator.fit(val_preds, y_val_np)
        
        # Calculate Spearman IC on val
        ic, _ = spearmanr(val_preds, y_val_np)
        return ic
        
    def predict(self, X: pl.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model not trained yet.")
        X_np = X.select(self.features).to_numpy()
        raw_preds = self.model.predict(X_np)
        calibrated_preds = self.calibrator.predict(raw_preds)
        return calibrated_preds

def get_purged_cv_splits(df: pl.DataFrame, n_splits: int = 5, embargo_bars: int = 4, train_days: int = 120, val_days: int = 30) -> List[Tuple[pl.DataFrame, pl.DataFrame]]:
    """
    Returns list of (train_df, val_df) splits using purged walk-forward CV.
    Assumes df is sorted by datetime.
    """
    # Get unique dates
    dates = df.select("date_only").unique().sort("date_only").to_series().to_list()
    
    splits = []
    step = max(1, (len(dates) - train_days - val_days) // n_splits)
    
    for i in range(0, len(dates) - train_days - val_days + 1, step):
        train_start = dates[i]
        train_end = dates[i + train_days - 1]
        
        # Embargo: skip 1 trading day + horizon bars. We just skip 1 full trading day here for simplicity.
        val_start = dates[i + train_days + 1] 
        val_end = dates[i + train_days + val_days]
        
        train_df = df.filter((pl.col("date_only") >= train_start) & (pl.col("date_only") <= train_end))
        val_df = df.filter((pl.col("date_only") >= val_start) & (pl.col("date_only") <= val_end))
        
        splits.append((train_df, val_df))
        
        if len(splits) == n_splits:
            break
            
    return splits
