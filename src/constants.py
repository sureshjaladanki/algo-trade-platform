from __future__ import annotations

DEFAULT_TARGET_CLASSES = {
    "stop_loss": {"num": 0, "weight": 2.0},
    "hold": {"num": 1, "weight": 1.0},
    "take_profit": {"num": 2, "weight": 3.0},
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
    "fast_ema_5m_roc",
    "natr_5m",
    "atr_5m_roc",
    # Market (5m joined to 1m)
    "market_vix_5m",
    # Sector (5m joined to 1m)
    "sector",
]
