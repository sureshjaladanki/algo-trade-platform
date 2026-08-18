# Horizon Fresh — M4R-b STOP memo (F1 + F2 FAIL → §14 capability FAIL)

**Date:** 2026-08-16  
**Authority:** [horizon-fresh-m4rb-preregistration.md](horizon-fresh-m4rb-preregistration.md)  
**Log:** `data/GOLDEN_PARQUET/m4rb_full_run.log`  
**Decision:** **F1 FAIL · F2 FAIL** → blueprint **§14 capability FAIL** for directional Nifty-100 MIS cash under the fresh hypothesis. Open **M9** (successor charter). Do not proceed to M5 re-read / M6 / geometry / Precision.

---

## What was run

| | Pre-registered | As run |
|---|---|---|
| Sleeve | `prior_day_high_reject` Short | same |
| Geometry | vertical-only + 500 bps disaster SL | same |
| Folds | A + B | A + B, 82 names |
| F1 gate | K4 three-way on **admitted** gross **and** selector IC ≥ 0.054 | same |
| F2 | row-level `c_eff` EV_net; flat-20 / archive-30 companions | same (`c_star=0` on net EV) |
| Expected | FAIL both | **FAIL both** |

Harness defect fixed before authority: lookback direction features were null on early-session first-crosses and `drop_nulls` collapsed the sleeve to ~3 rows. Filled lookback nulls with 0; sleeve mass became ~1.2k test rows / fold.

---

## F1 results

| Fold | Sleeve n | Admit | Selector IC | K4 gross (all) | K4 gross (admit) | EV_net@20 (admit pt) |
|---|---|---|---|---|---|---|
| A | 1264 | 69.8% (882) | **+0.022** | PASS \[+6.1, +47.8\] | PASS \[+5.8, +50.5\] | +6.7 bps |
| B | 1255 | 96.2% (1207) | **+0.023** | INCONCLUSIVE \[−5.7, +36.9\] | INCONCLUSIVE \[−2.1, +39.0\] | −3.1 bps |

Pre-registered need: IC ≥ **0.054** (breakeven) / 0.10 (margin).

**F1 FAIL.** Realized IC ≈ **0.022** on both folds — about **40% of breakeven**. Fold A’s K4 PASS is a *pool* property (all-events also PASS); the selector does not create dual-fold edge and does not reach the required IC. Fold B does not confirm PASS.

---

## F2 results

| Fold | c_eff p10/p50/p90 | Liquid ≤12 bps | EV_net @ c_eff | @ flat 20 | @ archive 30 |
|---|---|---|---|---|---|
| A | 4.7 / **6.8** / 14.2 | 85% | INCONCLUSIVE \[−2.4, +42.4\] | INCONCLUSIVE | INCONCLUSIVE |
| B | 4.8 / **7.9** / 15.8 | 78% | INCONCLUSIVE \[−11.2, +29.9\] | INCONCLUSIVE | INCONCLUSIVE |

**F2 FAIL.** Median achievable cost on the admitted set is **~7–8 bps**, well below the flat 20 average — Stage A’s `c_eff` story is real — but **no fold clears EV_net CI LB > 0** even on that cheaper hurdle. Lowering the tax is not enough when the selector cannot concentrate the +7 bps drift.

Capacity: liquid-tail share is high (~80%); a sparse book is feasible on ADV, but capacity without expectancy is irrelevant.

---

## Combined verdict

| F1 | F2 | Next (pre-registered) |
|---|---|---|
| FAIL | FAIL | **§14 capability FAIL → M9** |

Earned language (blueprint §14 FAIL, Rev 2/3 qualifier satisfied):

> Even with range gating, event clock, vertical-only geometry, repaired gates, and row-level `c_eff`, admitted-set edge (K4) / selector IC fails dual-fold on a harness that could have passed — Nifty-100 MIS **directional** cash under 20 bps is not a viable Horizon product with this hypothesis. Do not return to Top-K / H=6 / 60–30. Next requires a different product definition.

What **survives** for M9: Stage A, Stage B (range Spearman ~0.61), absolute-admit discipline, K-gate hygiene, sparse-book posture.

---

## Forbidden next steps (unchanged)

- Geometry grid search  
- Precision peeks to bail out Horizon  
- Remounting production Top-K / H=6 / 60–30  
- More directional feature engineering on cash MIS  
- Re-opening the M4R unconditional-pool sleeve search  

## Next

**M9 — Successor charter.** Primary: monetize Stage B range in options, gated on **V1** (incremental information vs *implied* range). Secondary: same thin drift on single-stock futures to cut \(c\). Prerequisite: NSE IV / OI history.

## Artifacts

- `data/GOLDEN_PARQUET/m4rb_full_run.log`  
- `src/experiments/eval_horizon_fresh_m4rb_falsify.py`  
- Prior: [horizon-fresh-m4r-stop-memo.md](horizon-fresh-m4r-stop-memo.md), [horizon-fresh-m4rb-preregistration.md](horizon-fresh-m4rb-preregistration.md)
