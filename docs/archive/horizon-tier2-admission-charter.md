# Horizon Tier-2 Admission Layer — Long-Only Selectivity Redesign (Nifty-100 MIS v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Split Tier 2 into **Rank (2a)** + **Admit (2b)** and falsify whether **inference-only admission** (conviction floor → path-quality veto; K only if Step 0 re-implicates) raises **naive-entry** Long path density under locked `c*=20` / `H=6` / floors — without remounting rejected Horizon levers, Short, Regime, or Precision WS2  
**Status:** **STOP-MEMO — CLOSED** (peeks **1/2**; remaining frozen on A1 sequential fail) — see [horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md)  
**Authority (prior):** WS0/WS1 escalate Horizon ([cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md)); cost STOP (`c*=20`, Long H5 PASS / Short H5 FAIL, H4 still neg); path-density STOP (Long SEP PASS; L1 no-merge; K 5→3 **not** implicated); Short architecture STOP (sleeve **disabled**); Regime A0 CLOSED  
**Judges (this charter):** [Claude Sonnet](b0d3653b-e13a-4ac3-a063-6977413114ab), [Gemini Flash](c9fb9c9f-49db-4a10-8496-ab4939d22cf7)  
**Date:** 2026-08-15  
**Depends on:** [cascade-strategy-overview.md](../cascade-strategy-overview.md), [horizon-tier2-verdict.md](../horizon-tier2-verdict.md), [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md), [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md), [horizon-short-architecture-stop-memo.md](horizon-short-architecture-stop-memo.md), [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md), [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md)  
**Does not reopen:** Cost ladder · Regime · Short architecture / B1 · path-room / L1 / E1 / E2 / Long TP50 · primary `H=6` · floors / vol multiples · Precision fills inside Horizon H5 · classifier-first / parallel AND at `P(TP)>0.6` · train ranker on classifier survivors · K grid sweep  
**Stop-memo:** [horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md)

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | Cascade fails as **admission policy**: Long Top-K TB+1 ~9–13%, H4 ~−12…−17 bps @20; WS1 over-fires ~88–93% non-+1 with `prec_tp ≥ tb_tp` → Precision is not the leak; escalate Horizon selectivity |
| Diagnosis | Ranker has relative skill (Long H5 PASS) but admits thin absolute path density; need Rank → Admit, not another direction model |
| Architecture | **Tier 2a** keep Long LightGBM Huber path-EV ranker; **Tier 2b** inference-only admission overlay |
| Sleeve posture | **Long-only**; Short stays **disabled / flat** — reopen only via [horizon-short-reopen-charter.md](../next/horizon-short-reopen-charter.md) (DRAFT; F&O list alone ≠ unlock) |
| Peek budget | **Max 2** Long Fold A+B admission peeks after mandatory Step 0; single-variable; sequential — **1/2 spent; 1 frozen** |
| Friction / floors / H | **Frozen** — `c*=20` / archive 30; floors 60/50/30; `H=6`; multiples unchanged |
| Build posture | **CLOSED** — stop-memo; Top-K=5 unchanged |

**One-line:** Keep the path-EV ranker; P80-of-eligible conviction floor is a null narrow on Top-K — stop without merging admission or spending veto under sequential A1 fail.

---

## Dual-judge scores (charter design)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | 9/10 | 7/10 | **ACCEPT** — Horizon selectivity leak (WS1); Claude flags rank-inversion risk if K-swept blind |
| Rank→Admit architecture | 9/10 | 7/10 | **ACCEPT** — 2a/2b split OK; un-bundle 2b into ordered ladder |
| Admission levers | 7/10 | 4/10 | **REVISE→LOCK** — kill K grid; one lever per peek |
| Gate design | 8/10 | 4/10 | **Claude wins** — no soft ship floors on abs TB+1 / H4≥0; CI-LB contrast + report-only companions |
| Freeze / reject hardness | 9/10 | 5/10 | **REVISE→LOCK** — import full rejected-lever registry by reference |
| Peek budget realism | 6/10 | 2/10 | **REVISE→LOCK** — max 2; Step 0; sequential no-regression |
| Cascade contract fit | 9/10 | 8/10 | **ACCEPT** |
| NSE practicality | 8/10 | 6/10 | **ACCEPT WITH coverage kill-switch** |
| Overall | **ACCEPT WITH REVISIONS** | **ACCEPT WITH REVISIONS** | **ACCEPT WITH REVISIONS** |

**Judge one-liners**

- Gemini: Decouple Rank→Admit; cap at 2 single-variable peeks; pause Precision bridge until admitted registry locks.  
- Claude: Right escalation per WS1, but lose the K-grid, vetoed absolute gates, and missing peek budget before claiming discipline.

---

## Authority from prior STOPs (do not reopen)

| Ledger | Fact | Implication |
|---|---|---|
| WS0/WS1 | `tb_tp` ~7–12% in fires; over-fire non-+1 ~88–93%; `prec_tp ≥ tb_tp`; ranks 1–2 often worse than 3–5 | Escalate **Horizon admission**, not Precision WS2 |
| Cost STOP | `c*=20`; Long H5 PASS; Short H5 FAIL; H4 −13…−17; Top-K TB+1 ~9–13% | Friction OK; economics fail on path admission |
| Path-density STOP | Long MFE/EXIT SEP PASS; L1 holds H5 but H2-B regresses; L2 K5→3 **not** implicated (Fold A ranks 1–2 *worse* MFE than 3–K) | Density is real; feature L1 closed; **do not default to K shrink** |
| Short architecture STOP | Listwise A2 FAIL; two-head complementarity fail; sleeve disabled | Short out of scope |
| Regime A0 | Architecture CLOSED | Soft overlay only |
| MFE / TP-floor STOPs | E1/E2 / TP50 no-merge; H4 still neg | Geometry / 15m exit-policy closed as primary |

**Baseline cite (do not re-estimate as a ship gate):** cost peek-1 Long Top-K TB+1 **10.9% / 8.9%** (A/B); H4 @20 **−17 / −14** bps; path-density L1 companions **−12 / −19**.

---

## Tier responsibility lock (hard)

| Tier | Owns | Does **not** own |
|---|---|---|
| **1 Regime** | Sleeve open/close (Long momentum when `TREND_UP` + daily ok) | Stock pick / admission / fill timing |
| **2a Horizon Rank** | Cross-sectional path-EV order under naive 15m close (H1–H5) | Hard TB+1 minting; rewriting barriers |
| **2b Horizon Admit (this charter)** | Inference-only narrow of 2a candidates (conviction / veto; contingent K) | Training ranker on survivors; `P(TP)>0.6` hard gate; Short remount |
| **3 Precision** | 1m timing on **locked admitted** registry | Re-ranking; salvaging a thin Top-K book as headline |

**Authorized hypothesis:** Admission can raise **absolute** naive-entry TB+1 density on Long while **holding** ranker H5/H1/H2/H3 — enough to justify a later Precision re-measure on the new registry.

**Forbidden claims even on PASS:**

- Horizon-path PASS / cascade-ready / book PnL from admission alone  
- “Precision recovered Horizon” / feeding Precision fills into H5  
- Activating Short from Long admission PASS  
- Soft-promoting inventable hit-rate targets (25–35%, 0.6) without measured coverage

---

## Carry-forward locks

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors | Long TP **60** / Short TP **50** / SL **30** |
| Vol multiples | Unchanged |
| Primary H | **H=6 / 90m** |
| Ranker | Locked Long v2 defaults (path-room off; chase demote; aux=0; `episode_balanced=True`) |
| Production K (until this ledger moves it) | Long **5** (parity with Precision); change only via authorized peek if Step 0 re-implicates |
| Horizon H5 entry | **Naive 15m decision-bar close** — never Precision fill |
| Regime | CLOSED |
| Short sleeve | **Disabled / flat** |
| Classifier hard cut `P(TP)>0.6` | **Forbidden** as admission threshold |

---

## Architecture lock — Rank (2a) → Admit (2b)

```
Regime soft overlay (frozen)
        │
        ▼
2a  Long path-EV LightGBM Huber  →  cross-sectional scores (full eligible density)
        │
        ▼
2b  Admission (inference only)
        │  Step 0 diagnostics → Peek ladder below
        ▼
   Admitted registry (0..K* names)  →  Precision (later charter / frozen rules)
```

| Stage | Model / policy | Train | Inference |
|---|---|---|---|
| **2a Rank** | LightGBM Huber path-EV (current) | Full cascade-eligible Long bars | Score all eligible; order descending |
| **2b Admit** | Conviction quantile ± multiclass TP/SL/TO veto | Full density (same eligible set); purged/OOF calibration | Narrow only — never redefine 2a training slice |
| Hygiene | ADV / MIS / auction-bleed masks | — | Precondition, not a peek |

**Hard rule:** never train 2a on 2b survivors. Never classifier-first. Never parallel AND with absolute `P(TP)>0.6`.

---

## Process locks

| Lock | Rule |
|---|---|
| Step 0 (no peek) | Mandatory diagnostics below; **no admission decision** without published tables |
| Peek budget | **Max 2** Long-only Fold A+B; one lever per peek; no grid |
| Sequential | Peek 2 only if Peek 1 clears primary gates **and** does not regress H1/H2/H3 vs Step-0 / cost Long baseline |
| Coverage kill-switch | If admitted book fails min-N / min-sessions (A2) → **NO-SHIP** that peek; do not stack another filter |
| Multiplicity | New ledger — cannot borrow path-density remaining peek or Precision-bridge peeks |
| Stop | Exhaust 2 **or** clean dual-fold hold with no regression → stop-memo |

---

## Step 0 — Admission diagnostics (no peek)

**Required before Peek 1.** Long only, Folds A and B. Ranker frozen at production defaults. Entry = naive 15m close; frozen TB geometry.

| Diagnostic | What to publish |
|---|---|
| Rank-tier refresh | MFE / exit-mix / TB+1 for ranks 1–2 vs 3–K on **current** Top-K=5 registry (confirm or refute path-density inversion) |
| Score distribution | Per-bar eligible score quantiles; fraction of Top-K below candidate floors P70/P80/P90 (**report only** — do not tune on A+B) |
| Veto-head val separation | OOF multiclass `P(SL)`, `P(TO)`, `P(TP)` Top-K vs Rest; reliability / ECE on purged val |
| Exit mix | Top-K TP / SL / timeout shares vs Rest |
| Coverage | Bars / sessions with ≥1 Top-K name under sleeve open |

**Stop-before-peek rule:** If ranker H5 dual-fold no longer holds on the frozen baseline reprint → **STOP at 0/2** (do not build admission on a broken ranker).

**K-authorization rule (mirrors path-density L2):** K shrink is **peek-eligible only if** Step 0 shows sharp post-rank decay favoring narrower K (not Fold-A-style 1–2 worse than 3–K). Otherwise K stays **out of peek ladder**.

### Pre-register quantile before Peek 1

After Step 0 score table exists, lock **one** conviction floor (default candidate **P80 of eligible scores that bar**) **before** Peek 1. Do not grid P70/P80/P90 on gated folds.

### Step 0 results — **DONE** 2026-08-15

**Harness:** `python -m src.experiments.analyze_horizon_admission --folds A,B`  
**Log:** `logs/horizon_admission_step0_ab.txt`  
**Regime runs:** Fold A `e9dbc994…` · Fold B `7fff95a9…`

| Gate / diagnostic | Fold A | Fold B | Read |
|---|---|---|---|
| **H5** (hard-gate reprint) | **PASS** 0.040 [0.021, 0.055] · p_top 10.9% | **PASS** 0.026 [0.011, 0.041] · p_top 8.9% | **HOLD** — do not STOP at 0/2 |
| H1 / H2 / H3 | PASS / FAIL / FAIL | PASS / PASS / PASS | Baseline companions (cost-era shape) |
| H4 @20 | −17 bps | −14 bps | Report-only; matches cost Long cite |
| Rank tier MFE 1–2 vs 3–K | **−0.084** (3–K higher) | +0.035 | **K not implicated** (Fold A inversion persists) |
| Top-K frac below P70/P80/P90 | **0 / 0 / 0** | **0 / 0 / 0** | Eligible-score floor is **score-rank tautology** on Top-K |
| Veto P(SL) top−rest | −0.035 (top 0.28 / rest 0.31) | −0.021 (0.35 / 0.37) | Mild SL separation; ECE ~0.01–0.02 |
| Veto P(TP) top−rest | +0.006 | +0.019 | Weak TP lift on Top-K |
| Coverage Top-K bars/sess | 633 / 96 | 593 / 93 | Dense sleeve open |
| MFE / EXIT SEP | PASS / PASS | PASS / PASS | Density signal reconfirmed |

**Hard-gate verdict:** Long H5 **dual-fold HOLD** → admission peeks authorized.

**Locks from Step 0 (before Peek 1):**

| Item | Lock |
|---|---|
| Conviction quantile | **P80** (charter default; P70/P90 not grid-tuned — all three reject 0% of Top-K) |
| A2 min bars / sessions | **296 / 46** (dual-fold min of Step 0 suggestions) |
| K shrink | **OUT of peek ladder** (no sharp post-rank-3 decay; Fold A still inverted) |
| Peek 1 lever | Conviction floor P80 only |

**Step 0 caution (not a stop):** P80-of-eligible cannot reject any Top-K name when Top-K is defined by the same score and \(n_{\mathrm{elig}}\gg K\). Peek 1 may be a **null narrow** — still spent as the pre-registered first lever; do not silently swap to veto.

**Not claimed:** Horizon-path PASS · admission ship · cascade-ready.

### Peek 1 results (conviction P80) — **DONE** 2026-08-15

**Log:** `logs/horizon_admission_peek1_p80_ab.txt`  
**CLI:** `python -m src.experiments.eval_horizon_admission_peek1 --quantile 0.80 --a2-min-bars 296 --a2-min-sessions 46`

| Gate | Fold A | Fold B | Dual-fold |
|---|---|---|---|
| **H5** | PASS · p_top 10.9% | PASS · p_top 8.9% | **HOLD** (identical to Step 0) |
| H1 | PASS | PASS | Hold |
| H2 / H3 | FAIL / FAIL | PASS / PASS | Same baseline companions |
| **A1** | **FAIL thin** (n=0 reject) | **FAIL thin** | **FAIL** — null narrow |
| A2 | PASS (633/96) | PASS (593/93) | Clear |
| H4 @20 | −17 bps | −14 bps | Unchanged |

**Peek 1 verdict:** **NO-SHIP / null** — admitted book = Top-K=5; A1 cannot contrast. Sequential rule **freezes Peek 2** (path-quality veto not spent).

**Stop:** See [horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md). Peeks **1/2**; remaining frozen.

---

## Pre-registered Long admission ladder

| Order | Lever | Single variable | Authorized when |
|---|---|---|---|
| **A1 Peek** | Conviction floor | One session XS quantile cut on 2a scores | Always first spend after Step 0 (cheapest selectivity; WS1 over-fire framing) |
| **A2 Peek** | Path-quality veto | Multiclass LightGBM; drop high relative `P(SL)` and/or high `P(dead-TO)` via **session quantile** (e.g. worst 20% within eligible bar) — not absolute `P(TP)>0.6` | Only if Peek 1 clears primary + coverage; no H1/H2/H3 regression |
| **K (contingent)** | Single K value (e.g. 5→3) | One K | **Only if** Step 0 re-implicates K; replaces A2 slot or requires fresh dual-judge amend — **no {1,2,3,5} sweep** |
| EV blend | `P(TP)·pay − P(SL)·loss` | — | **Diagnostic / report-only** this charter |
| Liquidity / MIS hygiene | ADV / cutoffs | — | **Precondition**, not a peek |

**Default spend order:** Step 0 → **conviction floor** → **path-quality veto**. K is not the default second peek.

---

## Gates

| ID | Metric | Role | Rule |
|---|---|---|---|
| **H5** | Top−Rest StockTB+1 (naive entry) | **PRIMARY** | Dual-fold CI LB > 0 — must **HOLD** vs cost Long baseline |
| **H1 / H2 / H3** | IC / Top−Rest excess / rank mono | **PRIMARY companions** | No regression vs Step-0 / cost Long read (session-block CI discipline) |
| **A1** | Admitted vs rejected-from-Top-K (or vs unconditional eligible) StockTB+1 contrast | **PRIMARY admission** | Dual-fold session-block **CI LB > 0** on the contrast — **not** a bare absolute % ship floor |
| **A2** | Coverage | **KILL-SWITCH** | Pre-register min bars / min sessions per fold before Peek 1; fail → NO-SHIP that arm |
| **H4 @20** | Cost-netted admitted excess | **Report-only** | Publish; may require “not further negative vs Step-0 companion” as soft health check — **never** H4≥0 as PASS/FAIL ship gate this charter |
| Abs admitted TB+1 | Point estimate | **Report-only** | Cite vs ~9–13% Top-K baseline; do **not** soft-promote 15%/20%/25–35%/0.6 as ship floors |
| H10 | Null / leakage | **PRECONDITION** | PASS |

**Rejected as primary ship gates this charter (Claude veto; path-density precedent):** absolute TB+1 ≥15%/20%/25%, H4 ≥0, `P(TP)>0.6`.

**Capability language (not pre-committed numbers):** intermediate usefulness = dual-fold A1 PASS + H5/H1/H2 hold + A2 clear; economic stretch discussed only after H4 companions improve; 0.6 realized precision is **aspirational research**, not a gate.

---

## Authorized vs diagnostic vs forbidden

### Authorized (peek ladder)

- Inference-only conviction quantile floor (Peek 1)  
- Inference-only multiclass path-quality veto via relative session quantiles (Peek 2 contingent)  
- Single-value K change **only if** Step 0 re-implicates  

### Diagnostic / report-only

- EV blend scoring  
- Rank 1–2 vs 3–K travel refresh  
- Admitted vs unadmitted H4@20 tracking  
- Raw multiclass `P(TP)` histograms / calibration plots  

### Forbidden

- Softening TB floors / changing H / cost shopping  
- Classifier-first or parallel AND with hard `P(TP)>0.6`  
- Training 2a on 2b survivors  
- K grid `{1,2,3,5}` or multi-knob conviction×veto×K sweeps on A+B  
- Short remount / Regime reopen / Precision WS2 headline  
- Remounting rejected registry: path-room, aux-excess, chase demote, L1 `tod_mfe_frac_60`, E1/E2, Long TP50, Short A1/A2/A3, listwise `rank_xendcg`  
- Precision fills inside Horizon H5  
- Claiming cascade-ready from this ledger alone  

---

## Sequencing vs Precision Execution Bridge

| Doc | Status after this lock |
|---|---|
| **This charter** | **CLOSED** — stop-memo; Top-K=5 unchanged |
| [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md) | Remains **DRAFT**; may re-anchor Step 0 to **locked Top-K=5** (admission did not change the registry) |

**Rationale (both judges):** Precision bridge assumes a frozen Top-K=5 book. This ledger left that book unchanged (null admission). After stop-memo, Precision Step 0 may proceed on Top-K=5 without waiting for a new admitted set — unless a fresh admission charter later moves K or overlays a non-null filter.

---

## Build sequence

1. **Step 0** — Rank-tier + score quantile + veto-head val separation + coverage (Long A+B). **DONE**  
2. **Hard gate** — if baseline H5 broken → STOP-MEMO at 0/2. **H5 HOLD**  
3. **Lock** one conviction quantile from Step 0 tables (no A+B grid). **P80 + A2 296/46**  
4. **Peek 1** — conviction floor only; evaluate H5/H1/H2/H3 + A1 + A2; publish H4 / abs TB+1. **DONE — A1 null FAIL**  
5. **Peek 2** — only if sequential + coverage pass → path-quality veto (or Step-0-authorized single K). **FROZEN**  
6. **Stop-memo** — [horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md).

---

## Related docs

| Doc | Role |
|---|---|
| [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md) | Held DRAFT — Tier 3 falsification after admitted registry locks |
| [horizon-short-reopen-charter.md](../next/horizon-short-reopen-charter.md) | DRAFT — Short stays flat; causal-hypothesis reopen gate (not F&O-alone) |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Cascade map |
| [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md) | H1–H5 harness |
| [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md) | Density SEP + L1/K implications |
| [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md) | Escalate Horizon / Precision ≠ leak |
| [horizon-short-architecture-stop-memo.md](horizon-short-architecture-stop-memo.md) | Short disabled |
| [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | `c*=20` + H4 baseline |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | Frozen geometry |
