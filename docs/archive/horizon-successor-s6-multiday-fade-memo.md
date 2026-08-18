# Successor S6 — Multi-day fade (2026-08-18)

**Verdict:** T+3 at c = 6 bps **INCONCLUSIVE** (realized MDE 10.2 ≥ 6). Sign 2/6. Do not buy SSF.  
**Log:** `data/GOLDEN_PARQUET/s6_multiday.log`  
**Charter:** [horizon-successor-s6-multiday-fade-charter.md](../next/horizon-successor-s6-multiday-fade-charter.md) (locked before the run)  
**Harness:** `src/experiments/eval_horizon_successor_s6_multiday.py`

## Modules

`src/horizon/successor/fade_bound.py` (`attach_multiday_close_drift`: daily close-to-close, unique symbol-date, disaster **clip**). First live multi-day caller of `k5_pooled`. Frozen rule only: `prior_day_high_reject` Short.

## Numbers

AdmitPowerPlan printed **before** the peek: n=6000 sess=1320 assumed σ=400 bps → sketch MDE 27 bps. Realized session-block is the authority.

Transition events 88,570 → 58,905 unique symbol-days at T+3 (entry = daily close, not the event bar). Authority folds R2017–R2022, n=40,272 sess=1,476. Disaster clip 4,413 rows at −500 bps (not dropped).

| Horizon | Pooled c=6 CI (bps) | Sign | MDE | Verdict |
|---|---|---|---|---|
| T+1 (companion) | [−17.0, −4.1] | 0/6 | 6.4 | INCONCLUSIVE (MDE) |
| T+2 (companion) | [−18.3, −1.3] | 2/6 | 8.5 | INCONCLUSIVE (MDE) |
| **T+3 (authority)** | **[−20.5, −0.0]** | **2/6** | **10.2** | **INCONCLUSIVE** |
| T+5 (companion) | [−16.4, +8.4] | 3/6 | 12.4 | INCONCLUSIVE |

Companions at 8 / 12 bps are the same sign family, weaker. No horizon is a PASS.

The T+3 interval sits on the non-positive side (UB ≈ 0). MDE ≥ 6 bps is the locked INCONCLUSIVE, not a licence to add years or download futures. Clip mass would have biased EV *up*; the pooled read is still not positive.

## Cleanup

No new event rules. No cash Stage C. No SSF download. Intraday P2 STOP at `c_max` ≈ 4.5 stands.

## Decision

**Do not buy SSF / F&O lot panel.** S6 is not a live product. Do not repair power on a negative-centered CI. V2p-c **PASS**ed, so this is not programme FAIL — next spend is **S4-P1** index-option marks, not another fade horizon.
