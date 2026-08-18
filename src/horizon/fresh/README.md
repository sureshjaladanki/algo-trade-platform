# Horizon fresh package

Clean-sheet Horizon (Stages A–D) under locked round-trip cost `c* = 20` bps.

| Doc | Role |
|---|---|
| [blueprint](../../../docs/next/horizon-fresh-architecture-blueprint.md) | Design authority |
| [implementation plan](../../../docs/next/horizon-fresh-architecture-implementation-plan.md) | M0–M8 milestone map |
| [quarantine index](../../../docs/archive/horizon-fresh-quarantine-index.md) | Audit-only vs live |

**Friction:** import `ROUND_TRIP_COST` / `C_STAR` from `src.horizon.fresh.friction` (re-exports production `triple_barrier` — do not fork cost).

**Production lock (M0–M6):** do not change `LONG_TOP_K`, production TB floors, or the `predict_horizon_gbm` ship path from this package.
