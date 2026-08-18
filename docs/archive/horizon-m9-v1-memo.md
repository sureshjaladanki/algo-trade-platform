# Horizon M9 V1 — incremental information (2026-08-17)

**Verdict:** dual-fold **PASS**  
**Log:** `data/GOLDEN_PARQUET/m9_v1_full.log`  
**Pre-registration:** [horizon-m9-v1-preregistration.md](horizon-m9-v1-preregistration.md)

Name-level ATM IV (M9-0 EOD bhavcopy, T+1 join) does **not** absorb Stage B `range_q50`.
OLS `remaining_range ~ implied_atm + range_q50` on opportunity-gated 15m bars:

| Fold | n | coverage | R² | b_imp | b_q50 | t_q50 |
|---|---|---|---|---|---|---|
| A (2018) | 377,539 | 81.3% | 0.389 | +0.153 | +0.952 | +219 |
| B (2019) | 375,364 | 79.7% | 0.401 | +0.127 | +0.917 | +239 |

Both folds: coverage ≥ 70%, `b_q50 > 0`, p ≪ 0.05.

## What this is not

PASS unlocks **V2** (gross option PnL on V1-selected sessions). It is not a ship, not K5,
and not a cash Stage C reopen. V0 / V1-index already showed increment vs *index* IV;
this is the same sign against *name* ATM IV.

## Next

V2 needs option marks (mids at least). Do not invent a cash directional recovery from this R².
