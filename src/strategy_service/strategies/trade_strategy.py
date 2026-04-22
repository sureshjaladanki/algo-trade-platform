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

            # if (
            #     all(key in self.symbol_profile for key in ["prev_close", "prev_atr"])
            #     and self.gap_atr_ratio is None
            # ):
            #     self.gap_atr_ratio = self._generate_gap_atr_ratio(df)

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

    # Note: Need check if this is really helping with postive signals
    # def _generate_gap_atr_ratio(self, df: pd.DataFrame):
    #     latest_date = None  # Initialize to prevent UnboundLocalError

    #     if "datetime" in df.columns:
    #         latest_date = pd.to_datetime(df["datetime"]).iloc[-1].date()
    #     elif isinstance(df.index, pd.DatetimeIndex):
    #         latest_date = df.index[-1].date()

    #     # Check if we successfully extracted a date
    #     if latest_date:
    #         # 1. Calculate the Opening Gap (Latest Open - Yesterday's Close)
    #         gap_abs = df["open"].iloc[-1] - self.symbol_profile["prev_close"]

    #         # 2. Gap Analysis relative to ATR
    #         # Gap as a multiple of ATR (e.g., 0.5 means the gap is 50% of the daily ATR)
    #         # Positive = Gap Up, Negative = Gap Down
    #         gap_atr_ratio = gap_abs / self.symbol_profile["prev_atr"]
    #         return gap_atr_ratio

    #     return None

    def _load_config(self) -> dict:
        # Assuming the script is run from the root of the project
        config_path = Path(f"config/{self.symbol}.yml")
        try:
            with open(config_path, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Warning: Config file for {self.symbol} not found.")
            return {}

    def check_entry(self, data, regime_data=None):
        if self.regime and regime_data is not None:
            trading_session = self.regime.trading_session(regime_data)
        else:
            trading_session = TradingSession.OPENING.value

        # Condition 1: Trading Session is safe for intraday positions
        if self.regime and regime_data is not None:
            safe_for_intraday_positions = (
                TradingSession.WARMUP.value < trading_session
            ) & (trading_session < TradingSession.CLOSING.value)
        else:
            safe_for_intraday_positions = True

        # Condition 2: Trading Volume is above the Time-Segmented Average Volume threshold for the symbol
        # For vectorization, we'll just use the default "opening" threshold if we can't easily map the session name.
        # To keep it simple, we'll use a single threshold or map it if it's a Series.
        # If it's a Series, mapping session names is complex, so we'll just use 1.0 for now or map it using replace.
        threshold = 1.0
        if isinstance(trading_session, pd.Series):
            # Map integer values back to session names for threshold lookup
            session_map = {
                v.value: k.lower() for k, v in TradingSession.__members__.items()
            }
            thresholds = self.config.get("session_volume_threshold", {})
            threshold_map = {k: thresholds.get(v, 1.0) for k, v in session_map.items()}
            threshold = trading_session.map(threshold_map).fillna(1.0)
        else:
            session_name = (
                TradingSession(trading_session).name.lower()
                if self.regime and regime_data is not None
                else "opening"
            )
            thresholds = self.config.get("session_volume_threshold", {})
            threshold = thresholds.get(session_name, 1.0)

        trading_volume_above_threshold = data.get("rvol", 1.0) > threshold

        # Condition 3: Gap ATR Ratio is within acceptable limits
        # gap_atr_ratio_limit = self.config.get("gap_atr_ratio_limit", 1.0)
        # gap_atr_ratio_within_limit = (
        #     abs(self.gap_atr_ratio) <= gap_atr_ratio_limit
        #     if self.gap_atr_ratio is not None
        #     else True
        # )

        return (
            safe_for_intraday_positions & trading_volume_above_threshold
        ), "Entry Conditions Met"

    def check_exit(self, data, prev_data=None, regime_data=None):
        """Determine if exit needs to be mandated."""
        if isinstance(data, pd.DataFrame):
            if self.regime and regime_data is not None:
                trading_session = self.regime.trading_session(regime_data)
                current_exit = trading_session > TradingSession.CLOSING.value
                just_crossed = current_exit & ~current_exit.shift(1, fill_value=False)
                return just_crossed, "End of Day Squareoff"
            return pd.Series(False, index=data.index), "End of Day Squareoff"

        current_exit = (
            self.regime.trading_session(regime_data) > TradingSession.CLOSING.value
            if self.regime and regime_data is not None
            else False
        )

        just_crossed = current_exit and not self._prev_exit
        self._prev_exit = current_exit

        return just_crossed, "End of Day Squareoff"
