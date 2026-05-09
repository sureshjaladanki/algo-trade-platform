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

