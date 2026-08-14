# Horizon Long TP-Floor Recalibration — Nifty-100 MIS v1

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Test whether **lowering Long TP floor** under locked `c*=20` / `H=6` / SL converts already-realized Top-K MFE into higher TB=+1 density and better path economics — **without** cutting vertical H or remounting rejected exit levers  
**Status:** **STOP-MEMO** — peek **1/1** spent; **no merge** — see [stop-memo](horizon-tp-floor-recalibration-stop-memo.md)  
**Authority (prior):** MFE-decay STOP next-workstream consensus ([Claude](51de4aee-3bc0-4f11-a4e9-b0ea2db8d9c8), [Gemini](e6b3c42e-dfba-4379-bc83-4d24ceddbb5b)); exit-timing ledger closed  
**Judges (this charter):** [Claude Sonnet](ed5cc1a2-5832-4e3c-a371-54ce6fc1d572), [Gemini Flash](230c5433-acf0-4e01-ab02-e6471b640d5b)  
**Date:** 2026-08-13  
**Depends on:** [horizon-exit-mfe-decay-stop-memo.md](horizon-exit-mfe-decay-stop-memo.md), [horizon-exit-mfe-decay-charter.md](horizon-exit-mfe-decay-charter.md), [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [cascade-strategy-overview.md](../cascade-strategy-overview.md), [horizon-tp-floor-recalibration-stop-memo.md](horizon-tp-floor-recalibration-stop-memo.md)  
**Does not reopen:** Cost ladder · Regime · Precision WS2 · primary `H=6` · Short floors · path-density L1 merge · MFE-decay E1/E2 · L3 sequential waive · v2 rejected levers (path-room-on, Short aux, Short chase demote, L1/L2/S1) · TP-floor grid / alternate floors

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | MFE-decay CLOSED: Long Top-K peaks early (~bar 2.3) and giveback is real (~0.39–0.43×), but E1 `H_eff=3` and E2 giveback-exit **collapsed abs TB+1** and left H4 −17/−14. Residual falsifiable lever is **barrier geometry vs realized MFE**, not another exit-clock tweak |
| Diagnosis to test | Abs Top-K MFE ~0.89–0.92× of **60 bps** ≈ **53–55 bps** — often clears a **50 bps (2.5×c)** floor that the current **3.0×c** floor misses |
| Single variable | Long TP multiple **3.0 → 2.5** only (floor **60 → 50 bps**). Hold `c*=20`, archive 30, `H=6`, SL floor **30**, Short TP **50**, vol multiples unchanged |
| Tier ownership | **Horizon owns economic viability.** Precision stays blocked until Horizon H4 / path economics clear under locked (or dual-judge-amended) geometry |
| Sleeve posture | **Long-only** (Step 0 + peeks); Short omitted this charter (SEP null + Short TP already 50 bps) |
| Peek budget | **Max 1** Long Fold A+B (**T1 only**); **1/1 spent** — ledger closed |
| Precision | **Out of scope** this charter |
| Build posture | **CLOSED** — stop-memo at 1/1; Long TP stays 60 bps; Precision still blocked |

**One-line:** Ask whether a 50 bps Long TP floor captures Top-K paths that already travel ~53–55 bps under `H=6` — without cutting H, relaxing cost, or remounting rejected exit levers.

---

## Dual-judge scores (charter design) — 2026-08-13

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | 10/10 | 9/10 | **ACCEPT** — barrier geometry vs realized MFE is the right residual after exit-timing FAIL |
| Scope / freeze | 10/10 | 9/10 | **ACCEPT** — `c`/H/SL/Short/vol/rejects frozen |
| Peek budget / hard-stop | 8/10 | 6/10 | **REVISE→LOCK** — drop T2; either-fold hard-stop; Long-only Step 0 |
| Gate design | 9/10 | 8/10 | **ACCEPT** — H5 primary; H4/TB+1 report-only |
| Reject hardness | 9/10 | 9/10 | **ACCEPT** |
| Metrics / results fidelity | 9/10 | 9/10 | **ACCEPT** — cites match MFE-decay / path-density STOP |
| Overall | ACCEPT WITH REVISIONS | ACCEPT WITH REVISIONS | **ACCEPT WITH REVISIONS → OPEN** |

**Judge one-liners**

- Gemini: single binary hypothesis 50 bps or stop; eliminate T2 grid; hard-stop on either fold; omit Short clutter.  
- Claude: diagnosis/freeze strong; T2 as written is a soft second bite — lock or kill; retrain+relabel is the right T1 semantic; hard-stop cuts are OR across conditions.

**Revisions applied (MUST_FIX consensus)**

1. **Eliminate T2** (55 bps / alternate floor) — Gemini MUST_FIX; Claude grid-risk YES → single hypothesis **T1 only** (Claude #1–4 solved by deletion).  
2. **Hard-stop = either fold** fires STOP @ 0/1 (Gemini); three cuts are **OR** across conditions (Claude).  
3. **Omit Short** from Step 0 (Gemini) — Short TP already 50 bps; peeks = 0.  
4. **Retrain + relabel** locked as T1 semantic (both YES) — not eval-only overlay.  
5. SL-contamination measurement clarified (Gemini NICE → applied).

---

## Authority from MFE-decay STOP (do not reopen)

From [stop-memo](horizon-exit-mfe-decay-stop-memo.md):

| Fact | Implication |
|---|---|
| Step 0: peak ~2.3; Abs MFE ~0.89–0.91×; giveback ~0.39–0.43× | Shape is real; hard-stop @ 0/2 did **not** fire |
| E1 `H_eff=3`: H5 hold; TB+1 **10.9→4.6 / 8.9→3.7**; H4 flat −17/−14 | Earlier vertical **falsified** as economics lever |
| E2 giveback 0.20: same signature | Second independent “exit sooner” fail |
| Exit clock ~55–60% bar-6 timeout | Early flatten amputates late TP paths |
| Precision bailout | Still **forbidden** |

**Diagnosis residual lock:** travel density is real; peak/giveback is real; **15m eval-exit policy alone does not convert that into TB+1 / non-negative H4**. Next falsifiable layer is **Long TP floor vs realized MFE**, not H&lt;6 soft reopen.

---

## Rejected-levers registry (carry-forward — do not remount)

| Lever | Ledger | Outcome | Code posture |
|---|---|---|---|
| Path-room features | Horizon v2 | Demoted (ablation hurt) | Off defaults |
| L1 `tod_mfe_frac_60` | Path-density | H5 hold; H2-B regress; H4 neg | `--l1-travel-adequacy` flag only |
| L2 Long K 5→3 | Path-density | Not implicated (Step 0) | Not spent |
| L3 min-travel screen | Path-density | Amend REJECTED | Closed |
| E1 `H_eff` ∈ {3,4} | MFE-decay | TB+1 collapse; H4 flat | `--eval-h-eff` rejected replay only |
| E2 giveback-exit 0.20 | MFE-decay | Same fail signature | CLI / labeler exit path **removed** |
| Cost ladder 15/10/25 | Cost | REJECT | Working `c*=20` locked |
| TP-floor grid / T2 55 bps | This charter (design) | **REJECTED at design lock** | Not authorized |
| Precision-as-H4-bailout | Cross-charter | Forbidden | Precision blocked |

---

## Tier responsibility lock (hard)

| Tier | Owns | Does **not** own |
|---|---|---|
| **1 Regime** | Sleeve open/close | Stock pick / barrier geometry |
| **2 Horizon + TB** | Name rank + **path EV under barrier geometry** — this charter may amend **Long TP floor only** via dual-judge peek | Dumping underwater books onto Tier 3; silent H cut |
| **3 Precision** | 1m fill timing on a viable Top-K set | Recovering Horizon H4; rewriting barriers |

**Anti-goal:** “Precision bridges the −14…−17 bps Horizon deficit” → **FAIL charter intent**.

---

## Carry-forward locks

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** — frozen |
| Short TP / SL floors | **50 / 30** — frozen; not in scope |
| Long SL floor | **30** (1.5×c) — frozen |
| Vol multiples | Long `2.5/1.0`; Short `2.0/0.9` — frozen |
| Primary H | **H=6 / 90m** — frozen (E1 already falsified eval-only earlier flatten) |
| MIS cutoffs | Unchanged |
| K | Long **5** / Short **3** |
| `tod_mfe_frac_60` / path-room / E1/E2 | Stay demoted / flag-replay only |
| Regime / Precision WS2 | CLOSED / blocked |
| Path-density + MFE-decay peeks | Ledgers **closed** |

**Single degree of freedom this charter:** Long TP floor multiple of working `c*` — **2.5× (50 bps)** vs locked **3.0× (60 bps)**. No alternate floor.

---

## Process locks

| Lock | Rule |
|---|---|
| Dual-judge gate | **DONE** — ACCEPT WITH REVISIONS applied; Step 0 unlocked |
| Step 0 (no peek) | Publish Long Top-K **absolute MFE (bps)** crossing rates at 50 vs 60 — see below |
| Hard stop @ 0 peeks | If **any** hard-stop cut fires on **either** fold → **STOP at 0/1** |
| Peek budget | **Max 1** Long-only Fold A+B (**T1**); Short = 0; no T2 |
| Single-variable | One Long TP-floor change; **no** simultaneous SL / H / Short / feature change |
| Multiplicity | **New ledger** — cannot borrow path-density / MFE-decay / cost peeks |
| Precision | No Precision experiments or bailout claims |
| Stop | Spend T1 → stop-memo; **or** Step 0 hard-stop; further peeks need fresh dual-judge amend |

---

## Gates

| Role | Metric | Rule |
|---|---|---|
| **Primary (peek)** | Long H5 (Top−Rest StockTB+1) | Dual-fold CI LB > 0 |
| **Anti-goal** | Breaking H5 / H2 to lift report-only abs TB+1 / H4 | **FAIL** |
| **Anti-goal** | Cutting primary H, remounting E1/E2/L1, or sneaking a second floor | **FAIL** |
| Report-only | Abs Top-K TB+1, H4 @20, H4arch @30, H1/H2/H3, Step-0 crossing stats, mean TP width, mean bars-to-TP | Never soft-promote H4≥0 / TB+1≥20% to ship without fresh dual-judge |

---

## Step 0 — Absolute MFE crossing diagnostic (no peek)

**Required before peek 1.** **Long only.** Fold A and B calendars (same as cost / path-density / MFE-decay).

**Measure in absolute return units (bps), not `mfe_frac` vs the candidate floor** — so the denominator does not silently move with the hypothesis.

Locked geometry for the diagnostic path: entry at decision bar-end; path over `t+1 … t+H` with `H=6`; current production barriers (Long TP 60 bps) for exit-type / event-order context; working `c*=20`.

| Diagnostic | What to publish |
|---|---|
| **Abs MFE (bps)** | Top-K vs Rest distribution of max favorable excursion in bps (Long: MFE return × 1e4) |
| **Crossing rates** | Share of Top-K with Abs MFE ≥ **50 bps** and ≥ **60 bps**; Δ = P(≥50) − P(≥60) |
| **Near-miss band** | Share with Abs MFE ∈ **[50, 60)** — the convertible mass if floor drops to 50 |
| **Conditional exit mix** | Among near-miss band: TP / SL / timeout shares under **current** 60-bps geometry |
| **SL contamination** | Among near-miss: share where SL event occurs **before** the path first reaches +50 bps favorable excursion (`t_SL < t_{MFE≥50}` within the hold window). Reaching +50 bps *before* SL counts as clean convertible mass, not contamination |
| **Rest comparison** | Same crossing table for Rest (report only) |
| **Bars-to-peak (report)** | Mean / median peak bar for near-miss vs ≥60 clearers |

**Hard-stop cuts (pre-registered — OR across cuts; fire on either fold):**

| Cut | Meaning |
|---|---|
| Near-miss mass **&lt; 5%** of Top-K on **either** fold | Too little convertible mass → STOP @ 0/1 |
| Among near-miss, **&gt; 50%** SL-contaminated (def above) on **either** fold | Lowering TP mostly re-labels losers → STOP @ 0/1 |
| Mean Abs MFE (bps) **&lt; 45** on Top-K on **either** fold | Paths do not reliably reach 2.5×c zone → STOP @ 0/1 |

**Implication gate (if hard-stop does not fire):**

| Step 0 pattern | Implication |
|---|---|
| Material near-miss mass (≥5% both folds) with majority **not** SL-contaminated | **T1** authorized — Long TP floor 60→50 is falsifiable |
| Near-miss dominated by SL-before-50 | Hard-stop / STOP |
| Rest near-miss ≫ Top-K near-miss | Ranking already concentrates travelers; floor change may still help abs TB+1 — watch H5 dilution on peek |

**Harness (proposed):** `python -m src.experiments.analyze_horizon_tp_floor --folds A,B`  
**Log (proposed):** `logs/horizon_tp_floor_step0_ab.txt`

---

## Pre-registered Long lever (contingent on Step 0)

**One lever. One peek. No grid.**

| Order | Lever | Single variable | Usable only if Step 0 shows |
|---|---|---|---|
| **T1** | Long TP floor **60 → 50 bps** (`3.0×c → 2.5×c`) | One floor value; **retrain + relabel** under new Long TP floor | Hard-stop not fired; near-miss mass ≥5% on both folds |

**T1 semantics (locked):** Rebuild TB labels with `TP_FLOOR_LONG = 2.5 * ROUND_TRIP_COST` (50 bps); Long vol multiple unchanged (`max(2.5×atr, 50bps)`); retrain Horizon path-EV on new labels; evaluate holdout under the same floor. Short unchanged. **Not** an eval-only overlay on a 60-bps-trained model (E1/E2 already showed eval-only exit tweaks fail; floor change must move the ranking target).

**No T2.** No 55 bps. No alternate floor from Step 0 percentiles. If T1 fails gates or economics stay null → **stop-memo**; further floors need a **new** dual-judge charter.

### Peek gates (if Step 0 clears)

| Item | Lock |
|---|---|
| Sleeve | Long only |
| Baseline | Cost peek-1 Long under `c*=20` + 60-bps Long TP (same as path-density / MFE-decay) |
| Gate | Long H5 dual-fold CI LB > 0; no H1/H2/H3 regression vs that baseline |
| Report-only | Abs TB+1, H4@20, H4arch@30, mean realized TP width, mean bars-to-TP, Step-0 Δ crossing |
| Merge | Only via stop-memo + dual-judge; default **off** until then |
| Ship language | Do **not** claim Horizon-path PASS from TB+1 lift alone without H4 / dual-judge |

---

## Forbidden moves

- Cutting primary `H=6` or remounting E1 `H_eff` / E2 giveback-exit  
- Cost shopping (15/10/25) or reverting working `c` to 30  
- Changing Long SL floor, Short TP/SL, or vol multiples in the same peek as Long TP  
- Any second TP floor (55 / 45 / grid) under this ledger  
- Reopening Regime or Precision WS2; Precision-as-bailout claims  
- Merging `tod_mfe_frac_60` / path-room; L3 waive on path-density ledger  
- Hyperparam / floor grid on A+B; Fold C locks; pooled Long+Short  
- Soft-promoting H4 ≥0 / TB+1 ≥20% to ship gates  
- Claiming Horizon-path PASS / cascade-ready / Precision-ready from Step 0 alone  
- Treating a TP-floor win as license to silently reopen H or cost  
- Eval-only floor overlay without retrain (wrong semantic for T1)  

---

## Build sequence

1. **Dual-judge sign-off** on this charter design → **DONE** (ACCEPT WITH REVISIONS; locks applied).  
2. **Step 0** — absolute MFE crossing @ 50 vs 60 bps, A+B (Long only) → **DONE** (hard-stop clear; T1 authorized).  
3. **Hard gate** — either-fold near-miss / SL-contamination / mean-MFE cuts → did **not** fire.  
4. Contingent lever lock → **T1** (50 bps) authorized.  
5. **Peek 1** — T1 Long A+B (retrain + relabel) → **DONE**; H5 hold; **H3-B regress**; economics null.  
6. **Stop-memo** — no merge; Long TP restored to 60. **No Peek 2 on this ledger.**

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-exit-mfe-decay-stop-memo.md](horizon-exit-mfe-decay-stop-memo.md) | Why this charter — exit timing exhausted |
| [horizon-exit-mfe-decay-charter.md](horizon-exit-mfe-decay-charter.md) | Prior ledger (CLOSED) |
| [horizon-tp-floor-recalibration-stop-memo.md](horizon-tp-floor-recalibration-stop-memo.md) | This ledger CLOSED — T1 no merge |
| [horizon-short-travel-separation-charter.md](horizon-short-travel-separation-charter.md) | Next — Short ranking / travel-separation (**OPEN**) |
| [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md) | Travel separation; L1 rejected |
| [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | Friction lock `c*=20` |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | Current H=6 + floors + multiples — Long TP stays 60 (T1 not merged) |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Tier jobs — Precision inherits geometry |
