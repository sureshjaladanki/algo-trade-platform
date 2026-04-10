# ETF Intraday Trading Configuration Rationale

This document explains the reasoning and expert judgment behind the intraday trading configurations applied to the various ETF `.yml` files in the `config/` directory.

## Core Philosophy

The trading configurations are built around a combination of **Mean Reversion** (using RSI and Bollinger Bands), **Trend Filtering** (using EMAs, VWAP, and ADX), and **Risk Management** (using ATR-based stops and R:R ratios). Because different indices and sectors exhibit unique price action, volatility, and liquidity profiles, applying a "one-size-fits-all" parameter set leads to suboptimal performance. 

Instead, parameters are tailored to the specific "personality" of each underlying index.

### Standardized Parameters Across All ETFs
*   **EMA Periods (`45` & `105`)**: Used for macro trend direction. These provide a stable baseline to filter out intraday noise and ensure we are trading in the direction of the dominant session trend.
*   **Micro EMA Periods (`9` & `21`)**: Used for short-term momentum and exit signals (e.g., price dropping below 9 EMA).
*   **ADX Period (`14` or `70`) & Threshold**: Used to measure macro trend strength and avoid whipsaws in ranging markets.
*   **Relative Volume (RVOL) Thresholds**: Ensures sufficient liquidity and participation based on the specific trading session (Opening, Midday, Closing).
*   **Gap ATR Ratio Limit**: Prevents entering trades when the opening gap is too large relative to the daily Average True Range (ATR), avoiding overextended markets.
*   **Profit Margin & Risk-to-Reward (R:R)**: Dynamic checks using ATR to ensure the expected profit (target: Upper BB) justifies the risk (stop: VWAP - ATR buffer), enforcing a minimum R:R ratio (e.g., `1.5`).
*   **Volatility Filter (BB Width %)**: Requires a minimum Bollinger Band width to ensure there is enough intraday volatility to capture meaningful moves.

### Dynamic Parameters
*   **RSI Period**: Set to `14` for stable indices (like Nifty 50) to filter out noise. Set to `9` for highly volatile/sectoral indices (like PSU Banks, IT, Junior Nifty) to ensure the indicator is fast enough to actually reach the extreme overbought/oversold bands during sharp intraday spikes, preventing "trade starvation".

---

## ETF-Specific Judgments

### 1. NIFTYBEES (Nifty 50)
*   **Profile**: The benchmark index. High liquidity, moderate volatility, and generally smooth price action.
*   **RSI Bands (40/70 Long, 60/30 Short)**: Because it is less volatile, we don't need extreme RSI levels to find good mean-reversion entries. Standard 40/60 levels work well for pullbacks within a trend.
*   **VWAP Stop Loss (`0.2%` or ATR Multiplier)**: Tight stop loss because Nifty 50 tends to respect VWAP closely. If it breaks VWAP by more than 0.2% (or the equivalent ATR buffer), the intraday trend has likely shifted.
*   **Bollinger Bands (`2.0` Std Dev)**: Standard 2.0 standard deviation is sufficient to capture 95% of price action without being overly restrictive.

### 2. JUNIORBEES (Nifty Next 50)
*   **Profile**: Higher beta and higher volatility compared to Nifty 50. Comprises large-cap stocks that are more prone to sudden momentum bursts.
*   **RSI Bands (35/75 Long, 65/25 Short)**: Widened compared to NIFTYBEES. The higher volatility means the index frequently pushes deeper into overbought/oversold territory before reversing. Uses a fast 9-period RSI to capture these rapid momentum shifts.
*   **VWAP Stop Loss (`0.3%`)**: Widened to accommodate larger intraday swings and prevent premature stop-outs from market noise.
*   **Bollinger Bands (`2.2` Std Dev)**: Increased to 2.2 to account for the higher standard deviation of price movements.

### 3. BANKBEES (Bank Nifty)
*   **Profile**: Highly volatile, strong trending moves, heavily weighted towards a few large private banks. Often drives the broader market direction.
*   **RSI Bands (35/75 Long, 65/25 Short)**: Similar to JUNIORBEES, requires wider bands to avoid getting caught in momentum traps during strong banking rallies or sell-offs.
*   **VWAP Stop Loss (`0.25%`)**: Slightly wider than Nifty, but tighter than Junior Nifty because when Bank Nifty breaks VWAP, it usually signals a strong reversal.
*   **Bollinger Bands (`2.2` Std Dev)**: Adjusted for higher banking volatility.

### 4. ITBEES (Nifty IT)
*   **Profile**: Heavily influenced by global cues (e.g., NASDAQ) leading to frequent gap-ups/gap-downs. Once a gap occurs, it can consolidate for long periods or trend strongly in one direction.
*   **RSI Bands (30/70 Long, 70/30 Short)**: IT stocks can stay overbought or oversold for extended periods. We require extreme RSI levels (30/70) for mean reversion to ensure the momentum has actually exhausted.
*   **VWAP Stop Loss (`0.35%`)**: Wider stop loss to account for gap-fill volatility and sudden currency-driven (USD/INR) price spikes.
*   **Bollinger Bands (`2.5` Std Dev)**: Very wide to avoid false breakouts during long consolidation periods.

### 5. PSUBNKBEES (Nifty PSU Bank)
*   **Profile**: Extremely volatile, highly news-driven (government policies, RBI regulations), and prone to sharp spikes followed by deep pullbacks.
*   **RSI Bands (30/75 Long, 70/25 Short)**: Very wide bands. PSU banks frequently exhibit "irrational exuberance" or panic selling. We only want to enter at absolute extremes. Coupled with a fast 9-period RSI to ensure these extremes are actually hit during intraday spikes.
*   **VWAP Stop Loss (`0.4%`)**: The widest stop loss in the portfolio. PSU banks frequently test and briefly pierce VWAP before resuming their trend. A tight stop here guarantees "death by a thousand cuts."
*   **Bollinger Bands (`2.5` Std Dev)**: Maximum width to filter out the extreme intraday noise characteristic of PSU stocks.

### 6. AUTOBEES (Nifty Auto)
*   **Profile**: Cyclical sector with moderate volatility. Tends to have steady, grinding intraday trends rather than explosive spikes.
*   **RSI Bands (35/70 Long, 65/30 Short)**: Moderate bands. Does not require the extremes of IT or PSU Banks, but needs slightly more room than Nifty 50.
*   **VWAP Stop Loss (`0.3%`)**: Standard widened stop loss for sector-specific ETFs.
*   **Bollinger Bands (`2.0` Std Dev)**: Standard deviation works well here due to the steady nature of auto sector trends.

---

## Conclusion
By tailoring RSI extremes, VWAP stop losses (or ATR buffers), Bollinger Band deviations, and risk-to-reward ratios to the specific volatility and liquidity profiles of each ETF, the algorithmic trading platform is better equipped to maximize win rates and minimize drawdowns caused by instrument-specific noise.
