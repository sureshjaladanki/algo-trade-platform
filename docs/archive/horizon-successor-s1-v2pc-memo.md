# Successor S1 — V2p-c short residual (2026-08-18)

**Verdict:** V2p-c dual-fold **PASS**. Pooled session-block CI LB > 0 on the paired difference.  
**Log:** `data/GOLDEN_PARQUET/s1_v2pc.log`  
**Pre-registration:** [horizon-successor-s1-v2pc-preregistration.md](horizon-successor-s1-v2pc-preregistration.md) (locked before the run)  
**Harness:** `src/experiments/eval_horizon_successor_s1_v2pc.py`

## Modules

`src/horizon/m9/v2p_range.py` (train-locked `realized ~ implied` scale; bottom-tercile z; paired `R_imp − R`). Residual>0 was not retuned. `eval_horizon_m9_v2_stub.py` was not called.

## Numbers

AdmitPowerPlan printed **before** selection: per-fold n=80 sess=245 expected_mde=11.0 bps (< 15 → peek). Pooled sketch 7.7 bps.

Clock = first bar at/after **09:45**. Residual = `range_q50 − (a + b·implied)` with `(a, b)` from train `remaining_range ~ implied`. Bottom tercile of train-standardized z on test. Statistic = selected mean(`R_imp − R`) minus the all-session mean.

| Fold | Test sessions | Selected | Share | Paired CI (bps) | MDE | Gate |
|---|---|---|---|---|---|---|
| A | 245 | 61 | 24.9% | **[+9.7, +29.1]** | 9.7 | PASS |
| B | 244 | 89 | 36.5% | **[+21.2, +40.4]** | 9.6 | PASS |

**Pooled:** mean **+26.1 bps**, CI **[+19.6, +32.6] bps**, sign **2/2**, MDE **6.5 bps**, n=150 sess=150.

This is range-space, cost-free, incremental to unconditional short vol. It is not option PnL.

## Cleanup

No 10:00 / q75 / residual>0 salvage. Name V1 not used. Purge is a no-op on A/B (0 days).

## Decision

**Go on P1.** Index-option marks (S4-P1) are **earned**, not started: same-session Nifty chain at 09:45, not EOD bhavcopy, not name marks. V2/V3 remain. Hard daily premium-loss cap still required before a book.
