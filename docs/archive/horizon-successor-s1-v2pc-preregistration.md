# Successor S1 — V2p-c pre-registration (T-02)

**Locked:** 2026-08-18, before the authority run  
**Harness:** `src/experiments/eval_horizon_successor_s1_v2pc.py`  
**Authority:** [horizon-successor-architecture-blueprint.md](../next/horizon-successor-architecture-blueprint.md) Rev 3 §4.3  
**Depends on:** V1n PASS (`s1_v1n.log`); V2p / V2p-b residual>0 **CLOSED** ([horizon-successor-s1-v2pb-memo.md](horizon-successor-s1-v2pb-memo.md))

This is a **new selection definition**, not a third clock and not a retune of residual>0.

## Locked choices

| Item | Value |
|---|---|
| Clock | First bar at/after **09:45** (Stage B `open_30m_range` complete). Do not scan 10:00 |
| Residual | Fit `realized remaining range ~ implied remaining range` on the **train** fold only. Standardize the residual on train; apply the same location/scale to test |
| Selection | **Bottom tercile** of standardized residual (implied richest vs the head). Short-premium side |
| Statistic | **Paired difference:** mean(`R_imp − R`) on selected sessions **minus** the all-session mean. Cost-free, range space. Incremental to unconditional short vol |
| Folds | Dual-fold A+B, pooled session-block CI; per-fold sign as companion |
| Power | `declare_admit_power` printed **before** selection. Expected ~1/3 of ~245 sessions/fold ≈ 80/fold, ~160 pooled |
| Abort | If declared MDE > **15 bps** before selection, do not peek; record INCONCLUSIVE |

## Decision rule

| Verdict | When |
|---|---|
| **PASS** | Pooled session-block CI LB > 0 on the paired difference |
| **FAIL** | LB ≤ 0 **and** declared MDE < 15 bps (harness was passable) |
| **INCONCLUSIVE** | Declared MDE > 15 bps — abort before the peek |

**On FAIL:** P1 CLOSED. Do not salvage with name V1. Do not acquire index-option marks.

## Forbidden

Residual>0, q75, 10:00 or any other clock, name V1 salvage, EOD bhavcopy as a V2 proxy, changing κ on this peek.
