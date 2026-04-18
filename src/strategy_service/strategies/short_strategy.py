from src.strategy_service.strategies.trade_strategy import TradeStrategy


class ShortStrategy(TradeStrategy):
    def __init__(self, symbol: str, symbol_profile=None, regime=None):
        super().__init__(symbol, symbol_profile=symbol_profile, regime=regime)
        rsi_period = self.config.get("rsi_period", 14)
        self.rsi_key = f"rsi_{rsi_period}"
        self.ema_micro_fast_key = f"ema_{self.config.get('ema_micro_fast_period', 9)}"
        self.ema_micro_slow_key = f"ema_{self.config.get('ema_micro_slow_period', 21)}"
        self.vwma_macro_slow_key = (
            f"vwma_{self.config.get('vwma_macro_slow_period', 45)}"
        )
        self.vwma_macro_fast_key = (
            f"vwma_{self.config.get('vwma_macro_fast_period', 21)}"
        )

    # Focus on trend following / resistance levels
    def check_entry(self, data):
        # Condition 1: Trading Session is safe for intraday positions (Shorting a trade)
        safe_for_intraday_positions = super().check_entry(data)

        # Condition 2: Market Regime is safe for shorts
        safe_for_short = self.regime.safe_for_shorts if self.regime else True

        # Condition 3: Micro Trend is DOWN (9 EMA < 21 EMA)
        micro_trend_down = data.get(self.ema_micro_fast_key, float("inf")) < data.get(
            self.ema_micro_slow_key, float("inf")
        )

        # Condition 4: Micro Pullback (RSI is overbought on 1m chart, indicating a rally to short)
        short_rsi_entry = self.config.get("short_rsi_entry", 60)
        pullback = data.get(self.rsi_key, 50) > short_rsi_entry

        # Condition 5: Price is above the Macro Fast VWMA (21 VWMA) and Macro Slow VWMA (45 VWMA)
        price_above_vwma_macro_fast = data["close"] > data.get(
            self.vwma_macro_fast_key, float("inf")
        )
        price_above_vwma_macro_slow = data["close"] > data.get(
            self.vwma_macro_slow_key, float("inf")
        )

        return (
            safe_for_intraday_positions
            and safe_for_short
            and micro_trend_down
            and pullback
            and price_above_vwma_macro_fast
            and price_above_vwma_macro_slow
        )

    def short(self, data):
        """Execute Short SELL if entry conditions are met."""
        if self.check_entry(data):
            return [
                {
                    "timestamp": data.name if hasattr(data, "name") else None,
                    "action": "SHORT",
                    "symbol": self.symbol,
                    "price": data["close"],
                    "reason": "Entry Conditions Met",
                }
            ]

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
        # We signal an exit if the market is currently oversold.
        # Made more sensitive (e.g., 35 or 40 instead of 30) for faster take profit during violent drops.
        short_rsi_exit = self.config.get("short_rsi_exit", 35)
        take_profit = data.get(self.rsi_key, 50) < short_rsi_exit

        # Exit 3: Micro Trend Reversal (5m 9 EMA crosses above 21 EMA)
        # Using faster EMAs (9/21) for exits cuts losses much quicker than waiting for macro (45/105) reversal.
        current_trend_up = data.get(self.ema_micro_fast_key, float("inf")) > data.get(
            self.ema_micro_slow_key, float("inf")
        )
        prev_trend_down = prev_data.get(
            self.ema_micro_fast_key, float("inf")
        ) <= prev_data.get(self.ema_micro_slow_key, float("inf"))
        trend_reversal = current_trend_up and prev_trend_down

        # Exit 4: Trend Failure Stop (Price breaks above VWAP + Buffer)
        # This is a structural market failure, valid regardless of entry price
        vwap_stop_loss_pct = self.config.get("vwap_stop_loss_pct", 0.2)
        stop_loss_multiplier = 1 + (vwap_stop_loss_pct / 100)
        stop_loss_price = data.get("vwap", float("inf")) * stop_loss_multiplier
        prev_stop_loss_price = (
            prev_data.get("vwap", float("inf")) * stop_loss_multiplier
        )

        current_stop_loss = data["close"] > stop_loss_price
        prev_no_stop_loss = prev_data["close"] <= prev_stop_loss_price
        stop_loss = current_stop_loss and prev_no_stop_loss

        if should_exit or take_profit or trend_reversal or stop_loss:
            if should_exit:
                reason = "End of Day Squareoff"
            elif take_profit:
                reason = "Take Profit (RSI Oversold)"
            elif trend_reversal:
                reason = "Trend Reversal"
            else:
                reason = "Trend Failure (VWAP Stop)"

            return [
                {
                    "timestamp": data.name if hasattr(data, "name") else None,
                    "action": "EXIT_SHORT",
                    "symbol": self.symbol,
                    "price": data["close"],
                    "reason": reason,
                }
            ]

        return []
