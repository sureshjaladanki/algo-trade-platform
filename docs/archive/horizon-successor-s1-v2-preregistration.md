# Successor S1 — V2 index-option pre-registration

**Locked:** 2026-08-18, before marks exist and before the authority run  
**Harness:** `src/experiments/eval_horizon_successor_s1_v2.py`  
**Charter:** [horizon-successor-s4-p1-index-marks-charter.md](../next/horizon-successor-s4-p1-index-marks-charter.md)  
**Depends on:** V2p-c PASS (`s1_v2pc.log`); S4-P1 coverage ≥ 70%

Do not peek until the coverage gate PASSes. This file is locked so premium PnL cannot retune selection.

## Locked choices

| Item | Value |
|---|---|
| Selection | **Frozen V2p-c** (09:45, train-locked bottom tercile). Do not retune residual, κ, or clock |
| Instrument | Short Nifty ATM straddle, nearest expiry with DTE ∈ [1, 10] |
| Entry / exit | 09:45 mid → 15:15 mid, same session |
| Statistic | Session-block mean of short-straddle PnL in **bps of spot** on selected sessions. Cost-free (mids) |
| Companion | Paired: selected mean minus all-session short-straddle mean (incremental to unconditional short vol) |
| Folds | Dual-fold A+B, pooled session-block CI; per-fold sign companion |
| Coverage | ≥ 70% of V2p-c selected sessions have both snapshots, else abort INCONCLUSIVE |
| V3 | Not this peek. 2026 STT 0.15% of premium is locked in the S4-P1 charter |

## Decision rule

| Verdict | When |
|---|---|
| **PASS** | Pooled session-block CI LB > 0 on selected gross PnL |
| **FAIL** | LB ≤ 0 on a passable sample (coverage ≥ 70%, MDE published) |
| **INCONCLUSIVE** | Coverage < 70%, or store missing, or declared MDE wider than a pre-printed abort (print MDE before the peek) |

**On FAIL:** P1 CLOSED in premium space. Do not salvage with name V1 or EOD bhavcopy.  
**On PASS:** V3 is earned (same sessions, quoted spread + 2026 STT). Not a ship.

## Forbidden

`eval_horizon_m9_v2_stub.py`, `option_marks_daily.parquet`, EOD bhavcopy, 10:00, residual>0, changing the V2p-c tercile after seeing PnL.
