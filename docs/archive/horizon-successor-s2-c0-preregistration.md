# Successor S2 — C0 fade cost-bound pre-registration

**Locked:** 2026-08-17, before the authority run  
**Harness:** `src/experiments/eval_horizon_successor_s2_c0.py`  
**Authority:** [horizon-successor-architecture-blueprint.md](../next/horizon-successor-architecture-blueprint.md) Rev 2 §5.2

First live caller of Fresh `k5_pooled`. No Stage C. No new event rules.

---

## Locked choices

| Item | Value |
|---|---|
| Sleeve | `prior_day_high_reject` Short, `transition_candidate_events` |
| Pool | **Unconditional** event pool (not F1’s 70–96% admit set). A∩B is not the gate |
| Geometry | MIS vertical-only + disaster **clip** to `−sl_floor` (500 bps). Do not drop the left tail |
| Authority folds | `ROLLING_FOLDS` **R2017–R2022** (**6** disjoint test years). A+B reprinted as companions only — pooling them would double-count 2018/2019. M5P’s “8/8” count was A/B **plus** these six. |
| Train / purge | None — C0 is a pool reprint, not a fit. Test windows are full calendar years |
| Costs | **3 / 5 / 8 bps** scalars on `side_drift`. Authority hurdle = **3 bps**. Cash `c_eff` is a companion |
| Gate | `k5_pooled` + sign test (**≥5/6** positive points) at c = 3 |
| Companions | `vwap_loss` Short, `gap_fill_short`. Do not pick a new winner after the log |
| Expected n (ex ante) | ~1,250 events/year × 6 ≈ **7,500**; ~220 sessions/year × 6 ≈ **1,320** (from M4R-b F1 sleeve mass) |
| Expected MDE | `declare_admit_power(7500, 1320, assumed_sigma=0.008)` — vertical-only path σ sketch, not 200/100 |

## Decision rule

| Verdict | When |
|---|---|
| **PASS** | Pooled CI LB > 0 **and** sign ≥ 5/6 at c = 3 |
| **FAIL** | Pooled CI LB ≤ 0 **or** sign fail, **and** realized MDE < 3 bps |
| **INCONCLUSIVE** | Realized MDE ≥ 3 bps (cannot resolve the 3 bps hurdle) |

Expected outcome (stated before the run): **INCONCLUSIVE** is more likely than PASS (power vs ~4 bps net). A FAIL at 3 bps on a passable harness stops P2; do not download SSF.

**Harness note (before pooled authority):** the first execution printed per-fold CIs then aborted `k5_pooled` because it required 8 folds of a 6-year `ROLLING_FOLDS` design. Sleeve, costs, clip, and disjoint years did not change. The pooled read is the authority; the abort was not a FAIL.

## Forbidden

Stage C fit, N-bar exhaustion, new sleeve after seeing the log, SSF download to manufacture power, remounting M6.
