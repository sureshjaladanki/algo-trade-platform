from pathlib import Path

import pandas as pd
import yaml

from src.strategy_service.strategies.regime_strategy import RegimeStrategy
from src.strategy_service.strategies.long_strategy import LongStrategy
from src.strategy_service.strategies.short_strategy import ShortStrategy
from src.strategy_service.data_adapter import DataAdapter, IDataAdapter
from src.strategy_service.features.rvol import get_volume_profile
from src.strategy_service.features.atr import get_atr


class StrategyEngine:
    """
    Engine to run trading strategies across multiple symbols.
    """

    def __init__(self, data_adapter: IDataAdapter):
        self.data_adapter = data_adapter
        self.config = self._load_config()
        self.regime_strategy = RegimeStrategy()

        self.trade_symbols = self.config.get("trade_symbols", {})
        self.regime_symbol = self.config.get("regime_symbol", None)
        self.advance_decline_symbols = self.config.get("advance_decline_symbols", [])
        self.symbol_dataframes = {}
        self.long_strategies = {}
        self.short_strategies = {}

    def _load_config(self) -> dict:
        config_path = Path("config/strategy_engine.yml")
        try:
            with open(config_path, "r") as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            print("Warning: Config file for strategy_config not found.")
            return {}

    def _init_data(self):
        for symbol in [self.regime_symbol, *self.advance_decline_symbols]:
            self._init_regime_symbol_data(symbol)

        for symbol in self.trade_symbols:
            self._init_trade_symbol_data(symbol)

    def _init_regime_symbol_data(self, symbol: str) -> None:
        self.symbol_dataframes[symbol] = pd.DataFrame()

    def _init_trade_symbol_data(self, symbol: str):
        # symbol 1day candles history dataframe
        symbol_1d_candles_history_dataframe = (
            self.data_adapter.read_1d_candles_history_dataframe(symbol)
        )
        day_atr_profile = get_atr(symbol_1d_candles_history_dataframe)

        # symbol 1min candles history dataframe
        symbol_1m_candles_history_dataframe = (
            self.data_adapter.read_1m_candles_history_dataframe(symbol)
        )
        minute_of_day_volume_profile = get_volume_profile(
            symbol_1m_candles_history_dataframe
        )
        symbol_profile = {
            "minute_of_day_volume": minute_of_day_volume_profile,
        }
        symbol_profile |= day_atr_profile  # merge the two dictionaries

        # Get the latest date available in the history dataframe, this is the previous day's date
        latest_date = symbol_1m_candles_history_dataframe.index.normalize().max()
        # Extract only the rows for prev date
        symbol_1min_candles_prev_day_dataframe = (
            symbol_1m_candles_history_dataframe.loc[str(latest_date.date())].copy()
        )
        self.symbol_dataframes[symbol] = symbol_1min_candles_prev_day_dataframe

        if self.trade_symbols[symbol].get("can_long", False):
            self.long_strategies[symbol] = LongStrategy(
                symbol, symbol_profile=symbol_profile, regime=self.regime_strategy
            )
        if self.trade_symbols[symbol].get("can_short", False):
            self.short_strategies[symbol] = ShortStrategy(
                symbol, symbol_profile=symbol_profile, regime=self.regime_strategy
            )

    def _on_1m_candle_closed(self, symbol: str, candle: pd.Series):
        """
        Process a newly closed 1-minute candle.
        Updates the current day's dataframe and evaluates strategies.
        """
        if symbol in self.symbol_dataframes:
            # Append the new candle to the current day's dataframe using .loc
            # Assuming the candle series has a name that represents the timestamp
            timestamp = candle.name
            if (
                self.symbol_dataframes[symbol].empty
                and len(self.symbol_dataframes[symbol].columns) == 0
            ):
                self.symbol_dataframes[symbol] = pd.DataFrame([candle])
            else:
                self.symbol_dataframes[symbol].loc[timestamp] = candle

    def _generate_regime_features(self):
        # Generate features for the regime strategy
        self.symbol_dataframes[self.regime_symbol] = (
            self.regime_strategy.generate_features(
                self.symbol_dataframes[self.regime_symbol],
                {
                    symbol: self.symbol_dataframes[symbol]
                    for symbol in self.advance_decline_symbols
                },
            )
        )

    def _generate_trade_features(self, symbol: str):
        # Since long and short strategies share the same feature logic
        # and config, we only need to compute features once.
        if symbol in self.long_strategies:
            self.symbol_dataframes[symbol] = self.long_strategies[
                symbol
            ].generate_features(self.symbol_dataframes[symbol])
        elif symbol in self.short_strategies:
            self.symbol_dataframes[symbol] = self.short_strategies[
                symbol
            ].generate_features(self.symbol_dataframes[symbol])

    def _generate_signals(self, symbol: str):
        df = self.symbol_dataframes[symbol]
        if len(df) < 2:
            return []

        latest_data = df.iloc[-1]
        prev_data = df.iloc[-2]
        regime_data = self.symbol_dataframes[self.regime_symbol].iloc[-1]
        signals = []

        if symbol in self.long_strategies:
            signals.extend(
                self.long_strategies[symbol].buy(latest_data, regime_data=regime_data)
            )
            signals.extend(
                self.long_strategies[symbol].exit(
                    latest_data, prev_data, regime_data=regime_data
                )
            )

        if symbol in self.short_strategies:
            signals.extend(
                self.short_strategies[symbol].short(
                    latest_data, regime_data=regime_data
                )
            )
            signals.extend(
                self.short_strategies[symbol].exit(
                    latest_data, prev_data, regime_data=regime_data
                )
            )

        return signals

    def run(self):
        self._init_data()

        all_signals = []
        regime_generator = self.data_adapter.process_next_1m_candle(
            self.config.get("regime_symbol", None)
        )
        advance_decline_generators = {
            symbol: self.data_adapter.process_next_1m_candle(symbol)
            for symbol in self.config.get("advance_decline_symbols", [])
        }
        # Initialize generators for all symbols
        trade_generators = {
            symbol: self.data_adapter.process_next_1m_candle(symbol)
            for symbol in self.trade_symbols
        }

        # Process candles minute-by-minute across all symbols
        while True:
            try:
                # Generate features for the regime strategy
                regime_candle = next(regime_generator)
                self._on_1m_candle_closed(self.regime_symbol, regime_candle)
                for symbol in self.advance_decline_symbols:
                    ad_candle = next(advance_decline_generators[symbol])
                    self._on_1m_candle_closed(symbol, ad_candle)

                self._generate_regime_features()

                # Generate features for the trade symbols
                for symbol in self.trade_symbols:
                    candle = next(trade_generators[symbol])
                    self._on_1m_candle_closed(symbol, candle)
                    self._generate_trade_features(symbol)

                # Generate signals for the trade symbols
                for symbol in self.trade_symbols:
                    signals = self._generate_signals(symbol)
                    all_signals.extend(signals)

            except StopIteration:
                break

        print(f"Total signals generated: {len(all_signals)}")
        return all_signals


if __name__ == "__main__":
    # Example usage: Auto-discover symbols from config/
    data_adapter = DataAdapter()
    engine = StrategyEngine(data_adapter)
    all_signals = engine.run()

    if all_signals:
        signals_df = pd.DataFrame(all_signals)
        signals_df.to_csv(Path("data/output/all_signals.csv"), index=False)
        print(f"Saved {len(all_signals)} signals to all_signals.csv")
    else:
        print("No signals generated to save.")

    # Print a summary
    symbol_signals = {}
    for sig in all_signals:
        sym = sig.get("symbol", "UNKNOWN")
        symbol_signals[sym] = symbol_signals.get(sym, 0) + 1

    for sym, count in symbol_signals.items():
        print(f"{sym}: {count} total signals generated.")
