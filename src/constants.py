from __future__ import annotations

DEFAULT_TARGET_CLASSES = {
    "stop_loss": {"num": 0, "weight": 2.0},
    "hold": {"num": 1, "weight": 1.0},
    "take_profit": {"num": 2, "weight": 3.0},
}

# Feature taxonomy (active + optional). Toggle optional cols by uncommenting in MODEL_FEATURE_COLS.
# [ INTRADAY VALUE ] ──► close_vwap_zscore, close_ema_21_pct, bb_pct_b
# [ MICRO MOMENTUM ] ──► fast_ema_slope, fast_slow_ema_ratio
# [ CORE TREND     ] ──► close_5m_reg_slope (period 12); optional: sharpe_5m
# [ INDEX ALPHA    ] ──► rs_5m_ratio; optional: rs_5m_roc
# [ MOMENTUM/ADX   ] ──► rsi_5m, natr_5m, atr_5m_roc, di_diff_5m; optional: rsi_5m_roc, adx_5m, adx_5m_roc, fast_ema_5m_roc
# [ CATALYST/RISK  ] ──► rvol, gap_atr
# [ MACRO REGIME   ] ──► market_vix_5m, sector
# [ TIME CIRCLE    ] ──► minute_of_day_sin, minute_of_day_cos; legacy: minute_of_day
MODEL_FEATURE_COLS = [
    # Symbol (1m)
    "close_vwap_zscore",
    "close_ema_21_pct",
    "minute_of_day_sin",
    "minute_of_day_cos",
    # "minute_of_day",  # superseded by sin/cos above
    "bb_pct_b",
    "rvol",
    "gap_atr",
    "fast_ema_slope",
    "fast_slow_ema_ratio",
    # Symbol (5m joined to 1m)
    "rsi_5m",
    # "rsi_5m_roc",
    "rs_5m_ratio",
    # "rs_5m_roc",
    # "adx_5m",
    # "adx_5m_roc",
    "di_diff_5m",
    # "fast_ema_5m_roc",
    "natr_5m",
    "atr_5m_roc",
    # "sharpe_5m",
    "close_5m_reg_slope",
    # Market (5m joined to 1m)
    "market_vix_5m",
    # Sector (5m joined to 1m)
    "sector",
]
