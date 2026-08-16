# Horizon Short Capacity / Regularization — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Test whether pre-registered Short LightGBM capacity / regularization slices (U1/U2/R1) under locked `SHORT_FEATURES`, path-EV, `c*=20` / `H=6` / floors / K=3 clear dual-fold Short H5  
**Status:** **STOP-MEMO — capacity charter CLOSED**; peeks **0 / 2** · Phase 1 hard-stop · **no authorized lever** — **no merge**  
**Date:** 2026-08-15  
**Charter:** [horizon-short-capacity-charter.md](horizon-short-capacity-charter.md)  
**Depends on:** [horizon-short-architecture-stop-memo.md](horizon-short-architecture-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-tier2-verdict.md](../horizon-tier2-verdict.md)  
**Trigger:** Phase 1 dual-fold numeric gate authorized **[]**; MUST_FIX val robustness applied; no peeks spent  
**A+B peeks spent:** **0 / 2** — hard-stop @ 0

---

## One-line

Relative Short leaf floor is ~2.75× Long (v1 constraint #5 confirmed), but easing or tightening `min_child_samples` / `reg_lambda` **does not** dual-fold-clear val H5-proxy lifts under locked physics — **stop @ 0/2**; Short H5 is not recoverable via the capacity / regularization slices tested this ledger; next = Long-only cascade economics; Short sleeve stays disabled.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| Holdout Short H5 FAIL / H2 PASS @ `c*=20` is still the residual | **Supported** — Phase 1 reprint (H5 FAIL/FAIL; H2 PASS/PASS; ADVt lo ~33%/33%) |
| Short train mass ~½ Long on same calendar windows | **Supported** — ratio **0.485 / 0.479** |
| Relative leaf floor `rel400 ≥ 1.25 × rel300_L` | **Supported** — **2.75× / 2.78×** |
| U1 (mcs 400→300) lifts val H5-proxy ≥ +0.010 both with H2>0 + robustness | **Disproven dual-fold** — Fold A Δ=**0.000**; Fold B Δ=+0.019 (seed7 +0.048) but Fold B `gap=0.116 > 0.05` blocks U1 mass lane |
| U2 (mcs 400→200) lifts val H5 ≥ +0.015 both | **Disproven** — Fold A **−0.064**; Fold B +0.005 |
| R1 (mcs 400→500 + λ 8→10) via gap≥0.08 both or ΔH5≥+0.010 both | **Disproven** — gap lane needs both folds (A **0.050 < 0.08**); delta lane Fold A **−0.064** |
| Capacity starvation alone explains holdout H5 FAIL | **Disproven as peekable residual** — asymmetry is real; authorized peeks = none |
| Feature remount / K=5 / Precision bailout may bridge Short H5 | **Forbidden** (unchanged) |

**Residual lock after this charter:** Short H5 is **not recoverable via the capacity / regularization slices tested this ledger** (U1/U2/R1 — none authorized). Next = **Long-only cascade economics** (architecture STOP posture). Short momentum sleeve stays **disabled / flat**.

---

## Terminal evidence

### Phase 1 (0 peeks)

**Log:** `logs/horizon_short_capacity_phase1_ab.txt`  
**Harness:** `python -m src.experiments.analyze_horizon_short_capacity --folds A,B`

Holdout H5 / H2 / ADVt = **frozen reprint**. Authorization = last-fold **train/val** + MUST_FIX robustness (min val-N ≥150/10; bootstrap CI LB > 0 **or** two-seed).

| Diagnostic | Fold A | Fold B | Cut / read |
|---|---|---|---|
| Holdout H5 / H2 (reprint) | FAIL / PASS | FAIL / PASS | not a Phase 1 gate |
| Holdout H5 point [CI] | 0.0019 [−0.018, 0.022] | 0.0143 [−0.002, 0.034] | FAIL/FAIL |
| ADVt lo (reprint) | 33% | 33% | publish-only |
| `n_train_Short` / `n_train_Long` | 63392 / 130587 | 60640 / 126469 | — |
| `ratio` | **0.485** | **0.479** | ≤0.60 both **CLEAR** |
| `rel400 / rel300_L` (×) | **2.75** | **2.78** | ≥1.25 both **CLEAR** |
| `gap` (train−val IC) | 0.0498 | **0.1161** | U1 needs ≤0.05 both → **FAIL**; R1 needs ≥0.08 both → **FAIL** |
| Val bars / sess | 3416 / 12 | 4416 / 15 | min-N **CLEAR** both |
| H5v0 / H2v0 | 0.033 / 0.0013 | 0.035 / 0.0012 | positive val H5-proxy both |
| ΔU1 [boot lo] | **0.000** [0.000] | +0.019 [0.000] | ≥+0.010 both **FAIL** |
| ΔU2 [boot lo] | **−0.064** [−0.129] | +0.005 [−0.025] | ≥+0.015 both **FAIL** |
| ΔR1 [boot lo] | **−0.064** [−0.129] | +0.014 [0.000] | ≥+0.010 both **FAIL** |
| Leaf occupancy (baseline) | 7 leaves; mean 9056; p10 1324 | 8 leaves; mean 7580; p10 1286 | report-only |

**Hard gate:** authorized ladder **[]**. Peek 1/2 unused.

### Phase 1 decision (pre-registered)

| Lever | Dual-fold authorize? | Why |
|---|---|---|
| **U1** mcs→300 | **No** | Fold B gap 0.116 > 0.05; Fold A ΔH5 = 0 |
| **U2** mcs→200 | **No** | Fold A ΔH5 negative; Fold B Δ < +0.015; U1 not authorized |
| **R1** mcs→500 + λ→10 | **No** | Gap lane not both folds; delta lane Fold A negative |

Tie-break U1→U2→R1 → **no peek**.

---

## Verdict

| Item | Lock |
|---|---|
| Peek ledger | **0 / 2 spent** — hard-stop; leftover slots **closed** |
| Merge U1 / U2 / R1 into `SHORT_PARAMS` | **No** |
| Path-EV GBM + `SHORT_FEATURES` + baseline `SHORT_PARAMS` | Unchanged |
| Architecture / EV–TB / travel / K / Precision / B1 | Stay CLOSED / blocked |
| Horizon-path PASS / cascade Short-ready | **Forbidden / unproven** |
| Short momentum sleeve | **Disabled / flat** in live or paper cascade |

**Capability sentence (FAIL path, as pre-registered):** Short H5 is **not recoverable via the capacity / regularization slices tested this ledger** (U1, U2, R1 — none Phase-1-authorized). Relative capacity asymmetry vs Long is **real** (~2.75× leaf floor) but is **not** a gated H5 lift under locked physics. Next = **Long-only cascade economics re-check** — **not** another Short-only remount, **not** feature remount, **not** Precision bailout, **not** another free param grid.

---

## Code / harness artifacts

| Path | Role |
|---|---|
| `logs/horizon_short_capacity_phase1_ab.txt` | Phase 1 A+B numeric gate |
| `src/experiments/analyze_horizon_short_capacity.py` | Phase 1 + peek harness |
| `src/horizon/eval/capacity.py` | Diagnostics, MUST_FIX robustness, authorize |

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-short-capacity-charter.md](horizon-short-capacity-charter.md) | This ledger’s charter (ACCEPT WITH REVISIONS → CLOSED) |
| [horizon-short-architecture-stop-memo.md](horizon-short-architecture-stop-memo.md) | Prior CLOSED — Short flat; Long-only next |
| [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) | v1 constraint #5 retune-after-measure (now measured + gated) |
