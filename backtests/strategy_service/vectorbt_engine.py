import pandas as pd
import vectorbt as vbt
from pathlib import Path
import yaml

from src.strategy_service.strategies.regime_strategy import RegimeStrategy
from src.strategy_service.strategies.long_strategy import LongStrategy
from src.strategy_service.strategies.short_strategy import ShortStrategy
from src.strategy_service.data_adapter import DataAdapter, IDataAdapter
from src.strategy_service.features.rvol import get_volume_profile


class VectorBTEngine:
    """
    Engine to run trading strategies across multiple symbols using vectorbt for single-pass backtesting.
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
        self.portfolios = {}

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

        # Load full historical data for trade symbols
        for symbol in self.trade_symbols:
            self._init_trade_symbol_data(symbol)

    def _init_regime_symbol_data(self, symbol: str) -> None:
        self.symbol_dataframes[symbol] = self.data_adapter.read_1m_candles_current_day(
            symbol
        )

    def _init_trade_symbol_data(self, symbol: str):
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

        self.symbol_dataframes[symbol] = symbol_1m_candles_history_dataframe

        # Get the latest date available in the history dataframe, this is the previous day's date
        latest_date = symbol_1m_candles_history_dataframe.index.normalize().max()
        # Extract only the rows for prev date
        prev_day_df = symbol_1m_candles_history_dataframe.loc[
            str(latest_date.date())
        ].copy()
        current_day_df = self.data_adapter.read_1m_candles_current_day(symbol)

        self.symbol_dataframes[symbol] = pd.concat([prev_day_df, current_day_df])

        if self.trade_symbols[symbol].get("can_long", False):
            self.long_strategies[symbol] = LongStrategy(
                symbol, symbol_profile=symbol_profile, regime=self.regime_strategy
            )
        if self.trade_symbols[symbol].get("can_short", False):
            self.short_strategies[symbol] = ShortStrategy(
                symbol, symbol_profile=symbol_profile, regime=self.regime_strategy
            )

    def _generate_regime_features(self) -> pd.DataFrame:
        # Generate features for the regime strategy in a single pass
        return self.regime_strategy.generate_features(
            self.symbol_dataframes[self.regime_symbol],
            {
                symbol: self.symbol_dataframes[symbol]
                for symbol in self.advance_decline_symbols
            },
        )

    def _generate_trade_features(self, symbol: str) -> pd.DataFrame:
        df = self.symbol_dataframes[symbol]

        # Since long and short strategies share the same feature logic
        # and config, we only need to compute features once.
        if symbol in self.long_strategies:
            df = self.long_strategies[symbol].generate_features(df)
        elif symbol in self.short_strategies:
            df = self.short_strategies[symbol].generate_features(df)

        return df

    def run(self):
        self._init_data()

        # 1. Generate regime features for the entire history
        regime_df = self._generate_regime_features()

        closes_by_symbol = {}
        entries_by_symbol = {}
        exits_by_symbol = {}
        short_entries_by_symbol = {}
        short_exits_by_symbol = {}

        # 2. Process each trade symbol
        for symbol in self.trade_symbols:
            print(f"Processing {symbol}...")

            # Generate features for the entire history
            df = self._generate_trade_features(symbol)
            # Align trade data df with regime data df. Trying to avoid per-symbol reindex/ffill as this is an expensive operation.
            df = df.reindex(regime_df.index, method="ffill")

            entries = pd.Series(False, index=df.index)
            exits = pd.Series(False, index=df.index)
            short_entries = pd.Series(False, index=df.index)
            short_exits = pd.Series(False, index=df.index)

            # Generate signals
            if symbol in self.long_strategies:
                strategy = self.long_strategies[symbol]
                entries = strategy.buy(df, regime_data=regime_df)
                exits = strategy.exit(df, prev_data=df.shift(1), regime_data=regime_df)

            if symbol in self.short_strategies:
                strategy = self.short_strategies[symbol]
                short_entries = strategy.short(df, regime_data=regime_df)
                short_exits = strategy.exit(
                    df, prev_data=df.shift(1), regime_data=regime_df
                )

            # 3. Run vectorbt backtest
            # Slice to current day only for backtest to match live engine behavior
            latest_date = df.index.normalize().max()
            current_date_str = str(latest_date.date())
            df_current = df.loc[current_date_str:]
            entries_current = entries.loc[current_date_str:]
            exits_current = exits.loc[current_date_str:]
            short_entries_current = short_entries.loc[current_date_str:]
            short_exits_current = short_exits.loc[current_date_str:]

            # Combine long and short signals (vectorbt handles both)
            # We can run separate portfolios or a combined one.
            # For simplicity, let's run a combined portfolio if vectorbt supports it,
            # or just long for now if short is not configured.

            # vectorbt Portfolio.from_signals supports entries, exits, short_entries, short_exits
            pf = vbt.Portfolio.from_signals(
                close=df_current["close"],
                entries=entries_current,
                exits=exits_current,
                short_entries=short_entries_current,
                short_exits=short_exits_current,
                freq="1min",
                init_cash=100000,
                size=1.0,
                fees=0.0006,  # 0.06% is a realistic average for intraday equity in India
            )

            self.portfolios[symbol] = pf

            # Collect wide inputs so we can build a single combined portfolio later
            closes_by_symbol[symbol] = df_current["close"]
            entries_by_symbol[symbol] = entries_current
            exits_by_symbol[symbol] = exits_current
            short_entries_by_symbol[symbol] = short_entries_current
            short_exits_by_symbol[symbol] = short_exits_current

        # 3. Build ONE combined multi-asset portfolio for reporting/aggregation
        close_wide = pd.concat(closes_by_symbol, axis=1)
        entries_wide = pd.concat(entries_by_symbol, axis=1).reindex(close_wide.index)
        exits_wide = pd.concat(exits_by_symbol, axis=1).reindex(close_wide.index)
        short_entries_wide = pd.concat(short_entries_by_symbol, axis=1).reindex(
            close_wide.index
        )
        short_exits_wide = pd.concat(short_exits_by_symbol, axis=1).reindex(
            close_wide.index
        )

        combined_pf = vbt.Portfolio.from_signals(
            close=close_wide,
            entries=entries_wide,
            exits=exits_wide,
            short_entries=short_entries_wide,
            short_exits=short_exits_wide,
            freq="1min",
            init_cash=100000,
            size=1.0,
            fees=0.0006,  # 0.06% is a realistic average for intraday equity in India
            cash_sharing=True,
        )

        return combined_pf


if __name__ == "__main__":
    data_adapter = DataAdapter()
    engine = VectorBTEngine(data_adapter)
    combined_pf = engine.run()

    stats = combined_pf.stats()

    stats_path = Path("data/output/vectorbt_combined_stats.csv")
    stats.to_csv(stats_path)
    print(f"Saved combined stats to {stats_path}")

    # Optional: plot (can be slow and requires a GUI backend)
    # combined_pf.plot().show()
