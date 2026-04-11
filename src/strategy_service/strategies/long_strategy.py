from src.strategy_service.strategies.trade_strategy import TradeStrategy

class LongStrategy(TradeStrategy):
    def __init__(self, symbol: str, symbol_profile=None, regime=None):
        super().__init__(symbol, symbol_profile=symbol_profile, regime=regime)
        rsi_period = self.config.get('rsi_period', 14)
        self.rsi_key = f'rsi_{rsi_period}'
        self.ema_micro_fast_key = f"ema_{self.config.get('ema_micro_fast_period', 9)}"
        self.ema_micro_slow_key = f"ema_{self.config.get('ema_micro_slow_period', 21)}"
        self.ema_macro_fast_key = f"ema_{self.config.get('ema_macro_fast_period', 45)}"
        self.ema_macro_slow_key = f"ema_{self.config.get('ema_macro_slow_period', 105)}"
        self.adx_key = f"adx_{self.config.get('adx_period', 14)}"

    # Focus on trend following / support levels
    def check_entry(self, data):
        # Condition 1: Trading Session is safe for intraday positions (Longing a trade)
        safe_for_intraday_positions = super().check_entry(data)

        # Condition 2: Market Regime is safe for longs
        safe_for_long = self.regime.safe_for_longs if self.regime else True

        # Condition 3: Macro Trend is UP (Simulated 5m 9 EMA > 5m 21 EMA)
        macro_trend_up = data.get(self.ema_macro_fast_key, 0) > data.get(self.ema_macro_slow_key, 0)

        # Condition 4: Macro Trend Strength (ADX > threshold indicates a strong trend, avoiding whipsaws)
        # NOTE: The Over-Fit Risk: ADX (ADX > threshold) is a proxy for trend strength. However, your sufficient_margin check already measures if the trend is strong enough to reach a target.
        # adx_threshold = self.config.get('adx_threshold', 25)
        # macro_trend_strong = data.get(self.adx_key, 0) > adx_threshold
        
        # Condition 5: Micro Intraday Trend is UP (Price above VWAP)
        # micro_trend_up = data['close'] > data.get('vwap', float('inf'))
        
        # Condition 6: Micro Pullback (RSI is oversold on 1m chart, indicating a dip)
        long_rsi_entry = self.config.get('long_rsi_entry', 40)
        pullback = data.get(self.rsi_key, 50) < long_rsi_entry
        
        # Condition 7: Volatility Filter (Bollinger Band Width)
        # NOTE: The Over-Fit Risk: Bollinger Band Width (bb_width_pct) is a proxy for volatility. However, your sufficient_margin check already measures if the volatility is high enough to reach a target.
        # bb_width_pct = data.get('bb_width_pct', 0)
        # min_bbw_pct = self.config.get('min_bbw_pct', 0.5)
        # sufficient_volatility = bb_width_pct > min_bbw_pct

        # Condition 8: Margin for Profit Check
        prev_atr = self.symbol_profile.get('prev_atr', 0) if self.symbol_profile else 0
        if prev_atr > 0:
            profit_margin_atr_multiplier = self.config.get('profit_margin_atr_multiplier', 0.2)
            expected_profit_abs = data.get('bb_upper', data['close']) - data['close']
            sufficient_margin = expected_profit_abs > (profit_margin_atr_multiplier * prev_atr)
        else:
            expected_profit_pct = data.get('expected_profit_pct_long', 0)
            profit_margin_pct_threshold = self.config.get('profit_margin_pct_threshold', 0.2)
            sufficient_margin = expected_profit_pct > profit_margin_pct_threshold

        # Condition 9: Risk-to-Reward (R:R) Ratio Check
        min_rr_ratio = self.config.get('min_rr_ratio', 1.5)
        entry_price = data['close']
        target_price = data.get('bb_upper', entry_price) # Target is Upper BB
        
        # Estimate stop loss price matching the exit logic
        if prev_atr > 0:
            vwap_atr_stop_multiplier = self.config.get('vwap_atr_stop_multiplier', 0.2)
            stop_loss_price = data.get('vwap', entry_price) - (vwap_atr_stop_multiplier * prev_atr)
        else:
            vwap_stop_loss_pct = self.config.get('vwap_stop_loss_pct', 0.2)
            stop_loss_multiplier = 1 - (vwap_stop_loss_pct / 100)
            stop_loss_price = data.get('vwap', entry_price) * stop_loss_multiplier

        risk = entry_price - stop_loss_price
        reward = target_price - entry_price
        
        # Ensure risk is positive to avoid division by zero
        favorable_rr = (reward / risk >= min_rr_ratio) if risk > 0 else False

        return safe_for_intraday_positions and safe_for_long and macro_trend_up and pullback and sufficient_margin and favorable_rr

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
        # We signal an exit if the market is currently overbought AND showing immediate weakness
        long_rsi_exit = self.config.get('long_rsi_exit', 70)
        rsi_overbought = data.get(self.rsi_key, 50) > long_rsi_exit
        
        current_price_below_fast_ema = data['close'] < data.get(self.ema_micro_fast_key, 0)
        # prev_price_above_fast_ema = prev_data['close'] >= prev_data.get(self.ema_micro_fast_key, 0)
        take_profit = rsi_overbought and current_price_below_fast_ema
        
        # Exit 3: Macro Trend Reversal (Simulated 5m 9 EMA crosses below 21 EMA)
        current_trend_down = data.get(self.ema_macro_fast_key, 0) < data.get(self.ema_macro_slow_key, 0)
        prev_trend_up = prev_data.get(self.ema_macro_fast_key, 0) >= prev_data.get(self.ema_macro_slow_key, 0)
        trend_reversal = current_trend_down and prev_trend_up
        
        # Exit 4: Trend Failure Stop (Price drops below VWAP - Buffer)
        # This is a structural market failure, valid regardless of entry price
        prev_atr = self.symbol_profile.get('prev_atr', 0) if self.symbol_profile else 0
        if prev_atr > 0:
            vwap_atr_stop_multiplier = self.config.get('vwap_atr_stop_multiplier', 0.2)
            stop_loss_price = data.get('vwap', 0) - (vwap_atr_stop_multiplier * prev_atr)
            prev_stop_loss_price = prev_data.get('vwap', 0) - (vwap_atr_stop_multiplier * prev_atr)
        else:
            vwap_stop_loss_pct = self.config.get('vwap_stop_loss_pct', 0.2)
            stop_loss_multiplier = 1 - (vwap_stop_loss_pct / 100)
            stop_loss_price = data.get('vwap', 0) * stop_loss_multiplier
            prev_stop_loss_price = prev_data.get('vwap', 0) * stop_loss_multiplier
            
        current_stop_loss = data['close'] < stop_loss_price
        prev_no_stop_loss = prev_data['close'] >= prev_stop_loss_price
        stop_loss = current_stop_loss and prev_no_stop_loss
        
        # Exit 5: Volatility Exhaustion (Instantaneous)
        # Reversal Pattern: Current Close is below the Previous Low (Bearish Engulfing/Reversal)
        candle_reversal = data['close'] < prev_data['low']
        # current_price_below_slow_ema = data['close'] < data.get(self.ema_micro_slow_key, 0)
        # prev_price_above_slow_ema = prev_data['close'] >= prev_data.get(self.ema_micro_slow_key, 0)
        bb_hit_upper_band = data['high'] >= data.get('bb_upper', float('inf'))
        volatility_exhaustion = bb_hit_upper_band and candle_reversal

        if should_exit or take_profit or trend_reversal or stop_loss or volatility_exhaustion:
            if should_exit:
                reason = "End of Day Squareoff"
            elif volatility_exhaustion:
                reason = "Volatility Exhaustion (BB + Slow EMA)"
            elif take_profit:
                reason = "Take Profit (RSI + Fast EMA)"
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
