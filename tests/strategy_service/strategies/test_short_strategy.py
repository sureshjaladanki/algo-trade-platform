import unittest
from unittest.mock import MagicMock
from src.strategy_service.strategies.short_strategy import ShortStrategy
from src.strategy_service.types.trading_session import TradingSession

class TestShortStrategy(unittest.TestCase):
    def setUp(self):
        self.mock_regime = MagicMock()
        self.mock_regime.trading_session = TradingSession.OPENING
        self.mock_regime.safe_for_shorts = True
        
        self.strategy = ShortStrategy(
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
            'short_rsi_entry': 60,
            'short_rsi_exit': 30,
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
            'close': 95.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'ema_45': 98.0,
            'ema_105': 102.0,
            'rsi_70': 70.0, # Overbought (> 60)
            'adx_14': 30.0,
            'bb_width_pct': 1.0,
            'bb_lower': 85.0,
            'expected_profit_pct_short': 0.5
        }
        self.assertTrue(self.strategy.check_entry(data))
        
        # Invalid: Macro trend up
        invalid_data = data.copy()
        invalid_data['ema_45'] = 103.0
        self.assertFalse(self.strategy.check_entry(invalid_data))
        
        # Invalid: Micro trend up
        invalid_data = data.copy()
        invalid_data['close'] = 101.0
        self.assertFalse(self.strategy.check_entry(invalid_data))
        
        # Invalid: No pullback
        invalid_data = data.copy()
        invalid_data['rsi_70'] = 50.0
        self.assertFalse(self.strategy.check_entry(invalid_data))

    def test_short(self):
        data = {
            'rvol': 1.5,
            'close': 95.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'ema_45': 98.0,
            'ema_105': 102.0,
            'rsi_70': 70.0,
            'adx_14': 30.0,
            'bb_width_pct': 1.0,
            'bb_lower': 85.0,
            'expected_profit_pct_short': 0.5
        }
        action = self.strategy.short(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['action'], 'SHORT')
        self.assertEqual(action[0]['symbol'], 'TEST_ETF')
        self.assertEqual(action[0]['price'], 95.0)
        self.assertEqual(action[0]['reason'], 'Entry Conditions Met')

    def test_exit_take_profit(self):
        data = {
            'close': 97.0, # Above ema_9
            'low': 89.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'ema_45': 98.0,
            'ema_105': 102.0,
            'rsi_70': 25.0, # Oversold (< 30)
            'bb_lower': 85.0
        }
        action = self.strategy.exit(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['action'], 'EXIT_SHORT')
        self.assertEqual(action[0]['reason'], 'Take Profit (RSI + 9EMA)')

    def test_exit_trend_reversal(self):
        data = {
            'close': 95.0,
            'low': 94.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'ema_45': 103.0, # Crossed above slow EMA
            'ema_105': 102.0,
            'rsi_70': 50.0,
            'bb_lower': 85.0
        }
        action = self.strategy.exit(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['reason'], 'Trend Reversal')

    def test_exit_volatility_exhaustion(self):
        data = {
            'close': 97.0, # Above ema_9
            'low': 84.0, # Hit lower BB
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'ema_45': 98.0,
            'ema_105': 102.0,
            'rsi_70': 50.0,
            'bb_lower': 85.0
        }
        action = self.strategy.exit(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['reason'], 'Volatility Exhaustion (BB + 9EMA)')

    def test_exit_stop_loss(self):
        data = {
            'close': 101.0, # Above VWAP stop loss (100 * 1.002 = 100.2)
            'low': 100.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'ema_45': 98.0,
            'ema_105': 102.0,
            'rsi_70': 50.0,
            'bb_lower': 85.0
        }
        action = self.strategy.exit(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['reason'], 'Trend Failure (VWAP Stop)')

if __name__ == '__main__':
    unittest.main()
