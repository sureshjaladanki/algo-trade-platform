# Horizon Tier-2 Admission — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Step 0 admission diagnostics + Long Peek 1 conviction floor under locked `c*=20` / `H=6` / floors  
**Status:** **STOP-MEMO — admission charter CLOSED**; peeks **1/2 spent**; remaining peek **frozen** (sequential A1 fail — not paused)  
**Date:** 2026-08-15  
**Charter:** [horizon-tier2-admission-charter.md](horizon-tier2-admission-charter.md)  
**Depends on:** [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md)  
**Trigger:** Peek 1 P80 eligible-score floor rejects **0** Top-K rows both folds → A1 thin FAIL; sequential freezes Peek 2  
**A+B peeks spent:** **1 / 2** — remaining peek **frozen unused**

---

## One-line

Locked Long path-EV still clears H5, but an inference-only **P80-of-eligible conviction floor cannot narrow Top-K** (score-rank tautology) — **stop at 1/2**; do not spend path-quality veto under this sequential lock; Top-K=5 registry unchanged.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| Baseline Long H5 still holds under frozen v2 defaults | **Supported** — dual-fold PASS (Step 0 + Peek 1 reprint) |
| Rank 1–2 vs 3–K still inverted on Fold A (K shrink not implicated) | **Supported** — MFE 1–2 −0.084 vs 3–K; K stays out |
| Eligible-score P70/P80/P90 floors reject mass from Top-K | **Disproven** — 0% / 0% / 0% both folds |
| Peek 1 P80 raises admitted vs rejected-Top-K TB+1 (A1) | **Disproven / null** — no rejected-Top-K mass; A1 thin FAIL |
| Path-quality veto (A2) is spendable this ledger | **Blocked** — sequential requires Peek 1 primary clear |
| Merge admission overlay into production Top-K | **No** — book identical to unlocked Top-K=5 |
| Horizon-path PASS / cascade-ready from admission | **Forbidden / unproven** |

---

## Terminal evidence

### Step 0 (no peek)

**Log:** `logs/horizon_admission_step0_ab.txt`  
**Harness:** `python -m src.experiments.analyze_horizon_admission --folds A,B`

| Diagnostic | Fold A | Fold B |
|---|---|---|
| **H5** | PASS · p_top 10.9% | PASS · p_top 8.9% |
| H4 @20 | −17 bps | −14 bps |
| Rank MFE 1–2 vs 3–K | −0.084 | +0.035 |
| Top-K below P70/P80/P90 | 0 / 0 / 0 | 0 / 0 / 0 |
| Veto P(SL) top−rest | −0.035 | −0.021 |
| Veto ECE P(TP) | 0.013 | 0.022 |
| K-implicated | **No** | **No** |

**Locks before Peek 1:** conviction **P80**; A2 floors **296 bars / 46 sessions**; K **out**.

### Peek 1 — conviction floor P80

**Log:** `logs/horizon_admission_peek1_p80_ab.txt`  
**CLI:** `python -m src.experiments.eval_horizon_admission_peek1 --quantile 0.80 --a2-min-bars 296 --a2-min-sessions 46`

| Gate | Peek 1 A | Peek 1 B | vs Step 0 / cost Long |
|---|---|---|---|
| **H5** | PASS · p_top 10.9% | PASS · p_top 8.9% | Hold (identical book) |
| H1 | PASS | PASS | Hold |
| H2 | FAIL | PASS | Same as Step 0 baseline |
| H3 | FAIL | PASS | Same as Step 0 baseline |
| **A1** | **FAIL thin** | **FAIL thin** | No rejected-from-Top-K mass |
| A2 | PASS | PASS | Full Top-K coverage |
| H4 @20 | −17 bps | −14 bps | Unchanged |

**Read:** Peek 1 is a **null narrow** — admitted registry = production Top-K=5. A1 cannot form a contrast. Sequential rule freezes Peek 2 (path-quality veto).

---

## Locked carry-forward

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors / H / multiples | Unchanged |
| Production Long K | **5** (unchanged) |
| Conviction P80 overlay | **Do not merge** — null operator on Top-K |
| Path-quality veto | **Not spent** this ledger; reopen only via fresh charter |
| Peeks | **1/2 spent; 1 frozen** — no resume on this ledger |
| Short / Regime / Precision WS2 | Stay out / CLOSED / held per prior locks |
| Soft abs TB+1 / H4≥0 ship floors | Still **not** primary |

---

## Reject (next 30 days)

- Spending Peek 2 (veto / K) by waiving A1 sequential without dual-judge amend  
- Grid P70/P90 or absolute `P(TP)>0.6` on A+B  
- Training 2a on 2b survivors / classifier-first  
- Claiming admission raised path density  
- Remounting rejected Horizon levers (path-room, L1 travel, E1/E2, TP50, …)  
- Treating remaining peek as “paused”

---

## Next workstream (recommended)

| Direction | Rationale |
|---|---|
| **Fresh dual-judge charter** for path-quality veto as **first** lever | → [horizon-path-quality-veto-charter.md](horizon-path-quality-veto-charter.md) (**DRAFT**) |
| Re-anchor [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md) Step 0 | **Held again** while veto charter may change Top-K; after veto stop-memo, re-anchor to locked admitted set |
| Do **not** reopen cost / Regime / Short from this stop | Prior STOPs stand |

**Owner note:** Admission Rank→Admit split remains the right architecture; the **first authorized lever definition** (P80-of-eligible) was the miss — not the H5 baseline.
