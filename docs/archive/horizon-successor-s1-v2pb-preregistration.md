# Successor S1 V2p-b — post-open residual (pre-registration)

**Locked:** 2026-08-18, before the authority run  
**Harness:** `src/experiments/eval_horizon_successor_s1_v2pb.py`  
**Parent:** [horizon-successor-s1-preregistration.md](horizon-successor-s1-preregistration.md) (V1n PASS; V2p-0 INCONCLUSIVE)  
**Authority:** [horizon-successor-architecture-blueprint.md](../next/horizon-successor-architecture-blueprint.md) Rev 2 §4.3 V2p

This is a **clock repair**, not a threshold search. V1n is not re-peeked.

---

## Why V2p-0 was unpassable

V2p-0 took the session’s **first** bar with `bars_to_mis > 0`. That bar is the 09:15–09:30 bleed (stamp 09:30). Stage B’s `open_30m_range` is only complete at **09:45**. A remaining-session vol decision before that clock is not the product. Selected mass was 3 sessions/fold against an AdmitPowerPlan of ~110. Thin = INCONCLUSIVE, not FAIL.

## Locked choices (one change)

| Item | V2p-0 (ledger) | V2p-b (this peek) |
|---|---|---|
| Folds | A, B | **same** |
| Universe | `^NSEI`, no `volume_z` | **same** |
| Residual | `range_q50 - range_imp_vix` | **same** |
| Threshold | **> 0** | **same** (do not move to a train quantile) |
| Decision bar | first bar of the session | first bar with `time_only > 09:30` (09:45 bar-end; Stage B open-30m known) |
| Statistic | session-block mean of `remaining_range - range_imp_vix` | **same** |
| Three-way | PASS if CI LB > 0; FAIL if CI UB < 0; else INCONCLUSIVE | **same** |
| Thin | n < 30 or sessions < 20 | **same** |

Expected selected sessions (ex ante): ~110 / fold (`declare_admit_power(110, 220, assumed_sigma=0.004)`).

## Expected outcome (stated before the run)

Clock repair should produce a **passable** sample. Then the three-way can fire. A still-thin read at 09:45 means residual > 0 is not a session product — **INCONCLUSIVE**, and **do not** try 10:00 / q75 / other clocks on this charter. FAIL (UB < 0) stops P1. PASS unlocks S4-P1 index marks, not name marks.

## Forbidden

Scanning other bar times after seeing the log. Changing the residual threshold. Name V1 salvage. `eval_horizon_m9_v2_stub.py`. Re-opening V1n.
