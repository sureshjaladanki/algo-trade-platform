# Successor S1 — V1n / V1κ / V2p (2026-08-17)

**Verdict:** V1n dual-fold **PASS**. V2p **INCONCLUSIVE** (thin). P1 is not a product yet.  
**Log:** `data/GOLDEN_PARQUET/s1_v1n.log`  
**Pre-registration:** [horizon-successor-s1-preregistration.md](horizon-successor-s1-preregistration.md)

## Modules

`src/horizon/m9/v1_incremental.py` (3+ regressors), `har_range.py`, `v2p_range.py`, `eval_horizon_successor_s1_v1n.py`.

## Numbers

Two-regressor V1 reprint at κ=1.6 matches the published V1-index (`b_q50` ≈ 0.60 / 0.61). V1κ does not flip the sign.

| Fold | V1n `b_q50` | t | p | within-clock `b_q50` |
|---|---|---|---|---|
| A | **+0.569** | +24.7 | ≪ 0.05 | +0.541 |
| B | **+0.616** | +16.7 | ≪ 0.05 | +0.618 |

HAR 1d/5d controls are small and mixed-sign; they do not absorb `range_q50`. Nested FAIL was the prior; it did not fire.

**V2p:** first-bar residual > 0 selected **3 / 3** Nifty sessions per fold (need ~110). Thin → INCONCLUSIVE. Do not record FAIL. Do not retune the threshold on this peek.

## Cleanup

Index path still drops `volume_z`. Name V2 stub was not called. Purge is a no-op on A/B (0 days).

## Decision

**Go on V1n. Rework V2p** under a **new** pre-registration (different clock than session-first-bar, or a train-fold residual quantile). Do not acquire index-option marks until V2p PASSes. Do not salvage with name V1.

Follow-on: [horizon-successor-s1-v2pb-memo.md](horizon-successor-s1-v2pb-memo.md) — 09:45 clock repair is also **INCONCLUSIVE** (still ~3 sessions/fold). Residual>0 is not a session product on this charter.
