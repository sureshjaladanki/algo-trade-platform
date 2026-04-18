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
            'vwma_macro_slow_period': 45,
            'vwma_macro_fast_period': 21,
            'short_rsi_entry': 60,
            'short_rsi_exit': 30,
            'vwap_stop_loss_pct': 0.2,
            'session_volume_threshold': {'opening': 1.0}
        }

        # Re-initialize keys based on overridden config
        self.strategy.rsi_key = 'rsi_70'
        self.strategy.ema_micro_fast_key = 'ema_9'
        self.strategy.ema_micro_slow_key = 'ema_21'
        self.strategy.vwma_macro_fast_key = 'vwma_21'
        self.strategy.vwma_macro_slow_key = 'vwma_45'

    def test_check_entry(self):
        # Valid entry data (short needs close above both macro VWMAs)
        data = {
            'rvol': 1.5,
            'close': 95.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'rsi_70': 70.0,  # Overbought (> 60)
            'vwma_21': 90.0,
            'vwma_45': 88.0,
        }
        self.assertTrue(self.strategy.check_entry(data))
        
        # Invalid: Micro trend not down
        invalid_data = data.copy()
        invalid_data['ema_9'] = 98.0
        invalid_data['ema_21'] = 97.0
        self.assertFalse(self.strategy.check_entry(invalid_data))
        
        # Invalid: No pullback
        invalid_data = data.copy()
        invalid_data['rsi_70'] = 50.0
        self.assertFalse(self.strategy.check_entry(invalid_data))

        # Invalid: Price not above macro fast VWMA (slow VWMA still below price)
        invalid_data = data.copy()
        invalid_data['close'] = 85.0
        invalid_data['vwma_21'] = 90.0
        invalid_data['vwma_45'] = 80.0
        self.assertFalse(self.strategy.check_entry(invalid_data))

        # Invalid: Price not above macro slow VWMA
        invalid_data = data.copy()
        invalid_data['vwma_45'] = 100.0
        self.assertFalse(self.strategy.check_entry(invalid_data))

    def test_short(self):
        data = {
            'rvol': 1.5,
            'close': 95.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'rsi_70': 70.0,
            'vwma_21': 90.0,
            'vwma_45': 88.0,
        }
        action = self.strategy.short(data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['action'], 'SHORT')
        self.assertEqual(action[0]['symbol'], 'TEST_ETF')
        self.assertEqual(action[0]['price'], 95.0)
        self.assertEqual(action[0]['reason'], 'Entry Conditions Met')

    def test_exit_take_profit(self):
        prev_data = {
            'close': 95.0,
            'low': 94.0,
            'high': 96.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'rsi_70': 50.0,
        }
        data = {
            'close': 97.0,
            'low': 89.0,
            'high': 98.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'rsi_70': 25.0,  # Oversold (default exit threshold 35)
        }
        action = self.strategy.exit(data, prev_data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['action'], 'EXIT_SHORT')
        self.assertEqual(action[0]['reason'], 'Take Profit (RSI Oversold)')

    def test_exit_trend_reversal(self):
        prev_data = {
            'close': 95.0,
            'low': 94.0,
            'high': 96.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'rsi_70': 50.0,
        }
        data = {
            'close': 95.0,
            'low': 94.0,
            'high': 96.0,
            'vwap': 100.0,
            'ema_9': 98.0,
            'ema_21': 97.0,
            'rsi_70': 50.0,
        }
        action = self.strategy.exit(data, prev_data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['reason'], 'Trend Reversal')

    def test_exit_volatility_exhaustion(self):
        prev_data = {
            'close': 96.0,
            'low': 90.0,
            'high': 90.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'rsi_70': 50.0,
        }
        data = {
            'close': 97.0,
            'low': 84.0,
            'high': 98.0,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'rsi_70': 50.0,
        }
        action = self.strategy.exit(data, prev_data)

        # No dedicated volatility-band exit; RSI / EMA / VWAP stops did not trigger.
        self.assertEqual(action, [])

    def test_exit_stop_loss(self):
        prev_data = {
            'close': 100.0,
            'low': 99.5,
            'high': 100.5,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'rsi_70': 50.0,
        }
        data = {
            'close': 101.0,  # Above VWAP stop (100 * (1 + 0.2/100) = 100.2)
            'low': 100.0,
            'high': 101.5,
            'vwap': 100.0,
            'ema_9': 96.0,
            'ema_21': 97.0,
            'rsi_70': 50.0,
        }
        action = self.strategy.exit(data, prev_data)
        
        self.assertTrue(len(action) > 0)
        self.assertEqual(action[0]['reason'], 'Trend Failure (VWAP Stop)')

if __name__ == '__main__':
    unittest.main()
