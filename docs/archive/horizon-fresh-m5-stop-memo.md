# Horizon Fresh — M5 STOP memo (K3 / K4 FAIL)

**Date:** 2026-08-16  
**Authority:** blueprint §10.3 / implementation plan M5 stop  
**Decision:** **STOP Stage C redesign path** — do not spend on geometry grids, Precision peeks, or Stage D soft thresholds.

> ## ⚠ SUPERSEDED — see the [addendum](#addendum--stop-vacated-2026-08-16) at the end of this memo
>
> This memo's **numbers stand** as the M5 ledger. Its **interpretation does not**. A post-mortem found
> seven harness defects, including a Stage C feature set with no directional input at all, so the
> reported K3/K4 FAIL measured the harness rather than the market. The STOP is **vacated** and
> reclassified **INCONCLUSIVE**; the repaired M5R run reaches a stop for the Long-continuation sleeve
> on much better grounds. Read the addendum before citing anything below.

## What was tested

- Decision set: Long events ∩ `opportunity_ok` (Stage B)  
- Labels: `MIS_WIDE_LONG_GEOMETRY` (200/100 floors, MIS vertical)  
- Model: multiclass LightGBM P(SL)/P(TO)/P(TP) + geometry argmax at inference  
- Universe: 82 trade names, folds A+B  

## Results (authority)

| Gate | Fold A | Fold B |
|---|---|---|
| K3 calib max \|gap\| pp | **16.1 FAIL** (≤3) | **24.4 FAIL** |
| K4 edge vs driftless | **−0.8 pp FAIL** (CI LB −6.6) | **−5.1 pp FAIL** (CI LB −10.1) |
| Admit rate (P(TP)>driftless) | 22.8% | 22.7% |
| TO mass (all / admit) | 8.9% / 3.4% | 11.4% / 4.7% |

Timeout control under MIS-vertical is **healthy** (≪20% target). The failure is **directional skill / calibration**, not span or TO drag.

## Interpretation (plan language)

> **K4 FAIL → STOP.** No directional skill after opportunity gating — isolate from “skill < friction.”

Ceiling mass exists (M3/M4 oracle top-decile ~170–190 bps on A∩B), but the meta-label + primary-rule stack does **not** recover positive edge over the driftless barrier race. That is a selector / causality failure, not a cost-knob or Top-K remount problem.

## Forbidden next steps

- Geometry grid search to “find a PASS”  
- Precision peeks to bail out Horizon  
- Remounting production Top-K / H=6 / 60–30 as recovery  

## Allowed next hypotheses (product / causal)

Per blueprint §14 FAIL path: change **product definition** (hedge, universe, session product) or redesign the **primary rule / event causality** with a new charter — not another barrier redraw on the same contract.

## Artifacts

- `data/GOLDEN_PARQUET/m5_full_run.log` (mis_wide authority)  
- Optional `m5_prod_diag.log` (report-only companion; not a salvage)  
- Prior PASS: M3 K1/K2 + M4 A∩B ceiling lift (`horizon-fresh-m3-m4-checkpoint.md`)

---

# Addendum — STOP vacated (2026-08-16)

**Authority:** blueprint Revision 2 §10.3–10.5, §14; implementation plan M5R  
**Decision:** the M5 STOP is **vacated** and reclassified **INCONCLUSIVE**. A separate stop is recorded
for the Long-continuation sleeve on the repaired harness. The forbidden-next-steps list above still
stands unchanged.

## Why the original reading was void

The memo above concluded "no directional skill after opportunity gating." The harness could not have
supported that conclusion, because it could not have produced a PASS under any state of the world.

| # | Defect | Evidence |
|---|---|---|
| 1 | **Stage C had no directional feature.** All 11 inputs were volatility / range / rule identity — quantities symmetric in the barrier race, which raise P(TP) and P(SL) together. | Univariate \|Spearman(feature, TP-first)\| ≤ 0.065; strongest was `rv_5d` at **−0.065**. The four rule one-hots — the only columns carrying directional information — received **10–141** LightGBM splits against 3,500–4,800 for the vol features. |
| 2 | **No calibrator was fitted**, though blueprint §8.2 requires isotonic on purged val. | Mean predicted P(TP) **0.230** vs realized **0.337**. K3 measured the missing isotonic step. |
| 3 | **`bars_to_mis` was scrambled by silent Int8 overflow** — `dt.hour()` returns `Int8`, so `hour * 60` wraps. | 15:00 mapped to −124 and 10:45 to −123; values ran 53–69 instead of 0–23. The clock feature was noise in both Stage B and Stage C. |
| 4 | **Stage A was never applied**, despite M4's exit note requiring A∩B before Stage C. | The M5 harness imports no tradability module. |
| 5 | **The event pool was 73% restatements** of a persisting condition, so the "event clock" was close to the bar clock. | Fresh-rate: `prior_day_high` 10.3%, `orb_break_vol` 28.2%, `range_expand_2x` 31.2%, `vwap_reclaim` 75.3%. |
| 6 | **K3's threshold was below its own null.** Max gap over 10 deciles against a flat 3 pp tolerance. | Bootstrap null p95 of the max gap is 6.0–9.4 pp on these samples. |
| 7 | **K4's null ignored timeout dilution.** `s/(g+s)` is a no-time-limit formula. | TO mass 8.9%/11.4% → a built-in penalty of roughly 1–3 pp. |

The reported geometry diagnostic was also void: `geometry_argmax` was called with geometry-invariant
probabilities, so it returned the grid corner (`tp_mult`=0.6, `sl_mult`=0.2) on every row. The logged
`g* med=0.0141 / s* med=0.0047` is exactly that 3.0 ratio, and its ~188 bps span was never the 300 bps
span the labels used.

## What the repaired harness says

`data/GOLDEN_PARQUET/m5r_full_run.log` — 82 names, folds A/B, with all seven defects addressed.

| Gate | M5 reading | M5R reading |
|---|---|---|
| K3 | 16.1 / 24.4 pp — FAIL | **ECE 4.64 / 2.38 pp** — fold B PASS, fold A marginal; max gaps 9.16 vs null 9.35 and 3.92 vs null 5.96, both **inside the null band** |
| K4 gross (all events) | not measured | **−10.55 / −5.29 bps**, CI \[−21.6, +1.2\] / \[−18.7, +7.7\] |
| K4 gross (admit) | not measured | −4.71 bps / admit set empty |
| K4 P(TP\|resolved) − driftless | −0.8 / −5.1 pp | −3.46 / −1.79 pp |
| Realized P(TP) | — | 0.293 / 0.308 vs driftless 0.333 |
| TO mass | 8.9% / 11.4% | 1.8% / 2.3% |
| MDE on K4 | not published | 11.4 / 13.2 bps |

**Calibration was never the problem** — its absence was. K3 essentially passes once isotonic is fitted
on a purged validation slice.

**K4 still fails, and now defensibly.** Gross return is negative in both folds with a consistent sign,
and the CI upper bounds (+1.2 / +7.7 bps) sit well below the +20 bps that K5 would require. Under the
Rev 2 three-way rule that is a **FAIL for this decision set**, not an INCONCLUSIVE.

Fold B's admit set is **empty** — calibrated P(TP) never cleared the driftless 1/3. That is the
architecture working: a pool with no admissible instance should fire zero trades.

## Corrected verdict

> **Long continuation on 15m breakout rules, Nifty-100 MIS cash, 200/100 barriers, MIS vertical:
> negative gross expectancy before cost, dual-fold. FAIL.**
>
> This is a verdict on the *sleeve*, not on the architecture. Stages A and B are sound; Stage B's K1 is
> genuine cross-sectional range skill (within-clock Spearman 0.617 vs pooled 0.635). The blueprint §14
> capability-FAIL sentence is **not** yet invoked.

## The finding that redirects the roadmap

Barrier-free drift from the event bar to MIS flatten, by rule:

| Rule | Kind | Drift A | Drift B |
|---|---|---|---|
| `vwap_reclaim` | fade / reversion | **+11.1 bps** | **+17.9 bps** |
| `range_expand_2x` | volatility | −7.1 bps | +12.5 bps |
| `orb_break_vol` | continuation | −9.8 bps | −5.5 bps |
| `prior_day_high` | continuation | −13.1 bps | −31.2 bps |

No CI excludes zero (±25–40 bps), so this is a direction-of-research signal and nothing more. But the
signs are **fold-consistent and opposite between rule families**, and M5 pooled all four into a single
Long head that gave rule identity ~1% of its splits. The one fade rule points with Long; both
continuation rules point against it.

That is a **primary-rule specification problem**, and fixing it is a different causal hypothesis — a
different entry clock *and* a different side — which is precisely what the EV-net stop memo named as
legitimate grounds for a fresh charter. It is not a barrier redraw.

## Next steps (implementation plan)

**M5R** harness repair (done, pending 1m first-hit) → **M5P** validation power (MDE < `c*` before
authority peeks) → **M4R** per-rule drift ledger and one-sleeve-at-a-time selection, Short now in
scope → re-read K3/K4 → M6.

## Artifacts (addendum)

- `data/GOLDEN_PARQUET/m5_forensics.log` — defect evidence (D1–D5)  
- `data/GOLDEN_PARQUET/m5r_full_run.log` — repaired dual-fold authority candidate  
- `src/experiments/diagnose_horizon_fresh_m5_forensics.py` — audit-only post-mortem harness  
- `src/experiments/eval_horizon_fresh_m5r_stage_c.py` — repaired Stage C harness  
- `tests/horizon/fresh/test_stage_c.py` — regression tests, including the Int8 clock overflow
