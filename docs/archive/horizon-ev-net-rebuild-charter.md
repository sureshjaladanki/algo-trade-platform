# Horizon EV-Net Rebuild — Fresh Tier-2 Design (Nifty-100 MIS v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** **Fresh** Horizon tier redesign under a single hard friction lock — cascade names only when **calibrated cost-netted path EV** clears **+20 bps round-trip**; free choice of barriers, sleeve, model family, and stack depth  
**Status:** **STOP-MEMO — CLOSED** @ **0/3** (Step 0 hard-stop) — see [stop-memo](horizon-ev-net-rebuild-stop-memo.md)  
**Authority (prior evidence, not freeze inheritance):** Admission v1 STOP ([stop-memo](horizon-tier2-admission-stop-memo.md)); path-quality veto STOP ([stop-memo](horizon-path-quality-veto-stop-memo.md)); cost STOP ([stop-memo](rt-cost-realism-re-derivation-stop-memo.md)); path-density / MFE / TP-floor / Short ledgers CLOSED as **motivation cites**  
**Judge (this charter):** [Claude Sonnet](a5bb766a-cbaa-4552-82e7-5f92d036f8b8) — **single judge** (owner lock; not dual-judge)  
**Date:** 2026-08-16  
**Depends on:** [cascade-strategy-overview.md](../cascade-strategy-overview.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md), [horizon-path-quality-veto-stop-memo.md](horizon-path-quality-veto-stop-memo.md), [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md), [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md)  
**Hard constraint:** `ROUND_TRIP_COST = 0.0020` (20 bps) — **only** owner-locked number entering this ledger  
**Does not inherit as sacred:** production `H=6` · floors 60/50/30 · Top-K=5 · Rank→Admit · conviction P80 · `P(SL)` veto · classifier-first · Precision-as-H4-bailout  
**Does not reopen by default:** Regime remount · Short remount without independent E0 clear · cost ladder shopping below 20 · waived sequential peeks · geometry redraw after 0/3 hard-stop  
**Stop-memo:** [horizon-ev-net-rebuild-stop-memo.md](horizon-ev-net-rebuild-stop-memo.md)

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | Prior Horizon clears Top−Rest (Long H5) but **fails economics** (H4 @20 ≈ −12…−19 bps) and **fails residual admit** (conviction null; `P(SL)` veto A1 FAIL). Shared LightGBM + same features cannot separate winners inside Top-K. Fresh ledger = **economic product**, not another quantile on the weak head |
| Product definition | Horizon emits an **admitted registry** only when \(\widehat{EV}_{net} > 0\) after 20 bps; **empty book is valid** |
| Architecture | **Lean:** hygiene → hard eligibility → **one** calibrated \(EV_{net}\) scorer → **absolute** admit (+ optional capacity). No mandatory Rank→Admit→Veto stack |
| Geometry | **Free** under Step 0 freeze — TP / SL / \(H\) / asymmetry chosen so selected book can clear 20 bps; not inherited floors |
| Sleeve | **Long-first**; Short only if it independently clears E0 under its own frozen geometry |
| Model freedom | Any family allowed; default bias = tabular GBM on cost-netted EV. Second head only with **orthogonal features** + proven E0 lift |
| Peek budget | **Max 3** Fold A+B after Step 0 geometry freeze; one variable per peek; sequential **without mid-ledger goalpost moves** |
| Precision | **Held** until this ledger stop-memo locks the admitted set (or confirms production Top-K unchanged) |
| Build posture | **CLOSED** — Step 0 hard-stop @ 0/3; no Peek 1 |

**One-line:** Rebuild Horizon so the only cascade contract is calibrated net path EV after 20 bps — barriers and models are free; relative Top−Rest lift without positive net EV is not a ship.

**Economic identity (hard):**

\[
EV_{net} = P(TP)\,TP + P(SL)\,(-SL) + P(TO)\,M_{TO} - 20\,\mathrm{bps}
\]

Cascade iff \(\widehat{EV}_{net} > 0\) (plus coverage kill-switch). “TP denser than SL+TO” is necessary folklore; **net after cost** is the product.

---

## Single-judge scores (charter design) — 2026-08-16

| Axis | Claude Sonnet | Lock |
|---|---|---|
| Diagnosis fidelity (why prior Horizon failed) | 9/10 | **ACCEPT** |
| Economic product / E0 primacy | 9/10 | **ACCEPT** |
| Architecture leanness (anti Rank→Admit stack) | 8/10 | **REVISE→LOCK** — capacity / second-head criteria closed |
| Geometry freedom + Step 0 freeze discipline | 8/10 | **REVISE→LOCK** — numeric hard-stop + no redraw |
| Gate design (E0/E1/E2/E3) | 8/10 | **REVISE→LOCK** — E2 formula + P2 interval |
| Peek budget / sequential / hard-stop | 6/10 | **REVISE→LOCK** — kill judge-amended advance hatch |
| Reject / remount hardness | 9/10 | **ACCEPT** |
| Cascade contract vs Precision | 9/10 | **ACCEPT** |
| Overall | **ACCEPT WITH REVISIONS** | **CLOSED** @ 0/3 hard-stop |

**Judge one-liner:** Diagnosis and absolute-EV / lean architecture are correct; peek-advance escape hatch, non-numeric Step 0 hard-stop, and undefined capacity / orthogonal criteria were soft-gate cracks — now closed.

**Explicit YES/NO locks (Claude):**

| # | Question | Lock |
|---|---|---|
| 1 | Absolute \(\widehat{EV}_{net}>0\) primary admit | **YES** |
| 2 | E0 admitted-book net PnL CI LB > 0 primary ship | **YES** |
| 3 | Geometry free but Step 0 freeze (≤3 candidates) | **YES** |
| 4 | Rank→Admit→Veto remains NON-mandatory | **YES** |
| 5 | Precision held until this stop-memo | **YES** |
| 6 | Max 3 peeks | **YES** (with escape hatch removed) |
| 7 | Step 0 hard-stop needs numeric cut | **YES — locked below** |
| 8 | Long-first; Short only on independent E0 | **YES** |

---

## Revisions applied (MUST_FIX)

1. **Peek advance = E0 only.** Removed “judge-amended learning criterion.” Peek \(n+1\) only if Peek \(n\) clears **E0 dual-fold** and E2 does not kill. Any alternate advance rule requires a **fresh charter**, not a mid-ledger amend after seeing results.  
2. **Numeric Step 0 hard-stop.** STOP @ 0/3 if, for **all** ≤3 geometry candidates, dual-fold CI **upper bound** of unconditional-eligible \(EV_{net}\) **≤ −10 bps** (half of working \(c\)).  
3. **Hard-stop terminates the ledger.** No redraw of new geometry candidates; no expanding beyond 3. Reopen only via a **new** charter with a new causal hypothesis.  
4. **Orthogonal second head.** Max pairwise \|corr\| of candidate feature set vs primary scorer feature set on train **< 0.70**, **or** a named distinct data family (e.g. microstructure toxicity vs path-level momentum) pre-registered at Step 0. Fail → head ineligible.  
5. **Capacity K never substitutes for admit.** Remains diagnostic/report-only this ledger unless a **fresh charter** promotes it. Promotion (if ever) cannot override or replace absolute \(\widehat{EV}_{net}>0\).  
6. **E2 formula locked before peeks.** At Step 0b freeze: `min_bars = max(MIN_BARS_LONG, floor(0.50 × projected_adm_bars))`, `min_sessions = max(MIN_SESSIONS, floor(0.50 × projected_adm_sess))`; dual-fold lock = **min across A/B**. Absolute integers published at freeze — **not** retuned after Peek 1+.

**NICE applied (non-blocking, hardened):**

- P2 uncertainty: session-block CI for \(\widehat{EV}_{net}\) that **contains 0** → no-fire that bar (same block scheme as E0).  
- E0 CI method: session-block bootstrap; block = trading session; scheme frozen at Step 0b (no post-hoc method shopping).  
- Short “independent E0”: same statistical bar as Long; own frozen geometry; no shared peek budget with Long.

---

## Motivation cites (evidence, not inherited freezes)

| Ledger | Terminal fact | Implication for this rebuild |
|---|---|---|
| Cost STOP | `c*=20` signed; Long H5 PASS; H4 **−17 / −14**; Top-K TB+1 **10.9% / 8.9%** | Friction lock stands; economics not cleared by cost alone |
| Path-density / MFE / TP-floor | Travel / exit / TP50 levers CLOSED; H4 still neg | Geometry+selection must be redesigned as one economic product |
| Admission v1 | P80-of-eligible rejects **0%** Top-K (score-rank tautology); A1 thin FAIL | Relative conviction on path-EV is null |
| Path-quality veto | `P(SL)` AUC ~0.60–0.65; reject-mass ~10–15%; A1 FAIL (Fold B rejects **better**) | Same-feature multiclass cannot admit winners inside Top-K |
| Short ledgers | Short H5 / SEP / architecture classes CLOSED | Short stays out until independent E0 |

**Diagnosis lock:** Prior miss is **weak within-book winner/loser separation + wrong ship contract** (lift / density without \(EV_{net}>0\)). Not “need another LightGBM quantile.”

---

## Tier responsibility lock (hard)

| Tier | Owns | Does **not** own |
|---|---|---|
| **1 Regime** | Sleeve open/close (frozen soft overlay OK) | Stock pick; rewriting \(EV_{net}\) gate |
| **2 Horizon (this charter)** | Barriers + eligibility + calibrated \(EV_{net}\) + absolute admit registry | Dumping underwater books onto Precision; silent cost cut |
| **3 Precision** | 1m timing on **locked admitted** registry | Salvaging Horizon E0 FAIL as headline success |

**Anti-goal:** “Precision bridges Horizon H4 while Horizon still emits negative-\(EV_{net}\) names” → **FAIL charter intent**.

---

## Architecture lock — lean EV-net Horizon

```
Universe hygiene (ADV / MIS / auction / spread masks)
        │
        ▼
Hard eligibility (session / liquidity / optional regime)
        │
        ▼
Single scorer:  EV̂_net  (calibrated on purged val)
        │
        ▼
Absolute admit: EV̂_net > 0
        │  optional capacity K / notional after gate (diagnostic)
        ▼
Admitted registry (0..N)  →  Precision (later)
```

| Stage | Policy | Train | Inference |
|---|---|---|---|
| Hygiene | Rules | — | Precondition |
| Eligibility | Rules (pre-registered) | — | Mask |
| Scorer | Cost-netted path EV (continuous primary) | Full eligible density; purged/OOF calibration | \(\widehat{EV}_{net}\) |
| Admit | **Absolute** \(\widehat{EV}_{net} > 0\) | Never train scorer on admit survivors only | Empty allowed |
| Capacity | Top-K / notional **after** EV gate | — | **Diagnostic only** this ledger — never substitutes for E0 |

**Hard rules:**

1. Never train the scorer only on admit survivors (selection leakage).  
2. Never classifier-first with absolute `P(TP)>0.6` as the ship gate.  
3. Never relative P80-of-same-score or `P(SL)` quantile as the **default** admit.  
4. Second model head only if orthogonal lock (§ Revisions #4) clears **and** peek shows E0 lift.  
5. Naive 15m close remains Horizon entry for E0 — Precision fills do not redefine Horizon E0.

---

## Geometry freedom + Step 0 freeze

**Owner freedom:** TP, SL, \(H\), asymmetry, Long vs Short — free under this ledger.

**Process lock (anti-grid):**

| Phase | What happens |
|---|---|
| Step 0a | Publish travel / timeout / unconditional \(EV_{net}\) under **≤3** pre-registered geometry candidates |
| Step 0b | **Freeze one** geometry before any gated peek; publish E2 floors + E0 CI method (no A+B retune) |
| Peeks | Model / eligibility / uncertainty-gate only — **not** silent TP/SL/\(H\) shopping |

**Step 0 hard-stop (numeric):**

| Rule | Cut |
|---|---|
| Feasibility | For **every** candidate: dual-fold CI **UB** of unconditional-eligible \(EV_{net}\) **≤ −10 bps** → candidate infeasible |
| Ledger stop | **All** candidates infeasible → **STOP @ 0/3** before Peek 1 |
| No redraw | Hard-stop **terminates** this ledger — no new candidate set; reopen only via fresh charter |

**Candidate design bias (non-binding until Step 0 freeze):**

| Lever | Bias | Why |
|---|---|---|
| Sleeve | Long-first | Short independent E0 historically failed |
| TP vs SL | Mild asymmetry (TP ≥ SL) or tighter SL | Symmetric wide barriers + ~9–11% Top-K hit rate structurally struggle at 20 bps |
| \(H\) | Match achievable upper-quartile travel | Barriers outside path physics mint TO/SL junk |
| Unconditional eligible \(EV_{net}\) | Near 0 or slightly negative | Horizon’s job is to push **selected** book clearly positive |

**Cite (do not re-litigate as freeze):** median ~28–50 bps 60m moves; Top-K MFE often ~53–55 bps under prior \(H=6\) — geometry must respect reachability under \(c=20\).

---

## Model policy

| Item | Lock |
|---|---|
| Primary target | Cost-netted path return / utility under frozen geometry + \(c=20\) |
| Default family | Tabular GBM (LightGBM/XGBoost/CatBoost) — allowed, not required |
| Calibration | Mandatory isotonic (or equal) on purged val for \(\widehat{EV}_{net}\) |
| Uncertainty (P2) | Session-block CI containing 0 → no-fire that bar |
| Forbidden default | Same-feature regressor + multiclass veto stack as the product |
| Optional hazard / second head | Only if orthogonal lock clears **and** improves calibrated \(EV_{net}\) / E0 vs single regressor |

---

## Process locks

| Lock | Rule |
|---|---|
| Step 0 | Mandatory geometry probe + freeze + E0/E2 baselines; **no Peek 1** without published freeze |
| Peek budget | **Max 3** Long Fold A+B; one variable per peek |
| Sequential | Peek \(n+1\) **only if** Peek \(n\) clears **E0 dual-fold** and E2 does not kill — **no** mid-ledger “learning criterion” waive |
| Coverage kill-switch | E2 floors from Step 0b formula; fail → **NO-SHIP** that peek |
| Hard-stop @ 0/3 | All candidates fail numeric feasibility (CI UB ≤ −10 bps) → **STOP**; ledger closed; no redraw |
| Stop | Exhaust 3 **or** clean dual-fold E0 hold → stop-memo |
| Multiplicity | **New ledger** — cannot borrow Admission / veto remaining peeks |

---

## Gates

| ID | Metric | Role | Rule |
|---|---|---|---|
| **E0** | Admitted-book mean \(PnL_{net}\) (naive entry, \(c=20\)) | **PRIMARY ship** | Dual-fold session-block **CI LB > 0** (scheme frozen at Step 0b) |
| **E1** | Economic decomposition (TP mass vs SL/TO drag) | **PRIMARY companion** | Report; fail only if pre-registered contribution floors missed |
| **E2** | Coverage | **KILL-SWITCH** | Step 0b floors: `max(harness_min, floor(0.50 × projected))` bars/sessions; dual-fold min |
| **E3** | Cost stress @ archive 30 | **Report-only** | Soft health — never require E3≥0 to ship under working 20 |
| Top−Rest / H5-style | Selected vs rest TB or EV | **Companion** | Useful diagnosis; **not** sufficient ship |
| Abs TB=+1 % | Point estimate | **Report-only** | No soft 15/20/25% floors |
| H10 | Null / leakage | **PRECONDITION** | PASS |

**Rejected as primary ship gates:** absolute TB=+1 floors, H4≥0 alone without E0 identity, `P(TP)>0.6`, relative quantile admit A1.

---

## Pre-registered Long peek ladder (after geometry freeze)

| Order | Lever | Single variable | Authorized when |
|---|---|---|---|
| **P1** | Absolute \(EV_{net}>0\) admit on calibrated scorer | Gate on/off vs always-fire / always-Top-K baseline | Always first after Step 0 |
| **P2** | Uncertainty / no-fire when session-block CI contains 0 | One uncertainty knob | Only if P1 clears E0 dual-fold |
| **P3** | Orthogonal second head **or** eligibility tighten | One variable | Only if P2 clears E0 dual-fold (or P1 cleared and P2 skipped by pre-registered skip) |
| Capacity K after gate | — | — | **Diagnostic only** this ledger |
| Relative `P(SL)` / conviction P80 | — | — | **Forbidden default** (falsified prior ledgers) |
| Cost / Regime / Short remount | — | — | Out of ladder |

---

## Authorized vs diagnostic vs forbidden

### Authorized

- Fresh geometry freeze via Step 0 (≤3 candidates → lock one)  
- Calibrated \(EV_{net}\) scorer + absolute admit  
- Long-only peeks under E0/E1/E2  
- Optional uncertainty no-fire (P2)  
- Optional orthogonal second head (P3) under corr / family lock  

### Diagnostic / report-only

- Top−Rest / classic H1–H5 companions  
- Hazard \(P(TP)/P(SL)/P(TO)\) histograms / ECE  
- Capacity K sweeps after EV gate  
- Archive \(c=30\) stress (E3)  

### Forbidden

- Shipping on Top−Rest lift with E0 FAIL  
- Relative same-score P80 / `P(SL)` quantile as default admit  
- Classifier-first / `P(TP)>0.6` hard ship gate  
- Train scorer on admit survivors only  
- Silent TP/SL/\(H\) retune after Step 0 freeze  
- Geometry redraw after 0/3 hard-stop  
- Mid-ledger peek-advance waives / “learning criterion”  
- Cost shopping below 20  
- Precision fills inside Horizon E0  
- Capacity K as substitute for absolute EV admit  
- Remounting CLOSED Short / path-room / L1 / E1/E2 / TP50 as “free peeks” without new causal hypothesis + fresh charter  
- Claiming cascade-ready / Horizon-path PASS from density alone  

---

## Judge-flagged failure modes (carry-forward)

1. Goalpost-moving peek advance — **closed** (MUST_FIX #1).  
2. Capacity-K as backdoor Rank→Admit — **closed** (MUST_FIX #5; diagnostic only).  
3. Non-numeric hard-stop / E2 negotiated post-hoc — **closed** (MUST_FIX #2, #6).

---

## Sequencing vs Precision Execution Bridge

| Doc | Status after this lock |
|---|---|
| **This charter** | **CLOSED** — Step 0 hard-stop @ 0/3 |
| [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md) | **Held** — registry unchanged (production Top-K=5); dual-judge may re-anchor Step 0 |

**Rationale:** Do not spend Precision peeks on a moving Horizon registry.

---

## Build sequence

1. Claude Sonnet single-judge — **DONE** ([Claude](a5bb766a-cbaa-4552-82e7-5f92d036f8b8)); MUST_FIX applied.  
2. Status was **OPEN** → Step 0 authorized.  
3. Step 0a — ≤3 geometry candidates on Fold A+B — **DONE** (`logs/horizon_ev_net_step0_ab.txt`).  
4. Step 0 hard-stop — **FIRED** (all candidates dual-fold CI UB ≤ −10 bps) → **STOP @ 0/3**.  
5. Step 0b freeze / Peek 1–3 — **not reached**.  
6. Stop-memo — [horizon-ev-net-rebuild-stop-memo.md](horizon-ev-net-rebuild-stop-memo.md); production Top-K unchanged; Precision bridge remains held for Top-K=5 re-anchor.

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-ev-net-rebuild-stop-memo.md](horizon-ev-net-rebuild-stop-memo.md) | This ledger close @ 0/3 |
| [horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md) | Why conviction admit failed |
| [horizon-path-quality-veto-stop-memo.md](horizon-path-quality-veto-stop-memo.md) | Why `P(SL)` veto failed |
| [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | Why `c*=20` stands and H4 still neg |
| [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md) | Held; re-anchor to production Top-K=5 |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Cascade contract |
