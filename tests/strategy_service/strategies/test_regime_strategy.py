import unittest
import pandas as pd
from datetime import datetime, time
from src.strategy_service.strategies.regime_strategy import RegimeStrategy
from src.strategy_service.types.trading_session import TradingSession


class TestRegimeStrategy(unittest.TestCase):
    def setUp(self):
        self.regime = RegimeStrategy()

    def test_initial_state(self):
        # Current RegimeStrategy is stateless and does not keep a `data` snapshot.
        self.assertFalse(hasattr(self.regime, "data"))
        self.assertFalse(hasattr(self.regime, "ad_ratio_thresholds"))

    def test_determine_trading_session(self):
        # Assuming default config: opening: 9:15-11:29, midday: 11:30-14:29, closing: 14:30-14:59, squareoff: 15:00-15:29
        times = pd.Series(
            [
                time(9, 20),
                time(10, 0),
                time(12, 0),
                time(14, 45),
                time(15, 15),
                time(16, 0),
            ],
            index=range(6),
        )
        sessions = self.regime._determine_trading_session(times)
        self.assertEqual(sessions.iloc[0], TradingSession.WARMUP.value)
        self.assertEqual(sessions.iloc[1], TradingSession.OPENING.value)
        self.assertEqual(sessions.iloc[2], TradingSession.MIDDAY.value)
        self.assertEqual(sessions.iloc[3], TradingSession.CLOSING.value)
        self.assertEqual(sessions.iloc[4], TradingSession.SQUAREOFF.value)
        self.assertEqual(sessions.iloc[5], TradingSession.UNKNOWN.value)

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

        out = self.regime.generate_features(vix_data, {"AD": ad_data})
        self.assertIn("trading_session", out.columns)
        self.assertEqual(out["close"].iloc[0], 18.5)
        self.assertEqual(out["ad_cumulative"].iloc[0], 10.0)
        self.assertEqual(out[f"ad_ema_{self.regime.ema_fast_period}"].iloc[0], 9.0)
        self.assertEqual(out[f"ad_ema_{self.regime.ema_slow_period}"].iloc[0], 8.0)
        self.assertEqual(out["trading_session"].iloc[0], TradingSession.OPENING.value)

    def test_safe_for_longs(self):
        data = {
            "vix": 20.0,
            "ad_cumulative": 3.0,
            f"ad_ema_{self.regime.ema_slow_period}": 2.0,
            f"ad_ema_{self.regime.ema_fast_period}": 2.5,
        }
        self.assertTrue(self.regime.safe_for_longs(data))

        # VIX >= configured high
        data["vix"] = self.regime.vix_levels["high"]
        self.assertFalse(self.regime.safe_for_longs(data))

        # A/D not trending up
        data["vix"] = 20.0
        data["ad_cumulative"] = 1.0
        data[f"ad_ema_{self.regime.ema_slow_period}"] = 2.0
        data[f"ad_ema_{self.regime.ema_fast_period}"] = 2.0
        self.assertFalse(self.regime.safe_for_longs(data))

    def test_safe_for_shorts(self):
        data = {
            "vix": 18.0,
            "ad_cumulative": 1.0,
            f"ad_ema_{self.regime.ema_slow_period}": 2.5,
            f"ad_ema_{self.regime.ema_fast_period}": 2.0,
        }
        self.assertTrue(self.regime.safe_for_shorts(data))

        # VIX <= low
        data["vix"] = self.regime.vix_levels["low"]
        self.assertFalse(self.regime.safe_for_shorts(data))

        # A/D not trending down
        data["vix"] = 18.0
        data["ad_cumulative"] = 3.0
        data[f"ad_ema_{self.regime.ema_slow_period}"] = 1.0
        data[f"ad_ema_{self.regime.ema_fast_period}"] = 1.0
        self.assertFalse(self.regime.safe_for_shorts(data))


if __name__ == "__main__":
    unittest.main()
