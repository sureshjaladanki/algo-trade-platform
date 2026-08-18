# M9 V1 — Pre-registration (name-level incremental information)

**Locked:** 2026-08-17, before the dual-fold authority run  
**Harness:** `src/experiments/eval_horizon_m9_v1.py`  
**Charter:** [horizon-m9-range-monetization-charter.md](../next/horizon-m9-range-monetization-charter.md)  
**IV store:** `data/GOLDEN_IV/atm_iv_daily.parquet` (M9-0, `nse_bhavcopy_bs`)

This is the Track A **authority** gate. V0 (India VIX on names) and V1-index (Nifty vs VIX)
are not substitutes. An 8-name smoke (`m9_v1_smoke.log`) is not this peek.

---

## Locked choices

| Item | Value |
|---|---|
| Folds | A and B (`FOLDS` in `src/horizon/fresh/folds.py`) |
| Universe | `sectoral_indices[*].trade_symbols` (same as V0) |
| Stage B | `OpportunityModel` + `OPPORTUNITY_FEATURES` (equities keep `volume_z`) |
| Implied | `range_imp_atm` from lagged ATM IV, κ = 1.6 |
| Join | `attach_lagged_atm_iv` — mark on T legal from T+1; asof last prior mark |
| OLS | `remaining_range ~ 1 + range_imp_atm + range_q50` |
| PASS | `coef_q50 > 0` and two-sided p < 0.05 on **both** folds, and IV coverage ≥ 70% on each test window |
| FAIL | Either fold has coef ≤ 0 or p ≥ 0.05 with coverage ≥ 70% |
| THIN / report-only | Coverage < 70% on a fold — do not record authority PASS or FAIL |

## Expected outcome (stated before the run)

Name ATM IV is a tighter control than India VIX. V0 and V1-index both found `range_q50`
incremental vs index IV; that **does not** imply V1 PASS. A FAIL is the charter's Track A
stop. A PASS only unlocks V2, not a ship.

## Forbidden

Geometry search, Top-K remount, treating the 8-name smoke as dual-fold authority,
running extra κ / feature peeks after seeing the ledger.
