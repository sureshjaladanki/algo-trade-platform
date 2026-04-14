from datetime import datetime
import yaml
import pandas as pd
from pathlib import Path
from typing import Dict
from src.strategy_service.types.trading_session import TradingSession
from src.strategy_service.features.advance_decline import add_ad_regime

class RegimeStrategy:
    """
    Tracks the overall market regime (e.g., Volatility via INDIA VIX, broader market trends).
    Designed to be injected into specific trading strategies via composition.
    """
    def __init__(self):
        self.config = self._load_config()
        self.vix_levels = self.config.get('vix_levels', {'low': 15.0, 'medium': 22.0, 'high': 28.0})
        self.ad_ratio_thresholds = self.config.get('ad_ratio_thresholds', {'bearish': 0.8, 'bullish': 1.2})
        self.trading_sessions = self.config.get('trading_sessions', {'warmup': {'start': '9:15', 'end': '9:29'}, 'opening': {'start': '9:30', 'end': '11:30'}, 'midday': {'start': '11:30', 'end': '14:30'}, 'closing': {'start': '14:30', 'end': '15:30'}})
        
        # Holds the current regime metrics that consuming strategies will read
        self.data = {
            "vix": 0.0,
            "ad_ratio": 0.0,
            "ad_cumulative": 0.0,
            "ad_ema": 0.0,
            "ad_roc": 0.0,
            "trading_session": TradingSession.UNKNOWN,
        }
        
    def _load_config(self) -> dict:
        config_path = Path("config/regime_indicators.yml")
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            print("Warning: Config file for regime_indicators not found.")
            return {}

    def _determine_trading_session(self, current_time) -> TradingSession:
        for session_name, times in self.trading_sessions.items():
            start_time = datetime.strptime(times['start'], '%H:%M').time()
            end_time = datetime.strptime(times['end'], '%H:%M').time()
            if start_time <= current_time <= end_time:
                try:
                    return TradingSession[session_name.upper()]
                except KeyError:
                    pass
        return TradingSession.UNKNOWN

    def generate_features(self, vixdf: pd.DataFrame, component_dfs: Dict[str, pd.DataFrame]):
        """
        Updates the regime data based on the latest macro data.
        
        Args:
            vixdf (pd.DataFrame): The main DataFrame containing INDIA VIX data.
            advance_declinedf (pd.DataFrame): DataFrame containing Advance/Decline data.
        """
        current_time = datetime.now().time()
        
        if vixdf is not None and not vixdf.empty:
            # Add the A/D ratio to the VIX DataFrame
            vixdf = add_ad_regime(vixdf, component_dfs, period=20)

            # Get the latest VIX value
            latest_vix = vixdf.iloc[-1]
            self.data["vix"] = latest_vix.get("close", self.data["vix"])
            self.data["ad_ratio"] = latest_vix.get("ad_ratio", self.data["ad_ratio"])
            self.data["ad_cumulative"] = latest_vix.get("ad_cumulative", self.data["ad_cumulative"])
            self.data["ad_ema"] = latest_vix.get("ad_ema", self.data["ad_ema"])
            self.data["ad_roc"] = latest_vix.get("ad_roc", self.data["ad_roc"])

            # Determine time from vixdf
            if 'datetime' in vixdf.columns:
                current_time = pd.to_datetime(latest_vix['datetime']).time()
            elif isinstance(vixdf.index, pd.DatetimeIndex):
                current_time = latest_vix.name.time()
    
        # Determine the trading session
        self.data["trading_session"] = self._determine_trading_session(current_time)

        return vixdf

    @property
    def trading_session(self) -> TradingSession:
        return self.data["trading_session"]

    @property
    def safe_for_longs(self) -> bool:
        """Helper property: Longs are generally unsafe during high volatility/panic."""
        ad_trend_strong = self.data["ad_ema"] and self.data["ad_cumulative"] > self.data["ad_ema"]
        ad_trending_up = self.data["ad_roc"] and self.data["ad_roc"] > 0

        return self.data["vix"] < self.vix_levels["high"] and ad_trend_strong and ad_trending_up
        # return self.data["vix"] < self.vix_levels["high"] and self.data["ad_ratio"] > self.ad_ratio_thresholds["bullish"]
        
    @property
    def safe_for_shorts(self) -> bool:
        """Helper property: Shorts are favored during high volatility/panic or bearish market breadth."""
        ad_trend_weak = self.data["ad_ema"] and self.data["ad_cumulative"] < self.data["ad_ema"]
        ad_trending_down = self.data["ad_roc"] and self.data["ad_roc"] < 0

        return self.data["vix"] > self.vix_levels["low"] and ad_trend_weak and ad_trending_down
        # return self.data["vix"] > self.vix_levels["low"] and self.data["ad_ratio"] < self.ad_ratio_thresholds["bullish"]
