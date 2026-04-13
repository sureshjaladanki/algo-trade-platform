from src.strategy_service.strategies.trade_strategy import TradeStrategy

class LongStrategy(TradeStrategy):
    def __init__(self, symbol: str, symbol_profile=None, regime=None):
        super().__init__(symbol, symbol_profile=symbol_profile, regime=regime)
        rsi_period = self.config.get('rsi_period', 14)
        self.rsi_key = f'rsi_{rsi_period}'
        # self.ema_micro_fast_key = f"ema_{self.config.get('ema_micro_fast_period', 9)}"
        # self.ema_micro_slow_key = f"ema_{self.config.get('ema_micro_slow_period', 21)}"
        self.ema_macro_fast_key = f"ema_{self.config.get('ema_macro_fast_period', 45)}"
        self.ema_macro_slow_key = f"ema_{self.config.get('ema_macro_slow_period', 105)}"
        self.adx_key = f"adx_{self.config.get('adx_period', 50)}"

    # Focus on trend following / support levels
    def check_entry(self, data):
        # Condition 1: Trading Session is safe for intraday positions (Longing a trade)
        safe_for_intraday_positions = super().check_entry(data)

        # Condition 2: Market Regime is safe for longs
        safe_for_long = self.regime.safe_for_longs if self.regime else True

        # Condition 3: Macro Trend is UP (Simulated 5m 9 EMA > 5m 21 EMA)
        macro_trend_up = data.get(self.ema_macro_fast_key, 0) > data.get(self.ema_macro_slow_key, 0)

        # Condition 4: Macro Trend Strength (ADX > threshold indicates a strong trend, avoiding whipsaws)
        adx_threshold = self.config.get('adx_threshold', 11)
        macro_trend_strong = data.get(self.adx_key, 0) > adx_threshold

        # Condition 5: Micro Pullback (RSI is oversold on 1m chart, indicating a dip)
        long_rsi_entry = self.config.get('long_rsi_entry', 40)
        pullback = data.get(self.rsi_key, 50) < long_rsi_entry
        
        return safe_for_intraday_positions and safe_for_long and macro_trend_up and pullback and macro_trend_strong

    def buy(self, data):
        """Execute Long BUY if entry conditions are met."""
        if self.check_entry(data):
            return [{
                "timestamp": data.name if hasattr(data, 'name') else None,
                "action": "LONG",
                "symbol": self.symbol,
                "price": data['close'],
                "reason": "Entry Conditions Met"
            }]

        return []

    def exit(self, data, prev_data=None):
        """
        Execute EXIT purely based on stateless, instantaneous market indicators.
        Trade-lifecycle exits (Time Stops, Trailing Stops) must be handled by the OMS.
        """
        if prev_data is None:
            return []
            
        # Exit 1: Trading Session is in squareoff window
        should_exit = self.check_exit(data, prev_data)

        # Exit 2: Momentum Exhaustion (Instantaneous)
        # We signal an exit if the market is currently overbought
        long_rsi_exit = self.config.get('long_rsi_exit', 70)
        take_profit = data.get(self.rsi_key, 50) > long_rsi_exit
        
        # Exit 3: Macro Trend Reversal (Simulated 5m 9 EMA crosses below 21 EMA)
        current_trend_down = data.get(self.ema_macro_fast_key, 0) < data.get(self.ema_macro_slow_key, 0)
        prev_trend_up = prev_data.get(self.ema_macro_fast_key, 0) >= prev_data.get(self.ema_macro_slow_key, 0)
        trend_reversal = current_trend_down and prev_trend_up
        
        # Exit 4: Trend Failure Stop (Price drops below VWAP - Buffer)
        # This is a structural market failure, valid regardless of entry price
        vwap_stop_loss_pct = self.config.get('vwap_stop_loss_pct', 0.2)
        stop_loss_multiplier = 1 - (vwap_stop_loss_pct / 100)
        stop_loss_price = data.get('vwap', 0) * stop_loss_multiplier
        prev_stop_loss_price = prev_data.get('vwap', 0) * stop_loss_multiplier
            
        current_stop_loss = data['close'] < stop_loss_price
        prev_no_stop_loss = prev_data['close'] >= prev_stop_loss_price
        stop_loss = current_stop_loss and prev_no_stop_loss
        
        if should_exit or take_profit or trend_reversal or stop_loss:
            if should_exit:
                reason = "End of Day Squareoff"
            elif take_profit:
                reason = "Take Profit (RSI Overbought)"
            elif trend_reversal:
                reason = "Trend Reversal"
            else:
                reason = "Trend Failure (VWAP Stop)"
                
            return [{
                "timestamp": data.name if hasattr(data, 'name') else None,
                "action": "EXIT_LONG",
                "symbol": self.symbol,
                "price": data['close'],
                "reason": reason
            }]
            
        return []#
