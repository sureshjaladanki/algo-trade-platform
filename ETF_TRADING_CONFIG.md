# ETF Intraday Trading Configuration (as implemented)

This document describes what the current `strategy_service` actually does with the per-ETF YAML files in `config/`, and why the current parameter values differ by ETF.

## What runs where

- **Engine**: `src/strategy_service/engine.py`
  - Loads `config/strategy_engine.yml` to choose trade symbols and the regime inputs.
  - Builds symbol profiles from historical files:
    - `data/processed/<SYMBOL>_1m_history.csv` (minute-of-day volume profile)
    - `data/processed/<SYMBOL>_1d_30d.csv` (previous close + previous ATR)
  - Replays the “current day” minute stream from `data/processed/<SYMBOL>_1m_current_day.csv`.
  - When run as a script, writes `data/output/all_signals.csv`.

- **Regime gate**: `src/strategy_service/strategies/regime_strategy.py`
  - Loads `config/regime_indicators.yml` for VIX levels, trading sessions, and A/D EMA lengths.
  - Uses `regime_symbol` + `advance_decline_symbols` from `config/strategy_engine.yml` to compute:
    - `safe_for_longs`
    - `safe_for_shorts`

- **Trade strategies**: `src/strategy_service/strategies/long_strategy.py`, `short_strategy.py`
  - Load per-symbol config from `config/<SYMBOL>.yml` (e.g., `config/NIFTYBEES.NS.yml`).
  - Emit **stateless** entry/exit *signals*; trade lifecycle management is expected downstream (OMS).

## Core strategy (current behavior)

This is **trend + pullback**, gated by regime, with structural exits.

### Shared pre-entry filters (apply to both long and short)
Implemented in `TradeStrategy.check_entry()`:

- **Session gate**: only trade when `TradingSession.WARMUP < session < TradingSession.CLOSING`.
- **Liquidity gate (RVOL)**: require `rvol > session_volume_threshold[opening|midday|closing]`.
  - `rvol` is computed vs each symbol’s minute-of-day average volume profile derived from `*_1m_history.csv`.
- **Gap filter**: require `abs(gap_atr_ratio) <= gap_atr_ratio_limit`.
  - `gap_atr_ratio` is computed once per run using the “current day” open vs `prev_close`, normalized by `prev_atr` from `*_1d_30d.csv`.

### Long entry
- **Regime**: `RegimeStrategy.safe_for_longs` must be true.
- **Micro trend**: `EMA(ema_micro_fast_period) > EMA(ema_micro_slow_period)` (configs use 9/21).
- **Trend strength**: `ADX(adx_period) > adx_threshold`.
- **Pullback**: `RSI(rsi_period) < long_rsi_entry`.
- **Location filter**: `close < VWMA(vwma_macro_fast_period)` (configs use 21).

Signal emitted: `LONG`.

### Short entry
- **Regime**: `RegimeStrategy.safe_for_shorts` must be true.
- **Micro trend**: `EMA(ema_micro_fast_period) < EMA(ema_micro_slow_period)`.
- **Trend strength**: `ADX(adx_period) > adx_threshold`.
- **Pullback**: `RSI(rsi_period) > short_rsi_entry`.
- **Location filter**: `close > VWMA(vwma_macro_slow_period)` (configs use 45).

Signal emitted: `SHORT`.

### Exits (signals only)
Both strategies emit exit signals on any of:

- **End-of-day squareoff edge**: first bar where `trading_session > CLOSING`.
- **RSI take-profit**:
  - Long: RSI \(>\) `long_rsi_exit`
  - Short: RSI \(<\) `short_rsi_exit`
- **Micro trend reversal edge**: an EMA(9/21) cross event vs the previous bar.
- **VWAP structural stop edge** (edge-triggered):
  - Long: `close < vwap * (1 - vwap_stop_loss_pct/100)`
  - Short: `close > vwap * (1 + vwap_stop_loss_pct/100)`

Signals emitted: `EXIT_LONG` / `EXIT_SHORT` with a `reason`.

## Regime definition (VIX + breadth)

Regime uses:

- **VIX source**: `regime_symbol` (currently `^INDIAVIX`).
- **Breadth**: advance/decline computed from `advance_decline_symbols` by comparing each component’s close vs its prior close per bar, producing:
  - `ad_net_breadth`
  - `ad_cumulative`
  - `ad_ema_<fast>` and `ad_ema_<slow>` (periods from `config/regime_indicators.yml`)

Then:

- **safe_for_longs**: `vix < vix_levels.high` AND `ad_cumulative > ad_ema_fast` AND `ad_cumulative > ad_ema_slow`
- **safe_for_shorts**: `vix > vix_levels.low` AND `ad_cumulative < ad_ema_fast` AND `ad_cumulative < ad_ema_slow`

## Per-ETF YAML keys: used vs not used (today)

### Keys currently used by `strategy_service`
- `rsi_period`
- `session_volume_threshold` (opening/midday/closing)
- `gap_atr_ratio_limit`
- `ema_micro_fast_period`, `ema_micro_slow_period`
- `adx_period`, `adx_threshold`
- `vwma_macro_fast_period`, `vwma_macro_slow_period`
- `long_rsi_entry`, `long_rsi_exit`, `short_rsi_entry`, `short_rsi_exit`
- `vwap_stop_loss_pct`

### Present in YAML but NOT currently enforced by `strategy_service`
These appear in per-ETF configs but are not referenced by the current entry/exit logic:

- `stop_loss_pct`
- `max_pos_size`, `min_pos_size`
- `vwap_atr_stop_multiplier`
- `profit_margin_pct_threshold`, `profit_margin_atr_multiplier`, `min_rr_ratio`
- `bb_period`, `bb_std_dev`, `min_bbw_pct`
- `ema_macro_fast_period`, `ema_macro_slow_period`

If you intend these controls to be active, they need to be wired into `TradeStrategy` / `LongStrategy` / `ShortStrategy` (or handled downstream by OMS).

---

## ETF-specific rationale (aligned to current configs)

The per-ETF files primarily tune:
- **Pullback depth** (RSI entry/exit levels)
- **Trend selectivity** (ADX threshold)
- **VWAP tolerance** (`vwap_stop_loss_pct`)
- **Liquidity + gap strictness** (`session_volume_threshold`, `gap_atr_ratio_limit`)

### NIFTYBEES.NS (Nifty 50)
- **Why tighter structure**: most liquid and typically cleaner intraday structure.
- **Config highlights**:
  - RSI(11): long entry 56 / exit 72; short entry 42 / exit 35
  - VWAP stop buffer: 0.52%
  - Gap filter: 0.78 ATR (stricter)
  - ADX threshold: 11

### JUNIORBEES.NS (Nifty Next 50)
- **Why slightly looser**: higher beta vs Nifty 50, more overshoot/mean “snapbacks.”
- **Config highlights**:
  - RSI(11): long entry 58 / exit 74; short entry 40 / exit 33
  - VWAP stop buffer: 0.60%
  - Gap filter: 0.85 ATR
  - ADX threshold: 12

### BANKBEES.NS (Bank Nifty)
- **Why strongest trend filter**: banking can chop violently; bias toward only stronger trends.
- **Config highlights**:
  - RSI(11): long entry 60 / exit 76; short entry 38 / exit 31
  - VWAP stop buffer: 0.70%
  - Gap filter: 1.05 ATR
  - ADX threshold: 14

### ITBEES.NS (Nifty IT)
- **Why cue/gap-aware**: IT is more prone to gap-driven sessions.
- **Config highlights**:
  - RSI(12): long entry 56 / exit 73; short entry 42 / exit 34
  - VWAP stop buffer: 0.48%
  - Gap filter: 0.95 ATR
  - ADX threshold: 12

### PSUBNKBEES.NS (Nifty PSU Bank)
- **Why widest structural tolerance**: highest noise; VWAP gets probed more often.
- **Config highlights**:
  - RSI(11): long entry 59 / exit 75; short entry 39 / exit 32
  - VWAP stop buffer: 0.74%
  - Gap filter: 1.10 ATR
  - ADX threshold: 13

### AUTOBEES.NS (Nifty Auto)
- **Why “middle ground”**: sectoral swings, but typically less chaotic than PSU banks.
- **Config highlights**:
  - RSI(11): long entry 59 / exit 75; short entry 39 / exit 32
  - VWAP stop buffer: 0.64%
  - Gap filter: 0.95 ATR
  - ADX threshold: 13

## Outputs

When running `src/strategy_service/engine.py` as a script, signals are saved to `data/output/all_signals.csv` with columns:
- `timestamp`
- `action` (`LONG`, `SHORT`, `EXIT_LONG`, `EXIT_SHORT`)
- `symbol`
- `price`
- `reason`
