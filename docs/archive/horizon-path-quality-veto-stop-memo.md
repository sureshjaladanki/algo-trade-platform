# Horizon Path-Quality Veto — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Step 0 veto diagnostics + Long Peek 1 `P(SL)` worst-20% eligible cut under locked `c*=20` / `H=6` / floors  
**Status:** **STOP-MEMO — path-quality veto charter CLOSED**; peeks **1/2 spent**; remaining peek **frozen** (A1 dual-fold FAIL — not paused)  
**Date:** 2026-08-15  
**Charter:** [horizon-path-quality-veto-charter.md](horizon-path-quality-veto-charter.md)  
**Depends on:** [horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md), [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md)  
**Trigger:** Peek 1 A1 admitted−rejected Top-K TB+1 CI LB ≤ 0 both folds (B point estimate **negative**)  
**A+B peeks spent:** **1 / 2** — remaining peek **frozen unused**

---

## One-line

`P(SL)` relative veto **does** narrow Top-K (reject-mass ~10–15%) and holds H5/H1–H3, but **does not** raise admitted vs rejected-from-Top-K StockTB+1 — **stop at 1/2**; do not merge the overlay.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| Orthogonal `P(SL)` veto can reject Top-K mass (unlike conviction P80) | **Supported** — 15.1% / 9.5% reject-mass; 477 / 283 rows |
| Null-lever / min-power gates catch tautology before Peek 1 | **Supported** — both cleared; Peek 1 was falsifiable |
| Veto raises admitted vs rejected-Top-K TB+1 (A1) | **Disproven** — A FAIL CI; B point **−4.3 pp** (rejected better) |
| H5 / H1–H3 hold under veto book | **Supported** — dual-fold PASS (H2/H3 A even flipped PASS vs Step 0 baseline) |
| Merge `P(SL)` veto into production | **No** |
| Horizon-path PASS / cascade-ready | **Forbidden / unproven** |

---

## Terminal evidence

### Step 0

**Log:** `logs/horizon_path_quality_veto_step0_ab.txt`

| Diagnostic | Fold A | Fold B |
|---|---|---|
| H5 | PASS · 10.9% | PASS · 8.9% |
| Reject-mass @P80 | 15.1% | 9.5% |
| Min-power rows | 477 | 283 |
| A2 suggestion | 316/48 | 296/46 |

**Locks:** `P(SL) >` elig P80; A2 **296/46**; K OUT.

### Peek 1 — `P(SL)` veto

**Log:** `logs/horizon_path_quality_veto_peek1_ab.txt`  
**CLI:** `python -m src.experiments.eval_horizon_path_quality_veto_peek1 --quantile 0.80 --a2-min-bars 296 --a2-min-sessions 46`

| Gate | Peek 1 A | Peek 1 B | Dual-fold |
|---|---|---|---|
| **H5** | PASS · p_top 11.0% | PASS · p_top 8.5% | **HOLD** |
| H1 / H2 / H3 | PASS / PASS / PASS | PASS / PASS / PASS | Hold (no regression) |
| **A1** | 0.013 [−0.032, 0.060] **FAIL** | −0.043 [−0.095, 0.017] **FAIL** | **FAIL** |
| A2 | PASS | PASS | Clear |
| Abs adm TB+1 | 10.6% | 8.5% | ≈ baseline; B slightly down |
| H4 @20 | −16 bps | −15 bps | Still neg |
| Reject mass | 15.1% | 9.5% | Non-null |

**Read:** Veto removes names, but the names it removes are **not** reliably worse on StockTB+1 than the names it keeps — Fold B rejects are *better* on TB+1 than admits. Orthogonal score ≠ useful admission contrast.

---

## Locked carry-forward

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / floors / H | Unchanged |
| Production Long K | **5** |
| `P(SL)` worst-20% eligible veto | **Do not merge** |
| Conviction P80-of-eligible | Still rejected (Admission v1) |
| Peeks | **1/2 spent; 1 frozen** — no resume on this ledger |
| Short / Regime | Disabled / CLOSED |
| Soft abs TB+1 / H4≥0 ship floors | Still **not** primary |

---

## Reject (next 30 days)

- Spending Peek 2 (`P(TO)` / within-Top-K veto tighten) by waiving A1 sequential  
- Grid {10,30}% or absolute `P(TP)>0.6` on A+B  
- Training 2a on veto survivors / classifier-first  
- Remounting falsified conviction or rejected Horizon levers  
- Claiming admission raised path density  
- Treating remaining peek as “paused”

---

## Next workstream

| Direction | Rationale |
|---|---|
| Re-anchor [precision-execution-bridge-charter.md](../next/precision-execution-bridge-charter.md) | Top-K=5 **unchanged** (veto no-merge) — Precision book stable |
| Do **not** chase another Horizon admission overlay without a **new** causal hypothesis | Two ledgers (conviction + `P(SL)` veto) failed to clear A1 |
| Short / cost / Regime | Stay closed |

**Owner note:** Rank→Admit architecture still correct; both *score-floor* and *path-type relative veto* failed as first admission levers under current multiclass skill (AUC ~0.60–0.65). Next Horizon selectivity needs a stronger path-quality signal or a different admit definition — not another quantile tweak on this head.
