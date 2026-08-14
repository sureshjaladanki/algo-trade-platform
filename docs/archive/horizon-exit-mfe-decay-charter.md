# Horizon Exit Timing / MFE-Decay Diagnostic — Nifty-100 MIS v1

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Measure **when** Long Top-K favorable excursion peaks inside locked `H=6`, how much is **given back** before TB exit, and whether a **Tier-2-adjacent** exit/hold lever (not Precision) is falsifiable — under signed `c*=20`  
**Status:** **STOP-MEMO** — peeks **2/2** exhausted; no merge — see [stop-memo](horizon-exit-mfe-decay-stop-memo.md)  
**Authority (prior):** Path-density STOP dual-judge next-workstream lock ([Claude](f9256c28-1e53-43be-acc3-cc3e9f6349e1), [Gemini](5515a43a-2941-42c3-9ad2-9d31d4ecca71)); owner preference: **Claude track** (exit/MFE-decay) over Gemini Precision-bailout  
**Judges (this charter):** [Claude Sonnet](c4500985-a244-43ed-abbf-0386b8996d4f), [Gemini Flash](9062b928-5983-4967-a01a-f88da5d3f8a9)  
**Date:** 2026-08-13  
**Depends on:** [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md), [horizon-path-density-charter.md](horizon-path-density-charter.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [cascade-strategy-overview.md](../cascade-strategy-overview.md), [horizon-exit-mfe-decay-stop-memo.md](horizon-exit-mfe-decay-stop-memo.md)  
**Does not reopen:** Cost ladder · Regime · Precision WS2 · H / multiples · path-density L1 merge · L3 sequential waive · v2 rejected levers (path-room-on, Short aux, Short chase demote, L1/L2/S1)

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | Path-density CLOSED: Long Top-K **does** travel farther than Rest, but entry-side density lever L1 fails sequential + economics (H4 −12/−19 bps). Residual unknown is **intra-horizon path shape / exit timing**, not another 15m travel-adequacy feature |
| Diagnosis to test | Edge may peak mid-path and be given back before TP / timeout — or never approach TP at all; these imply different Tier-2 levers (or stop) |
| Tier ownership | **Horizon owns economic viability.** Precision may **juice** a non-negative book; it must **not** be asked to recover Horizon’s H4 deficit |
| Friction / floors | **Frozen** — `c*=20` / archive 30; floors 60/50/30; multiples `3/2.5/1.5` |
| Primary H | **H=6 / 90m** (frozen); H=4 report-only |
| Sleeve posture | **Long-first** diagnostic; Short = Step 0 companion only (path-density Short SEP null stands) |
| Peek budget | **Max 2** Long Fold A+B — **2/2 spent** (E1 then E2); ledger closed |
| Precision | **Out of scope** this charter — deferred until Horizon H4 / path economics clear under locked geometry |
| Build posture | **CLOSED** — stop-memo at 2/2; no E1/E2 merge; Precision still blocked |

**One-line:** Diagnose MFE peak timing and giveback inside `H=6` for Long Top-K under `c*=20`; only then consider ≤2 Tier-2 exit/hold peeks — never hand the −12…−19 bps deficit to Precision.

---

## Dual-judge scores (charter design) — 2026-08-13

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | 10/10 | 9/10 | **ACCEPT** — residual leak is intra-horizon peak/giveback, not another entry density feature |
| Scope / freeze | 10/10 | 9/10 | **ACCEPT** — cost/H/floors/L1-off/path-density ledger stay frozen |
| Tier ownership (Horizon vs Precision) | 10/10 | 9/10 | **ACCEPT** — Precision ≠ Horizon bailout (**Gemini concurs**; Precision later only after Horizon viable) |
| Peek budget | 10/10 | 9/10 | **ACCEPT** — max 2 Long; Step 0 mandatory; hard-stop @ 0/2 |
| Gate design | 10/10 | 8/10 | **ACCEPT WITH REVISIONS** — H5 primary holds; tighten E1/E2 selection + hard-stop cuts (below) |
| Reject hardness | 10/10 | 9/10 | **ACCEPT** |
| Metrics/results fidelity | 10/10 | 9/10 | **ACCEPT** — Step 0 / Peek 1 cites match path-density STOP |
| Overall | ACCEPT WITH REVISIONS | ACCEPT WITH REVISIONS | **ACCEPT WITH REVISIONS → OPEN** |

**Judge one-liners**

- Gemini: exit diagnostic is the right residual; owner tier lock accepted — Precision must not salvage Horizon H4.  
- Claude: diagnosis/tier/peek budget faithful; tighten E1 `H_eff` pick + E2 calibration before any peek spend (Step 0 OK as written).

**Revisions applied (MUST_FIX consensus)**

1. Step 0 hard-stop quantitative cuts (Gemini).  
2. E1: exactly one `H_eff` from Step 0 peak-bar rule — no {3,4} grid (both).  
3. E2: single calibration path — pooled Step 0 pre-registered cut; **not** Fold-A-tune / B-confirm (Claude).  
4. Tie-break: if E1 and E2 both match → **E1 first** (ladder order) (Claude).

---

## Authority from path-density STOP (do not reopen)

From [stop-memo](horizon-path-density-stop-memo.md):

| Fact | Implication |
|---|---|
| Long Step 0 MFE + EXIT SEP dual-fold PASS | Travel density is real; entry levers still did not clear economics |
| Short SEP FAIL both folds | Short levers stay deferred |
| L1 `tod_mfe_frac_60` H5 hold; H2-B regress; H4 −12/−19 | Sequential freeze correct; L1 **not** merged |
| L3 waive REJECTED; remaining peek **closed** | No resume on path-density ledger |
| Abs Top-K MFE ~0.89–0.92× TP; timeout ~50% | Need **when** travel peaks / decays, not another density feature on that ledger |

---

## Tier responsibility lock (hard)

| Tier | Owns | Does **not** own |
|---|---|---|
| **1 Regime** | Sleeve open/close | Stock pick / exit physics |
| **2 Horizon + TB** | Name rank + **path EV under frozen geometry**; exit-contract diagnostics this charter | Dumping underwater books onto Tier 3 |
| **3 Precision** | 1m fill timing + firing **inherited** TP/SL/timeout on a viable Top-K set | Recovering Horizon H4 / TB+1 failure; re-ranking; rewriting barriers |

**Anti-goal:** “Precision bridges the 12–19 bps Horizon deficit” as a success criterion → **FAIL charter intent**.

---

## Carry-forward locks

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors | Long TP **60** / Short TP **50** / SL **30** |
| H=6; MIS cutoffs | Unchanged |
| Path-room / Long chase / aux | Demoted / 0 (unchanged) |
| `tod_mfe_frac_60` | **Flag-gated only**; not in default `LONG_FEATURES` |
| K | Long **5** / Short **3** |
| Regime / Precision WS2 | CLOSED / blocked |
| Path-density peeks | Ledger **closed** (1/2 spent; remainder not paused) |

---

## Process locks

| Lock | Rule |
|---|---|
| Dual-judge gate | **DONE** — ACCEPT WITH REVISIONS applied; Step 0 unlocked |
| Step 0 (no peek) | Publish Long Top-K (and Rest) **MFE peak bar**, **giveback**, **exit-time mix**, Fold A/B — see below |
| Hard stop @ 0 peeks | Dual-fold Top-K mean **peak MFE &lt; 0.70× TP floor** **AND** mean **giveback &lt; 0.10× TP floor** → exit-timing lever is noise → **STOP at 0/2** (selection/geometry exhausted). Qualitative read “never approaches TP + null giveback” maps to these cuts. |
| Peek budget | **Max 2** Long-only Fold A+B; Short lever peeks = **0** |
| Single-variable | One Tier-2 exit/hold lever per peek; no grid; no pooled Long+Short |
| Sequential | Peek 2 only if peek 1 clears Long H5 dual-fold **without** regressing H1/H2/H3 vs cost peek-1 Long read |
| Multiplicity | **New ledger** — cannot borrow path-density’s closed peek or Horizon v2 / cost peeks |
| Precision | No Precision experiments, 1m peeks, or “bailout” claims inside this charter |
| Stop | Exhaust 2 **or** clean economics-relevant hold with no regression → stop-memo; **or** Step 0 hard-stop |

---

## Gates

| Role | Metric | Rule |
|---|---|---|
| **Primary (peeks)** | Long H5 (Top−Rest StockTB+1) | Dual-fold CI LB > 0 |
| **Anti-goal** | Breaking H5 / H2 to lift report-only H4 or abs TB+1 | **FAIL** |
| **Anti-goal** | Claiming Precision recovered Horizon deficit | **FAIL** — out of scope |
| Report-only | Abs Top-K TB+1, H4 @20, H4arch @30, H1/H2/H3, peak-bar / giveback stats, time-to-exit | Never soft-promote to ship without fresh dual-judge |

**Not primary this charter:** TB+1 ≥20%, H4 ≥0, ADV lo caps, Precision fill-improvement bps.

---

## Step 0 — MFE peak / giveback / exit-clock diagnostic (no peek)

**Required before peek 1.** Long primary; Short companion publish-only. Fold A and B calendars (same as cost / path-density).

Locked geometry: entry at decision bar-end; path over bars `t+1 … t+H` with `H=6`; TP/SL floors as locked; working `c*=20`.

| Diagnostic | What to publish |
|---|---|
| **Peak bar** | Bar index of max favorable excursion within H (1…6); Top-K vs Rest distribution + mean |
| **Peak MFE / TP floor** | `mfe_frac` at peak — **same underlying Abs MFE / TP-floor statistic as path-density Step 0**, carried forward as the giveback baseline (not a re-litigation of travel separation) |
| **Giveback** | `(MFE − favorable excursion at TB exit) / TP floor` — how much peak edge is lost before TP/SL/timeout exit |
| **Exit clock** | Share of exits by barrier bar (1…6) × exit type (TP / SL / timeout) for Top-K |
| **Early vs late peak** | Peak in bars 1–3 vs 4–6: subsequent TP-hit rate and mean giveback (Top-K) |
| **Rank tier (report)** | Peak bar / giveback for ranks 1–2 vs 3–K |
| **Short companion** | Same tables; no Short peek authorization from null path-density SEP alone |

**Separation / implication gate (pre-registered):**

| Step 0 pattern | Implication |
|---|---|
| Dual-fold Top-K mean peak MFE **&lt; 0.70×** TP **AND** mean giveback **&lt; 0.10×** TP | Never reaches TP / null giveback — **STOP @ 0/2** |
| Peak MFE near/above ~1× **and** material giveback (not hard-stop) | **Exit/hold timing implicated** → contingent lever ladder |
| Peaks early (1–3) with high later SL/timeout | Early capture / shorter effective hold → **E1** candidate |
| Peaks late (4–6) with low TP share | Timeout / MIS clock interaction — report; do **not** reopen H without dual-judge; **E3** only if TOD buckets dominate |

**Harness (proposed):** `python -m src.experiments.analyze_horizon_mfe_decay --folds A,B`  
**Log (proposed):** `logs/horizon_mfe_decay_step0_ab.txt`

---

## Pre-registered Long lever ladder (contingent on Step 0)

Execute in order; spend ≤2 peeks total. All levers are **Tier-2 / TB-contract adjacent** on 15m path — **not** Precision 1m.

| Order | Lever | Single variable | Usable only if Step 0 shows |
|---|---|---|---|
| **E1** | Earlier vertical / effective hold — **exactly one** `H_eff ∈ {3,4}` chosen **before Peek 1** from Step 0 peak-bar rule below | One `H_eff` vs locked H=6 timeout on **eval exit only** (training labels + barrier floors unchanged) | Early peak + material giveback after peak; offline path replay shows TP share rises under earlier flatten |
| **E2** | Giveback / peak-aware hold rule — **one** threshold **pre-registered from Step 0 pooled publish** (no Fold-A tune / B-confirm; no A+B threshold search) | One fixed giveback fraction of TP floor | Material giveback; clean percentile cut visible in Step 0 pooled publish |
| **E3** | Time-bucket eligibility screen (skip entries whose TOD historically never peaks before bar 4 — causal TOD prior only) | One TOD screen on/off | Late-peak + timeout-dominated buckets dominate Top-K loss |

**E1 `H_eff` selection lock (no grid):** After Step 0, set `H_eff = 3` if Top-K median peak bar ≤ 3 on **both** folds; else `H_eff = 4` if median peak bar ≤ 4 on both folds and early-peak pattern holds; if neither rule fires → **E1 not usable** (do not invent a third value; do not peek both 3 and 4).

**Tie-break:** If E1 and E2 both match Step 0 evidence → spend **E1 first** (ladder order). If neither matches → **STOP @ 0/2**.

No E4. No Precision entry/exit peeks. No L1 re-merge. No cost / H-label / multiple changes.

### Peek gates (if Step 0 clears)

| Item | Lock |
|---|---|
| Sleeve | Long only |
| Baseline | Cost peek-1 Long under `c*=20` (same as path-density) |
| Gate | Long H5 dual-fold CI LB > 0; no H1/H2/H3 regression vs that baseline |
| Report-only | Abs TB+1, H4@20, H4arch@30, giveback / peak-bar deltas |
| Merge | Only via stop-memo + dual-judge; default **off** until then |
| E1 semantics | `H_eff` flattens eval path at `t+H_eff` if TP/SL not hit earlier; **does not** retrain labels or change primary H |

---

## Forbidden moves

- Asking Precision / 1m timing to **recover** Horizon H4 or abs TB+1  
- Cost shopping (15/10/25) or reverting working `c` to 30  
- Changing label H or TP/SL / vol multiples  
- Reopening Regime or Precision WS2  
- Merging `tod_mfe_frac_60` into defaults; L3 waive on path-density ledger  
- Re-testing path-room-on, Short aux-excess, Short chase demote, density L1/L2 as “new”  
- Hyperparam / feature grid on A+B; Fold C locks; pooled Long+Short  
- Soft-promoting H4 ≥0 / TB+1 ≥20% to ship gates  
- Claiming Horizon-path PASS / cascade-ready / Precision-ready from Step 0 alone  
- Treating exit-policy `H_eff` diagnostic as a silent primary-H reopen for training labels  

---

## Build sequence

1. **Dual-judge sign-off** → **DONE** (ACCEPT WITH REVISIONS; locks applied).  
2. **Step 0** — peak bar + giveback + exit-clock A+B → **DONE** (`logs/horizon_mfe_decay_step0_ab.txt`). Hard-stop did **not** fire.  
3. **Hard gate** — MFE&lt;0.70× **and** giveback&lt;0.10× dual-fold → STOP @ 0/2. → **DID NOT FIRE** (Long MFE ~0.89–0.91; GB ~0.39–0.43).  
4. Contingent lever lock → **E1 `H_eff=3`** (median peak ≤3 both folds); E2 threshold **0.20** pre-registered (pooled GB mean/2).  
5. **Peek 1** — E1 Long A+B → **DONE** (H5 hold; TB+1 collapse; H4 unchanged).  
6. **Peek 2** — E2 Long A+B → **DONE** (H5 hold; TB+1 still collapsed; H4 unchanged).  
7. **STOP-MEMO** — [horizon-exit-mfe-decay-stop-memo.md](horizon-exit-mfe-decay-stop-memo.md); Precision remains **blocked**.

### Step 0 results (2026-08-13)

| Sleeve | MFE | Giveback | Peak-bar med | Early share | HARDSTOP |
|---|---|---|---|---|---|
| Long A/B | 0.913 / 0.894 | 0.432 / 0.392 | 2.29 / 2.40 | 0.70 / 0.67 | no / no |
| Short | companion | ~0.44 | ~2.7 | ~0.65 | no peek |

### Peek results vs cost Long baseline

| Gate | Cost A/B | E1 A/B | E2 A/B |
|---|---|---|---|
| H5 | PASS / PASS · p_top 10.9 / 8.9% | PASS / PASS · **4.6 / 3.7%** | PASS / PASS · **4.1 / 3.3%** |
| H1/H2/H3 | cost pattern | hold | hold |
| H4 @20 | −17 / −14 bps | −17 / −14 | −17 / −14 |

---

## Dual-judge checklist (signed)

| Question | Claude | Gemini | Lock |
|---|---|---|---|
| MFE-decay / exit-clock right residual leak? | yes | yes | **Yes** |
| Precision recovers Horizon deficit forbidden? | yes | yes (concurs; later only after Horizon viable) | **Yes** |
| Max 2 peeks + Step 0 hard-stop adequate? | yes | yes | **Yes** |
| E1/E2/E3 non-circular Tier-2-only? | yes (w/ E1/E2 amend) | yes | **Yes after revisions** |
| Amend before Step 0 code? | none for Step 0 | hard-stop cuts + E1 single `H_eff` | **Applied** |

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-exit-mfe-decay-stop-memo.md](horizon-exit-mfe-decay-stop-memo.md) | This charter CLOSED — 2/2 peeks; no merge |
| [horizon-tp-floor-recalibration-charter.md](horizon-tp-floor-recalibration-charter.md) | Next — Long TP floor 60→50 (**OPEN**, dual-judge locked) |
| [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md) | Why this charter exists; Claude vs Gemini next-step split |
| [horizon-path-density-charter.md](horizon-path-density-charter.md) | Prior ledger (CLOSED) |
| [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | Friction lock; economics still fail |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | H=6 + floors + `c*=20` |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Tier jobs — Precision inherits geometry |
| [precision-tier3-verdict.md](../precision-tier3-verdict.md) | Deferred — juice only after Horizon viable |
