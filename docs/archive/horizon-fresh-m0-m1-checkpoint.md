# Horizon Fresh — M0/M1 checkpoint memo

**Date:** 2026-08-16  
**Decision:** Go on M2–M3 (ceiling material; infra ready)

## What changed

- Package `src/horizon/fresh/` (friction, folds, parquet, microstructure, tradability, diagnostics, gates K1–K5, opportunity, events, stage_c, admit, registry, precision_bridge, cutover)
- `src/labels/fresh_barrier.py` — `ev_net_abs` / `ev_net_excess`
- Quarantine index + AUDIT-ONLY markers on CLOSED peeks
- Experiments: `materialize_golden_parquet`, `eval_horizon_fresh_m{0,1,2,3_m4}_*`
- Unit tests under `tests/horizon/fresh/` (8 passed)

## Numbers (M1 fold A, 5-symbol smoke)

| Metric | Value |
|---|---|
| Pool mean EV_net | −24.3 bps (CI [−27.7, −20.2]) |
| Pos-mass | 27.6% |
| Oracle top-decile | **+184 bps** |
| Abs vs excess sign disagree | 6.1% |
| TP/SL/TO | 10% / 44% / 45% |

**Diagnosis:** Ceiling high → selector / Stage C problem later; Stage B still required to enlarge span before deep scorers. Matches blueprint §10.4 “ceiling high” branch.

## Cleanup done vs deferred

| Done | Deferred |
|---|---|
| Fresh package boundary | Full GOLDEN Parquet materialization (`--all`) |
| Quarantine index | Dual-fold M1 on full universe |
| Production freeze doc | AR spread estimator often → 0 (tune in M2) |
| Shared `session_block_mean_ci` reuse | M3 K1/K2 fit on full folds |

## Go / Stop / Rework

**Go** to M2 (tradability filter live) and M3 (range head → K1/K2). Do not remount Top-K peeks.
