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
        self.assertEqual(self.regime.data["ad_ratio"], 1.0)
        self.assertEqual(self.regime.data["trading_session"], TradingSession.UNKNOWN)

    def test_determine_trading_session(self):
        # Assuming default config: opening: 9:15-11:29, midday: 11:30-14:29, closing: 14:30-14:59, squareoff: 15:00-15:29
        self.assertEqual(self.regime._determine_trading_session(time(9, 20)), TradingSession.WARMUP)
        self.assertEqual(self.regime._determine_trading_session(time(10, 0)), TradingSession.OPENING)
        self.assertEqual(self.regime._determine_trading_session(time(12, 0)), TradingSession.MIDDAY)
        self.assertEqual(self.regime._determine_trading_session(time(14, 45)), TradingSession.CLOSING)
        self.assertEqual(self.regime._determine_trading_session(time(15, 15)), TradingSession.SQUAREOFF)
        self.assertEqual(self.regime._determine_trading_session(time(16, 0)), TradingSession.UNKNOWN)

    @unittest.mock.patch('src.strategy_service.strategies.regime_strategy.add_ad_ratio')
    def test_generate_features(self, mock_add_ad_ratio):
        vix_data = pd.DataFrame({
            'datetime': [datetime(2023, 1, 1, 10, 0)],
            'close': [18.5]
        })
        ad_data = pd.DataFrame({
            'datetime': [datetime(2023, 1, 1, 10, 0)],
            'close': [100.0]
        })
        
        mock_vix_data = vix_data.copy()
        mock_vix_data['ad_ratio'] = 1.5
        mock_add_ad_ratio.return_value = mock_vix_data
        
        self.regime.generate_features(vix_data, {'AD': ad_data})
        
        self.assertEqual(self.regime.data["vix"], 18.5)
        self.assertEqual(self.regime.data["ad_ratio"], 1.5)
        self.assertEqual(self.regime.trading_session, TradingSession.OPENING)

    def test_safe_for_longs(self):
        # VIX < panic (25.0), AD > bearish (0.8)
        self.regime.data["vix"] = 20.0
        self.regime.data["ad_ratio"] = 1.0
        self.assertTrue(self.regime.safe_for_longs)
        
        # VIX >= panic
        self.regime.data["vix"] = 26.0
        self.assertFalse(self.regime.safe_for_longs)
        
        # AD <= bearish
        self.regime.data["vix"] = 20.0
        self.regime.data["ad_ratio"] = 0.5
        self.assertFalse(self.regime.safe_for_longs)

    def test_safe_for_shorts(self):
        # VIX > low (15.0), AD < bullish (1.2)
        self.regime.data["vix"] = 18.0
        self.regime.data["ad_ratio"] = 1.0
        self.assertTrue(self.regime.safe_for_shorts)
        
        # VIX <= low
        self.regime.data["vix"] = 14.0
        self.assertFalse(self.regime.safe_for_shorts)
        
        # AD >= bullish
        self.regime.data["vix"] = 18.0
        self.regime.data["ad_ratio"] = 1.5
        self.assertFalse(self.regime.safe_for_shorts)

if __name__ == '__main__':
    unittest.main()
