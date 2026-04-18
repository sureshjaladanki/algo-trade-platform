import unittest
import pandas as pd
from datetime import time
from unittest.mock import MagicMock, patch

from src.strategy_service.strategies.trade_strategy import TradeStrategy
from src.strategy_service.types.trading_session import TradingSession


class MockStrategy(TradeStrategy):
    def exit(self, data):
        pass


class TestTradeStrategy(unittest.TestCase):
    def setUp(self):
        self.symbol = "TEST_ETF"
        self.mock_regime = MagicMock()
        self.mock_regime.trading_session = TradingSession.OPENING

        self.strategy = MockStrategy(
            symbol=self.symbol,
            symbol_profile={"minute_of_day_volume": {time(9, 15): 1000}},
            regime=self.mock_regime,
        )

        # Override config for testing
        self.strategy.config = {
            "rsi_period": 70,
            "ema_micro_fast_period": 9,
            "ema_micro_slow_period": 21,
            "vwma_macro_fast_period": 15,
            "vwma_macro_slow_period": 45,
            "session_volume_threshold": {"opening": 1.5},
        }

    @patch("src.strategy_service.strategies.trade_strategy.add_ema")
    @patch("src.strategy_service.strategies.trade_strategy.add_rsi")
    @patch("src.strategy_service.strategies.trade_strategy.add_vwma")
    @patch("src.strategy_service.strategies.trade_strategy.add_vwap")
    @patch("src.strategy_service.strategies.trade_strategy.add_minute_of_day")
    def test_generate_features(
        self, mock_add_minute, mock_add_vwap, mock_add_vwma, mock_add_rsi, mock_add_ema
    ):
        # Setup mocks to just return the dataframe
        mock_add_minute.side_effect = lambda df: df.assign(minute_of_day=time(9, 15))
        mock_add_vwap.side_effect = lambda df: df
        mock_add_vwma.side_effect = lambda df, **kwargs: df
        mock_add_rsi.side_effect = lambda df, **kwargs: df
        mock_add_ema.side_effect = lambda df, **kwargs: df

        df = pd.DataFrame({"volume": [2000]})

        result = self.strategy.generate_features(df)

        # Check if rvol was calculated correctly (2000 / 1000)
        self.assertEqual(result["rvol"].iloc[0], 2.0)

        # Verify feature functions were called
        mock_add_vwap.assert_called_once()
        self.assertEqual(mock_add_vwma.call_count, 2)
        mock_add_vwma.assert_any_call(result, period=15)
        mock_add_vwma.assert_any_call(result, period=45)
        mock_add_rsi.assert_called_once_with(result, rsi_period=70)
        self.assertEqual(mock_add_ema.call_count, 2)
        mock_add_ema.assert_any_call(result, period=9)
        mock_add_ema.assert_any_call(result, period=21)

    def test_check_entry(self):
        # Test valid entry
        data = {"rvol": 2.0}  # Above threshold of 1.5
        self.assertTrue(self.strategy.check_entry(data))

        # Test invalid entry (low volume)
        data = {"rvol": 1.0}  # Below threshold of 1.5
        self.assertFalse(self.strategy.check_entry(data))

        # Test invalid entry (wrong session)
        self.mock_regime.trading_session = TradingSession.CLOSING
        data = {"rvol": 2.0}
        self.assertFalse(self.strategy.check_entry(data))

        # Test invalid entry (warmup session)
        self.mock_regime.trading_session = TradingSession.WARMUP
        data = {"rvol": 2.0}
        self.assertFalse(self.strategy.check_entry(data))

        # Reset session
        self.mock_regime.trading_session = TradingSession.OPENING

        # Test valid entry with gap_atr_ratio within limit
        self.strategy.gap_atr_ratio = 0.5
        self.strategy.config["gap_atr_ratio_limit"] = 1.0
        data = {"rvol": 2.0}
        self.assertTrue(self.strategy.check_entry(data))

        # Test invalid entry with gap_atr_ratio outside limit
        self.strategy.gap_atr_ratio = 1.5
        self.assertFalse(self.strategy.check_entry(data))

        # Test invalid entry with negative gap_atr_ratio outside limit
        self.strategy.gap_atr_ratio = -1.5
        self.assertFalse(self.strategy.check_entry(data))


if __name__ == "__main__":
    unittest.main()
