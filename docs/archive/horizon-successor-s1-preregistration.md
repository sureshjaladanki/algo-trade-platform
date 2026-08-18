# Successor S1 — V1n / V1κ / V2p pre-registration

**Locked:** 2026-08-17, before the authority run  
**Harness:** `src/experiments/eval_horizon_successor_s1_v1n.py`  
**Authority:** [horizon-successor-architecture-blueprint.md](../next/horizon-successor-architecture-blueprint.md) Rev 2 §4.3

V1-index dual-fold PASS is already published (`m9_v1_index.log`). This peek is **V1n** (nested HAR). **V2p** runs only if V1n PASSes. Name V1 is not this peek.

---

## Locked choices

| Item | Value |
|---|---|
| Folds | A and B (`FOLDS`) — same as V1-index |
| Universe | `^NSEI` only; `volume_z` dropped |
| Stage B | `OpportunityModel` + `INDEX_OPPORTUNITY_FEATURES` |
| Implied | `range_imp_vix`, κ = **1.6** (authority) |
| HAR | Causal Parkinson 1d + 5d from **completed** prior sessions, scaled \(\kappa \cdot \sigma \cdot \sqrt{f}\) |
| OLS V1n | `remaining_range ~ 1 + range_imp_vix + range_har_1d + range_har_5d + range_q50` |
| V1n PASS | `coef_q50 > 0` and two-sided p < 0.05 on **both** folds |
| V1n FAIL | Either fold coef ≤ 0 or p ≥ 0.05 |
| V1κ | Reprint two-regressor V1 at κ ∈ {1.4, 1.6, 1.8} — **report-only** |
| Clock | Within-`bars_to_mis` demeaned nested OLS — report-only companion |
| V2p threshold | **residual > 0** where residual = `range_q50 − range_imp_vix` at the **first** bar of the session with `bars_to_mis > 0` |
| V2p statistic | Session-block mean of `(remaining_range − range_imp_vix)` on selected Nifty sessions; cost-free |
| V2p three-way | PASS if CI LB > 0; FAIL if CI UB < 0; else INCONCLUSIVE (`k4_three_way`, `c_star=0`) |

## Expected outcome (stated before the run)

V1n is the more likely **FAIL**: VIX already embeds a HAR-style forecast. A PASS only unlocks V2p, not marks and not name options.

## Forbidden

Name V1 salvage, `eval_horizon_m9_v2_stub.py`, extra κ / HAR peeks after seeing the ledger, geometry / Top-K remount.
