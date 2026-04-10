import unittest
from unittest.mock import MagicMock
from src.strategy_service.strategies.long_strategy import LongStrategy
from src.strategy_service.types.trading_session import TradingSession

class TestLongStrategy(unittest.TestCase):
    def setUp(self):
        self.mock_regime = MagicMock()
        self.mock_regime.trading_session = TradingSession.OPENING
        self.mock_regime.safe_for_longs = True
        
        self.strategy = LongStrategy(
            symbol="TEST_ETF",
            symbol_profile=None,
            regime=self.mock_regime
        )
        
        # Override config
        self.strategy.config = {
            'rsi_period': 70,
            'ema_micro_fast_period': 9,
            'ema_micro_slow_period': 21,
            'ema_fast_period': 45,
            'ema_slow_period': 105,
            'adx_period': 14,
            'long_rsi_entry': 40,
            'long_rsi_exit': 70,
            'vwap_stop_loss_pct': 0.2,
            'session_volume_threshold': {'opening': 1.0}
        }
        
        # Re-initialize keys based on overridden config
        self.strategy.rsi_key = 'rsi_70'
        self.strategy.ema_micro_fast_key = 'ema_9'
        self.strategy.ema_micro_slow_key = 'ema_21'
        self.strategy.ema_fast_key = 'ema_45'
        self.strategy.ema_slow_key = 'ema_105'
        self.strategy.adx_key = 'adx_14'

    def test_check_entry(self):
        # Valid entry data
        data = {
            'rvol': 1.5,
            'close': 105.0,
            'vwap': 100.0,
            'ema_9': 104.0,
            'ema_21': 103.0,
            'ema_45': 102.0,
            'ema_105': 98.0,
            'rsi_70': 30.0, # Oversold (< 40)
            'adx_14': 30.0,
            'bb_width_pct': 1.0,
            'bb_upper': 115.0,
            'expected_profit_pct_long': 0.5
        }
        self.assertTrue(self.strategy.check_entry(data))
        
        # Invalid: Macro trend down
        invalid_data = data.copy()
        invalid_data['ema_45'] = 97.0
        self.assertFalse(self.strategy.check_entry(invalid_data))
        
        # Invalid: Micro trend down
        invalid_data = data.copy()
        invalid_data['close'] = 99.0
        self.assertFalse(self.strategy.check_entry(invalid_data))
        
        # Invalid: No pullback
        invalid_data = data.copy()
        invalid_data['rsi_70'] = 50.0
        self.assertFalse(self.strategy.check_entry(invalid_data))

    def test_buy(self):
        data = {
            'rvol': 1.5,
            'close': 105.0,
            'vwap': 100.0,
            'ema_9': 104.0,
            'ema_21': 103.0,
            'ema_45': 102.0,
            'ema_105': 98.0,
            'rsi_70': 30.0,
            'adx_14': 30.0,
            'bb_width_pct': 1.0,
            'bb_upper': 115.0,
            'expected_profit_pct_long': 0.5
        }
        action = self.strategy.buy(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['action'], 'LONG')
        self.assertEqual(action[0]['symbol'], 'TEST_ETF')
        self.assertEqual(action[0]['price'], 105.0)
        self.assertEqual(action[0]['reason'], 'Entry Conditions Met')

    def test_exit_take_profit(self):
        data = {
            'close': 107.0, # Below ema_9
            'high': 111.0,
            'vwap': 100.0,
            'ema_9': 108.0,
            'ema_21': 106.0,
            'ema_45': 102.0,
            'ema_105': 98.0,
            'rsi_70': 75.0, # Overbought (> 70)
            'bb_upper': 115.0
        }
        action = self.strategy.exit(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['action'], 'EXIT_LONG')
        self.assertEqual(action[0]['reason'], 'Take Profit (RSI + 9EMA)')

    def test_exit_trend_reversal(self):
        data = {
            'close': 105.0,
            'high': 106.0,
            'vwap': 100.0,
            'ema_9': 104.0,
            'ema_21': 103.0,
            'ema_45': 97.0, # Crossed below slow EMA
            'ema_105': 98.0,
            'rsi_70': 50.0,
            'bb_upper': 115.0
        }
        action = self.strategy.exit(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['reason'], 'Trend Reversal')

    def test_exit_volatility_exhaustion(self):
        data = {
            'close': 101.0, # Below ema_9
            'high': 116.0, # Hit upper BB
            'vwap': 100.0,
            'ema_9': 102.0,
            'ema_21': 103.0,
            'ema_45': 104.0,
            'ema_105': 98.0,
            'rsi_70': 50.0,
            'bb_upper': 115.0
        }
        action = self.strategy.exit(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['reason'], 'Volatility Exhaustion (BB + 9EMA)')

    def test_exit_stop_loss(self):
        data = {
            'close': 99.0, # Below VWAP stop loss (100 * 0.998 = 99.8)
            'high': 100.0,
            'vwap': 100.0,
            'ema_9': 104.0,
            'ema_21': 103.0,
            'ema_45': 102.0,
            'ema_105': 98.0,
            'rsi_70': 50.0,
            'bb_upper': 115.0
        }
        action = self.strategy.exit(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['reason'], 'Trend Failure (VWAP Stop)')

if __name__ == '__main__':
    unittest.main()
