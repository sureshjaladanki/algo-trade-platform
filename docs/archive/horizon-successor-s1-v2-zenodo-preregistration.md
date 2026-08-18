# Successor S1 — V2 Zenodo last-trade (report-only)

**Locked:** 2026-08-18, before the ingest and before any premium number  
**Harness:** `src/experiments/eval_horizon_successor_s1_v2.py --snapshots data/GOLDEN_IV/nifty_option_snapshots_zenodo.parquet`  
**Source:** Bhat, Aparna (2024). *Nifty spot, futures and options one-minute data from 2017 to 2020*. Zenodo. https://doi.org/10.5281/zenodo.10899828 (CC0)  
**Depends on:** V2p-c PASS (`s1_v2pc.log`)

This is **not** quote V2 and **not** V3. Last-trade OHLC close is used as mid; bid = ask = close (spread ≡ 0). Quote S4-P1 stays open.

## Locked choices

| Item | Value |
|---|---|
| Selection | **Frozen V2p-c** on folds **A+B** (2018 / 2019). Do not retune |
| Instrument | Short Nifty ATM straddle. ATM = strike closest to GOLDEN `^NSEI` 09:45 close among strikes with CE **and** PE last-trade at 09:45 |
| Expiry | Prefer DTE ∈ **[1, 10]**. If none (2018 monthly-only), nearest expiry with **DTE ≥ 1**. Never 0-DTE |
| Entry / exit | 09:45 last-trade close → 15:15 last-trade close, **same** expiry/strike. Missing minute → drop session |
| Statistic | Session-block mean of short-straddle PnL in bps of GOLDEN spot (cost-free last-trade) |
| Companion | Paired vs all-session last-trade short straddle |
| Coverage | ≥ 70% of V2p-c selected sessions with both clocks |
| Authority | **Report-only.** Does not close P1. Does not earn V3 |

## Decision rule (report-only)

| Label | When |
|---|---|
| **PASS (report)** | Pooled CI LB > 0 and coverage ≥ 70% |
| **FAIL (report)** | LB ≤ 0 and coverage ≥ 70% |
| **INCONCLUSIVE** | Coverage < 70%, or missing 09:45/15:15 minute |

A report FAIL does **not** invoke P1 STOP. A report PASS does **not** acquire vendor quotes automatically. Quote V2 remains the authority peek.

## Forbidden

Treating this as quote V2, filling `ce_bid`/`ce_ask` from last-trade as if they were quotes, EOD bhavcopy, name V2 stub, retuning V2p-c, TradingTuitions 2021–22 as a substitute for this sample.
