from __future__ import annotations

DEFAULT_TARGET_CLASSES = {
    "stop_loss": {"num": 0, "weight": 2.0},
    "hold": {"num": 1, "weight": 1.0},
    "take_profit": {"num": 2, "weight": 3.0},
}

# Balanced training defaults (between high-conviction and aggressive signal upweighting).
DEFAULT_XGBOOST_PARAMS = {
    "learning_rate": 0.02,
    "n_estimators": 2500,
    "max_depth": 4,
    "min_child_weight": 7,
    "gamma": 1.0,
    "subsample": 0.75,
    "colsample_bytree": 0.75,
}

# Probability gates for training-time backtest in `src/model.py`.
DEFAULT_INFERENCE = {
    "entry_tp_prob": 0.73,
    "exit_tp_prob": 0.32,
}

MODEL_FEATURE_COLS = [
    # Symbol (1m)
    "close_vwap_zscore",
    "close_ema_21_pct",
    "minute_of_day",
    "bb_pct_b",
    "rvol",
    "gap_atr",
    "fast_ema_slope",
    # Symbol (5m joined to 1m)
    "rsi_5m",
    "rsi_5m_roc",
    "rs_5m_ratio",
    "rs_5m_roc",
    "adx_5m",
    "adx_5m_roc",
    "di_diff_5m",
    # "di_diff_5m_roc",
    "fast_ema_5m_roc",
    "natr_5m",
    "atr_5m_roc",
    # "close_5m_pos",
    # Market (5m joined to 1m)
    "market_vix_5m",
    # Sector (5m joined to 1m)
    "sector",
]
