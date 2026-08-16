# Horizon Path-Quality Veto — Long Admission v2 (Nifty-100 MIS v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Falsify whether an **inference-only multiclass path-quality veto** (relative `P(SL)` / contingent `P(TO)`) can raise **naive-entry** Long StockTB+1 density on the locked Top-K=5 book under `c*=20` / `H=6` / floors — without remounting rejected Horizon levers, Short, Regime, conviction P80-of-eligible, or Precision WS2  
**Status:** **STOP-MEMO — CLOSED** (peeks **1/2**; A1 dual-fold FAIL) — see [horizon-path-quality-veto-stop-memo.md](horizon-path-quality-veto-stop-memo.md)  
**Authority (prior):** Admission v1 STOP ([horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md)) — P80-of-eligible conviction = **null narrow**; path-quality veto **never spent**; Rank→Admit architecture still right; WS0/WS1 escalate Horizon selectivity  
**Judges (this charter):** [Claude Sonnet](c77385bf-2d69-41e4-a009-0f504c91ac31), [Gemini Flash](b3ef79c4-72b0-4916-b584-6294f5744f43)  
**Date:** 2026-08-15  
**Depends on:** [horizon-tier2-admission-charter.md](horizon-tier2-admission-charter.md), [horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md), [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md), [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md), [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md)  
**Does not reopen:** Cost ladder · Regime · Short · path-room / L1 / E1 / E2 / Long TP50 · primary `H=6` · floors / multiples · Precision fills in Horizon H5 · classifier-first / `P(TP)>0.6` hard gate · train 2a on 2b survivors · K grid · **P80-of-eligible conviction** (falsified null) · Admission v1 frozen peek · **K shrink** (locked out — Admission v1 Fold-A inversion; not re-litigated here)

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | Admission v1 proved Rank→Admit is right but **eligible-score conviction is tautological with Top-K**; veto head showed mild Top−Rest `P(SL)` separation and was never spent |
| Diagnosis | Path-EV ranks names; path **type** (SL / timeout junk) is a different axis — veto on `P(SL)` can reject Top-K members that conviction-on-same-score cannot |
| Architecture | Keep **2a** Long Huber path-EV; **2b** = multiclass LightGBM veto overlay at inference only |
| First spend | **Path-quality veto** (not conviction, not K) |
| Sleeve | **Long-only**; Short stays disabled |
| Peek budget | **Max 2** Long Fold A+B; one lever per peek; sequential — **1/2 spent; 1 frozen** |
| Friction / floors / H | **Frozen** — `c*=20` / archive 30; floors 60/50/30; `H=6` |
| Build posture | **CLOSED** — stop-memo; Top-K=5 unchanged |

**One-line:** `P(SL)` veto narrows Top-K but fails A1 dual-fold — stop without merging; remaining peek frozen.

---

## Dual-judge scores (charter design)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity (vs Admission v1 miss) | 9/10 | 8/10 | **ACCEPT** — orthogonal `P(SL)` axis; weak prior signal → mandatory reject-mass probe |
| Veto-first ladder | 9/10 | 9/10 | **ACCEPT** |
| Quantile scope (eligible vs within-Top-K) | 8/10 | 8/10 | **ACCEPT WITH REVISIONS** — eligible P80 + tie rule locked |
| Gate design | 9/10 | 9/10 | **ACCEPT** — A1 CI-LB; no abs / H4≥0 ship floors |
| Peek budget / sequential | 9/10 | 8/10 | **REVISE→LOCK** — numeric null-lever + min-power bars |
| Freeze / reject hardness | 9/10 | 9/10 | **ACCEPT** |
| Cascade contract fit | 10/10 | 8/10 | **ACCEPT** |
| NSE practicality / coverage | 9/10 | 7/10 | **REVISE→LOCK** — A2 from veto projection only (no soft inherit) |
| Overall | **ACCEPT WITH REVISIONS** | **ACCEPT WITH REVISIONS** | **ACCEPT WITH REVISIONS** |

**Judge one-liners**

- Gemini: Separates path-EV rank from path-type `P(SL)` veto; exemplary single-variable sequential protocol with 0/2 null stop.  
- Claude: Right fix for the v1 tautology; tighten soft thresholds (null %, A2 inherit, min reject-mass power, dangling K rule) before OPEN.

**Explicit judge locks (both YES):** (a) `P(SL)` worst-20% eligible → `Top-K ∩ not-vetoed` as Peek 1 · (b) null-lever STOP at 0/2 · (c) hold Precision bridge until this ledger stops.

---

## Authority from prior STOPs (do not reopen)

| Ledger | Fact | Implication |
|---|---|---|
| **Admission v1 STOP** | P80 eligible floor rejects **0%** Top-K; A1 thin FAIL; Peek 2 frozen | New ledger; veto as **first** spend; do not waive Admission sequential |
| Admission Step 0 (cite) | Veto `P(SL)` top−rest **−0.035 / −0.021**; ECE ~0.01–0.02; Fold A rank inversion | Veto falsifiable; **K locked OUT** (no re-litigate) |
| WS0/WS1 | Over-fire non-+1 ~88–93%; Precision ≠ leak | Path-type selectivity still the Horizon job |
| Cost / path-density | Long H5 PASS; H4 neg; L1/K closed | Friction + density locks stand |
| Short / Regime | Disabled / CLOSED | Out of scope |

**Baseline cite (do not re-estimate as ship gate):** cost / Admission Long Top-K TB+1 **10.9% / 8.9%**; H4 @20 **−17 / −14** bps; Admission Step 0 H5 **PASS / PASS**.

---

## Tier responsibility lock (hard)

| Tier | Owns | Does **not** own |
|---|---|---|
| **1 Regime** | Sleeve open/close | Stock pick / admission |
| **2a Horizon Rank** | Path-EV order (frozen v2 Long defaults) | Hard TB minting; training on veto survivors |
| **2b Horizon Admit (this charter)** | Inference-only path-quality narrow of Top-K | Absolute `P(TP)>0.6`; conviction P80-of-eligible; Short remount; K shrink |
| **3 Precision** | 1m timing on **locked admitted** registry | Salvaging thin book as headline |

**Authorized hypothesis:** Relative `P(SL)` veto can raise **absolute** naive TB+1 on the admitted Long book while **holding** H5/H1/H2/H3 vs Admission / cost Long baseline.

**Forbidden claims even on PASS:** Horizon-path PASS / cascade-ready / “Precision recovered Horizon” / Short activate / soft abs hit-rate ship floors.

---

## Carry-forward locks

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors / H / multiples | Unchanged |
| Ranker | Locked Long v2 (path-room off; chase demote; aux=0; `episode_balanced=True`) |
| Production K | Long **5** — **K shrink OUT** this ledger (Admission v1 Fold-A inversion stands) |
| Horizon H5 entry | **Naive 15m close** — never Precision fill |
| Conviction P80-of-eligible | **Rejected** — do not re-peek |
| Short / Regime | Disabled / CLOSED |
| `P(TP)>0.6` hard cut | **Forbidden** |

---

## Architecture lock — Rank (2a) → Veto-Admit (2b)

```
Regime soft overlay (frozen)
        │
        ▼
2a  Long path-EV LightGBM Huber  →  Top-K=5 by eval_score
        │
        ▼
2b  Multiclass veto (inference only)
        │  drop high relative P(SL) [Peek 1]
        │  optional P(TO) or within-Top-K P(SL) tighten [Peek 2 contingent]
        ▼
   Admitted registry (0..K names)  →  Precision (later)
```

| Stage | Model / policy | Train | Inference |
|---|---|---|---|
| **2a Rank** | Path-EV Huber (current) | Full cascade-eligible Long | Score + Top-K=5 |
| **2b Veto** | Multiclass LGBM on TB class SL/TO/TP | Full density; purged/OOF calibration | Narrow Top-K only |
| Hygiene | ADV / MIS / auction masks | — | Precondition, not a peek |

**Hard rule:** never train 2a on 2b survivors. Never classifier-first. Never parallel AND with absolute `P(TP)>0.6`.

**Why veto ≠ conviction tautology:** veto score is **`P(SL)`** (path type), not path-EV. A Top-K name can sit in the worst eligible `P(SL)` quantile even when it ranks #1–5 on path-EV.

### Veto quantile mechanics (locked)

| Item | Lock |
|---|---|
| Floor definition | Per bar, among eligible names: `p80 = quantile(P(SL), 0.80)` |
| Veto set | `P(SL) > p80` (**strict** — ties at exactly `p80` are **retained**, not vetoed) |
| Admit set | `eval_rank ≤ K` **and** not in veto set |
| Sparse bars | If `n_eligible < 5`, skip veto that bar (admit full Top-K); report skip rate |

---

## Process locks

| Lock | Rule |
|---|---|
| Step 0 (no peek) | Mandatory; **no Peek 1** without published veto tables + H5 reprint |
| Peek budget | **Max 2** Long-only Fold A+B; one lever per peek; no grid |
| Sequential | Peek 2 only if Peek 1 clears primary gates **and** no H1/H2/H3 regression vs Step 0 / cost Long |
| Coverage kill-switch | Admitted book fails pre-registered min-N / min-sessions → **NO-SHIP** that peek; do not stack filters |
| Multiplicity | **New ledger** — cannot borrow Admission v1 remaining peek |
| Stop | Exhaust 2 **or** clean dual-fold hold with no regression → stop-memo |

---

## Step 0 — Veto diagnostics (no peek)

**Required before Peek 1.** Long only, Folds A and B. Ranker frozen. Entry = naive 15m close.

| Diagnostic | What to publish |
|---|---|
| H5 / H1 / H2 / H3 / H4 reprint | Confirm ranker still holds (hard-gate) |
| Veto-head val separation | OOF multiclass `P(SL)`, `P(TO)`, `P(TP)` Top-K vs Rest; **ECE + ROC-AUC for `P(SL)`** on purged val |
| Reject-mass probe (report-only at 10/20/30%) | Fraction of Top-K bar-instances with `P(SL) >` eligible P70/P80/P90 that bar — lock spend at **20%** only |
| Exit mix | Top-K TP/SL/TO vs Rest |
| Coverage | Bars / sessions with ≥1 Top-K; **projected admitted bars** under locked worst-20% `P(SL)` cut |
| Rank-tier MFE (report-only) | 1–2 vs 3–K companion reprint — **does not re-authorize K** |

### Hard stop / null / power rules (pre-registered)

| Rule | Numeric lock |
|---|---|
| **H5 hard-gate** | Dual-fold H5 CI LB ≤ 0 → **STOP at 0/2** |
| **Null-lever stop** | Mean Top-K reject-mass at worst-20% (`P(SL) >` eligible P80) **< 2.0%** on **both** folds → **STOP at 0/2** (do not burn Peek 1) |
| **Min-power bar (Peek 1 authorize)** | Per fold, rejected-from-Top-K **row count ≥ 100** under locked cut — else underpowered A1 → **STOP at 0/2** (or dual-judge amend before spend) |
| **K** | **OUT** — Admission v1 Fold-A inversion stands; rank-tier reprint is companion only |

**Why 20% (not 10/30):** same discipline as Admission P80 — publish 10/20/30 in Step 0; **lock 20% before Peek 1**; do not retune on A+B after seeing gated metrics.

### Pre-register before Peek 1

| Item | Lock |
|---|---|
| Veto head | **`P(SL)`** |
| Quantile | **Worst 20%** eligible (`P(SL) >` bar P80); strict inequality |
| Admit set | `Top-K ∩ not vetoed` |
| A2 coverage floors | **Always** from Step 0 projected admitted bars/sessions under the locked cut: `min_bars = max(MIN_BARS_LONG, floor(0.50 × projected_adm_bars))`, `min_sessions = max(MIN_SESSIONS, floor(0.50 × projected_adm_sess))` — dual-fold lock = **min across A/B**. **Never** soft-inherit Admission 296/46 |

Do **not** grid {10,20,30}% × {SL, TO, TP} on A+B.

### Step 0 results — **DONE** 2026-08-15

**Harness:** `python -m src.experiments.analyze_horizon_path_quality_veto --folds A,B`  
**Log:** `logs/horizon_path_quality_veto_step0_ab.txt`

| Gate / diagnostic | Fold A | Fold B | Read |
|---|---|---|---|
| **H5** | **PASS** · p_top 10.9% | **PASS** · p_top 8.9% | **HOLD** |
| Null-lever reject-mass @P80 | **15.1%** (477/3165) | **9.5%** (283/2965) | **Non-null** (≫ 2%) |
| Min-power reject rows | **477** | **283** | **PASS** (≥100) |
| Reject-mass P70/P80/P90 | 23.6 / 15.1 / 8.3% | 17.8 / 9.5 / 3.2% | Lock spend at **20%** |
| P(SL) AUC holdout / val | 0.63 / 0.64 | 0.60 / 0.65 | Weak–moderate calibration skill |
| Veto P(SL) top−rest (val) | −0.035 | −0.021 | Mild separation |
| K-implicated | No | No | K stays **OUT** |
| Projected admitted bars/sess | 633 / 96 | 592 / 93 | Dense |

**Hard-gate verdict:** H5 HOLD · null PASS · power PASS → **Peek 1 authorized**.

**Locks before Peek 1:**

| Item | Lock |
|---|---|
| Veto | `P(SL) >` eligible P80 (strict); admit = Top-K ∩ not vetoed |
| A2 min bars / sessions | **296 / 46** (dual-fold min of Step 0 suggestions) |
| K | **OUT** |

**Not claimed:** Admission ship · Horizon-path PASS · cascade-ready.

### Peek 1 results (`P(SL)` veto) — **DONE** 2026-08-15

**Log:** `logs/horizon_path_quality_veto_peek1_ab.txt`  
**CLI:** `python -m src.experiments.eval_horizon_path_quality_veto_peek1 --quantile 0.80 --a2-min-bars 296 --a2-min-sessions 46`

| Gate | Fold A | Fold B | Dual-fold |
|---|---|---|---|
| **H5** | PASS · p_top 11.0% | PASS · p_top 8.5% | **HOLD** |
| H1 / H2 / H3 | PASS / PASS / PASS | PASS / PASS / PASS | Hold |
| **A1** | 0.013 [−0.032, 0.060] **FAIL** | −0.043 [−0.095, 0.017] **FAIL** | **FAIL** |
| A2 | PASS | PASS | Clear |
| Abs adm TB+1 | 10.6% | 8.5% | ≈ / slightly below baseline |
| H4 @20 | −16 bps | −15 bps | Still neg |

**Peek 1 verdict:** **NO-SHIP** — non-null narrow but A1 does not clear; Fold B rejects beat admits on TB+1. Sequential **freezes Peek 2**.

**Stop:** [horizon-path-quality-veto-stop-memo.md](horizon-path-quality-veto-stop-memo.md). Peeks **1/2**.

---

## Pre-registered Long admission ladder

| Order | Lever | Single variable | Authorized when |
|---|---|---|---|
| **V1 Peek** | Path-quality veto | `P(SL)` worst 20% eligible (strict `>`) | Always first after Step 0 clears H5 + null + min-power |
| **V2 Peek** | Timeout veto **`P(TO)`** **or** within-Top-K **veto-score** tighten | One variable only | Only if V1 clears primary + coverage; no H1/H2/H3 regression |
| Within-Top-K **rank** cut | Drop bottom path-EV score inside Top-K | — | **Diagnostic / report-only** (not V2 default; needs dual-judge promote) |
| K shrink | — | — | **Forbidden** this ledger |
| Conviction P80-of-eligible | — | — | **Forbidden** (Admission v1 null) |
| EV blend / raw `P(TP)` | — | — | Report-only |

**Naming lock:** V2 “within-Top-K **veto-score** tighten” ≠ diagnostic “within-Top-K **rank** cut” (path-EV).

**Default spend:** Step 0 → **`P(SL)` veto** → contingent `P(TO)` or within-Top-K veto-score tighten.

---

## Gates

| ID | Metric | Role | Rule |
|---|---|---|---|
| **H5** | Admitted−Rest StockTB+1 (naive) | **PRIMARY** | Dual-fold CI LB > 0 — must **HOLD** vs cost / Admission Long |
| **H1 / H2 / H3** | IC / excess / mono | **PRIMARY companions** | No regression vs Step 0 / cost Long |
| **A1** | Admitted vs rejected-from-Top-K StockTB+1 | **PRIMARY admission** | Dual-fold session-block **CI LB > 0** |
| **A2** | Coverage | **KILL-SWITCH** | Pre-registered min bars / sessions from Step 0 veto projection; fail → NO-SHIP |
| **H4 @20** | Cost-netted | **Report-only** | Soft health vs Step 0 companion — never H4≥0 ship gate |
| Abs admitted TB+1 | Point estimate | **Report-only** | Cite vs ~9–13%; no soft 15/20/25% floors |
| H10 | Null / leakage | **PRECONDITION** | PASS |

**Rejected as primary ship gates:** absolute TB+1 ≥15%/20%/25%, H4 ≥0, `P(TP)>0.6`.

---

## Authorized vs diagnostic vs forbidden

### Authorized

- Inference-only multiclass `P(SL)` relative quantile veto (Peek 1)  
- Contingent Peek 2: `P(TO)` veto **or** within-Top-K **veto-score** tighten  

### Diagnostic / report-only

- Within-Top-K **rank** (path-EV) cut  
- EV blend; raw `P(TP)` histograms / ECE / ROC-AUC  
- Reject-mass at 10/30% (publish Step 0 only — do not retune peeks)  
- Rank-tier MFE 1–2 vs 3–K reprint  

### Forbidden

- P80-of-eligible conviction remount  
- K shrink / K grid  
- Softening TB / changing H / cost shopping  
- Classifier-first or `P(TP)>0.6` hard gate  
- Train 2a on 2b survivors  
- Multi-knob SL×TO×K sweeps on A+B  
- Short / Regime / Precision WS2 headline  
- Rejected registry: path-room, L1 `tod_mfe_frac_60`, E1/E2, TP50, listwise, aux-excess, …  
- Precision fills inside Horizon H5  
- Waiving Admission v1 sequential to “finish” its frozen peek  

---

## Sequencing vs Precision Execution Bridge

| Doc | Status after this lock |
|---|---|
| **This charter** | **CLOSED** — stop-memo; Top-K=5 unchanged |
| [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md) | **Unblocked for dual-judge** — re-anchor Step 0 to production Top-K=5 |

**Rationale:** This charter may narrow Top-K=5. Do not spend Precision peeks on a moving book.

---

## Build sequence

1. Dual-judge — **DONE**.  
2. **Step 0** — **DONE** (H5/null/power clear).  
3. Hard gates — cleared.  
4. Lock A2 **296/46** — **DONE**.  
5. **Peek 1** — **DONE — A1 FAIL**.  
6. **Peek 2** — **FROZEN**.  
7. **Stop-memo** — [horizon-path-quality-veto-stop-memo.md](horizon-path-quality-veto-stop-memo.md).

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md) | Why conviction-first failed; veto deferred here |
| [horizon-tier2-admission-charter.md](horizon-tier2-admission-charter.md) | Closed Rank→Admit v1 ledger |
| [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md) | Held until admitted registry locks |
| [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md) | Escalate Horizon / Precision ≠ leak |
| [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md) | H1–H5 harness |
