import unittest
import pandas as pd
from datetime import datetime, time
from src.strategy_service.strategies.regime_strategy import RegimeStrategy
from src.strategy_service.types.trading_session import TradingSession


class TestRegimeStrategy(unittest.TestCase):
    def setUp(self):
        self.regime = RegimeStrategy()

    def test_initial_state(self):
        self.assertEqual(self.regime.data["vix"], 0.0)
        self.assertEqual(self.regime.data["ad_cumulative"], 0.0)
        self.assertEqual(self.regime.data[f"ad_ema_{self.regime.ema_fast_period}"], 0.0)
        self.assertEqual(self.regime.data[f"ad_ema_{self.regime.ema_slow_period}"], 0.0)
        self.assertEqual(self.regime.data["trading_session"], TradingSession.UNKNOWN)
        self.assertFalse(hasattr(self.regime, "ad_ratio_thresholds"))

    def test_determine_trading_session(self):
        # Assuming default config: opening: 9:15-11:29, midday: 11:30-14:29, closing: 14:30-14:59, squareoff: 15:00-15:29
        self.assertEqual(
            self.regime._determine_trading_session(time(9, 20)), TradingSession.WARMUP
        )
        self.assertEqual(
            self.regime._determine_trading_session(time(10, 0)), TradingSession.OPENING
        )
        self.assertEqual(
            self.regime._determine_trading_session(time(12, 0)), TradingSession.MIDDAY
        )
        self.assertEqual(
            self.regime._determine_trading_session(time(14, 45)), TradingSession.CLOSING
        )
        self.assertEqual(
            self.regime._determine_trading_session(time(15, 15)),
            TradingSession.SQUAREOFF,
        )
        self.assertEqual(
            self.regime._determine_trading_session(time(16, 0)), TradingSession.UNKNOWN
        )

    @unittest.mock.patch(
        "src.strategy_service.strategies.regime_strategy.add_ad_regime"
    )
    def test_generate_features(self, mock_add_ad_regime):
        vix_data = pd.DataFrame(
            {"datetime": [datetime(2023, 1, 1, 10, 0)], "close": [18.5]}
        )
        ad_data = pd.DataFrame(
            {"datetime": [datetime(2023, 1, 1, 10, 0)], "close": [100.0]}
        )

        mock_vix_data = vix_data.copy()
        mock_vix_data["ad_cumulative"] = 10.0
        mock_vix_data[f"ad_ema_{self.regime.ema_fast_period}"] = 9.0
        mock_vix_data[f"ad_ema_{self.regime.ema_slow_period}"] = 8.0
        mock_add_ad_regime.return_value = mock_vix_data

        self.regime.generate_features(vix_data, {"AD": ad_data})

        self.assertEqual(self.regime.data["vix"], 18.5)
        self.assertEqual(self.regime.data["ad_cumulative"], 10.0)
        self.assertEqual(self.regime.data[f"ad_ema_{self.regime.ema_fast_period}"], 9.0)
        self.assertEqual(self.regime.data[f"ad_ema_{self.regime.ema_slow_period}"], 8.0)
        self.assertEqual(self.regime.trading_session, TradingSession.OPENING)

    def test_safe_for_longs(self):
        self.regime.data["vix"] = 20.0
        self.regime.data["ad_cumulative"] = 3.0
        self.regime.data[f"ad_ema_{self.regime.ema_slow_period}"] = 2.0
        self.regime.data[f"ad_ema_{self.regime.ema_fast_period}"] = 2.5
        self.assertTrue(self.regime.safe_for_longs)

        # VIX >= configured high
        self.regime.data["vix"] = self.regime.vix_levels["high"]
        self.assertFalse(self.regime.safe_for_longs)

        # A/D not trending up
        self.regime.data["vix"] = 20.0
        self.regime.data["ad_cumulative"] = 1.0
        self.regime.data[f"ad_ema_{self.regime.ema_slow_period}"] = 2.0
        self.regime.data[f"ad_ema_{self.regime.ema_fast_period}"] = 2.0
        self.assertFalse(self.regime.safe_for_longs)

    def test_safe_for_shorts(self):
        self.regime.data["vix"] = 18.0
        self.regime.data["ad_cumulative"] = 1.0
        self.regime.data[f"ad_ema_{self.regime.ema_slow_period}"] = 2.5
        self.regime.data[f"ad_ema_{self.regime.ema_fast_period}"] = 2.0
        self.assertTrue(self.regime.safe_for_shorts)

        # VIX <= low
        self.regime.data["vix"] = self.regime.vix_levels["low"]
        self.assertFalse(self.regime.safe_for_shorts)

        # A/D not trending down
        self.regime.data["vix"] = 18.0
        self.regime.data["ad_cumulative"] = 3.0
        self.regime.data[f"ad_ema_{self.regime.ema_slow_period}"] = 1.0
        self.regime.data[f"ad_ema_{self.regime.ema_fast_period}"] = 1.0
        self.assertFalse(self.regime.safe_for_shorts)


if __name__ == "__main__":
    unittest.main()
