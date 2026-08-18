# Precision Execution Bridge — Nifty-100 MIS v1

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Falsify whether Tier 3 **1m entry-timing / exit-management** on a **frozen** Long Top-K registry can recover the measured **~12–19 bps** Horizon H4 deficit under locked `c*=20` / `H=6` / floors — without rewriting Horizon gates or geometry  
**Status:** **DRAFT — unblocked for dual-judge** — EV-net rebuild [stop-memo](../archive/horizon-ev-net-rebuild-stop-memo.md) hard-stopped @ 0/3 with Top-K=5 unchanged; re-anchor Step 0 to production Top-K=5  
**Authority (prior):** Path-density STOP next-workstream ([Claude](f9256c28-1e53-43be-acc3-cc3e9f6349e1), [Gemini Flash](5515a43a-2941-42c3-9ad2-9d31d4ecca71)); Gemini recommended Precision bridge; owner then preferred Claude exit/MFE track. Exit / TP-floor / Short-architecture / Admission / path-quality veto / EV-net ledgers **CLOSED** with Long H4 still negative. **Owner reopen** of Gemini’s Precision track as a **falsification charter** — not a silent bailout.  
**Sequencing (2026-08-16):** Admission + path-quality veto + EV-net rebuild all closed without changing the Long Top-K=5 registry — Precision Step 0 may dual-judge against production Top-K=5.  
**Judges (this charter):** *pending dual-judge*  
**Date:** 2026-08-14 · **sequencing amend:** 2026-08-16  
**Depends on:** [horizon-tier2-admission-charter.md](../archive/horizon-tier2-admission-charter.md), [horizon-path-density-stop-memo.md](../archive/horizon-path-density-stop-memo.md), [horizon-exit-mfe-decay-stop-memo.md](../archive/horizon-exit-mfe-decay-stop-memo.md), [horizon-tp-floor-recalibration-stop-memo.md](../archive/horizon-tp-floor-recalibration-stop-memo.md), [horizon-short-architecture-stop-memo.md](../archive/horizon-short-architecture-stop-memo.md), [precision-tier3-verdict.md](../precision-tier3-verdict.md), [precision-tier3-eval-verdict.md](../precision-tier3-eval-verdict.md), [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [cascade-tier3-ws01-verdict.md](../archive/cascade-tier3-ws01-verdict.md), [cascade-strategy-overview.md](../cascade-strategy-overview.md), [rt-cost-realism-re-derivation-stop-memo.md](../archive/rt-cost-realism-re-derivation-stop-memo.md)  
**Does not reopen:** Cost ladder · Regime · Horizon features / path-room / L1 / E1 / E2 / Long TP50 · Short architecture / B1 · primary `H=6` · floors / vol multiples · Precision fills inside Horizon H5 · cascade-ready claims from Precision alone · Admission peek ladder (owned by Admission charter)

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | Path-density Gemini next-workstream: *“can execution bridge the ~12–19 bps Horizon deficit?”* Claude exit/MFE + TP-floor ledgers exhausted Tier-2 levers; Long H4 still ~−12…−19 (path-density) / −17/−14 (MFE). Residual falsifiable layer is **1m monetization on the same Top-K book**, not another Horizon peek |
| Diagnosis to test | Naive decision-close Top-K path EV is underwater; 1m fill timing + skip selectivity **might** recover enough bps on fires to clear friction — or prove they cannot |
| Single degree of freedom | Precision **rules / timing / selectivity** only — frozen Horizon registry, frozen TB geometry, frozen `c*` |
| Tier ownership | **Horizon still owns path viability under naive entry.** This charter measures whether Precision can **monetize** that book enough to clear absolute net — it does **not** redefine Horizon H5/H4 as Precision skill |
| Sleeve posture | **Long-first** (deficit + Long H5 dual-fold PASS under cost/path-density). Short = companion report-only; Short sleeve stays **disabled** pending separate authority; **no B1 activate** |
| Peek budget | **Max 2** Long Fold A+B Precision peeks after mandatory Step 0 Phase-1 baseline |
| Friction / floors / H | **Frozen** — `c*=20` / archive 30; floors 60/50/30; `H=6`; multiples unchanged |
| Build posture | **DRAFT — ready for dual-judge** — EV-net hard-stop left Top-K=5 unchanged ([stop-memo](../archive/horizon-ev-net-rebuild-stop-memo.md)) |

**One-line:** Ask whether Precision 1m entry-timing / exit-management can bridge the measured ~12–19 bps Long Horizon H4 deficit on a frozen Top-K registry — or stop and lock that execution cannot salvage an underwater Horizon book.

**Hold note:** EV-net rebuild STOP @ 0/3 left production Top-K=5 unchanged — Precision Step 0 may dual-judge against that registry.

**Gemini source quote (path-density STOP):**

> Tier 3 **Precision 1m entry-timing / exit-management** — can execution bridge the ~12–19 bps Horizon deficit

---

## Dual-judge scores (charter design) — pending

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | — | — | *pending* |
| Scope / freeze | — | — | *pending* |
| Tier ownership / anti-confounding | — | — | *pending* |
| Peek budget / hard-stop | — | — | *pending* |
| Gate design (P1/P2/P3 bridge) | — | — | *pending* |
| Reject hardness | — | — | *pending* |
| Overall | — | — | **DRAFT → dual-judge** |

**Owner intent for judges (non-binding until scored):**

- This is an **explicit falsification** of the Precision-bridge hypothesis, not a soft reopen of WS2 knob-chasing.
- Prior “Precision ≠ Horizon bailout” language stays as **anti-claim discipline** (no Horizon-path PASS / cascade-ready from Precision alone). The charter **authorizes measurement** of absolute P3 on a Long H5-cleared sleeve.
- Prefer Claude’s historical caution: juice a viable book; do not launder Horizon failure into Precision success language.

---

## Authority from prior STOPs (do not reopen)

| Ledger | Fact | Implication |
|---|---|---|
| Path-density STOP | Long H5 PASS; H4 **−12 / −19** bps after L1; Gemini → Precision bridge; owner → Claude exit track | Deficit number this charter cites; Gemini residual still open as measurement |
| MFE-decay STOP | E1/E2 hold H5, **collapse** abs TB+1; H4 **−17 / −14**; Precision still blocked | 15m exit-policy alone cannot clear economics |
| TP-floor STOP | Long TP 60→50 no merge; H4 still null | Barrier floor alone cannot clear economics |
| Short architecture STOP | Short H5 not recoverable via tested classes; Short sleeve **disabled**; next = Long-only cascade economics | This charter = Long-only economics measurement at Tier 3; Short out of peek scope |
| WS0/WS1 | Under old `c*=30` + weak registry, Precision could not clear friction (`tb_tp` ~7–12%) | Must **re-measure** under `c*=20` + current Long Top-K (H5 PASS) — do not cite WS1 as final Precision FAIL under today’s locks |

**Deficit lock (cite, do not re-estimate as a gate):** path-density Peek-1 Long H4 @20 = **−12 bps (A) / −19 bps (B)**; cost / MFE companions ≈ **−13…−17**. Charter success language uses **~12–19 bps** as the named residual, not a retuned target.

---

## Tier responsibility lock (hard)

| Tier | Owns | Does **not** own |
|---|---|---|
| **1 Regime** | Sleeve open/close | Stock pick / fill timing |
| **2 Horizon + TB** | Name rank + path EV under **naive** 15m close + frozen geometry (H1–H5 unchanged) | Dumping H5 failure onto Precision; rewriting barriers mid-Precision peek |
| **3 Precision (this charter)** | 1m fill timing, skip selectivity, firing **inherited** TP/SL/timeout on frozen Top-K | Re-ranking; rewriting TB widths / H / floors; feeding Precision fills into Horizon H5; cascade-ready claims |

**Authorized hypothesis:** Precision **may** clear absolute Long fire expectancy (P3) on a sleeve where Horizon **H5 already PASSes**, even while naive H4 is negative.

**Forbidden claims even on PASS:**

- “Horizon-path PASS” from Precision metrics  
- “Cascade-ready” / book PnL without Regime+Horizon+Precision joint gate  
- “Precision recovered Horizon H5” (H5 stays naive-entry)  
- Activating Short / B1 from Long P3 PASS

**Anti-goal:** Using this ledger to silently reopen Horizon features, cost, or Short architecture → **FAIL charter intent**.

---

## Rejected-levers registry (carry-forward — do not remount)

| Lever | Ledger | Outcome |
|---|---|---|
| Path-room · aux-excess · chase demote | Horizon v2 | Demoted / rejected |
| L1 / L2 / L3 | Path-density | No-merge / closed |
| E1 `H_eff` / E2 giveback-exit | MFE-decay | No-merge; H4 flat |
| Long TP 60→50 | TP-floor | No-merge |
| Cost ladder 15/10/25 | Cost | REJECT; `c*=20` locked |
| Short C1 / A2 / B1 | Short ledgers | No-merge / FAIL / inactive |
| WS2 knob grid as first move | WS0/WS1 | Skip until upstream path quality — **this charter starts at Phase-1 baseline, not a grid** |
| Precision fills inside H5 | Eval lock | Forbidden forever |

---

## Carry-forward locks

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors | Long TP **60** / Short TP **50** / SL **30** |
| Vol multiples | Long `2.5/1.0`; Short `2.0/0.9` |
| Primary H | **H=6 / 90m** |
| K | Long **5** / Short **3** (parity with Horizon; P0 fail if pipeline drifts) |
| Horizon features / labels | Frozen production defaults (path-room off; L1 flag-only; aux=0) |
| Horizon H5 entry | **Naive 15m decision-bar close** — never Precision fill |
| TB widths | Frozen at 15m decision bar — Precision **inherits**, does not recompute from 1m |
| Regime | CLOSED |
| Short sleeve | **Disabled / flat** in live/paper cascade; companion report-only here |
| Soft ship floors (H4≥0 / TB+1≥15%/20%) | Still **not** Horizon primary; do not soft-promote via Precision language |

---

## Process locks

| Lock | Rule |
|---|---|
| Dual-judge gate | **Required** before Step 0 — DRAFT until ACCEPT / ACCEPT WITH REVISIONS |
| Step 0 (no peek) | Phase-1 Precision rules baseline on Long Fold A+B under locked `c*=20` — see below |
| Hard stop @ 0 peeks | If Step 0 Long **P0 FAIL**, or min-N thin both folds → **STOP at 0/2** (harness / registry broken — fix infra, not knobs) |
| Peek budget | **Max 2** Long-only Fold A+B; Short peeks = **0**; no meta-label LightGBM peeks this ledger |
| Single-variable | One pre-registered Precision lever per peek; no grid; no pooled Long+Short |
| Sequential | Peek 2 only if peek 1 clears Long **P1 + P2** dual-fold **and** does not regress Step-0 Long P3 point estimate on both folds |
| Multiplicity | **New ledger** — cannot borrow WS0/WS1 arms as gated peeks; may **cite** them as priors only |
| Horizon freeze | No Horizon retrain / relabel / feature / barrier edits inside this charter |
| Stop | Exhaust 2 **or** clean Long bridge PASS → stop-memo; **or** Step 0 hard-stop |

---

## Gates

Uses [precision-tier3-eval-verdict.md](../precision-tier3-eval-verdict.md) metric IDs. Session-block-bootstrap 95% CI. Unsized. Long primary.

| Role | Metric | Rule |
|---|---|---|
| **Precondition** | **P0** | Causality / leakage / fill realism / MIS / circuit / K parity — binary PASS both folds |
| **Primary** | **P1** selectivity | Long CI LB > 0 on Fold A **and** B |
| **Primary / bridge** | **P2** timing lift | Long CI LB > 0 on Fold A **and** B |
| **Primary / absolute** | **P3** cost-netted fire expectancy | Long H5 upstream **already clears** (cost/path-density) → **P3 promoted**: Long CI LB > 0 on Fold A **and** B |
| **Bridge success (charter-specific)** | Long P3 dual-fold PASS **and** Step-0 / peek Long mean `P3` ≥ 0 interpretation vs named −12…−19 deficit | **PASS** only with P1+P2+P3 all dual-fold; report Δ vs naive Top-K H4 companion |
| **Anti-goal** | Claiming Horizon-path PASS / cascade-ready / Short activate from Precision | **FAIL** |
| **Anti-goal** | Feeding Precision fills into H5 or recomputing TB at fill | **FAIL** |
| Report-only | P4–P11, P1r, P2n, P3s (archive-30), Short companion P1–P3, naive Top-K H4 reprint | Never soft-promote alone |
| Min-N | Long ≥ **100** fires **and** ≥ **30** sessions per fold; else `thin` — not gated PASS |

**Short companion:** publish P0–P3 + diagnostics; **do not gate** this charter on Short; do not activate B1.

---

## Step 0 — Phase-1 rules baseline (no peek)

**Required before any peek.** Long primary. Folds A+B. Frozen Horizon Top-K registry + Phase-1 Precision rules ([precision-tier3-verdict.md](../precision-tier3-verdict.md)).

| Publish | Detail |
|---|---|
| Upstream reprint | Long H5 cost/path-density dual-fold PASS cite; Short H5 FAIL / sleeve disabled cite |
| Naive companion | Long Top-K naive H4 @20 reprint (path-density / cost) — the **deficit baseline** |
| P0 | Pass/fail checklist |
| P1 / P2 / P3 | Long point + 95% CI both folds; Short companion |
| P3s | Archive `c*=30` companion (WS0/WS1 comparability) |
| P4 / P5 / P6 / P11 | Exit mix; setup vs fallback; rank bands; `prec_tp` vs `tb_tp` |
| Coverage | Fire rate, n fires, n sessions |

**Step 0 outcomes:**

| Outcome | Action |
|---|---|
| Long P0 FAIL or thin both folds | **STOP @ 0/2** — fix harness / registry |
| Long P1+P2+P3 all dual-fold PASS | **Bridge PASS at 0 peeks** — stop-memo; no knob peeks; still no cascade-ready claim |
| Long P3 FAIL (or P1/P2 FAIL) with P0 OK | Proceed to peek ladder (≤2) **or** stop-memo FAIL if judges lock “baseline-only” |
| Absolute P3 still ≈ −12…−19 with null P2 | Supports “execution does not bridge” — likely STOP without peeks if P1 also null |

---

## Peek ladder (only if Step 0 does not PASS or hard-stop)

Pre-register **before** dual-judge OPEN. One lever per peek. No hyperparam grid.

| ID | Lever | Intent | Forbidden twin |
|---|---|---|---|
| **R1** | `--no-chase` (WS0 prior; CLI already exists) | Cut flip-chase toxicity; lift P1/P3 | Combining with rank-skip in same peek |
| **R2** | Single pre-registered wait / setup tightening (one numeric cut locked at dual-judge) | Improve P2 fill quality without shrinking coverage to thin | Wait×spread×conviction grid |

**Selection rule:** If Step 0 shows chase/fresh-flip toxicity dominates (P9 / P1r) → **R1 first**. If Step 0 P2 ≈ 0 but P1 strong → **R2 first**. If both weak and P11 shows non-+1 overfire mass → **STOP** (upstream path density, not timing) — do not spend peeks.

**Peek PASS:** Long P1+P2+P3 dual-fold CI LB > 0; no P3 regression vs Step 0 on the other fold’s point estimate beyond noise (report CIs).  
**Peek FAIL:** H5-adjacent language, Horizon edits, or Short activate — instant charter FAIL.

---

## Capability sentences (pre-register)

| Path | Sentence |
|---|---|
| **PASS** | Under locked `c*=20` / `H=6` / floors, Phase-1 (or ≤2 peeked) Precision rules clear Long **P1+P2+P3** dual-fold on the frozen Top-K registry — execution **can** monetize past the named ~12–19 bps naive H4 deficit on Long fires. Horizon H5 remains a separate naive-entry gate. Cascade-ready still requires joint Regime+Horizon+Precision ship review. |
| **FAIL** | Precision 1m entry-timing / exit-management **cannot** bridge the measured Long Horizon H4 deficit under locked geometry on this ledger. Confirm prior anti-bailout: juice requires a non-negative (or near) Horizon book; do not hand residual economics to further Precision knobs. Next = Long-only cascade redesign / stop cascade claims — **not** WS2 grid, **not** Short/B1, **not** cost/H reopen. |

---

## Anti-patterns (locked)

1. Scoring Precision with Regime I1/I5 or Horizon H1 IC  
2. Putting Precision fills into Horizon H5 / claiming H5 recovered  
3. Pooling Long+Short acceptance  
4. Soft-promoting cascade-ready / Horizon-path PASS from P3 alone  
5. Recomputing TB widths from 1m post-decision data  
6. Activating B1 / Short sleeve from Long bridge PASS  
7. Remounting L1 / E1 / E2 / TP50 / path-room / cost ladder inside this ledger  
8. Treating WS0/WS1 `c*=30` nets as the Step 0 result under today’s `c*=20` locks  
9. Hyperparam grid on wait / spread / conviction / K on A+B  
10. Meta-label LightGBM as a peek before rules P1/P2 clear  
11. Inventing absolute bps floors instead of CI LB > 0 for P1/P2/P3  
12. Using `size_mult` inside confirmatory gates  

---

## Build order

1. Dual-judge lock this charter (revisions applied).  
2. Confirm Precision eval harness (`src/precision/eval/` + `python -m src.experiments.eval_precision`) implements P0–P3 per eval verdict.  
3. **Step 0** Long A+B Phase-1 baseline + naive H4 companion reprint.  
4. Stop-memo **or** peek R1/R2 per selection rule (max 2).  
5. Stop-memo with PASS/FAIL capability sentence; update path-density / exit / TP-floor “Precision blocked” carry-forwards only via that memo.

**Harness:** `python -m src.experiments.eval_precision --train-period … --test-period … --direction long`  
(Short companion: `--direction short` report-only.)

---

## Out of scope

- Horizon retrain / feature / barrier / cost peeks  
- Regime reopen  
- Short architecture / B1 activate  
- Trailing stops / L2 OBI fills  
- Meta-label ship gates  
- Claiming full-cascade PnL attribution  

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-path-density-stop-memo.md](../archive/horizon-path-density-stop-memo.md) | Gemini Precision-bridge quote; −12/−19 H4 deficit |
| [horizon-exit-mfe-decay-stop-memo.md](../archive/horizon-exit-mfe-decay-stop-memo.md) | Claude track closed; Precision still blocked then |
| [horizon-tp-floor-recalibration-stop-memo.md](../archive/horizon-tp-floor-recalibration-stop-memo.md) | Last Long Tier-2 economics lever closed |
| [horizon-short-architecture-stop-memo.md](../archive/horizon-short-architecture-stop-memo.md) | Points next at Long-only cascade economics |
| [precision-tier3-verdict.md](../precision-tier3-verdict.md) | Rules / features / cascade contract |
| [precision-tier3-eval-verdict.md](../precision-tier3-eval-verdict.md) | P0–P11 harness + P3↔H5 precondition |
| [cascade-tier3-ws01-verdict.md](../archive/cascade-tier3-ws01-verdict.md) | Prior Precision FAIL under weak registry / `c*=30` |
