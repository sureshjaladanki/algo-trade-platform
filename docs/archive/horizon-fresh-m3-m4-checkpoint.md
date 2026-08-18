# Horizon Fresh — M3/M4 checkpoint memo

**Date:** 2026-08-16  
**Decision:** Go to M5 (Stage C). M3 closed. M4 closed with note.

## M3 — Stage B (authority, 82 trade names)

| Gate | Fold A | Fold B |
|---|---|---|
| K1 Spearman | **0.607 PASS** | **0.607 PASS** |
| K2 mean \|move\| | **0.0377 PASS** (≥0.016) | **0.0353 PASS** |
| opportunity_ok rate | 13.2% | 11.5% |
| med remaining range (gated) | 328 bps | 309 bps |

Post-gate ceiling vs ungated (production-shaped labels):

| Fold | top10% ungated → gated | pos-mass | TO |
|---|---|---|---|
| A | 105 → **175** bps | 28% → 33% | 47% → 41% |
| B | 101 → **172** bps | 29% → 34% | 48% → 43% |

Stage B creates span and cuts timeout mass. **M3 exit: PASS.**

## M4 — Event clock

- Events/day ~560–570 across 82 names (pre-admit clock, not fires).
- Raw **event** ceiling ≈ bar ceiling (no lift) → events alone are not a selector.
- **Event ∩ tradable ∩ opportunity_ok:** top10% **174 / 189** bps; TO **28% / 30%**; pos-mass up.

**Go:** use events as the decision *clock* only inside Stage A∩B. Do not treat ungated events as the economic pool.

## Cleanup

| Done | Deferred |
|---|---|
| Full-universe K1/K2 | Regime soft overlay on M4 (optional) |
| Post-gate + event ceilings | Tighten rules to cut event density |
| Finite-row hygiene for LightGBM | AR spread estimator still weak |

## Next

M5 Stage C (multiclass + geometry argmax) on event ∩ opportunity → K3 / K4.
