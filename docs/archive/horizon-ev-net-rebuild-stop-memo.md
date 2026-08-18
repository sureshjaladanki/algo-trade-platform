# Horizon EV-Net Rebuild — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Fresh Horizon tier redesign under `c*=20` — Step 0a geometry feasibility (≤3 Long candidates) before any absolute-\(\widehat{EV}_{net}\) peek  
**Status:** **STOP-MEMO — EV-net rebuild charter CLOSED** @ **0/3** peeks (Step 0 hard-stop)  
**Date:** 2026-08-16  
**Charter:** [horizon-ev-net-rebuild-charter.md](horizon-ev-net-rebuild-charter.md)  
**Depends on:** [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-tier2-admission-stop-memo.md](horizon-tier2-admission-stop-memo.md), [horizon-path-quality-veto-stop-memo.md](horizon-path-quality-veto-stop-memo.md), [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md)  
**Trigger:** All ≤3 pre-registered Long geometries dual-fold CI **UB** of unconditional-eligible \(EV_{net}\) **≤ −10 bps**  
**A+B peeks spent:** **0 / 3** — Peek 1 **not authorized**; geometry redraw **forbidden** on this ledger

---

## One-line

Unconditional Long eligible path EV after 20 bps is **deeply negative** (~−20…−22 bps; CI UB ~−17…−19) under all three reachable-asymmetry geometries — **hard-stop @ 0/3**; no absolute-admit peek; no geometry redraw without a fresh charter.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| At least one of ≤3 free geometries has dual-fold CI UB of unconditional-eligible \(EV_{net}\) **> −10 bps** | **Disproven** — all three FAIL both folds |
| Travel / MFE is absent under reachable TP floors | **Disproven** — mean MFE ~43–54 bps (travel real; economics still fail) |
| Mild TP≥SL asymmetry + shorter H clears pool feasibility | **Disproven** — G1/G2/G3 all CI UB ≤ −17 bps |
| Absolute \(\widehat{EV}_{net}>0\) admit can be peeked under this candidate set | **Blocked** — Step 0 hard-stop terminates ledger |
| Geometry redraw / expand beyond 3 on this ledger | **Forbidden** (charter MUST_FIX #3) |
| Precision Execution Bridge may spend peeks on a moving book | **No** — registry unchanged; bridge stays held pending production Top-K re-anchor |

---

## Terminal evidence

### Step 0a (no peek)

**Log:** `logs/horizon_ev_net_step0_ab.txt`  
**Harness:** `python -m src.experiments.analyze_horizon_ev_net_step0 --folds A,B`

**Pre-registered Long candidates (frozen at design; not production floors):**

| ID | H | TP / SL floors | Vol mult |
|---|---|---|---|
| G1_reach_h6 | 6 | 40 / 25 bps | 2.0 / 1.0 |
| G2_early_h4 | 4 | 35 / 25 bps | 2.0 / 1.0 |
| G3_mid_h5 | 5 | 45 / 25 bps | 2.25 / 1.0 |

**Eligibility:** TB-eligible + MIS entry-ok for H + Regime soft overlay (`TREND_UP` ∩ tradeable daily).  
**Metric:** unconditional-eligible mean \(EV_{net} = path\_ret - 0.0020\) (absolute path; session-block bootstrap 95% CI; block = trading session; `n_boot=500`).

| Geometry | Fold | Mean EV_net (bps) | CI [lo, hi] (bps) | n | TP / SL / TO | Mean MFE (bps) | Feasible (UB > −10) |
|---|---|---|---|---|---|---|---|
| G1_reach_h6 | A | −22 | [−25, **−18**] | 48408 | 0.15 / 0.44 / 0.42 | 52.6 | **No** |
| G1_reach_h6 | B | −21 | [−24, **−17**] | 47636 | 0.14 / 0.42 / 0.44 | 54.0 | **No** |
| G2_early_h4 | A | −22 | [−24, **−19**] | 57828 | 0.10 / 0.35 / 0.55 | 43.1 | **No** |
| G2_early_h4 | B | −20 | [−23, **−18**] | 56026 | 0.09 / 0.34 / 0.57 | 44.5 | **No** |
| G3_mid_h5 | A | −22 | [−24, **−19**] | 52956 | 0.10 / 0.40 / 0.50 | 48.1 | **No** |
| G3_mid_h5 | B | −20 | [−24, **−18**] | 51679 | 0.09 / 0.39 / 0.52 | 49.6 | **No** |

**Hard-stop lock:** candidate infeasible iff **both** folds CI UB ≤ −10 bps; ledger STOP iff **all** candidates infeasible → **FIRED**.

**Oracle pos-mass (report-only):** ~27–30% of eligible bars have realized \(EV_{net}>0\) — selection room exists inside a still-negative pool; not enough to waive the numeric UB cut.

### Step 0b

**Not reached** — no geometry freeze; E2 floors unpublished; Peek 1 unauthorized.

---

## Diagnosis lock (carry-forward)

1. **Pool economics, not only within-book separation.** Prior ledgers showed Top−Rest lift with negative selected-book nets. This Step 0 shows the **unconditional eligible pool** under reachable Long geometries is itself ~−20 bps after `c*=20`, with CI UB stuck ≤ −17 bps.  
2. **Travel without TP mass.** MFE ~43–54 bps coexists with TP hit rates ~9–15% and SL ~34–44% — path travel does not convert into barrier wins at these widths.  
3. **No scorer bailout on this candidate set.** Absolute admit can concentrate the ~30% positive-mass tail, but the charter’s numeric feasibility gate forbids Peek 1 when every geometry’s dual-fold CI UB ≤ −10 bps.  
4. **Do not redraw barriers on this ledger.** Charter MUST_FIX #3 — reopen only via a **new** charter with a new causal hypothesis (e.g. different product definition, eligibility universe, or entry clock — not another ≤3 H/TP/SL grid).

---

## Merge / production posture

| Item | Lock |
|---|---|
| Production Horizon Top-K / floors / H=6 | **Unchanged** |
| Absolute \(EV_{net}\) admit scorer | **Not merged** (never peeked) |
| Geometry candidates G1–G3 | **Closed** this ledger |
| Peek budget remainder | **Frozen unused** (0/3 spent) |
| Precision Execution Bridge | **Held** — re-anchor Step 0 to production Top-K=5 (registry unchanged) |
| Cost `c*=20` | **Stands** |

---

## Explicit rejects (do not remount from this STOP)

- Geometry redraw / 4th candidate under this charter  
- Mid-ledger hard-stop waive because oracle pos-mass ~30%  
- Shipping on travel / Top−Rest without \(EV_{net}\) feasibility  
- Precision fills inside Horizon E0 / Precision-as-bailout  
- Cost shopping below 20  
- Remounting CLOSED Admission / `P(SL)` veto / TP50 / E1–E2 as “free peeks”

---

## Next workstream (outside this ledger)

Requires a **fresh charter** with a new causal hypothesis. This STOP does **not** authorize another barrier grid under the same EV-net Step 0 contract.

**Code / harness retained for audit:**  
`src/labels/ev_net_geometry.py`, `src/horizon/eval/ev_net_rebuild.py`, `src/experiments/analyze_horizon_ev_net_step0.py`
