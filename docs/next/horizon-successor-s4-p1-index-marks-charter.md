# Successor S4-P1 — Index option marks (same-session Nifty)

**Status:** **STOPPED / waived** — earned by V2p-c PASS; do **not** acquire after last-trade V2 FAIL (report). See [horizon-successor-stop-memo.md](../archive/horizon-successor-stop-memo.md).  
**Date:** 2026-08-18  
**Authority:** [horizon-successor-architecture-blueprint.md](horizon-successor-architecture-blueprint.md) Rev 3 §4.3 V2/V3  
**Why this is earned:** V2p-c pooled paired CI [+19.6, +32.6] bps on remaining-session range space. That is not option PnL. V2 needs a **09:45 Nifty chain**, not EOD settle.

This is an **acquisition charter**, not a peek. Do not run V2 until coverage PASSes.

## Hypothesis (product)

Short the Nifty ATM straddle from the V2p-c decision bar (09:45) to MIS flatten (15:15) on the **same** selected sessions. V2 is gross (mid–mid). V3 is net of the 2026 forward schedule below.

## Locked source

| Option | Use |
|---|---|
| Vendor **intraday** Nifty option quotes (bid/ask) at **09:45** and **15:15** | **Required** for V2 |
| NSE FO bhavcopy / EOD FO reports | **Forbidden** as a remaining-session mark (clock mismatch; same class as name V1 `b_imp` ≈ 0.14) |
| India VIX / synthetic BS(path, VIX) | Not V2. Range-space residual already measured |
| `option_marks_daily.parquet` / name V2 stub | **Forbidden**. Name book, overnight hold |
| Unofficial scraped live APIs as history | **Forbidden** for authority (M9-0 lock) |

Do **not** download SSF. Do **not** extend M9-0 name IV.

## Target schema

Store: `data/GOLDEN_IV/nifty_option_snapshots.parquet` (gitignored). One row per `(date_only, time_only)` snapshot of the **held** ATM contract.

| Column | Type | Meaning |
|---|---|---|
| `underlying` | Utf8 | `^NSEI` |
| `date_only` | Date | Session date |
| `time_only` | Time | Quote clock (**09:45** entry or **15:15** flatten) |
| `spot` | Float64 | Nifty spot at that clock |
| `expiry` | Date | Held expiry |
| `strike` | Float64 | ATM strike (closest to spot at **09:45**; held through flatten) |
| `dte` | Int32 | Calendar days to expiry at the snapshot |
| `ce_bid`, `ce_ask` | Float64 | Call quotes |
| `pe_bid`, `pe_ask` | Float64 | Put quotes |
| `source` | Utf8 | Vendor id (not `nse_bhavcopy_bs`) |

ATM is chosen **once** at 09:45. The 15:15 row is the **same** expiry/strike.

## Contract / expiry

| Item | Value |
|---|---|
| Underlying | Nifty only (`^NSEI`) |
| Instrument | Short ATM straddle (sell CE + sell PE) |
| Expiry | Nearest expiry with DTE ∈ **[1, 10]** at 09:45 (weekly when it exists, else monthly). Do not default 0-DTE pin |
| Entry | 09:45 (Stage B `open_30m` complete) |
| Exit | 15:15 MIS flatten, same session. No overnight |

## Coverage gate (before V2)

Rebuild V2p-c selection (frozen definition; do not retune). Require **≥ 70%** of selected sessions in folds A and B to have **both** 09:45 and 15:15 snapshots on the held contract. Below that → V2 is **INCONCLUSIVE** (thin marks), not FAIL.

## V3 friction (locked before V2; applied only after V2 PASS)

Forward **2026-04-01** schedule (Finance Act 2026). Sample-era STT is a companion, not the hurdle.

| Line | Lock |
|---|---|
| STT options sell | **0.15% of premium**, seller (open short straddle). Buy-to-close: no STT |
| STT on exercise | Not used — flatten is a close-out, not exercise |
| Spread | Quoted: sell at bid, buy-to-close at ask. V2 is mid–mid; V3 uses the quotes |
| Slippage companion | +₹0.05 per leg (4 ticks round-trip on the straddle) |
| Brokerage companion | ₹20 × 4 orders, converted to bps of spot with contemporaneous lot — report-only |
| Sample-era STT reprint | 0.0625% of premium (2018–19) — companion only |

Do not delta-hedge on this charter.

## Exit criteria

- [ ] Vendor identified and licensed for 2018–2019 (folds A/B test windows)  
- [ ] `nifty_option_snapshots.parquet` readable by `src.horizon.m9.index_option_store`  
- [ ] Coverage ≥ 70% of V2p-c selected sessions, both clocks  
- [ ] V2 peek only after that coverage PASS, under [horizon-successor-s1-v2-preregistration.md](../archive/horizon-successor-s1-v2-preregistration.md)

## Forbidden

EOD bhavcopy as V2, name marks, unblocking `eval_horizon_m9_v2_stub.py`, synthetic VIX-BS as authority, scanning a new clock, retuning V2p-c after seeing premium PnL, SSF download.

**Report-only companion (not this charter):** Zenodo last-trade 1m (Bhat 2024) may fill `nifty_option_snapshots_zenodo.parquet` with bid = ask = close. That run does not start or close S4-P1. See [horizon-successor-s1-v2-zenodo-memo.md](../archive/horizon-successor-s1-v2-zenodo-memo.md).
