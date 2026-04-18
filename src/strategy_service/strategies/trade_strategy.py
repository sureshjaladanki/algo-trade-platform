from abc import ABC
import yaml
from pathlib import Path
import pandas as pd
from datetime import datetime
from src.strategy_service.features.minute_of_day import add_minute_of_day
from src.strategy_service.features.rsi import add_rsi
from src.strategy_service.features.ema import add_ema
from src.strategy_service.features.vwap import add_vwap
from src.strategy_service.features.vwma import add_vwma
from src.strategy_service.types.trading_session import TradingSession


# Abstract base class for all ETF trading strategies
class TradeStrategy(ABC):
    def __init__(self, symbol: str, symbol_profile=None, regime=None):
        self.symbol = symbol
        self.symbol_profile = symbol_profile
        self.regime = regime
        self.config = self._load_config()
        self.gap_atr_ratio = None
        self._prev_exit = False

    def generate_features(self, df):
        """
        Generate features for the strategy.
        """
        df = add_minute_of_day(df)

        if "minute_of_day" not in df.columns:
            df["minute_of_day"] = datetime.now().time()

        if self.symbol_profile is not None:
            if "minute_of_day_volume" in self.symbol_profile:
                avg_volume = df["minute_of_day"].map(
                    self.symbol_profile["minute_of_day_volume"]
                )
                df["rvol"] = df["volume"] / avg_volume
            else:
                df["rvol"] = 1

            if (
                all(key in self.symbol_profile for key in ["prev_close", "prev_atr"])
                and self.gap_atr_ratio is None
            ):
                self.gap_atr_ratio = self._generate_gap_atr_ratio(df)

        # 1. Micro Indicators (1-minute timeframe)
        df = add_vwap(df)
        vwma_macro_fast_period = self.config.get("vwma_macro_fast_period", 21)
        vwma_macro_slow_period = self.config.get("vwma_macro_slow_period", 45)
        df = add_vwma(df, period=vwma_macro_fast_period)
        df = add_vwma(df, period=vwma_macro_slow_period)

        ema_micro_fast_period = self.config.get("ema_micro_fast_period", 9)
        ema_micro_slow_period = self.config.get("ema_micro_slow_period", 21)
        df = add_ema(df, period=ema_micro_fast_period)
        df = add_ema(df, period=ema_micro_slow_period)

        rsi_period = self.config.get("rsi_period", 14)
        df = add_rsi(df, rsi_period=rsi_period)

        return df

    def _generate_gap_atr_ratio(self, df: pd.DataFrame):
        latest_date = None  # Initialize to prevent UnboundLocalError

        if "datetime" in df.columns:
            latest_date = pd.to_datetime(df["datetime"]).iloc[-1].date()
        elif isinstance(df.index, pd.DatetimeIndex):
            latest_date = df.index[-1].date()

        # Check if we successfully extracted a date
        if latest_date:
            # 1. Calculate the Opening Gap (Latest Open - Yesterday's Close)
            gap_abs = df["open"].iloc[-1] - self.symbol_profile["prev_close"]

            # 2. Gap Analysis relative to ATR
            # Gap as a multiple of ATR (e.g., 0.5 means the gap is 50% of the daily ATR)
            # Positive = Gap Up, Negative = Gap Down
            gap_atr_ratio = gap_abs / self.symbol_profile["prev_atr"]
            return gap_atr_ratio

        return None

    def _load_config(self) -> dict:
        # Assuming the script is run from the root of the project
        config_path = Path(f"config/{self.symbol}.yml")
        try:
            with open(config_path, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Warning: Config file for {self.symbol} not found.")
            return {}

    def check_entry(self, data):
        # Condition 1: Trading Session is safe for intraday positions
        if self.regime:
            safe_for_intraday_positions = (
                TradingSession.WARMUP
                < self.regime.trading_session
                < TradingSession.CLOSING
            )
        else:
            safe_for_intraday_positions = True

        # Condition 2: Trading Volume is above the Time-Segmented Average Volume threshold for the symbol
        session_name = (
            self.regime.trading_session.name.lower() if self.regime else "opening"
        )
        thresholds = self.config.get("session_volume_threshold", {})
        threshold = (
            thresholds.get(session_name, 1.0) if isinstance(thresholds, dict) else 1.0
        )
        trading_volume_above_threshold = data.get("rvol", 1.0) > threshold

        # Condition 3: Gap ATR Ratio is within acceptable limits
        gap_atr_ratio_limit = self.config.get("gap_atr_ratio_limit", 1.0)
        gap_atr_ratio_within_limit = (
            abs(self.gap_atr_ratio) <= gap_atr_ratio_limit
            if self.gap_atr_ratio is not None
            else True
        )

        return (
            safe_for_intraday_positions
            and trading_volume_above_threshold
            and gap_atr_ratio_within_limit
        )

    def check_exit(self, data, prev_data=None):
        """Determine if exit needs to be mandated."""
        current_exit = (
            self.regime.trading_session > TradingSession.CLOSING
            if self.regime
            else False
        )

        just_crossed = current_exit and not self._prev_exit
        self._prev_exit = current_exit

        return just_crossed
