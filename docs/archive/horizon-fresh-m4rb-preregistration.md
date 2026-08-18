# Horizon Fresh — M4R-b pre-registration (F1 + F2)

**Date:** 2026-08-16  
**Authority:** implementation plan M4R-b; blueprint Rev 3 §1.6, §3.1, §10.2–10.3, §15A  
**Prerequisite:** M5P-b EXIT PASS  
**Expected outcome:** **FAIL** on both falsifications (a PASS is the surprise)

This document is written **before** the authority runs. Do not edit the
pre-registered fields after `m4rb_f1_full_run.log` / `m4rb_f2_full_run.log` exist.

---

## F1 — Stage C selector on the winning sleeve

| Field | Pre-registered value |
|---|---|
| Sleeve | `prior_day_high_reject` Short (reversion) |
| Pool | transition events ∩ Stage A ∩ Stage B (`opportunity_ok`) |
| Geometry | `MIS_VERTICAL_ONLY_SHORT_GEOMETRY` (MIS flatten + 500 bps disaster SL; no 200/100 race) |
| Head | Fresh multiclass + isotonic on purged val; M5R directional + XS-vol features |
| Admit | calibrated P(favorable) > driftless baseline **or** conformal LB(`ev_net_hat`) > 0 — state which in the harness print |
| Authority gate | K4 three-way on **admitted** set gross / martingale residual |
| Cost in F1 | Flat `c*` companions only; row-level `c_eff` is F2 |
| Folds | A + B decision ledger; R2017–R2022 report-only |
| Expected admit (ex ante) | ~400–800 / fold A-year (sparse; declare exact `AdmitPowerPlan` in harness stdout before fit) |
| Expected MDE | must print via `declare_admit_power` before the peek |
| Required IC | breakeven **0.054** @ 20 bps; margin **0.10** (blueprint §15A) |
| Expected verdict | **FAIL** — CI UB of admitted gross < `c*` or realized IC ≪ 0.054 |

### F1 STOP language (pre-registered)

- **PASS** → unblock M5 re-read / M6 on this sleeve only (vertical-only).  
- **FAIL / INCONCLUSIVE with UB < c\*** → F1 closed; proceed to F2.  
- Do **not** retune features, geometry, or admit threshold after seeing the log.

---

## F2 — Row-level `c_eff` reprint

| Field | Pre-registered value |
|---|---|
| Cost model | `path_ev_net(path_ret, c_eff)` / `expected_ev_net(..., cost=c_eff)` |
| Universe | Stage A liquid tail: publish `c_eff` distribution (p10/p50/p90) of the admitted / event set |
| Capacity | State max concurrent notionals the liquid-tail ADV can support at 1–4 fires/day |
| Reprints | (a) M4R drift ledger on `c_eff`; (b) F1 K4 on `c_eff` if F1 ran; flat-`c*` and archive-30 companions |
| Expected verdict | **FAIL** — even on the liquid tail, CI UB of EV_net does not clear zero with margin |

### F2 STOP language (pre-registered)

- **PASS on liquid-tail `c_eff`** → product is a capacity-constrained liquidity-tail book; open M6 with capacity statement.  
- **FAIL** → together with F1 FAIL, earn blueprint §14 capability FAIL and open **M9**.

---

## Combined verdict rule

| F1 | F2 | Next |
|---|---|---|
| PASS | any | M5 re-read → M6 on vertical-only Short reject sleeve |
| FAIL | PASS | M6 on `c_eff` hurdle + capacity caps; F1 sleeve still needs a selector PASS later or stays report-only |
| FAIL | FAIL | **§14 capability FAIL** → M9 (range-in-options primary; SSF secondary) |

---

## Forbidden during M4R-b

- Geometry grid search  
- Precision peeks  
- Remounting Top-K / H=6 / 60–30  
- Expanding the feature set after seeing F1  
- Re-opening M4R unconditional-pool sleeve search  

## Artifacts (to be written by the harnesses)

- `data/GOLDEN_PARQUET/m4rb_f1_full_run.log`  
- `data/GOLDEN_PARQUET/m4rb_f2_full_run.log`  
- Harness: `src/experiments/eval_horizon_fresh_m4rb_falsify.py`
