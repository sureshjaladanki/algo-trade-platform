from __future__ import annotations

DEFAULT_TARGET_CLASSES = {
    "stop_loss": {"num": 0, "weight": 3.0},
    "hold": {"num": 1, "weight": 0.5},
    "take_profit": {"num": 2, "weight": 1.5},
}

MODEL_FEATURE_COLS = [
    # Symbol (1m)
    "close_vwap_zscore",
    "close_ema_14_pct",
    "minute_of_day",
    "bb_pct_b",
    "rvol",
    "gap_atr",
    "ema_slope_5",
    # Symbol (5m joined to 1m)
    "rsi_5m",
    "adx_5m",
    "natr_5m",
    "close_pos_5m",
    # Market (5m joined to 1m)
    "market_vix_5m",
    # Sector (5m joined to 1m)
    "sector",
]
