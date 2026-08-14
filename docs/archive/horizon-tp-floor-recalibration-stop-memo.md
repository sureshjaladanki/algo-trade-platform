# Horizon Long TP-Floor Recalibration — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Step 0 absolute MFE crossing @ 50 vs 60 bps + ≤1 Long TP-floor peek under locked `c*=20` / `H=6`  
**Status:** **STOP-MEMO — TP-floor charter CLOSED**; peek **1 / 1** spent — **no merge**  
**Date:** 2026-08-13  
**Charter:** [horizon-tp-floor-recalibration-charter.md](horizon-tp-floor-recalibration-charter.md)  
**Depends on:** [horizon-exit-mfe-decay-stop-memo.md](horizon-exit-mfe-decay-stop-memo.md), [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md)  
**Trigger:** T1 holds Long H5 dual-fold but **regresses Fold B H3** vs cost baseline and leaves abs TB+1 / H4 economically null — no merge; no Peek 2 on this ledger  
**A+B peeks spent:** **1 / 1** — ledger **closed**

---

## One-line

Near-miss Abs MFE mass at [50, 60) is real (~6%) and mostly clean of SL-before-50, but **retrain+relabel at Long TP 50 bps does not lift Top-K TB+1 or clear H4** — and Fold B H3 flips PASS→FAIL — **stop at 1/1**; production Long TP stays **60 bps**.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| Top-K Abs MFE often clears 50 bps while missing 60 | **Supported** — Step 0 near-miss ~6.2–6.4% both folds; mean Abs MFE ~54–55 bps |
| Near-miss is mostly SL-contaminated (lowering TP just re-labels losers) | **Disproven** — SL-contam ~8–9% ≪ 50% cut |
| Step 0 hard-stop @ 0/1 | **Did not fire** — T1 authorized |
| T1 (60→50, retrain+relabel) clears H5 without H1/H2/H3 regression | **Partial FAIL** — H5 holds dual-fold; **H3-B regresses** PASS→FAIL |
| T1 converts near-miss into higher abs TB+1 / non-neg H4 | **Disproven** — TB+1 flat (~10.8 / 8.4 vs 10.9 / 8.9); H4 still −14/−15 bps |
| Merge Long TP floor 50 bps | **No** |
| Second floor / T2 under this ledger | **Forbidden** (design-locked) |
| Precision may recover Horizon deficit | **Forbidden** — still blocked |

---

## Terminal evidence

### Step 0 (no peek)

**Log:** `logs/horizon_tp_floor_step0_ab.txt`  
**Harness:** `python -m src.experiments.analyze_horizon_tp_floor --folds A,B --direction long`

| Fold | Mean Abs MFE (bps) | P(≥50) | P(≥60) | Near-miss [50,60) | SL-contam | HARDSTOP |
|---|---|---|---|---|---|---|
| Long A | 54.97 | 0.381 | 0.319 | **0.062** | 0.085 | no |
| Long B | 53.62 | 0.362 | 0.298 | **0.064** | 0.091 | no |

Near-miss under locked 60-bps geometry: ~TP/SL/TO = 0 / 0.21 / 0.78 (timeout-dominated). Rest near-miss ≈ Top-K (not ≫). Peak-bar near-miss med ~4 vs clearers ~5.

**Implication lock:** T1 authorized (hard-stop clear; near-miss ≥5% both folds).

### Peek 1 — T1 Long TP floor 60→50 (retrain + relabel)

**Logs:** `logs/horizon_tp_floor_t1_peek1_fold_a.txt` · `logs/horizon_tp_floor_t1_peek1_fold_b.txt`  
**Baseline:** cost peek-1 Long @ `c*=20` + 60-bps Long TP (`logs/horizon_cost_c20_peek1_fold_*.txt`)

| Gate | T1 A | T1 B | vs cost Long |
|---|---|---|---|
| **H5** | PASS · 0.037 [0.021, 0.053] · p_top **10.8%** | PASS · 0.021 [0.007, 0.037] · p_top **8.4%** | Hold gate; TB+1 **flat** (was 10.9 / 8.9) |
| H1 | PASS | PASS | Hold |
| H2 | PASS (was FAIL) | PASS | Hold / improve A |
| H3 | FAIL | **FAIL** (was PASS) | **Regression on B** |
| H4 @20 | −14 bps | −15 bps | A −17→−14; B −14→−15 — still neg |
| H4arch @30 | −24 bps | −25 bps | still neg |

**Gate read:** primary H5 dual-fold CI LB > 0 **holds**; sequential **no H1/H2/H3 regression** **fails** on Fold B H3. Report-only economics stay null. **No merge.**

---

## Verdict

| Item | Lock |
|---|---|
| Peek ledger | **1 / 1 spent — CLOSED** |
| Long TP floor merge (50 bps) | **No** — production stays **60 bps** (`3.0×c`) |
| Alternate floor / T2 | **Not authorized** — needs a new dual-judge charter |
| Precision | **Still blocked** until Horizon H4 / path economics clear under locked geometry |
| Horizon-path PASS / cascade-ready | **Forbidden / unproven** |

**Diagnosis residual after this charter:** near-miss mass at 50–60 bps is real and mostly clean, but **changing the Long TP floor alone** does not convert that mass into Top-K TB+1 lift or non-negative H4 under locked `c*=20` / `H=6`. Exit-timing and entry density levers already exhausted. Do not hand the deficit to Precision as a bailout; do not silently reopen H or cost.

---

## Code / harness artifacts

| Path | Role |
|---|---|
| `src/labels/triple_barrier.py` | `TP_FLOOR_LONG = 3×c` (60) restored; report-only `mfe_bps_*`, `mfe50_first_bar_long`, `mfe_abs_peak_bar_*` |
| `src/horizon/eval/tp_floor.py` | Step 0 absolute-MFE crossing / hard-stop |
| `src/experiments/analyze_horizon_tp_floor.py` | Step 0 CLI |
| `src/experiments/eval_horizon.py` | Unchanged — T1 was constant flip + retrain (not eval-only overlay) |

---

## Next workstream (outside this ledger)

**No automatic next peek on this ledger.** Further Long TP floors (55 / 45 / grid) or joint barrier edits need a **fresh dual-judge charter**.

**Primary (dual-judge CLOSED):** [horizon-short-travel-separation-stop-memo.md](horizon-short-travel-separation-stop-memo.md) — Short ranking / travel-separation under locked `c*=20` / `H=6`; peeks **1/2**; C1 no-merge; Precision / B1 still blocked.

Still deferred / forbidden without a separate charter:

- Remounting E1/E2 / L1 / path-room / L3  
- Cost ladder 15/10/25 or revert `c` to 30  
- Cutting primary `H=6`  
- Precision WS2 as Horizon H4 bailout  
