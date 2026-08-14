# Horizon Path-Density Diagnostic & Selection — Nifty-100 MIS v1

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Measure and (conditionally) lift **path travel / TB=+1 density** of Horizon Top-K under signed `c*=20` — without cost shopping or exhausted-lever reopen  
**Status:** **STOP-MEMO** — peeks **1/2** · L3 amend **REJECTED** · remaining peek **closed** — see [stop-memo](horizon-path-density-stop-memo.md)  
**Authority:** Cost STOP dual-judge next-workstream lock ([Claude](9f8909d2-7a13-474b-b3cf-532e73c906e0), [Gemini](ee0ccc6e-8060-463f-8e06-d82a83e9e76a)); this charter dual-judge ([Claude](07cdfff1-b47e-4ba5-8576-aeddc58e02bc), [Gemini](d1d28423-a5b8-4611-b28b-16a06b4923c9)); stop/amend judges ([Claude](f9256c28-1e53-43be-acc3-cc3e9f6349e1), [Gemini](5515a43a-2941-42c3-9ad2-9d31d4ecca71))  
**Date:** 2026-08-13  
**Depends on:** [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [rt-cost-realism-re-derivation-charter.md](rt-cost-realism-re-derivation-charter.md), [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md)  
**Does not reopen:** Cost ladder · Regime · Precision WS2 · H / multiples · v2 rejected levers (path-room-on, Short aux, Short chase demote, L1/L2/S1)

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | Cost STOP: `c*=20` is realistic but economics still fail — Long H5 PASS with Top-K TB+1 ~9–13% and H4 −13…−17 bps → leak is **path travel density**, not friction |
| Diagnosis | Selector does not concentrate names that travel far enough to clear TP inside H=6 |
| Friction / floors | **Frozen** — `c*=20` / archive 30; floors 60/50/30; multiples `3/2.5/1.5` |
| Primary H | **H=6 / 90m** (frozen) |
| Sleeve posture | **Long-only lever peeks**; Short = Step 0 diagnostic only (deferred) |
| Peek budget | **Max 2** Long Fold A+B invocations; Step 0 **not** a peek |
| Build posture | **CLOSED** — stop-memo at 1/2; L1 off defaults; L3 amend rejected |

**One-line:** Measure whether Top-K paths actually travel farther than Rest under `c*=20`; only then spend ≤2 Long peeks on a single-variable density lever — do not shop cost or revive rejected features.

---

## Dual-judge scores (charter design)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | 9.5/10 | 8/10 | **ACCEPT** — path density is the right leak name; still unmeasured as MFE/exit physics |
| Scope / freeze | 9/10 | 9/10 | **ACCEPT** — freeze `c`/H/multiples/Regime/Precision/v2 rejects |
| Peek budget | 10 (want 3 both) | 9 (want 2 Long) | **REVISE→LOCK** — **max 2 Long-only**; Short deferred |
| Gate design | Promote TB+1≥20% / H4≥0 / ADV≤15% | H5 primary; abs TB+1 & H4 report-only | **Claude wins** — no soft ship-gate promotion |
| Reject hardness | 10/10 | 9/10 | **ACCEPT** |
| Overall | ACCEPT WITH REVISIONS | ACCEPT WITH REVISIONS | **ACCEPT WITH REVISIONS** |

**Judge one-liners**

- Gemini: realign selection to travel capacity / TB=+1 under locked `c*=20`; do not move goalposts.  
- Claude: “path density” is still a name — **Step 0 MFE/exit decomposition before any peek**; Short lever list is exhausted → defer Short.

---

## Cost charter outcome (authority — do not reopen)

From [stop-memo](rt-cost-realism-re-derivation-stop-memo.md):

| Fact | Implication |
|---|---|
| `c*=20` signed; statutory+broker ~5–6 bps | Friction identity OK |
| Peek 1: Long H5 dual PASS; Short H5 dual FAIL | Cost cut ≠ economics clear |
| H4 @20 ≈ −13…−17 bps | Still underwater |
| Top-K TB+1 ≈ 9–13% | Absolute path arrival still thin |
| ADVt lo share ≈ 30–36% | Single-`c` Top-K not all-liquid |
| REJECT 15/10/25 | Cost shopping closed |

---

## Carry-forward locks

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors | Long TP **60** / Short TP **50** / SL **30** |
| H=6; MIS cutoffs | Unchanged |
| Path-room | **Demoted** |
| Long `stock_r_15` | **Demoted**; `episode_balanced=True` |
| Short `stock_r_15` | **Keep** |
| Aux excess | **0** |
| K | Long **5** / Short **3** (change only if Step 0 implicates dilution — L2 below) |
| Regime / Precision WS2 | CLOSED / blocked |

---

## Process locks

| Lock | Rule |
|---|---|
| Step 0 (no peek) | Publish Top-K vs Rest **MFE** (as fraction of side TP floor) + **TB exit-type** decomposition (TP/SL/timeout) + rank-tier cut (1–2 vs 3–K); both sleeves, Folds A/B |
| Hard stop @ 0 peeks | If Top-K vs Rest MFE/exit distributions are **not meaningfully separated** → stop-memo with **0/2** spent (no differentiable density signal) |
| Peek budget | **Max 2** Long-only Fold A+B; Short lever peeks = **0** this charter |
| Single-variable | One lever per peek; no grid; no pooled Long+Short |
| Sequential | Peek 2 only if peek 1 clears Long H5 dual-fold **without** regressing H1/H2/H3 below current locked read |
| Multiplicity | New ledger — cannot borrow Horizon v2's 5 or cost charter's frozen 2 |
| Stop | Exhaust 2 **or** clean Long H5 hold with no regression → stop-memo |

---

## Gates

| Role | Metric | Rule |
|---|---|---|
| **Primary** | Long H5 (Top−Rest StockTB+1) | Dual-fold CI LB > 0 |
| **Anti-goal** | Breaking Long H5 to lift report-only abs TB+1 / H4 | **FAIL** — not a partial win |
| Report-only | Abs Top-K TB+1, H4 @20, H4arch @30, H1/H2/H3, ADVt lo share, Step-0 MFE/exit stats | Never soft-promote to ship without fresh dual-judge |

**Rejected as primary gates this charter (Gemini proposed; Claude veto):** TB+1 ≥20%, H4 ≥0, ADV lo ≤15% as hard ship floors.

---

## Step 0 — Path-travel diagnostic (no peek) — **DONE** 2026-08-13

**Required before peek 1.** Both sleeves, Fold A and B calendars (same as cost/Horizon v2).

| Diagnostic | What to publish |
|---|---|
| MFE @ H=6 | Top-K vs Rest distribution of max favorable excursion / TP floor (Long 60 bps, Short 50 bps) |
| Exit mix | Top-K vs Rest share of TP-first / SL-first / timeout |
| Rank tier | Same for ranks 1–2 vs 3–K (ties to soft-H3) |
| ADV cut (report) | MFE/TB=+1 by ADV tercile (no post-hoc tier `c`) |

**Stop-before-peek rule:** If Top-K does not travel meaningfully farther than Rest (MFE separation null / exit mix indistinguishable) → density lever is noise-chasing → **STOP at 0/2**.

### Step 0 results

**Harness:** `python -m src.experiments.analyze_horizon_path_density --folds A,B`  
**Log:** `logs/horizon_path_density_step0_ab.txt`  
**Regime runs:** Fold A `e9dbc994…` · Fold B `7fff95a9…`  
**Separation gate:** session-block CI LB > 0 on Top−Rest mean MFE/TP-floor **or** Top−Rest TP-share.

| Sleeve · Fold | MFE Top−Rest (CI) | Abs MFE top/rest | EXIT TP Top−Rest (CI) | Top TP/SL/TO | SEP |
|---|---|---|---|---|---|
| **Long A** | **+0.159 [0.085, 0.232] PASS** | 0.92 / 0.76 | **+0.040 [0.023, 0.056] PASS** | 0.11 / 0.40 / 0.49 | **PASS** |
| **Long B** | **+0.094 [0.021, 0.161] PASS** | 0.89 / 0.80 | **+0.026 [0.011, 0.044] PASS** | 0.09 / 0.38 / 0.53 | **PASS** |
| Short A | +0.014 [−0.050, 0.080] FAIL | 1.01 / 1.00 | +0.002 [−0.017, 0.023] FAIL | 0.13 / 0.33 / 0.54 | **FAIL** |
| Short B | −0.014 [−0.067, 0.040] FAIL | 1.01 / 1.03 | +0.014 [−0.002, 0.031] FAIL | 0.13 / 0.33 / 0.54 | **FAIL** |

| Report-only | Long A | Long B | Short A | Short B |
|---|---|---|---|---|
| Rank tier MFE 1–2 vs 3–K | **−0.090** (3–K higher) | +0.037 | −0.036 | −0.026 |
| ADVt lo share (Top-K) | 36% | 30% | 33% | 33% |
| ADVt MFE lo/mid/hi | 0.76 / 0.92 / 1.04 | 0.86 / 0.96 / 0.86 | 0.98 / 0.98 / 1.10 | 1.05 / 0.90 / 1.06 |

**Hard-stop verdict:** **Long SEPARATED both folds** → density lever is falsifiable → **do not STOP at 0/2**. Short **no travel separation** either fold → Short levers stay deferred (already locked).

**Lever implication (pre-registered ladder):**

| Lever | Step 0 match? | Read |
|---|---|---|
| **L1** travel-adequacy feature | **Yes — first spend** | Top-K travels farther than Rest, but abs MFE still ~0.9× TP floor and timeout ~50% → residual travel capacity not fully selected |
| **L2** K 5→3 | **No** | Fold A rank-tier is inverted (1–2 *worse* MFE than 3–K); B only mild +0.04 — not a sharp post-rank-3 decay |
| **L3** min-travel screen | Hold | Only if L1 inconclusive |

**Not claimed:** Horizon-path PASS · economics clear · cascade-ready · abs TB+1 / H4 ship.

---

## Pre-registered Long lever ladder (contingent on Step 0)

Execute in order; spend ≤2 peeks total.

| Order | Lever | Single variable | Usable only if Step 0 shows |
|---|---|---|---|
| **L1** | Causal travel-adequacy feature (non-circular; path-room non-circularity lock applies — **not** demoted `tp_room_atr_*`) | One feature on/off vs locked Long config | Top-K MFE separated from Rest but not captured by current features |
| **L2** | Long K narrow **5→3** (one value, not sweep) | `K` | Travel/MFE density decays sharply after rank ~3 (soft-H3-aligned) |
| **L3** | One pre-registered min-travel eligibility screen (threshold fixed from Step 0 distribution, **not** tuned on A+B) | One threshold | L1/L2 inconclusive and Step 0 shows a clean percentile cut |

No L4 spend this charter. No Short levers (aux, chase demote, S1/S2, F&O timing packs) — deferred to a future charter if Step 0 shows Short shares Long’s travel shape **and** a novel non-rejected variable exists.

**Step 0 lock → Peek 1 candidate:** **L1** (L2 not implicated).

### L1 lock (Peek 1 — single variable)

| Item | Lock |
|---|---|
| Feature | `tod_mfe_frac_60` |
| Definition | Causal same-clock mean of prior-session Long `mfe_frac_long` (MFE / 60bps floor), lookback 60, `shift(1)` within `(symbol, time_only)` |
| Circularity | **Not** `tp_room_atr_*` — no rv→eligibility reconstruct; scale is locked floor via realized path MFE |
| Sleeve | **Long only** (append to `LONG_FEATURES`; Short unchanged) |
| CLI | `python -m src.experiments.eval_horizon --l1-travel-adequacy --direction long …` |
| Gate | Long H5 dual-fold CI LB > 0; no H1/H2/H3 regression vs cost peek-1 Long read |
| Report-only | Abs Top-K TB+1, H4@20, H4arch@30, ADVt, soft-H3 |

### Peek 1 results (L1 `tod_mfe_frac_60`) — 2026-08-13

**Logs:** `logs/horizon_path_density_l1_peek1_fold_a.txt` · `logs/horizon_path_density_l1_peek1_fold_b.txt`  
**Baseline:** cost peek-1 Long under `c*=20` ([stop-memo](rt-cost-realism-re-derivation-stop-memo.md)).

| Gate | L1 Long A | L1 Long B | vs cost peek-1 Long |
|---|---|---|---|
| **H5** | **0.051 [0.036, 0.068] PASS** (p_top=12.0%) | **0.027 [0.011, 0.045] PASS** (p_top=9.0%) | Dual-fold **hold** (A TB+1 10.9→12.0; B 8.9→9.0) |
| H1 | 0.078 [0.056, 0.099] PASS | 0.050 [0.032, 0.069] PASS | Hold |
| H2 | 0.0008 [0.0004, 0.0012] **PASS** | 0.0001 [−0.0004, 0.0005] **FAIL** | A FAIL→PASS; **B PASS→FAIL (regression)** |
| H3 | −0.0009 FAIL (m12&lt;m3k) | −0.0005 PASS | Soft-H3 unresolved on A |
| H4 @20 | −12 bps | −19 bps | A −17→−12; B −14→−19 |
| ADVt lo | 28% | 28% | ≈30–36% baseline |

**Sequential gate:** Peek 2 only if Peek 1 clears Long H5 dual-fold **without** regressing H1/H2/H3 vs locked cost read → **FAIL** (Long B H2 regresses). Peek budget **1/2**; remaining peek **frozen** unless dual-judge amends to allow L3 under H2-B regression.

**Read:** L1 keeps primary H5 and slightly lifts Fold A abs TB+1, but does **not** clear economics (H4 still negative) and **fails** the no-regression sequential rule. Do **not** merge `tod_mfe_frac_60` into default `LONG_FEATURES`. Do **not** claim path-density PASS.

**Default next:** stop-memo at **1/2** (L1 inconclusive / sequential block). L3 only via fresh dual-judge amend (not auto-spend).

### Dual-judge amend (Peek 2 / L3 waive) — **REJECTED** 2026-08-13

**Judges:** [Claude Sonnet](f9256c28-1e53-43be-acc3-cc3e9f6349e1), [Gemini Flash](5515a43a-2941-42c3-9ad2-9d31d4ecca71)

| Axis | Gemini | Claude | Consensus |
|---|---|---|---|
| Overall | **ACCEPT STOP** | **ACCEPT STOP** | **ACCEPT STOP** |
| Amend necessity (L3) | 0/10 | 3/10 | **No waive** |
| Merge L1 | no | no | **Keep flag-gated** |
| Remaining peek | closed | closed | **Not paused** |

**One-liners:** Gemini — L3 waive = post-hoc rule softening. Claude — sequential lock + still-negative H4 is the stop signal, not a last-peek license.

**Stop-memo:** [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md)

---

## Forbidden moves

- Cost shopping (15/10/25) or reverting working `c` to 30  
- Changing H or TP/SL / vol multiples  
- Reopening Regime or Precision WS2  
- Re-testing path-room-on, Short aux-excess, Short chase demote, L1/L2/S1  
- Hyperparam / feature grid on A+B; Fold C locks; pooled Long+Short  
- Spending Short A+B peeks this charter  
- Soft-promoting abs TB+1 / H4 / ADV caps to ship gates  
- Claiming Horizon-path PASS / cascade-ready / book PnL from Step 0 or a single Long lever  

---

## Build sequence

1. **Step 0** — MFE + exit-type + rank-tier diagnostic A+B (both sleeves). → **DONE** (Long SEP dual-fold; Short null)  
2. **Hard gate** — if no Top-K vs Rest separation → STOP-MEMO at 0/2. → **cleared for Long**  
3. Else pick first contingent lever (L1→L2→L3) matching Step 0 evidence. → **L1**  
4. **Peek 1** — Long A+B only. → **DONE** (H5 hold; H2-B regression → Peek 2 blocked)  
5. At most **peek 2** if sequential gate passes. → **blocked**; L3 dual-judge amend → **REJECTED**  
6. Stop-memo / merge — → **DONE** ([stop-memo](horizon-path-density-stop-memo.md)); Short remains deferred.

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md) | STOP record + next-workstream pointers |
| [horizon-exit-mfe-decay-charter.md](horizon-exit-mfe-decay-charter.md) | Next after path-density — MFE-decay / exit-timing (**CLOSED**) |
| [horizon-tp-floor-recalibration-charter.md](horizon-tp-floor-recalibration-charter.md) | Next — Long TP floor 60→50 (**OPEN**) |
| [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | Cost STOP — why path density was next |
| [rt-cost-realism-re-derivation-charter.md](rt-cost-realism-re-derivation-charter.md) | Cost charter record |
| [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md) | Path-EV STOP; feature locks |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | H=6 + `c*=20` floors |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Cascade map |
