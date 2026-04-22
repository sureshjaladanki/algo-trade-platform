from datetime import datetime
import yaml
import pandas as pd
from pathlib import Path
from typing import Dict
from src.strategy_service.types.trading_session import TradingSession
from src.strategy_service.features.advance_decline import add_ad_regime
from src.utils.pd_functions import isna_safe
import numpy as np


class RegimeStrategy:
    """
    Tracks the overall market regime (e.g., Volatility via INDIA VIX, broader market trends).
    Designed to be injected into specific trading strategies via composition.
    """

    def __init__(self):
        self.config = self._load_config()
        self.vix_levels = self.config.get(
            "vix_levels", {"low": 15.0, "medium": 22.0, "high": 28.0}
        )
        self.trading_sessions = self.config.get(
            "trading_sessions",
            {
                "warmup": {"start": "9:15", "end": "9:29"},
                "opening": {"start": "9:30", "end": "11:29"},
                "midday": {"start": "11:30", "end": "14:29"},
                "closing": {"start": "14:30", "end": "14:59"},
                "squareoff": {"start": "15:00", "end": "15:29"},
            },
        )
        self.ema_fast_period = self.config.get("ema_fast_period", 5)
        self.ema_slow_period = self.config.get("ema_slow_period", 21)

        # Holds the current regime metrics that consuming strategies will read
        # self.data = {
        #     "vix": 0.0,
        #     "ad_cumulative": 0.0,
        #     f"ad_ema_{self.ema_fast_period}": 0.0,
        #     f"ad_ema_{self.ema_slow_period}": 0.0,
        #     "trading_session": TradingSession.UNKNOWN,
        # }

    def _load_config(self) -> dict:
        config_path = Path("config/regime_indicators.yml")
        try:
            with open(config_path, "r") as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            print("Warning: Config file for regime_indicators not found.")
            return {}

    def _determine_trading_session(self, times_series: pd.Series) -> pd.Series:
        # 1. Build conditions and choices
        conditions = []
        choices = []

        for session_name, times in self.trading_sessions.items():
            start = datetime.strptime(times["start"], "%H:%M").time()
            end = datetime.strptime(times["end"], "%H:%M").time()

            conditions.append((times_series >= start) & (times_series <= end))
            choices.append(TradingSession[session_name.upper()].value)

        # 2. Apply piecewise logic
        result = np.select(conditions, choices, default=TradingSession.UNKNOWN.value)

        return pd.Series(result, index=times_series.index)

    def generate_features(
        self, vixdf: pd.DataFrame, component_dfs: Dict[str, pd.DataFrame]
    ):
        """
        Updates the regime data based on the latest macro data.

        Args:
            vixdf (pd.DataFrame): The main DataFrame containing INDIA VIX data.
            advance_declinedf (pd.DataFrame): DataFrame containing Advance/Decline data.
        """

        # Add the A/D ratio to the VIX DataFrame
        vixdf = add_ad_regime(
            vixdf,
            component_dfs,
            fast_period=self.ema_fast_period,
            slow_period=self.ema_slow_period,
        )
        # Add VIX to the VIX DataFrame (i.e close column)
        vixdf["vix"] = vixdf["close"]

        # Determine time from vixdf
        if "datetime" in vixdf.columns:
            times_series = pd.to_datetime(vixdf["datetime"]).dt.time
        else:
            # vixdf.index.time returns a numpy array, so wrap it in a Series to keep the index
            times_series = pd.Series(vixdf.index.time, index=vixdf.index)

        # Determine the trading session
        vixdf["trading_session"] = self._determine_trading_session(times_series)

        return vixdf

    def trading_session(self, data):
        val = data.get("trading_session", TradingSession.UNKNOWN.value)

        return val

    def safe_for_longs(self, data):
        """Helper property: Longs are generally unsafe during high volatility/panic."""
        # Cumulative must be above the Slow EMA (Trend) and above the Fast EMA (Acceleration/Momentum)
        ad_cumulative = data.get("ad_cumulative", 0.0)
        ad_cumulative = isna_safe(ad_cumulative)

        slow_ema = data.get(f"ad_ema_{self.ema_slow_period}")
        fast_ema = data.get(f"ad_ema_{self.ema_fast_period}")

        # Validity Guard: Return False if EMAs are missing/NaN
        is_emas_valid = pd.notna(slow_ema) & pd.notna(fast_ema)

        # Convert to na safe (0.0 float)
        slow_ema = isna_safe(slow_ema)
        fast_ema = isna_safe(fast_ema)

        ad_trend_strong = ad_cumulative > slow_ema
        ad_trending_up = ad_cumulative > fast_ema

        vix = data.get("vix", 0.0)
        vix = isna_safe(vix)

        return (
            is_emas_valid
            & (vix < self.vix_levels["high"])
            & ad_trend_strong
            & ad_trending_up
        )

    def safe_for_shorts(self, data):
        """Helper property: Shorts are favored during high volatility/panic or bearish market breadth."""
        # Cumulative must be below the Slow EMA (Trend) and below the Fast EMA (Decline/Momentum)
        ad_cumulative = data.get("ad_cumulative", 0.0)
        ad_cumulative = isna_safe(ad_cumulative)

        slow_ema = data.get(f"ad_ema_{self.ema_slow_period}", 0.0)
        fast_ema = data.get(f"ad_ema_{self.ema_fast_period}", 0.0)

        # Validity Guard: Return False if EMAs are missing/NaN
        is_emas_valid = pd.notna(slow_ema) & pd.notna(fast_ema)

        # Convert to na safe (0.0 float)
        slow_ema = isna_safe(slow_ema)
        fast_ema = isna_safe(fast_ema)

        ad_trend_weak = ad_cumulative < slow_ema
        ad_trending_down = ad_cumulative < fast_ema

        vix = data.get("vix", 0.0)
        vix = isna_safe(vix)

        return (
            is_emas_valid
            & (vix > self.vix_levels["low"])
            & ad_trend_weak
            & ad_trending_down
        )
