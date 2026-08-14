# Horizon Short Ranking / Travel-Separation — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Step 0 Short travel / anti-selection / gated C1–C2 ρ + ≤2 Short ranking peeks under locked `c*=20` / `H=6` / floors  
**Status:** **STOP-MEMO — short-travel charter CLOSED**; peeks **1 / 2** · remaining peek **closed** — **no merge**  
**Date:** 2026-08-13  
**Charter:** [horizon-short-travel-separation-charter.md](horizon-short-travel-separation-charter.md)  
**Depends on:** [horizon-tp-floor-recalibration-stop-memo.md](horizon-tp-floor-recalibration-stop-memo.md), [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md)  
**Trigger:** Peek 1 (S1b C1) fails dual-fold Short H5 and regresses Fold A H2 vs cost baseline → sequential Peek 2 freeze  
**A+B peeks spent:** **1 / 2** — remaining peek **closed** (not paused; reopen needs a fresh dual-judge charter)

---

## One-line

Short Top-K still does **not** separate travel vs Rest, but pre-registered C1 (`tod_mfe_frac_50_short`) clears gated feature→travel ρ dual-fold — and **still fails** as a ranking lever (H5 A FAIL; H2-A PASS→FAIL) — **stop at 1/2**; do not merge; Precision / B1 stay blocked.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| Short SEP / Top−Rest travel still FAIL under locked geometry | **Supported** — Step 0 SEP FAIL both folds (reconfirm) |
| Anti-selection (Top ≤ Rest − 0.05×TP) authorizes S1a | **Disproven** — gaps +0.012 / −0.018; ANTI both FAIL |
| Rank-tier inversion authorizes S-K (K 3→2) | **Disproven** — r1−r23 ≈ −0.04 / −0.04 ≫ −0.10 cut |
| Abs Top-K MFE below economic zone → geometry STOP @ 0/2 | **Disproven** — Top Abs MFE ~50.4 bps ≈ 1.01× Short TP both folds |
| C1 `tod_mfe_frac_50_short` clears holdout \|ρ\|≥0.10 sign-consistent + non-dup | **Supported** — ρ ≈ **0.30 / 0.32**; nondup pass (`stock_r_15` ~0; vs Long L1 ~0.48–0.50 < 0.70) |
| C2 `unfinished_downside_z` clears gated ρ | **Disproven** — ρ ≈ 0.04 / 0.03 |
| S1b C1 clears Short H5 dual-fold without H1/H2/H3 regression | **FAIL** — H5-A FAIL; **H2-A regresses** PASS→FAIL |
| Merge C1 into default `SHORT_FEATURES` | **No** |
| Spend Peek 2 (no other Step 0 lever left) | **Forbidden** — sequential freeze; S1a / S-K never authorized |
| Precision / B1 may bridge Short H5 | **Forbidden** — still blocked |

---

## Terminal evidence

### Step 0 (no peek)

**Log:** `logs/horizon_short_travel_step0_ab.txt`  
**Harness:** `python -m src.experiments.analyze_horizon_short_travel --folds A,B`

| Diagnostic | Fold A | Fold B | Cut |
|---|---|---|---|
| SEP (MFE\|EXIT) | **FAIL** | **FAIL** | reconfirm |
| ANTI Top−Rest MFE | +0.012 | −0.018 | ≤ −0.05 both → no |
| Abs Top MFE (bps) | 50.4 (~1.01×) | 50.4 (~1.01×) | < 0.70× → no |
| RANKtier r1−r23 | −0.045 | −0.040 | ≤ −0.10 → no |
| K2 trades | 1558 | 1840 | ≥150 ok (S-K still no) |
| RHO_C1 vs Abs MFE | **+0.297 CLEAR** | **+0.316 CLEAR** | \|ρ\|≥0.10 + nondup |
| RHO_C2 vs Abs MFE | +0.039 | +0.031 | no |
| Long companion SEP | PASS | PASS | publish-only |

**Hard-stop:** did **not** fire (C1 novel signal present).  
**Authorized ladder:** **S1b_C1** only (tie-break S1a→S1b→S-K; S1a/S-K never cleared).

### Peek 1 — S1b C1 `tod_mfe_frac_50_short`

**Logs:** `logs/horizon_short_travel_s1b_c1_peek1_fold_a.txt` · `logs/horizon_short_travel_s1b_c1_peek1_fold_b.txt`  
**Baseline:** cost peek-1 Short @ `c*=20` (`logs/horizon_cost_c20_peek1_fold_*.txt`)

| Gate | S1b A | S1b B | vs cost Short |
|---|---|---|---|
| **H5** | **FAIL** · 0.015 [−0.004, 0.034] · p_top **14.1%** | **PASS** · 0.032 [0.015, 0.049] · p_top **14.7%** | Dual-fold **FAIL** (was FAIL/FAIL; B flips PASS; A stays FAIL) |
| H1 | PASS | PASS | Hold / improve |
| H2 | **FAIL** | PASS | **A PASS→FAIL — sequential freeze** |
| H3 | PASS | PASS | Hold |
| H4 @20 | −16 bps | −15 bps | A −13→−16 (worse); B −16→−15 — still neg |
| ADVt lo | 34% | 42% | report-only |

**Gate read:** primary Short H5 dual-fold CI LB > 0 **fails** (A). Sequential **no H1/H2/H3 regression** **fails** on Fold A H2. Report-only TB+1 lifts slightly (12.8→14.1 / 13.0→14.7) but H4 stays negative. **No merge. No Peek 2.**

Note (judge optional): Fold A H2 CI LB ≈ **−0.0000** — razor-edge FAIL vs cost baseline PASS, not a large point-estimate collapse.

---

## Dual-judge outcome (2026-08-13)

**Judges:** [Claude Sonnet](da885c4c-55c0-4e9b-8858-ee8dcdf8147d), [Gemini Flash](58645e66-3607-4c89-9aa3-933442a01765)

| Axis | Gemini | Claude | Consensus |
|---|---|---|---|
| Overall | **ACCEPT STOP** | **ACCEPT STOP** | **ACCEPT STOP** |
| Metrics fidelity | 10/10 | 9/10 | Numbers match logs |
| Process discipline | 10/10 | 9/10 | Sequential freeze + C1 no-merge correct |
| Amend necessity | 10/10 | 9/10 | **Do not** spend Peek 2 |
| Merge C1 | no | no | **Keep flag-gated; off defaults** |
| Precision / B1 | blocked | blocked | **Still blocked** |
| Remaining peek | closed | closed | **1/2 spent; 1 closed** |

**Judge one-liners**

- Gemini: C1 cleared Step 0 ρ but failed as ranking lever (H5-A FAIL; H2-A regress) — obligatory freeze; Precision stays blocked.  
- Claude: Numbers check out; no-merge / no-Peek-2 is the only defensible gate reading — clean conservative STOP.

**MUST_FIX:** none.

## Verdict

| Item | Lock |
|---|---|
| Peek ledger | **1 / 2 spent — remaining closed** |
| Merge `tod_mfe_frac_50_short` into default `SHORT_FEATURES` | **No** — flag-gated replay only (`--short-s1b`) |
| S1a / S-K under this ledger | **Not authorized** by Step 0; do not spend residual peek |
| C2 `unfinished_downside_z` | Stay off defaults (ρ null) |
| Precision / B1 | **Still blocked** until Short dual-fold H5 + economics clear under locked geometry |
| Horizon-path PASS / cascade Short-ready | **Forbidden / unproven** |

**Diagnosis residual after this charter:** Short paths *can* travel (~1.01× TP) and a causal TOD Short-MFE feature *does* correlate with Abs MFE (ρ~0.30), but appending it to the locked Short ranking list does **not** create dual-fold Top−Rest StockTB+1 separation without regressing H2. Anti-selection and rank-tier dilution were not present as numeric levers. Do not remount reject-list features; do not hand the deficit to Precision.

---

## Code / harness artifacts

| Path | Role |
|---|---|
| `src/horizon/eval/short_travel.py` | Step 0 SEP / ANTI / rank-tier / gated C1–C2 ρ / hard-gate |
| `src/experiments/analyze_horizon_short_travel.py` | Step 0 CLI |
| `src/horizon/horizon_model.py` | `SHORT_S1B_C*` constants; `features_for_direction(..., short_s1b_feature=)` |
| `src/experiments/eval_horizon.py` | `--short-s1b` flag-gated peek (off defaults) |

---

## Locked carry-forward

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors / H / multiples / K | Unchanged (Short K stays **3**) |
| `tod_mfe_frac_50_short` | **Flag-gated only** (`--short-s1b tod_mfe_frac_50_short`); **not** in default `SHORT_FEATURES` |
| `unfinished_downside_z` | Off defaults |
| Path-room / aux / chase demote / S1 / S2 / Long L1/E1/E2 / Long TP50 | Stay rejected / demoted |
| Soft ship floors (H4≥0 / TB+1≥15%) | Still **not** primary |

---

## Reject (next 30 days)

- Merging C1 into Short defaults without a new dual-judge charter  
- Spending Peek 2 on S1a / S-K / C2 after Step 0 non-authorization or sequential freeze  
- Remounting path-room / Short aux / chase demote / S1 / S2  
- Cost shopping or cutting `H=6`  
- Activating Precision WS2 / B1 as Short H5 bailout  
- Scanning full `SHORT_FEATURES` ρ to pick an unregistered S1b post-hoc  

---

## Next workstream (outside this ledger)

**No automatic next peek on this ledger.** Long density / exit / TP-floor and Short travel-separation novel levers under locked `c*=20` / `H=6` are exhausted on their charters.

**Dual-judge next (2026-08-13):** both judges **ACCEPT STOP**. Consensus: do **not** activate Precision / B1 as a Short H5 bailout. Fresh dual-judge charter required for any further Horizon geometry / Short signal family work. Claude optionally allows scoping **Long-only** Precision P1/P2 selectivity *measurement* (not Short/B1; not cascade-ready claims) — Gemini prefers Horizon redesign first. Either path needs an explicit new charter; do not silently escalate.

Further Horizon work (joint barrier edits, new Short feature family outside C1/C2, or economics-first redesign) needs a **fresh dual-judge charter**. Precision stays blocked until Short dual-fold H5 + path economics clear under locked geometry — do not treat this STOP as license to activate B1.
