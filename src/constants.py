from __future__ import annotations

DEFAULT_TARGET_CLASSES = {
    "stop_loss": {"num": 0, "weight": 3.0},
    "hold": {"num": 1, "weight": 0.5},
    "take_profit": {"num": 2, "weight": 1.5},
}

# Default intraday session windows used by `add_trading_session`.
# Mirrors `config/market_features.yml` -> `trading_session` block:
# Values represent the *last* minute_of_day included in each session window.
DEFAULT_TRADING_SESSIONS = {
    "initial_range": 9 * 60 + 59,   # 09:59
    "morning_trend": 11 * 60 + 29,  # 11:29
    "midday_dax": 12 * 60 + 29,     # 12:29
    "london_overlap": 14 * 60 + 29, # 14:29
    "closing_push": 15 * 60 + 8,    # 15:08
    "square_off": 15 * 60 + 29,     # 15:29
}

MODEL_FEATURE_COLS = [
    # Symbol (1m)
    "close_vwap_zscore",
    "close_ema_14_pct",
    "minute_of_day",
    "bb_pct_b",
    "vol_z_score",
    "rvol",
    "gap_atr",
    # Symbol (5m joined to 1m)
    "rsi_5m",
    "adx_5m",
    "rsi_5m_roc",
    "adx_5m_roc",
    # Market (5m joined to 1m)
    "market_vix_5m",
    "market_vix_roc_5m",
    "trading_session",
    # Sector (5m joined to 1m)
    "sector",
    "sector_index_roc_5m",
    "sector_ad_5m",
]

FEATURE_COLS = [
    "close", # Close price is used in the vectorBT backtest metrics
    *MODEL_FEATURE_COLS
]
