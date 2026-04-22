import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

from src.strategy_service.engine import StrategyEngine


class TestStrategyEngine(unittest.TestCase):
    def setUp(self):
        self.mock_data_adapter = MagicMock()

        # Define a mock config
        self.mock_config = {
            "trade_symbols": {
                "AAPL": {"can_long": True, "can_short": False},
                "MSFT": {"can_long": False, "can_short": True},
            },
            "regime_symbol": "SPY",
            "advance_decline_symbols": ["VIX"],
        }

    @patch("src.strategy_service.engine.yaml.safe_load")
    @patch("builtins.open", new_callable=MagicMock)
    def test_init_and_load_config(self, mock_open, mock_yaml_load):
        mock_yaml_load.return_value = self.mock_config

        engine = StrategyEngine(self.mock_data_adapter)

        self.assertEqual(engine.trade_symbols, self.mock_config["trade_symbols"])
        self.assertEqual(engine.regime_symbol, "SPY")
        self.assertEqual(engine.advance_decline_symbols, ["VIX"])
        self.assertIsNotNone(engine.regime_strategy)

    @patch("src.strategy_service.engine.StrategyEngine._load_config")
    @patch("src.strategy_service.engine.get_volume_profile")
    def test_init_data(self, mock_get_volume_profile, mock_load_config):
        mock_load_config.return_value = self.mock_config
        mock_get_volume_profile.return_value = {"09:30": 1000}

        # Setup mock dataframes for data adapter
        # 1m df with the last date being 2023-01-02
        dates_1m = pd.date_range(start="2023-01-01 09:30", periods=100, freq="1min")
        mock_1m_df = pd.DataFrame({"close": np.random.rand(100)}, index=dates_1m)

        self.mock_data_adapter.read_1m_candles_history_dataframe.return_value = (
            mock_1m_df
        )

        engine = StrategyEngine(self.mock_data_adapter)
        engine._init_data()

        # Check if dataframes are initialized for regime and AD symbols
        self.assertIn("SPY", engine.symbol_dataframes)
        self.assertIn("VIX", engine.symbol_dataframes)

        # Check if trade symbols are initialized
        self.assertIn("AAPL", engine.symbol_dataframes)
        self.assertIn("MSFT", engine.symbol_dataframes)

        # Check if strategies are created based on config
        self.assertIn("AAPL", engine.long_strategies)
        self.assertNotIn("AAPL", engine.short_strategies)

        self.assertNotIn("MSFT", engine.long_strategies)
        self.assertIn("MSFT", engine.short_strategies)

    @patch("src.strategy_service.engine.StrategyEngine._load_config")
    def test_on_1m_candle_closed(self, mock_load_config):
        mock_load_config.return_value = self.mock_config
        engine = StrategyEngine(self.mock_data_adapter)

        # Setup initial dataframe
        initial_time = pd.Timestamp("2023-01-01 09:30:00")
        engine.symbol_dataframes["AAPL"] = pd.DataFrame(
            {"close": [150]}, index=[initial_time]
        )

        # New candle
        new_time = pd.Timestamp("2023-01-01 09:31:00")
        new_candle = pd.Series({"close": 151}, name=new_time)

        engine._on_1m_candle_closed("AAPL", new_candle)

        # Verify candle was appended
        self.assertEqual(len(engine.symbol_dataframes["AAPL"]), 2)
        self.assertEqual(engine.symbol_dataframes["AAPL"].loc[new_time]["close"], 151)

    @patch("src.strategy_service.engine.StrategyEngine._load_config")
    def test_generate_signals(self, mock_load_config):
        mock_load_config.return_value = self.mock_config
        engine = StrategyEngine(self.mock_data_adapter)

        # Setup mock data
        t1 = pd.Timestamp("2023-01-01 09:30:00")
        t2 = pd.Timestamp("2023-01-01 09:31:00")
        engine.symbol_dataframes["AAPL"] = pd.DataFrame(
            {"close": [150, 151]}, index=[t1, t2]
        )
        engine.symbol_dataframes["SPY"] = pd.DataFrame(
            {"trading_session": [2]}, index=[t2]
        )

        # Setup mock strategies
        mock_long_strategy = MagicMock()
        mock_long_strategy.buy.return_value = [{"action": "LONG", "symbol": "AAPL"}]
        mock_long_strategy.exit.return_value = []
        engine.long_strategies["AAPL"] = mock_long_strategy

        signals = engine._generate_signals("AAPL")

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["action"], "LONG")
        mock_long_strategy.buy.assert_called_once()
        mock_long_strategy.exit.assert_called_once()

    @patch("src.strategy_service.engine.StrategyEngine._load_config")
    @patch("src.strategy_service.engine.StrategyEngine._init_data")
    @patch("src.strategy_service.engine.StrategyEngine._generate_regime_features")
    @patch("src.strategy_service.engine.StrategyEngine._generate_trade_features")
    @patch("src.strategy_service.engine.StrategyEngine._generate_signals")
    def test_run(
        self,
        mock_generate_signals,
        mock_trade_features,
        mock_regime_features,
        mock_init_data,
        mock_load_config,
    ):
        mock_load_config.return_value = self.mock_config

        # Setup mock signals
        mock_generate_signals.return_value = [{"action": "LONG", "symbol": "AAPL"}]

        # Setup mock generators to yield one candle then stop
        def mock_generator(symbol):
            yield pd.Series({"close": 100}, name=pd.Timestamp("2023-01-01 09:30:00"))

        self.mock_data_adapter.process_next_1m_candle.side_effect = mock_generator

        engine = StrategyEngine(self.mock_data_adapter)

        # Initialize empty dataframes so _on_1m_candle_closed doesn't fail
        engine.symbol_dataframes = {
            "SPY": pd.DataFrame(columns=["close"]),
            "VIX": pd.DataFrame(columns=["close"]),
            "AAPL": pd.DataFrame(columns=["close"]),
            "MSFT": pd.DataFrame(columns=["close"]),
        }

        all_signals = engine.run()

        # We have 2 trade symbols, so generate_signals should be called twice per iteration
        # Since the generator yields 1 item, we get 2 signals total (1 for AAPL, 1 for MSFT)
        self.assertEqual(len(all_signals), 2)
        mock_init_data.assert_called_once()
        mock_regime_features.assert_called_once()
        self.assertEqual(mock_trade_features.call_count, 2)
        self.assertEqual(mock_generate_signals.call_count, 2)


if __name__ == "__main__":
    unittest.main()
