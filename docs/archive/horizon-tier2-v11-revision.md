# Tier 2 Horizon — v1.1 Revision (proposal)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Long / Short LightGBM **ranker** revisions after first A+B Horizon eval baselines  
**Status:** **CLOSED this cycle** — Short + Long stop-memos filed; no v1.1 merges  
**Stop memos:** [horizon-tier2-short-stop-memo.md](horizon-tier2-short-stop-memo.md), [horizon-tier2-long-stop-memo.md](horizon-tier2-long-stop-memo.md)  
**Judges:** [Gemini Flash](e982525b-460f-4f93-ab3d-697138b790ba), [Claude Sonnet](af622bc8-c824-4e30-8832-25ddf9e2c7c1)  
**Date:** 2026-08-11  
**Depends on:** [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) (locked v1 features/hyperparams — do not edit for this cycle), [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md), [cascade-tier3-ws01-verdict.md](../cascade-tier3-ws01-verdict.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [regime-tier1-stop-memo.md](regime-tier1-stop-memo.md)  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Harness:** `python -m src.experiments.eval_horizon`

---

## How to use this doc

1. Keep [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) frozen as the shipped v1 feature/hyperparam contract.  
2. Land candidate changes, ablations, and judge notes **here**.  
3. When a change clears **A+B** gates (H1/H2/H3/H5 separately per sleeve) and is accepted, **merge** that slice into the locked verdict and mark it **MERGED** below.  
4. Do **not** retune features / hyperparams / K against gated H1–H5 on the same fold used for selection without a fresh A+B check ([eval anti-pattern #5](../horizon-tier2-eval-verdict.md)).  
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
| Sequence next | **Done** — stop-memos filed; new work needs a fresh dual-judge charter |
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

From [cascade-tier3-ws01-verdict.md](../cascade-tier3-ws01-verdict.md) (Fold A Precision book):

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
Scope: A+B baseline read + v1.1 revision strategy against [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md). Harness design not re-litigated.

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
| **D1** | Report H7 F&O Short coverage + circuit/expiry slices (diagnostic) | ACCEPT | ACCEPT | **DONE** — see D1 results; F&O list absent | DONE (diag) |
| **D2** | H9 calibration / top-vs-bottom; K-sweep {3,5,8} diagnostic | ACCEPT | ACCEPT-if report-only | **DONE** — see D2 results; gated K unchanged | DONE (diag) |
| **S1** | Short path hygiene: F&O-active eligibility + UC/circuit exclude | ACCEPT | ACCEPT-if pre-registered | **A+B FAIL** — Fold A H5 CI LB≤0; Fold B H10 regress; mask reverted off | FAIL (no merge) |
| **S2** | Short TOD soft cut / afternoon down-weight | ACCEPT-IF | REVISE report-first | **DONE (report)** — PM H5 ≥ AM both folds; do **not** hard-cut | DONE (diag; no gate) |
| **S3** | Short episode-weight / bounce hygiene ablation | REVISE | DEFER | **DEFER** until S1 exhausted; one pre-registered ablation max | DEFERRED |
| **L1** | Long monotonicity / score-tail guard | ACCEPT | **REVISE** (underspecified) | **A+B FAIL** — soft-H3 closes on B only; A still m12&lt;m3k; mask reverted off | FAIL (no merge) |
| **L2** | Long Top-K emission threshold (~1×c buffer) | ACCEPT-IF | ACCEPT-IF | **DONE (report)** — floor rarely binds; A keep H5 &lt; drop; no gated A+B | DONE (diag; no gate) |
| **B1** | Align Precision Short registry **K=3** (Long stays 5) | ACCEPT now | ACCEPT-if activate later | **SPEC LOCKED** below; activate after Short H5 dual-fold | OPEN (spec) |
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

### D1 results (2026-08-11) — diagnostic only

Harness: `python -m src.experiments.eval_horizon` with H7 flags (`CIRCUIT_RANGE_EPS=1e-4`, `H_BARS=4`, Thursday expiry). Logs: `logs/horizon_d1_fold_a.txt`, `logs/horizon_d1_fold_b.txt`.

| Slice | Fold A Short | Fold B Short |
|---|---|---|
| F&O list | **absent** | **absent** |
| `is_circuit_bar` row % | 0.49% | 0.53% |
| `fwd_circuit_hit` row % | 1.18% | 1.07% |
| Top-K `fwd_circuit` % | 1.61% | 0.78% |
| Expiry row % (Thu) | 20.8% (26/128 sess) | 20.5% (28/137 sess) |
| H5 point — clean | 0.0203 | 0.0407 |
| H5 point — fwd_circuit | ~0 (n≪ min-N) | ~0 (n≪ min-N) |
| H5 point — expiry / non-expiry | 0.0304 / 0.0169 | 0.0314 / 0.0413 |
| Gated H5 (baseline) | 0.020 [−0.001, 0.043] **FAIL** | 0.039 [0.019, 0.060] PASS |

**Read:** Circuit/UC contamination is rare (~1% fwd; Top-K fwd ≤ 1.6%). Clean-slice H5 ≈ pooled H5 — Fold A H5 fail is **not** explained by flat-bar density alone. Expiry vs non-expiry H5 sign flips across folds — report-only; do not gate. F&O hard filter blocked until a static membership list exists.

### S1 rule (LOCKED — measured; **no merge**)

Exact eligibility subtract for Short eval mask (one lever; no ε retune to H5):

1. **Exclude** if `is_circuit_bar` **OR** `fwd_circuit_hit`, where  
   - `is_circuit_bar` ⇔ `(high == low) ∨ (range_pct ≤ 1e-4)`  
   - `fwd_circuit_hit` ⇔ any of the next **4** same-session bars is `is_circuit_bar`  
2. **F&O-active:** **blocked** — `fno_list=absent`; do not invent coverage.  
3. **Coverage floor:** after exclusion, Short must still clear min-N (≥150 bars / ≥30 sessions) on **both** A and B.  
4. **Success / stop:** dual-fold Short H5; no H10 regress.

### S1 A+B results (2026-08-11) — FAIL

Code: `APPLY_S1_SHORT` in `src/horizon/eval/common.py` (reverted **False** after measure). Logs: `logs/horizon_s1_fold_a.txt`, `logs/horizon_s1_fold_b.txt`.

| Gate | Fold A Short | Fold B Short | vs baseline |
|---|---|---|---|
| S1 drop | 1.33% (1634/123315) | 1.20% (1739/144533) | ~1% as D1 predicted |
| H10 | PASS | **FAIL** (null IC 0.008 [0.003, 0.013]) | **regress** on B |
| H1 | 0.058 [0.041, 0.075] PASS | precondition-fail | — |
| H2 | 0.0006 PASS | precondition-fail | — |
| H3 | PASS | precondition-fail | — |
| H5 | 0.021 [**−0.0009**, 0.043] **FAIL** | precondition-fail | A: LB still ≤0 (was −0.0013) |
| Long A/B | unchanged PASS (incl. soft H3) | unchanged PASS | no Long regress |

**Verdict:** S1 does **not** clear dual-fold Short H5. Fold A H5 CI LB remains ≤ 0; Fold B trips H10 after the mask (gated Short metrics not scorable). **Do not merge.** Per stop rule: at most one report-first **S2**, else **Short stop-memo** for this cycle. Long path (L1) proceeds separately.

### L1 transform (LOCKED — measured; **no merge**)

1. **Transform (inference only — honors D0 freeze):** within each bar, rank actionable scores descending; set scores of ranks **1 and 2** equal to the **rank-3** score; re-rank. No retrain, no loss change, no hyperparam edit.  
2. **Success:** soft H3 closes (`m12` ≥ `m3k`) on **A and B** **and** H2/H5 CI LBs stay &gt; 0 vs baseline.  
3. **One lever only** in that A+B pass — separate from S1.

### L1 A+B results (2026-08-11) — FAIL

Code: `APPLY_L1_LONG` (reverted **False** after measure). Logs: `logs/horizon_l1_fold_a.txt`, `logs/horizon_l1_fold_b.txt`.

| Gate | Fold A Long | Fold B Long | vs baseline |
|---|---|---|---|
| H3 soft | m12=0.0004 **&lt;** m3k=0.0006 (still soft) | m12=0.0008 **=** m3k=0.0008 (closes) | A unresolved |
| H3 gate | PASS | PASS | — |
| H2 | 0.0008 [0.0004, 0.0011] PASS | 0.0009 [0.0005, 0.0014] PASS | no gate regress |
| H5 | 0.044 [0.029, 0.060] PASS | 0.034 [0.013, 0.056] PASS | no gate regress |
| Short | baseline (S1 off) | baseline | unchanged |

**Verdict:** L1 does **not** clear dual-fold soft-H3. **Do not merge.** → Long stop-memo this cycle.

### S2 report-first (2026-08-11) — no hard cut

Afternoon = bar-end `time_only ≥ 13:00`. Metrics: `S2cov` / `S2h*`. Logs: `logs/horizon_s2l2_fold_a.txt`, `logs/horizon_s2l2_fold_b.txt`.

| Fold | PM row % | H5 morning / afternoon | H2 am / pm |
|---|---:|---:|---:|
| A Short | 27.4% (645 / 244 bars) | 0.018 / **0.024** | 0.0006 / 0.0006 |
| B Short | 30.0% (722 / 310 bars) | 0.029 / **0.065** | 0.0005 / 0.0005 |

**Read:** Afternoon is **not** the weaker Short path on H5 — PM ≥ AM on both folds. A soft afternoon cut would likely **hurt** dual-fold H5. **Do not promote S2 to gated A+B.** → Short stop-memo.

### L2 report-first (2026-08-11) — no gated A+B

Floor: mean Top-K `eval_score` ≥ `ROUND_TRIP_COST` (0.003). Metrics: `L2cov` / `L2gap` / `L2h*`.

| Fold | Keep bars | L2gap (K vs K+1) | H5 keep / drop |
|---|---:|---:|---:|
| A Long | 23/749 (3.1%) | ≈0 | 0.016 / **0.047** |
| B Long | 23/696 (3.3%) | ≈0 | 0.215 (n=15 thin) / 0.029 |

**Read:** 1×c mean-Top-K floor almost never fires; when it does on Fold A it **selects worse** H5 than the drop mass. Fold B keep looks strong but n≪ min-N. **Do not charter gated L2 A+B this cycle.** → Long stop-memo stands.

### D2 results (2026-08-11) — diagnostic only

Harness H9: top20−bot20 `adj_excess` (`H9sep`); Q5−Q1 StockTB+1 (`H9cal`); point H2 value + H5 in note for K∈{3,5,8} (`H9ks`). Logs: `logs/horizon_d2_fold_a.txt`, `logs/horizon_d2_fold_b.txt`. **Gated K unchanged.**

| Sleeve · Fold | H9sep | H9cal (Q5−Q1) | K=3 H5 / p_top | K=5 H5 / p_top | K=8 H5 / p_top |
|---|---:|---:|---:|---:|---:|
| Long A | 0.0009 | 0.038 | 0.053 / 0.097 | **0.047 / 0.091** (gated) | 0.037 / 0.081 |
| Long B | 0.0007 | 0.016 | 0.037 / 0.075 | **0.034 / 0.072** (gated) | 0.028 / 0.066 |
| Short A | 0.0006 | 0.026 | **0.020 / 0.110** (gated) | 0.027 / 0.118 | 0.023 / 0.114 |
| Short B | 0.0002 | 0.018 | **0.039 / 0.110** (gated) | 0.029 / 0.100 | 0.023 / 0.095 |

**Read:** Score separation and quintile TB calibration are positive on both sleeves/folds (ordering skill real). Long: tighter K concentrates H5; K=8 dilutes — keep gated K=5. Short Fold A: diagnostic K=5 H5 point &gt; gated K=3, but Fold B prefers K=3 — **do not retune gated Short K=3 from this sweep** (O8 / anti-pattern #5). No ship claims from D2.

### B1 spec (LOCKED — not activated)

Cascade / Precision contract only — **never feeds Horizon H1–H5 gates**.

| Item | Spec |
|---|---|
| Long registry K | **5** (unchanged; matches `src/precision/session.py` `TOP_K=5` today) |
| Short registry K | **3** (align with Horizon eval `K_SHORT`) |
| Activate when | Short Horizon ranker clears **dual-fold H5** under S1 (or stop-memo path explicitly re-opens B1) |
| Forbidden until then | Editing live Precision Short admit to K=3 against an unshipped Short sleeve |
| Metrics after activate | Cascade / Precision book only — not a Horizon re-gate |

---

## Build order (working — dual-judge revised)

1. **D0 done** — A+B baselines + judge lock recorded here.  
2. **D1 done** — H7 circuit/expiry + S1/L1 pre-register.  
3. **D2 done** — H9 + K-sweep report-only; gated K unchanged. **B1 spec locked** (activate later).  
4. **S1 done — FAIL** — circuit/UC exclude does not clear Short dual-fold H5; mask off.  
5. **L1 done — FAIL** — rank-3 floor closes soft-H3 on B only; A still soft; mask off.  
6. **S2 / L2 report-first done** — no gated activation (PM not weaker; 1×c floor not useful).  
7. **Stop-memos done** — [short](horizon-tier2-short-stop-memo.md) / [long](horizon-tier2-long-stop-memo.md). B1 stays spec-only. X1 deferred.

---

## Explicit non-goals (this cycle)

- Merging any Horizon feature/hyperparam change into [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) before dual-fold clear  
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
| H7 hygiene | Not in v1 gated mask | Eval-only flags in `annotate_hygiene_flags` (`CIRCUIT_RANGE_EPS`, Thu expiry); S1 may later reuse |
| H9 / K-sweep | Not in v1 | `H9sep` / `H9cal` / `H9ks` report-only; `K_SWEEP=(3,5,8)` never changes gated K |
| Precision K | `TOP_K=5` shared today | B1: Short registry K=3 (spec locked; activate after Short H5) |
| Episode weights | `episode_balanced_weights` already on | Deferred under S3 |
| Regime | Soft overlay, CLOSED | Pass-through only |

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) | Locked v1 features / hyperparams |
| [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md) | Gate taxonomy this revision obeys |
| [cascade-tier3-ws01-verdict.md](../cascade-tier3-ws01-verdict.md) | Why escalate — low TB+1 + rank inversion |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | Frozen TB geometry for H5 |
| [precision-tier3-verdict.md](../precision-tier3-verdict.md) | Downstream consumer — B1 contract only |
| [regime-tier1-stop-memo.md](regime-tier1-stop-memo.md) | Regime CLOSED |
| [horizon-tier2-v11-short-stop-memo.md](horizon-tier2-v11-short-stop-memo.md) | Short v1.1 stop (this cycle) |
| [horizon-tier2-v11-long-stop-memo.md](horizon-tier2-v11-long-stop-memo.md) | Long v1.1 stop (this cycle) |

---

## Closeout dual-judge validation (2026-08-11)

Judges: [Gemini Flash](000bb389-95c4-4a24-a768-ab4293580712), [Claude Sonnet](2b4f85d0-81d3-4545-a520-319774652d4c)  
Scope: post-cycle metrics + S1/L1/S2/L2 outcomes + stop-memos + next steps (vs baseline A+B and eval verdict).

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Metric fidelity | 10/10 ACCEPT | 8/10 ACCEPT | Numbers verified; keep soft-H3 foregrounded |
| Long vs Short | 10/10 ACCEPT | 8/10 ACCEPT | Decoupled; Short path-fail not null IC |
| Optimization honesty | 10/10 ACCEPT | 8/10 ACCEPT | O8 + no-merge match code flags |
| Stop / next steps | 10/10 ACCEPT | 9/10 **REVISE** | Direction right; add peek-budget ledger |
| Process / overfit | 10/10 ACCEPT | 7/10 | Strong O8; **7 A+B peeks** this cycle — ledger now on stop-memos |
| Cascade honesty | 10/10 ACCEPT | 8.5/10 ACCEPT | Not cascade-ready; B1 not live |
| Overall | **ACCEPT** | **REVISE** | **ACCEPT-IF** peek budget recorded → **CLOSED** |

### Claim locks (both judges)

| Claim | Gemini | Claude | Locked |
|---|---|---|---|
| Long Horizon-ranker PASS; not cascade-ready; soft H3 unresolved | ACCEPT | ACCEPT | **Locked** |
| Short no ship; ranking skill real | ACCEPT | ACCEPT | **Locked** |
| S1/L1 no-merge | ACCEPT | ACCEPT | **Locked** |
| S2/L2 not gated | ACCEPT | ACCEPT | **Locked** |
| Next steps = freeze + new charter only | ACCEPT | **REVISE** (+ peek ledger) | **Locked after peek ledger on stop-memos** |
| TB+1 ≪ 15% and H4&lt;0 with H2&gt;0 coherent | ACCEPT | ACCEPT | **Locked** |

**Closeout:** Peek-budget line (**7** Fold A+B harness invocations) added to both stop-memos per Claude. Cycle remains **CLOSED**; no S1/L1 reopen on these folds.

---

## Next step

**None this cycle.** Stop-memos:

- [horizon-tier2-v11-short-stop-memo.md](horizon-tier2-v11-short-stop-memo.md) — Short ship / H5 bridge CLOSED  
- [horizon-tier2-v11-long-stop-memo.md](horizon-tier2-v11-long-stop-memo.md) — Long soft-H3 / cascade-ready CLOSED  

Do **not** activate B1. Do **not** merge S1/L1. Baseline flags remain `APPLY_S1_SHORT=False`, `APPLY_L1_LONG=False`. Reopen only under a new dual-judge charter that inherits the **7-peek** multiplicity baseline.
