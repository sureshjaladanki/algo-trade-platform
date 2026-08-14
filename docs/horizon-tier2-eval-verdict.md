# Tier 2 Horizon — Evaluation Framework Verdict

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Tier-level **eval harness** for Horizon ranking only (Long + Short) — feature set / hyperparams locked elsewhere  
**Judges:** Gemini Flash, Claude Sonnet  
**Date:** 2026-08-11  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Depends on:** [horizon-tier2-verdict.md](horizon-tier2-verdict.md), [regime-tier1-eval-verdict.md](regime-tier1-eval-verdict.md), [triple-barrier-verdict.md](triple-barrier-verdict.md), [cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md), [regime-tier1-stop-memo.md](archive/regime-tier1-stop-memo.md)  
**Status:** **REVISE → harness shipped** (philosophy + primary metrics locked; run A+B baselines next)

---

## Summary

| Decision | Locked choice |
|---|---|
| Role of eval | Measure Horizon as a **ranker** (cross-sectional ordering + bridge into raw path quality) — **not** a PnL engine or direction forecaster |
| Confounding | **Never** score Horizon with Precision fire PnL/fills or Regime index hit-rate |
| Confirmatory / gated | **H1, H2, H3, H5** — H3 promoted this escalation cycle; H10 + universe parity are preconditions |
| Long vs Short | **Shared metric taxonomy, separate gates** — not a different metric language |
| Sign convention | Eval-only: `adj_excess = side · fwd_excess` with `side ∈ {+1 Long, −1 Short}` so one formula serves both |
| H5 contrast | **Top-K vs Rest** (primary); Top-K vs sleeve-average as diagnostic companion |
| H5 entry reference | **Naive fill at 15m decision-bar close**, frozen TB geometry — never Precision timing |
| K | **Long K=5** (matches Precision `TOP_K`); **Short K=3** (asymmetric); sweep {3,5,8} diagnostic |
| Gate rigor | **Session-block-bootstrap 95% CI LB > 0**; absolute floors provisional |
| Folds | Reuse Regime calendar: **A+B gate**; **C informational** |
| Build posture | **REVISE → harness shipped** — run Fold A/B baselines next |

**One-line:** Horizon eval measures whether the ranker's ordering carries real, cost-agnostic cross-sectional skill and whether that skill survives translation into raw triple-barrier path quality — never whether Precision monetizes it or Regime admits it.

---

## Why this eval exists

WS0/WS1 ([cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md)) showed admitted fires with `tb_tp_rate` only ~7–12%, and **rank 1–2 worse than rank 3–5**. Optimizing Precision alone on that book is a category error. Tier 1 Regime search is **CLOSED** ([A0 stop memo](archive/regime-tier1-stop-memo.md)). This harness answers, at Horizon alone: *does the model's ordering of names carry real skill, and does that skill invert near the top of the ranking?*

---

## Judge scores

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Long eval design | 9.5/10 | 7.5/10 | **Strong taxonomy; fix per-bar IC / bootstrap unit** |
| Short eval design | 9/10 | 6/10 | **Shared formulas + asymmetric K / min-N — operationalize Short** |
| Long ≠ Short separation | 10/10 | 6.5/10 | **Shared taxonomy, separate gates — lock** |
| Tier 1/3 anti-confounding | 10/10 | 6/10 | **Anti-patterns good; pin H5 entry reference** |
| Gate rigor | 9.5/10 | 6/10 | **CI LB > 0; promote H3 this cycle; harden formulas** |
| NSE practicality | 9.5/10 | 7/10 | **MIS / bleed / PIT mandatory; circuit / F&O Short as hygiene** |
| Overall | **ACCEPT + revisions** | **REVISE** | **REVISE → build** |

---

## Locked philosophy

1. **Horizon is a ranker**, not a strategy PnL attribution layer or market-direction forecaster.  
2. Prefer **cross-sectional ranking economics** over cascade end-to-end PnL.  
3. **Long ≠ Short** — every confirmatory metric is a *separate, separately-gated* number. No pooled acceptance. Shared metric IDs and formulas; asymmetric K, min-N, and MIS cutoffs.  
4. **Only H1 / H2 / H3 / H5 gate ship decisions** this cycle. H4, H6–H9 are diagnostic. **H10 + universe parity are preconditions.**  
5. **Do not score with Precision fills** (bounded-wait, spread ceilings, fallback) or **Regime index I1/I5**.  
6. **Do not retune** features / hyperparams / K against gated metrics on the same fold used for ship without a fresh A+B check. Trainer-internal purged-WF IC is **diagnostic only** — never a ship gate.  
7. **Inference:** session-block bootstrap CIs — no bar-level binomial “significance.”

---

## Metric catalog

| ID | Metric | Role |
|---|---|---|
| **H1** | Cross-sectional Spearman IC (score vs side-adjusted fwd excess) | **PRIMARY / GATED** |
| **H2** | Top-K vs Rest excess spread (raw, uncosted) | **PRIMARY / GATED** |
| **H3** | Rank monotonicity (rank-tier disaggregation) | **GATED this cycle** (WS0/WS1 inversion) |
| **H5** | StockTB+1 Top-K vs Rest (frozen geometry, naive entry) | **PRIMARY / GATED / BRIDGE** |
| H4 | Cost-netted top-K excess (flat 30 bps) | Diagnostic companion to H2 |
| H6 | Sleeve coverage / episode count / scarcity | Diagnostic |
| H7 | PIT / ADV / Short F&O eligibility audit | Diagnostic → feeds universe precondition |
| H8 | Fold stability (A/B; C informational) | Diagnostic |
| H9 | Calibration / top-vs-bottom score separation | Diagnostic |
| **H10** | Null / leakage audit | **PRECONDITION** (binary) |

---

## Primary metric definitions (locked)

### Shared setup

For decision bar `t` (post-hysteresis sleeve, session date `d`), `side = +1` Long / `−1` Short:

```
eligible(t) = PIT Nifty100 ∩ ADV-liquid ∩ sleeve-active(t)
              ∩ not halted/circuit-pinned ∩ within MIS entry cutoff
              ∩ (Short only: F&O-active names — see NSE pitfalls)

score_i(t)      = Horizon score, eval-harness sign-flipped so higher = more actionable for BOTH sleeves
fwd_excess_i(t) = R_i(t, t+H) − R_nifty(t, t+H)   # identical to Tier-2 training target
adj_excess_i(t) = side · fwd_excess_i(t)
```

| Constraint | Lock |
|---|---|
| Auction bleed | Bar-end **09:30** excluded from gated metrics |
| Long last decision | ≤ **~14:15** bar-end |
| Short last decision | ≤ **~14:00** bar-end |
| Horizon | **H = 4** bars (60m) |
| Cost in gated H1/H2 | **Raw / uncosted** — friction belongs in H4 (diagnostic) and TB floors inside H5 |
| Bootstrap unit | **Trading session** for per-bar series (H1/H2/H3); episode-block as robustness diagnostic |

### H1 — Spearman IC (PRIMARY)

```
IC(t) = Spearman({score_i(t)}, {adj_excess_i(t)})   over i ∈ eligible(t)
H1_side = mean_t IC(t) over sleeve-active decision bars in the fold
```

**Per-bar cross-sectional** — not a pooled panel correlation (pooling fakes DoF and mixes within-day skill with across-day drift).

**Gate (A+B):** session-block-bootstrap 95% CI LB on `H1_Long` and `H1_Short` each **> 0**.

### H2 — Top-K vs Rest excess spread (PRIMARY)

```
TopK(t) = K names with highest score_i(t) in eligible(t)
Rest(t) = eligible(t) \ TopK(t)          # sleeve-eligible only — never pad with ineligible names
Spread(t) = mean(adj_excess | TopK) − mean(adj_excess | Rest)
H2_side = mean_t Spread(t)
```

**Mandatory companion:** report `mean(adj_excess | rank=r)` for ranks 1..K (at minimum **1–2 vs 3–K**). Aggregate Top-K alone can hide the WS0/WS1 inversion.

**Gate (A+B):** CI LB on `H2_Long` and `H2_Short` each **> 0**. Raw/uncosted by design.

### H3 — Rank monotonicity (GATED this cycle)

```
Buckets {1–2, 3–K, K+1..2K, rest}: mean(adj_excess) should be non-increasing in rank order
```

**Gate (A+B, this cycle):** no fold may show rank **1–2** mean `adj_excess` **below** rank **3–K** with CI(diff) excluding zero in the wrong direction. Demote to diagnostic only after two consecutive folds clear it.

**Why gated:** WS0/WS1's damning finding is a *monotonicity* failure. H1/H2 aggregates can look clean while top-tier inverts — Claude's promotion; Gemini kept H3 diagnostic — **evidence wins → gate**.

### H5 — StockTB+1 bridge (PRIMARY / BRIDGE)

```
StockTB(i,t) ∈ {+1, −1, 0} over (t, t+H)
  using FROZEN TB geometry (ATR TP/SL + cost floors, hard H=4) on the stock path
Entry reference: LOCKED at 15m decision-bar CLOSE
  — never Precision bounded-wait / spread ceiling / fallback fills

H5_side(t) = P(StockTB=+1 | TopK(t)) − P(StockTB=+1 | Rest(t))
H5_side    = pooled over t, session-block-bootstrap CI
```

Also **report** (diagnostic, not gate): Top-K vs sleeve-average `P(TB=+1 | eligible)` — Gemini's marginal-value framing (proportional to Top vs Rest up to scale; useful readout, not a second gate).

**Gate (A+B):** CI LB > 0 for Long and Short separately. Report absolute `P(StockTB=+1 | TopK)` as **context** vs WS1 ~7–12% — not as an equivalence claim (different entry assumptions).

**Why this stays Horizon skill (not Precision):** frozen geometry + naive uniform entry + fixed K / no size scaling. If H5 uses Precision timing, it smuggles Tier 3 skill.

---

## Long vs Short — expert lock

| Item | Lock |
|---|---|
| Metric language | **Same IDs and formulas** (`side` folded in) |
| Acceptance | **Separate** CI gates, min-N, K — never pool |
| K | Long **5** / Short **3** |
| Min-N (provisional) | Long ≥ 30 sessions / ≥ 100 bars; Short ≥ 30 sessions / ≥ **150** bars |
| MIS cutoff | Long ~14:15 / Short ~14:00 (inherited) |
| Short universe | Prefer **F&O-active** names (Gemini) — promote toward hard Short eligibility after measuring coverage; until then report as H7 slice |
| Verdict | Separate eval **runs** and **acceptance**, not a wholly different Short metric set |

---

## Path / universe discipline

| Item | Lock |
|---|---|
| Series for H1/H2/H3/H5 | **Individual stock paths** — not index, not EW basket (those are Regime's job) |
| Universe per bar | Exact Tier-2 train/infer mask (PIT + ADV + cascade sleeve) |
| `Rest(t)` | Remaining **sleeve-eligible** names only |
| Excess definition | Identical to training target (vs Nifty) — no sector-relative substitute for gated metrics |
| Trainer CV IC | Report as diagnostic; **external A/B harness is the sole ship gate** |

---

## Acceptance gates (hardened)

### Precondition (binary, before research metrics)

| Gate | Rule |
|---|---|
| H10 leakage / null | Pass/fail — no forward-looking joins; score-shuffle / label-permutation → IC ≈ 0 |
| Universe parity | Eval universe == train/infer universe (PIT + ADV + cascade mask) |

### Confirmatory (must pass Fold A **and** B)

| Gate | Rule |
|---|---|
| H1 | CI(IC) LB > 0, Long and Short separately |
| H2 | CI(Spread) LB > 0, Long and Short separately (raw) |
| H3 | No rank 1–2 vs 3–K inversion with CI wrong-way significant |
| H5 | CI(H5) LB > 0, Long and Short separately |

### Diagnostic (report; do not ship-lock alone)

| Check | Guidance |
|---|---|
| H4 cost-netted spread | Sanity at flat 30 bps — not Precision PnL |
| Absolute IC / tb_tp floors | Gemini aspirational (IC ≳ 0.01 / Short ≳ 0.015; Top-K TB+1 ≳ 15%) — **provisional readouts only** until A+B baselines exist |
| H6 coverage / eligible N | Grounds K; if `N_eligible < 15`, report dynamic `K_eff = min(K, ⌊0.15 N⌋)` as diagnostic, do not change gated K silently |
| H7 PIT / ADV / F&O Short | Compliance + Short F&O coverage |
| H8 / H9 | Fold stability; calibration |
| Episode-block bootstrap | Robustness companion to session-block primary |
| Fold C | Informational only — never a lock input |
| Expiry / gap / squeeze MAE | Slices — never pooled gate inputs |

### Minimum-N floor

Any cell below Long/Short min-N → **insufficient data**, never gated.

---

## Top 5 to implement first (80% diagnostic value)

| Rank | Metric | Why |
|---|---|---|
| 1 | **H10 + universe parity** | Preconditions — cheapest binary fail-fast |
| 2 | **H1** | Does the score carry any XS information? |
| 3 | **H3** | Directly tests WS0/WS1 rank inversion |
| 4 | **H2** | Selection-quality gate (safe once #3 is visible) |
| 5 | **H5** | Cascade bridge: does top-K carry better raw TB paths? |

Second wave: H4, H6–H9, episode-block robustness, K-sweep, expiry/circuit slices.

*(Gemini preferred H5 earlier in the build order; locked order puts preconditions and fail-fast IC/monotonicity first — same pattern as Regime D5/I7 → I1 → I5.)*

---

## Anti-patterns (locked)

1. Scoring Horizon with Precision fire PnL or Precision **fill prices / timing**  
2. Using Regime index I1/I5 as a Horizon score (or vice versa)  
3. Pooling Long + Short into one acceptance number  
4. Locking K / thresholds / gates on Fold C  
5. Retuning features / hyperparams / K against H1–H5 on the same selection fold without fresh A+B  
6. Bar-level binomial tests ignoring within-day IC autocorrelation  
7. Aggregate Top-K spread **without** rank-tier disaggregation  
8. Padding `Rest(t)` with non-sleeve-eligible names  
9. Treating trainer-internal purged-WF IC as the ship gate  
10. Silently swapping eval `fwd_excess` (e.g. sector-relative) vs training Nifty-excess  
11. Claiming cascade net ≥ 0 from Horizon eval alone  

---

## Where judges disagreed

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Overall | ACCEPT + revisions (9.4) | REVISE (formulas unbuildable as drafted) | **REVISE → build** |
| H3 role | Diagnostic | Promote to gated (WS0/WS1 is inversion) | **Gated this cycle** |
| H5 contrast | Top-K vs sleeve-average (Rest “too easy”) | Top-K vs Rest (mirrors Regime I5) | **Top-K vs Rest primary**; sleeve-average diagnostic |
| Cost in H1/H2 | Cost-net fwd labels | Raw gate; cost in H4 | **Raw gated**; H4 diagnostic |
| Absolute floors | Hard safety (IC ≥ 0.01, TB+1 ≥ 15%) | CI LB > 0 only until baselines | **CI LB > 0 gates**; Gemini floors provisional |
| Bootstrap unit | Regime-episode blocks | Session blocks | **Session primary**; episode diagnostic |
| Implement #1 | Path gen → H5 | Preconditions → H1 | **Preconditions → H1 → H3 → H2 → H5** |
| Dynamic K | `K_eff` when N thin | Fixed K + sweep | Fixed gated K; `K_eff` diagnostic if N < 15 |
| Short F&O-only | Hard rule | Not emphasized | **H7 → promote after coverage measure** |
| Trainer CV as gate | (implicit OK) | Reject | **Reject — external A/B only** |

---

## NSE / India pitfalls (eval harness)

1. **Auction bleed** — exclude 09:30 from gated metrics.  
2. **MIS cutoffs** — Long ~14:15 / Short ~14:00 / live flat ~15:00 — no unrealizable windows.  
3. **Upper-circuit short traps** — cash short stuck in UC is catastrophic (auction / penalty risk). Flag circuit-hit forward windows; exclude from eligible or treat as max-adverse on Short diagnostic slices.  
4. **F&O eligibility for Short** — non-F&O Nifty 100 names often lack clean MIS short depth; report coverage, stage toward Short hard filter.  
5. **Expiry days** — Thursday pinning; report expiry vs non-expiry; do not let gamma pollute pooled gates.  
6. **ADV drift / PIT** — daily ADV update; never today's membership list over history.  
7. **Squeeze / SLB** — diagnostic / ideal only (no clean v1 short-interest lineage).  
8. **Fold C** — COVID / circuit-halt quarantine — informational only.

---

## Implementation sequence

1. Path + mask generator: PIT Nifty 100, cascade sleeves, MIS/auction masks, `fwd_excess` identical to training target, frozen StockTB labels.  
2. Preconditions: H10 leakage/null + universe-parity.  
3. Primaries: **H1 → H3 → H2 → H5** on Folds A and B (Long/Short split, session-block bootstrap).  
4. Diagnostics: H4, H6–H9, K-sweep, episode-block, expiry/circuit/F&O slices.  
5. Promote absolute IC / TB+1 floors only after A+B baselines exist.

**Harness (shipped):** `src/horizon/eval/` (`common.py`, `metrics.py`) + CLI  
`python -m src.experiments.eval_horizon --train-period 2015-2017 --test-period 2018-2018 --direction both`  
(`--n-boot` default 500; Long/Short gated separately; trainer CV IC is diagnostic only).

---

## Out of scope

- Redesigning Horizon features / hyperparameters ([horizon-tier2-verdict.md](horizon-tier2-verdict.md))  
- Regime index evals / Precision fire evals (separate tier harnesses)  
- Mean-reversion under `CHOP` as a gated path  
- Using this harness to claim cascade net ≥ 0  

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-tier2-verdict.md](horizon-tier2-verdict.md) | Locked features / hyperparams this eval judges |
| [regime-tier1-eval-verdict.md](regime-tier1-eval-verdict.md) | Sibling harness pattern (I5 → H5) |
| [triple-barrier-verdict.md](triple-barrier-verdict.md) | Frozen TB geometry for H5 |
| [cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md) | Why escalate (rank inversion; low `tb_tp_rate`) |
| [precision-tier3-verdict.md](precision-tier3-verdict.md) | Downstream consumer — do not confound |
| [regime-tier1-stop-memo.md](archive/regime-tier1-stop-memo.md) | Regime CLOSED; Horizon is active escalation |
