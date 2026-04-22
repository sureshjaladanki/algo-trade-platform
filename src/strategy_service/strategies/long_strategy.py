import pandas as pd
from src.strategy_service.strategies.trade_strategy import TradeStrategy


class LongStrategy(TradeStrategy):
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

    # Focus on trend following / support levels
    def check_entry(self, data, regime_data=None):
        # Condition 1: Trading Session is safe for intraday positions (Longing a trade)
        safe_for_intraday_positions, _ = super().check_entry(data, regime_data)

        # Condition 2: Market Regime is safe for longs
        if self.regime and regime_data is not None:
            safe_for_long = self.regime.safe_for_longs(regime_data)
        else:
            safe_for_long = True

        # Condition 3: Micro Trend is UP (9 EMA > 21 EMA)
        micro_trend_up = data.get(self.ema_micro_fast_key, 0) > data.get(
            self.ema_micro_slow_key, 0
        )

        # Condition 4: Micro Pullback (RSI is oversold on 1m chart, indicating a dip)
        long_rsi_entry = self.config.get("long_rsi_entry", 40)
        pullback = data.get(self.rsi_key, 50) < long_rsi_entry

        # Condition 5: Price is below the Macro Fast VWMA (21 VWMA) and Macro Slow VWMA (45 VWMA)
        price_below_vwma_macro_slow = data["close"] < data.get(
            self.vwma_macro_slow_key, float("inf")
        )
        price_below_vwma_macro_fast = data["close"] < data.get(
            self.vwma_macro_fast_key, float("inf")
        )

        return (
            safe_for_intraday_positions
            & safe_for_long
            & micro_trend_up
            & pullback
            & price_below_vwma_macro_fast
            & price_below_vwma_macro_slow
        ), "Entry Conditions Met"

    def check_exit(self, data, prev_data=None, regime_data=None):
        # Exit 1: Trading Session is in squareoff window
        should_exit, _ = super().check_exit(data, prev_data, regime_data)

        # Exit 2: Momentum Exhaustion (Instantaneous)
        # We signal an exit if the market is currently overbought
        long_rsi_exit = self.config.get("long_rsi_exit", 70)
        take_profit = data.get(self.rsi_key, 50) > long_rsi_exit

        # Exit 3: Micro Trend Reversal (9 EMA crosses below 21 EMA — exit long on bearish micro cross)
        current_trend_down = data.get(self.ema_micro_fast_key, float("inf")) < data.get(
            self.ema_micro_slow_key, float("inf")
        )
        prev_trend_up = prev_data.get(
            self.ema_micro_fast_key, float("inf")
        ) >= prev_data.get(self.ema_micro_slow_key, float("inf"))
        trend_reversal = current_trend_down & prev_trend_up

        # Exit 4: Trend Failure Stop (Price drops below VWAP - Buffer)
        # This is a structural market failure, valid regardless of entry price
        vwap_stop_loss_pct = self.config.get("vwap_stop_loss_pct", 0.2)
        stop_loss_multiplier = 1 - (vwap_stop_loss_pct / 100)
        stop_loss_price = data.get("vwap", 0) * stop_loss_multiplier
        prev_stop_loss_price = prev_data.get("vwap", 0) * stop_loss_multiplier

        current_stop_loss = data["close"] < stop_loss_price
        prev_no_stop_loss = prev_data["close"] >= prev_stop_loss_price
        stop_loss = current_stop_loss & prev_no_stop_loss

        exits = should_exit | take_profit | trend_reversal | stop_loss

        if isinstance(should_exit, pd.Series):
            reason = "Exit Condition Met"
        else:
            if should_exit:
                reason = "End of Day Squareoff"
            elif take_profit:
                reason = "Take Profit (RSI Overbought)"
            elif trend_reversal:
                reason = "Trend Reversal"
            else:
                reason = "Trend Failure (VWAP Stop)"

        return exits, reason

    def buy(self, data, regime_data=None):
        """Execute Long BUY if entry conditions are met."""
        entries, reason = self.check_entry(data, regime_data)

        if isinstance(data, pd.DataFrame):
            return entries.fillna(False)

        if entries:
            return [
                {
                    "timestamp": data.name if hasattr(data, "name") else None,
                    "action": "LONG",
                    "symbol": self.symbol,
                    "price": data["close"],
                    "reason": reason,
                }
            ]

        return []

    def exit(self, data, prev_data=None, regime_data=None):
        """
        Execute EXIT purely based on stateless, instantaneous market indicators.
        Trade-lifecycle exits (Time Stops, Trailing Stops) must be handled by the OMS.
        """
        exits, reason = self.check_exit(data, prev_data, regime_data)

        if isinstance(data, pd.DataFrame):
            return exits.fillna(False)

        if exits:
            return [
                {
                    "timestamp": data.name if hasattr(data, "name") else None,
                    "action": "EXIT_LONG",
                    "symbol": self.symbol,
                    "price": data["close"],
                    "reason": reason,
                }
            ]

        return []
