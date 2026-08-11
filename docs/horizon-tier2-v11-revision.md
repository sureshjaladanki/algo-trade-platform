# Tier 2 Horizon — v1.1 Revision (proposal)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Long / Short LightGBM **ranker** revisions after first A+B Horizon eval baselines  
**Status:** **OPEN — REVISE** (dual-judge validated 2026-08-11; process gaps locked before next A+B)  
**Judges:** [Gemini Flash](e982525b-460f-4f93-ab3d-697138b790ba), [Claude Sonnet](af622bc8-c824-4e30-8832-25ddf9e2c7c1)  
**Date:** 2026-08-11  
**Depends on:** [horizon-tier2-verdict.md](horizon-tier2-verdict.md) (locked v1 features/hyperparams — do not edit for this cycle), [horizon-tier2-eval-verdict.md](horizon-tier2-eval-verdict.md), [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md), [triple-barrier-verdict.md](triple-barrier-verdict.md), [regime-tier1-stop-memo.md](regime-tier1-stop-memo.md)  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Harness:** `python -m src.experiments.eval_horizon`

---

## How to use this doc

1. Keep [horizon-tier2-verdict.md](horizon-tier2-verdict.md) frozen as the shipped v1 feature/hyperparam contract.  
2. Land candidate changes, ablations, and judge notes **here**.  
3. When a change clears **A+B** gates (H1/H2/H3/H5 separately per sleeve) and is accepted, **merge** that slice into the locked verdict and mark it **MERGED** below.  
4. Do **not** retune features / hyperparams / K against gated H1–H5 on the same fold used for selection without a fresh A+B check ([eval anti-pattern #5](horizon-tier2-eval-verdict.md)).  
5. Do **not** reopen Regime search (CLOSED). Horizon owns path quality / selection this cycle.  
6. Never say bare “Long ship” — always **Horizon-ranker ship** (not cascade-ready).

---

## Summary

| Decision | Working choice (not merged) |
|---|---|
| Overall posture | **REVISE** (Claude) over Gemini ACCEPT+revisions — process gaps are preconditions, not cosmetics |
| Long A+B | **Horizon-ranker PASS** all confirmatory gates — H3 still **soft unresolved**; not cascade-ready |
| Short A+B | **FAIL ship** — H5 Fold A CI LB ≤ 0; Fold B recovers |
| Cascade link (WS0/WS1) | Explains Precision dead-end: Top-K `tb_tp` still ~7–11%; H4 always &lt; 0 under 30 bps |
| Root cause | Excess-return IC ≠ TB+1 density; Short H5 fold-unstable; Long soft rank 1–2 &lt; 3–K (H3 soft) |
| Ship / merge | **Nothing** until Short dual-fold H5 + Long soft-H3 closed without H2/H5 regress |
| Sequence next | D1/D2 → pre-register S1 rule → S1 A+B → (spec B1 now; activate after Short H5) → pre-register L1 mechanism → L1 A+B |
| Reject this cycle | Regime reopen, Precision WS2, pooled Long+Short gate, Fold-C locks, hyperparam grid on A+B, LambdaRank as first lever |

**One-line:** Dual judges confirm ranking skill is real and Short fails the path bridge on Fold A — fix Short hygiene and Long mono with one lever per A+B; do not claim cascade readiness from Horizon gates alone.

---

## Eval evidence (A+B) — validated

Harness: `python -m src.experiments.eval_horizon --direction both`  
K lock: Long **5** / Short **3** · `n_boot=500` · session-block CI  
Trainer CV IC reported as diagnostic only (not a ship gate).

| Fold | Train → Test | Regime run (context) |
|---|---|---|
| **A** | 2015–2017 → 2018 | `e9dbc994…` |
| **B** | 2016–2018 → 2019 | `7fff95a9…` |

### Gate matrix

| Gate | Long A | Long B | Short A | Short B | Dual-fold ship? |
|---|---|---|---|---|---|
| Universe / H10 | PASS | PASS | PASS | PASS | Yes (precondition) |
| **H1** IC | 0.074 [0.055, 0.095] | 0.067 [0.050, 0.083] | 0.058 [0.042, 0.074] | 0.024 [0.007, 0.040] | Long yes / Short yes (thin on B) |
| **H2** Top-K−Rest | 0.0008 PASS | 0.0008 PASS | 0.0006 PASS | 0.0005 PASS | Yes |
| **H3** mono | PASS (soft) | PASS (soft) | PASS | PASS | Yes (Long soft unresolved) |
| **H5** TB lift | 0.047 [0.031, 0.063] | 0.034 [0.013, 0.055] | **0.020 [−0.001, 0.043] FAIL** | 0.039 [0.019, 0.060] | **Long yes / Short NO** |

### Absolute path density (context — not gate)

| Sleeve · Fold | `P(TB=+1 \| TopK)` | `P(TB=+1 \| Rest)` | H4 (Top-K − 30 bps) |
|---|---:|---:|---:|
| Long A | **9.1%** | 4.4% | −22 bps |
| Long B | **7.2%** | 3.8% | −22 bps |
| Short A | **11.0%** | 9.0% | −24 bps |
| Short B | **11.0%** | 7.1% | −25 bps |

Gemini provisional aspirational floor (Top-K TB+1 ≳ **15%**) remains **unmet** on both sleeves — provisional readout only; hard ablation-attempt cap this cycle (Claude).

### H3 soft signal (Long)

| Fold | mean adj_excess ranks 1–2 (`m12`) | ranks 3–K (`m3k`) | Gate |
|---|---:|---:|---|
| A | 0.0004 | 0.0006 | PASS (CI not wrong-way sig) |
| B | 0.0006 | 0.0009 | PASS |

Same shape as WS0/WS1 rank 1–2 &lt; 3–5 — measured at Horizon before Precision fills. Two soft folds do **not** demote H3 to diagnostic.

### Sample scarcity (H6 diagnostic)

| Sleeve · Fold train | Bars | Sessions | Episodes | Median bars/episode |
|---|---:|---:|---:|---:|
| Long A | 245k | 299 | 377 | 532 |
| Short A | 117k | 316 | 411 | **224** |
| Long B | 265k | 308 | 386 | 540 |
| Short B | 125k | 329 | 440 | **224** |

Short remains ~½ Long bars with shorter episodes — locked Short regularization remains justified.

---

## Link to cascade WS0/WS1 (why this revision exists)

From [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md) (Fold A Precision book):

| WS finding | Horizon A+B echo |
|---|---|
| `tb_tp_rate` only **7–12%** in admitted fires | Top-K StockTB+1 still **7–11%** under naive close entry |
| Ranks **1–2 worse than 3–5** | Long H3 soft: `m12` &lt; `m3k` both folds |
| Precision not under-monetizing main mass | Do **not** open WS2 rules; fix upstream selection |
| Escalate Horizon / Regime | Regime **CLOSED**; this doc owns the Horizon lever |
| Absolute net ≥ 0 unmet under 30 bps | H4 always **≈ −22 to −25 bps** — XS edge ≪ friction |

**Decision-tree confirmation:** WS1’s `escalate_horizon_regime` call is still correct. A+B proves Horizon has **ordering skill** (H1/H2) but has **not** yet closed the path-density gap that made Precision selectivity futile.

---

## Dual-judge validation (2026-08-11)

Judges: [Gemini Flash](e982525b-460f-4f93-ab3d-697138b790ba), [Claude Sonnet](af622bc8-c824-4e30-8832-25ddf9e2c7c1)  
Scope: A+B baseline read + v1.1 revision strategy against [horizon-tier2-eval-verdict.md](horizon-tier2-eval-verdict.md). Harness design not re-litigated.

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Metric interpretation fidelity | 9.8/10 | 8/10 | Numbers correct; Claude: keep H3 **soft** qualifier on every Long restatement |
| Long ship read | 9.5/10 | 7/10 | **Horizon-ranker PASS** only — not cascade-ready (TB+1 7–9%; H3 soft) |
| Short ship read | 9.7/10 | 9/10 | **Do not ship Short** — H5 A fail; ranking skill still real |
| Cascade / WS1 honesty | 10/10 | 8.5/10 | Top-K TB+1 ~7–11% explains WS1; H4 &lt; 0 expected; no Precision WS2 |
| Revision strategy quality | 9.6/10 | 7/10 | Diagnostics-first OK; Claude: L1 underspecified; stop rule must decouple sleeves |
| Overfitting / process rigor | 10/10 | 7.5/10 | O8 strong; L1/S1 must be fully pre-registered before peek |
| Overall | **ACCEPT + revisions** | **REVISE** | **REVISE** — process gaps are preconditions before next A+B |

### Metric validation (both judges)

| Claim | Gemini | Claude | Locked |
|---|---|---|---|
| Long A+B PASS all confirmatory gates | ACCEPT | **REVISE** (retain soft-H3 qualifier) | **Horizon-ranker PASS; H3 soft unresolved** |
| Short FAIL ship solely on H5 Fold A | ACCEPT | ACCEPT | **Locked** |
| Short still has ranking skill (H1/H2) despite H5 A fail | ACCEPT | ACCEPT | **Locked** — path translation, not null IC |
| Absolute Top-K TB+1 ≪ 15% and insufficient vs 30 bps | ACCEPT | ACCEPT | **Locked** — provisional floor unmet; report-only |
| H4 negative while H2 positive is coherent | ACCEPT | ACCEPT | **Locked** (raw ~5–8 bps ≪ 30) |
| Long `m12` &lt; `m3k` both folds is soft WS1 echo | ACCEPT | ACCEPT | **Keep H3 gated** — two soft folds ≠ demotion to diagnostic |
| Trainer CV IC must not be ship gate | ACCEPT | ACCEPT | **Locked** (Short B trainer 0.109 vs holdout H1 0.024) |

### Where judges disagreed → locked choice

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Overall posture | ACCEPT + revisions | REVISE (process preconditions) | **REVISE** before next A+B |
| “Long ship OK” | Strong accept (gates clear; L1 still needed) | Overstated without Horizon-only qualifier | **Horizon-ranker PASS** language only |
| B1 Precision Short K=3 | Parallelize with D1/D2 now | Spec now; **activate after** Short dual-fold H5 | **Spec now / activate later**; never feeds Horizon gates |
| Stop rule | Asymmetric per sleeve | Decouple Short vs Long budgets | **Decoupled stop** (S1±S2 for Short; L1 for Long) |
| L1 mechanism | ACCEPT as direction | **REVISE** — underspecified | Pre-register exact transform + no H2/H5 regress before peek |
| S2 | ACCEPT-IF after S1 | REVISE → report-first only | **Report-first**; own A+B if ever gated |
| S3 | REVISE (single ablation) | DEFER | **DEFER** until S1 exhausted |
| TB+1 ≥ 15% soft objective | OK as readout | OK if hard ablation-attempt cap | **Report-only** + **hard attempt cap this cycle** |

---

## Diagnosis (locked for this cycle)

1. **Horizon is a working ranker, not a path factory.** H1/H2 prove cross-sectional ordering; H5 absolute rates prove most Top-K names still die in the TB dead zone / timeout — same economic story as WS1 (~86% of TIMEOUTs were `tb_label=0`).  
2. **Long ≠ Short.** Shared taxonomy, separate acceptance — Short fails the bridge gate on Fold A; Long clears confirmatory gates as a **Horizon ranker** only. No pooled “Horizon PASS.” No cascade-net claim.  
3. **Short failure mode is path translation, not null IC.** Fold A: scores order excess returns (H1/H2 PASS) but Top-3 barely beat Rest on StockTB+1. Fold B recovers — treat as **fold-unstable path filter**, not “delete Short sleeve.”  
4. **Long failure mode for cascade is soft top-rank toxicity + low absolute TB density.** Soft H3 + ~7–9% Top-K TB+1 → Precision sees ranks 1–2 drag and cannot clear 30 bps. Two soft H3 folds do **not** demote H3 to diagnostic.  
5. **Do not confuse eval entry with Precision fills.** H5 uses naive 15m close + frozen TB geometry by lock — lifts here are necessary but not sufficient for cascade PnL.

---

## Candidate ledger

| ID | Change | Gemini | Claude | Working lock | Merge status |
|---|---|---|---|---|---|
| **D0** | Freeze v1 features/hyperparams; log A+B as baseline | ACCEPT | ACCEPT | **DONE** (this doc) | N/A |
| **D1** | Report H7 F&O Short coverage + circuit/expiry slices (diagnostic) | ACCEPT | ACCEPT | **Run before model surgery** | OPEN |
| **D2** | H9 calibration / top-vs-bottom; K-sweep {3,5,8} diagnostic | ACCEPT | ACCEPT-if report-only | Diagnostic only — sweep **cannot** silently change gated K | OPEN |
| **S1** | Short path hygiene: F&O-active eligibility + UC/circuit exclude | ACCEPT | ACCEPT-if pre-registered | Primary Short lever; **exact rule before peek** | OPEN |
| **S2** | Short TOD soft cut / afternoon down-weight | ACCEPT-IF | REVISE report-first | **Report-first only**; own A+B if gated later | OPEN |
| **S3** | Short episode-weight / bounce hygiene ablation | REVISE | DEFER | **DEFER** until S1 exhausted; one pre-registered ablation max | DEFERRED |
| **L1** | Long monotonicity / score-tail guard | ACCEPT | **REVISE** (underspecified) | Pre-register transform + no H2/H5 regress before peek | OPEN |
| **L2** | Long Top-K emission threshold (~1×c buffer) | ACCEPT-IF | ACCEPT-IF | Only after L1; separate A+B; H6 floor | OPEN |
| **B1** | Align Precision Short registry **K=3** (Long stays 5) | ACCEPT now | ACCEPT-if activate later | **Spec now; activate after Short H5 dual-fold**; cascade metrics only | OPEN |
| **X1** | LambdaRank / multi-task TB auxiliary loss | DEFER | DEFER | After S1/L1 plateau | DEFERRED |
| **X2** | Reopen Regime / Precision WS2 / widen TP-SL | REJECT | REJECT | **REJECT this cycle** | REJECTED |
| **O8** | No H1–H5 / hyperparam search on A+B; one lever per fresh A+B | ACCEPT | ACCEPT — LOCK | **LOCK** | N/A |

---

## Pre-registration (LOCKED before next A/B peek)

| Item | Lock |
|---|---|
| Primary objective | Dual-fold **Short H5 PASS**; close Long soft-H3 without H2/H5 regress; report Top-K TB+1 (15% aspirational readout only) |
| Success (Short) | H5 CI LB &gt; 0 on **A and B**; H1/H2/H3 still PASS; no H10 regress |
| Success (Long) | H3 soft closes (`m12` ≥ `m3k` or CI(diff) not adverse) **and** H1/H2/H5 do not regress vs this baseline |
| Stop (Short) | After S1 (± one report-first S2 pass) fails dual-fold H5 → Short stop-memo for this cycle |
| Stop (Long) | After L1 fails soft-H3 without regress → Long stop-memo for this cycle |
| Attempt cap | Hard cap on total ablations this cycle regardless of proximity to TB+1 15% |
| Forbidden | Hyperparam grids on A+B; pooling sleeves; Fold C locks; Precision fills in H5; cascade net ≥ 0 from Horizon alone; activating B1 live before Short H5 dual-fold |
| Compare | One-shot vs **this doc’s baseline table** only |

### L1 pre-register requirement (Claude lock — before peek)

Write down before any Long A+B:

1. Exact transform (prefer **inference-time** score clip / rank-tier dampening — do not breach D0 hyperparam freeze via retrain-time loss change unless separately chartered).  
2. Success = H3 soft closes **and** H2/H5 CI LBs stay &gt; 0 (no “fix mono by killing signal”).  
3. One lever only in that A+B pass.

### S1 pre-register requirement (both judges)

Exact F&O-active + circuit/UC exclusion rule (thresholds, windows, coverage floor) written from D1 — not tuned post-hoc to H5.

---

## Build order (working — dual-judge revised)

1. **D0 done** — A+B baselines + judge lock recorded here.  
2. **D1 → D2** — F&O/circuit/expiry + calibration + K-sweep diagnostics (no ship claims).  
3. **B1 spec** (parallel with D1/D2) — document Precision Short `K=3`; **do not activate** until Short H5 dual-fold.  
4. **S1** — pre-register rule → Short F&O/circuit hygiene → fresh A+B (Short only success metric).  
5. **L1** — pre-register mechanism → Long mono guard → fresh A+B (separate pass from S1).  
6. **L2 / S2** — only if residual; each gets its own A+B; S2 stays report-first unless separately gated.  
7. **X1** — deferred after path hygiene / mono plateau.

---

## Explicit non-goals (this cycle)

- Merging any Horizon feature/hyperparam change into [horizon-tier2-verdict.md](horizon-tier2-verdict.md) before dual-fold clear  
- Reopening Tier 1 Regime search or Daily/HMM emissions  
- Precision WS2 runway / fallback / no-chase promotion  
- Treating trainer purged-WF IC as acceptance  
- Promoting Gemini absolute TB+1 ≥ 15% to a hard gate before another A+B cycle  
- Using Fold C (COVID / halt) as a lock input  
- Activating B1 live against an unshipped Short ranker  

---

## Implementation notes (code posture)

| Area | Current v1 (frozen) | v1.1 touchpoint |
|---|---|---|
| Features | `LONG_FEATURES` / `SHORT_FEATURES` in `src/horizon/horizon_model.py` | Prefer mask/eligibility changes (S1) before feature surgery |
| Hyperparams | Long Huber α0.9 depth4; Short Huber α0.7 depth3 `min_child=400` | **No grid** this cycle |
| Eval K | Long 5 / Short 3 in `src/horizon/eval/` | Keep; B1 aligns Precision Short after Short ships |
| Precision K | `TOP_K=5` shared today | B1: Short registry K=3 (spec now) |
| Episode weights | `episode_balanced_weights` already on | Deferred under S3 |
| Regime | Soft overlay, CLOSED | Pass-through only |

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-tier2-verdict.md](horizon-tier2-verdict.md) | Locked v1 features / hyperparams |
| [horizon-tier2-eval-verdict.md](horizon-tier2-eval-verdict.md) | Gate taxonomy this revision obeys |
| [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md) | Why escalate — low TB+1 + rank inversion |
| [triple-barrier-verdict.md](triple-barrier-verdict.md) | Frozen TB geometry for H5 |
| [precision-tier3-verdict.md](precision-tier3-verdict.md) | Downstream consumer — B1 contract only |
| [regime-tier1-stop-memo.md](regime-tier1-stop-memo.md) | Regime CLOSED |

---

## Next step

Run **D1** (Short F&O / circuit / expiry diagnostic slices) and **pre-register** the exact S1 eligibility rule + L1 transform before any retrain. Re-eval with:

```text
python -m src.experiments.eval_horizon --train-period 2015-2017 --test-period 2018-2018 --direction both
python -m src.experiments.eval_horizon --train-period 2016-2018 --test-period 2019-2019 --direction both
```

Update this ledger’s Merge status after each isolated try — one lever per A+B pass.
