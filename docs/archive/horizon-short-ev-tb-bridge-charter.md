# Horizon Short EV–TB Bridge — Nifty-100 MIS v1

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Diagnose Short path-EV vs StockTB=+1 discordance; gated peeks on **TB-aware ranking objective**, **parsimony**, and **Horizon-owned eligibility** under locked `c*=20` / `H=6` / floors — **without** remounting the Short reject list, remounting C1, hybrid/aux-style label blends, or handing the deficit to Precision  
**Status:** **CLOSED** — Phase 1 hard-stop @ **0 / 2**; stop-memo written; Precision / B1 still blocked  
**Authority (prior):** Short travel-separation STOP ([stop-memo](horizon-short-travel-separation-stop-memo.md)); Long density / MFE-decay / TP-floor / cost ledgers **CLOSED**  
**Judges (this charter):** [Claude Sonnet](71463e56-7d57-4c78-8b74-83575db725a3), [Gemini Flash](b7c4761a-8752-4050-b772-bee7cfaeb195)  
**Date:** 2026-08-14  
**Depends on:** [horizon-short-travel-separation-stop-memo.md](horizon-short-travel-separation-stop-memo.md), [horizon-short-travel-separation-charter.md](horizon-short-travel-separation-charter.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md), [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md), [horizon-tier2-v11-short-stop-memo.md](horizon-tier2-v11-short-stop-memo.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [cascade-strategy-overview.md](../cascade-strategy-overview.md)  
**Does not reopen:** Cost ladder · Regime · Precision WS2 / B1 · primary `H=6` · floors / vol multiples · path-room · Short aux-excess · chase demote · S1 / S2 · C1 merge · hybrid λ label blend · Long L1/E1/E2 / Long TP50 · travel-separation S1a / S-K / C2 · unnamed novel features

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | Travel-separation CLOSED: Short paths *can* travel (~1.01× TP) and C1 cleared Abs-MFE ρ (~0.30) but **failed as ranking lever** (H5-A FAIL; H2-A regress). Residual is **EV / XS skill without StockTB=+1 bridge** |
| Diagnosis to test | `horizon_score` ranks path-EV (H2 PASS) but not Top−Rest StockTB=+1 (H5 FAIL). Test **TB-aware ranking loss**, optional **parsimony**, optional **score-quantile eligibility** |
| Single degree of freedom | One pre-registered Short lever per peek. No barrier / cost / H / Regime edits |
| Tier ownership | **Horizon owns Short path EV + TB bridge.** Precision blocked; B1 inactive until Short dual-fold H5 |
| Sleeve posture | **Short-only peeks**; Long = companion report-only |
| Peek budget | **Max 2** Short Fold A+B; Phase 1 mandatory; immediate stop on first H5 clear |
| Novel feature family (F1) | **STRUCK** — no unnamed slot; fresh charter required to name candidates |
| Hybrid / aux-style label blend | **REJECTED** (v2 aux pattern) |
| Precision | **Out of scope** — no bailout |

**One-line:** Ask whether Short can clear dual-fold H5 by fixing **EV–TB objective discordance** (rank-loss ± parsimony/eligibility) under locked geometry — or stop cleanly and escalate to architecture, not Precision.

---

## Dual-judge scores (charter design) — 2026-08-14

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | 9.5/10 | 8/10 | **ACCEPT** — EV–TB bridge is the right residual after short-travel STOP; C1 falsified Abs-MFE→H5 |
| Scope / freeze | 8.5/10 | 9/10 | **ACCEPT** — reject registry + geometry locks hard |
| Phase 1 design | 8.5/10 | 7/10 | **REVISE→LOCK** — train/val-only label–gate; min-N / TB=+1 counts before O1 |
| Lever ladder / budget | 6.5/10 | 7/10 | **REVISE→LOCK** — O1=rank-loss only; strike F1; max **2** peeks; fix sequential rule |
| Gate design | 9/10 | 9/10 | **ACCEPT** — H5 primary; no H1/H2/H3 regression |
| Capability / FAIL path | 9.5/10 | 8/10 | **ACCEPT** — FAIL → architecture, not Precision/Regime/C1 |
| Overall | ACCEPT WITH REVISIONS | ACCEPT WITH REVISIONS | **ACCEPT WITH REVISIONS → OPEN** |

**Judge one-liners**

- Gemini: Strong diagnosis and FAIL→architecture boundary; fix sequential contradiction; lock O1 to rank-loss; kill unnamed F1; cut peeks to 2.  
- Claude: Evidence-true residual; F1 empty slot and O1 “diagnostic head” ambiguity must close; peek budget 3 is too loose given prior Short H5 fails.

**Revisions applied (MUST_FIX consensus)**

1. Label–gate audit = **train/val only** (holdout H5 = frozen baseline reprint only).  
2. **F1 struck** — no unnamed novel-feature lane this charter.  
3. Publish **TB=+1 positive-label counts** + numeric **min-N** (Short ≥150 holdout bars / ≥30 sessions per fold — path-density convention) before authorizing O1.  
4. **O1 locked to ranking-loss** (loss swap or separately trained ranker); path-EV model stays independent diagnostic artifact — **not** jointly-trained multi-head.  
5. Peek budget **3 → 2**; first dual-fold H5 clear **stops immediately** (no further peeks).  
6. Sequential rule fixed: if peek *n* **fails** H5, peek *n+1* may try next **authorized** lever; if any peek **clears** H5 without regression → **STOP** (no stacking).  
7. **Hybrid `(1−λ)·path_EV + λ·TB` rejected** (aux-adjacent).  
8. **E1 locked** to score-quantile keep (train **P25** cutoff); ADV keep not a mid-charter switch.  
9. **P1 locked** to top-N by train/val gain under a StockTB=+1 ranking fit; N∈{8,12,16} chosen by Phase-1 rule before peek (not post-hoc best).

---

## Authority from short-travel STOP (binding — do not re-litigate)

| Fact | Implication |
|---|---|
| Short SEP FAIL; Abs Top MFE ~50.4 bps ≈ **1.01×** Short TP | Paths reach economic zone; ranking does not concentrate travelers |
| Anti-selection / rank-tier did **not** authorize S1a / S-K | Do not remount |
| C1 ρ ≈ **0.30 / 0.32** vs Abs MFE; S1b H5-A FAIL + H2-A regress | **Travel feature ≠ H5 lever** — C1 flag-only |
| Cost @ `c*=20`: Short H5 **FAIL/FAIL**; H2 **PASS/PASS**; H4 −13/−16; TB+1 ~13% | XS / path skill without TB bridge |

**Residual lock:** score ranks EV-ish mass without Top−Rest TB=+1 separation.

---

## Rejected-levers registry (carry-forward)

| Lever | Ledger | Outcome |
|---|---|---|
| Path-room | v2 peek 2 | Demoted |
| Short aux-excess `w=0.5` | v2 peek 4 | H5-A PASS→FAIL |
| Short `stock_r_15` demote | v2 peek 5 | Worse H5-A |
| S1 / S2 | v1.1 Short | FAIL / cut would hurt |
| C1 merge · C2 · S1a · S-K | short-travel | No-merge / unauthorized |
| Hybrid λ path_EV+TB | this charter | **REJECTED** (aux-adjacent) |
| Unnamed F1 novel feature | this charter | **STRUCK** |
| Long L1/E1/E2 · Long TP50 · cost ladder · Precision/B1 bailout | cross-charter | Forbidden |

---

## Tier responsibility lock (hard)

| Tier | Owns | Does **not** own |
|---|---|---|
| **1 Regime** | Sleeve open/close | Stock pick / Short TB bridge |
| **2 Horizon + TB** | Short name rank + path EV **and** TB=+1 separation under frozen geometry | Precision bailout; Regime re-checks inside T2; silent barrier/H/cost edits |
| **3 Precision** | 1m fill on a **shipped** Short Top-K | Recovering Short H5 / H4; early B1 |

**Anti-goal:** Precision/B1 bridges Short H5 · Abs-MFE feature remount after C1 · hybrid/aux label blend → **FAIL charter intent**.

---

## Carry-forward locks

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors | Long TP **60** / Short TP **50** / SL **30** |
| Vol multiples | Long `2.5/1.0`; Short `2.0/0.9` |
| Primary H | **H=6 / 90m** |
| K | Short **3** (frozen) |
| Defaults | Current `SHORT_FEATURES` + path-EV label; aux=0; C1 flag-only |
| Long / Regime / Precision | Frozen companion / CLOSED / blocked |

---

## Process locks

| Lock | Rule |
|---|---|
| Dual-judge gate | **DONE** — ACCEPT WITH REVISIONS applied; Phase 1 unlocked |
| Phase 1 | Diagnosis only — **0 peeks**; train/val authorize; holdout H5 = baseline reprint only |
| Peek budget | **Max 2** Short-only Fold A+B |
| Single-variable | One lever per peek; no grid; no pooled Long+Short |
| Sequential (fixed) | Peeks evaluate **alternative** Phase-1-authorized hypotheses. If peek *n* **fails** H5, peek *n+1* may try next authorized lever (≤ budget). If **any** peek clears Short H5 dual-fold **without** H1/H2/H3 regression → **STOP immediately** (no stacking / no margin-chasing) |
| Immediate win-stop | Clean Short H5 hold ends the ledger even if budget remains |
| Multiplicity | **New ledger** — cannot borrow short-travel’s closed residual peek |
| Abs-MFE ρ / full `SHORT_FEATURES` ρ fishing | **Not** peek authorization / **forbidden** |
| Stop | Exhaust 2 **or** hard-stop @ 0 **or** first H5 clear → stop-memo |

---

## Gates

| Role | Metric | Rule |
|---|---|---|
| **Primary (peek)** | Short H5 (Top−Rest StockTB+1) | Dual-fold CI LB > 0 |
| **Companion** | Short H1/H2/H3 | No regression vs cost peek-1 Short (weight heavily — O1 optimizes toward TB order) |
| **Anti-goal** | Break H5/H2 for report-only abs TB+1 / H4 | **FAIL** |
| Report-only | Abs Top-K TB+1, H4 @20, H4arch @30, ADVt lo, Phase-1 discordance / keep-rate | Never soft-promote H4≥0 / TB+1≥15% |
| Long companion | Long H5/H1–H4 vs cost peek-1 Long | Report-only; must match cost baseline shape (H5 PASS/PASS) |

---

## Phase 1 — Diagnosis (0 peeks)

**Required before any peek.** Short primary. Long companion publish-only. Folds A+B.

| Diagnostic | What to publish |
|---|---|
| **Label–gate audit (train/val only)** | Top-K vs Rest joint: path-EV, Abs MFE, exit reason (TP/SL/TO), TB=+1; Spearman(score, path-EV) vs Spearman(score, TB=+1) on eligible Short **train/val** panel; path-EV among TB=+1 vs non-hit; **TB=+1 positive counts** per fold |
| **Min-N gate** | Short ≥**150** holdout bars / ≥**30** sessions per fold (path-density convention) — required before O1 authorize |
| **Travel reconfirm** | SEP / Top−Rest Abs MFE / time-to-TP — **publish-only**; cite short-travel STOP; do **not** reopen S1a/S-K/C1 |
| **Feature forensic (train/val)** | Gain + leave-one-family on val path-EV IC **and** val Spearman(·, TB=+1). Families: RS / anti-extension / structure / clock-liquidity. **No merge** |
| **Parsimony stress (diagnostic)** | N∈{8,12,16} under TB-oriented gain (StockTB=+1 ranking fit on train/val) **and** path-EV IC/gain — compare; promote nothing here |
| **Calibration note** | Whether isotonic on path-EV preserves TB rank order on val (report) |
| **ADVt lo (Phase 1)** | Top-K ADVt lo share on baseline Short (cost ~33%) — publish early |

### Phase 1 decision gate (pre-registered)

| If Phase 1 shows | Authorize |
|---|---|
| Score ranks path-EV but **not** TB=+1 / TP-share **and** min-N + TB=+1 counts clear | **O1** (default expected) |
| Pre-registered S* (TB-oriented top-N rule) improves val TB-rank without collapsing val H2 proxy | **P1** |
| Top ≈ Rest on travel **and** exit mix → keep-rate problem | **E1** |
| None / only reject remounts look attractive | **STOP @ 0/2** → architecture escalate |

**Hard-stop @ 0 peeks:** no EV–TB discordance **and** no TB-oriented parsimony signal **and** no eligibility pattern → STOP.

---

## Pre-registered Short lever ladder

Spend ≤**2** peeks. **Tie-break if multiple authorize:** **O1 → P1 → E1**. **F1 = STRUCK.**

| ID | Lever | Single variable | Usable only if Phase 1 shows |
|---|---|---|---|
| **O1** | TB-aware **ranking loss** | LightGBM pairwise/listwise (e.g. lambdarank) toward StockTB=+1 (or TB exit order). **Same single-output ranker family** — loss swap or separately trained ranker. Path-EV GBM remains **independent diagnostic** (not jointly multi-head). **No hybrid λ blend.** | EV–TB discordance + min-N |
| **P1** | Parsimony subset | Top-N features by train/val **gain under StockTB=+1 ranking fit**; N fixed ∈{8,12,16} by Phase-1 rule before peek | Val TB-rank improves without H2-proxy collapse |
| **E1** | Score-quantile keep | Exclude bottom **25%** of model scores using **train P25** cutoff (frozen before peek). **Not** ADV keep, bounce P90, unfinished-downside, or C2 | Keep-rate / exit-mix pattern |
| **F1** | Novel feature | — | **STRUCK this charter** |

**Peek plan (locked):**

| Slot | Content |
|---|---|
| Peek 1 | **O1** if authorized; else first authorized of P1/E1 |
| Peek 2 | Next authorized of P1/E1 **only if** Peek 1 fails H5 **and** Phase 1 authorized it |
| On any H5 clear | **STOP** → stop-memo (PASS path) |
| Both fail / hard-stop | **STOP** → architecture charter (FAIL path) |

**Peek gates:**

| Item | Lock |
|---|---|
| Sleeve | Short only |
| Baseline | Cost peek-1 Short @ `c*=20` |
| Gate | Short H5 dual-fold CI LB > 0; no Short H1/H2/H3 regression |
| Report-only | Abs TB+1, H4@20, H4arch@30, ADVt, keep-rate / N, discordance deltas |
| Merge | Only via stop-memo + dual-judge; default **off** |
| Ship language | H5 alone ≠ B1-ready / cascade-ready / book net ≥ 0 |

---

## Phase 3 — Capability verdict

| Path | Lock |
|---|---|
| **PASS** | Dual-fold Short H5 + no H1/H2/H3 regression → unlocks **Short Precision remeasure** charter only — **not** cascade-ready; H4 still diagnostic |
| **FAIL** | O1 + (authorized) P1/E1 fail or hard-stop → lock: **single path-EV LightGBM under current Short feature physics is insufficient for Short H5**. Next = **architecture** charter (two-head / true listwise redesign / coarser Short universe) — **not** Regime-inside-Horizon, **not** Precision bailout, **not** C1 merge |

**O1 vs architecture:** O1 = same LightGBM ranker family with ranking loss. Jointly-trained two-head / LambdaMART-scale redesign / universe coarsening = **new charter**.

**Forward pointer (non-binding):** if a later architecture charter also fails Short H5, escalate includes **Long-only cascade economics re-check** rather than open-ended Short-only remounts.

---

## Phase 4 — Cascade hygiene (only after Short H5)

- Re-measure Precision Phase 1 Short book only after Short H5 dual-fold clears.  
- Holistic PnL only after Long soft-H3 / Short H5 residuals dual-judge clear — **H5 alone ≠ book net ≥ 0**.

---

## Forbidden moves

- Remounting path-room, aux-excess, chase demote, S1, S2, C1 merge, C2, S1a, S-K, Long L1/E1/E2, Long TP50  
- Hybrid λ path_EV+TB blend; jointly-trained multi-head under O1  
- Unnamed F1 / Abs-MFE ρ authorization / full `SHORT_FEATURES` holdout ρ fishing  
- Holdout family ΔH5 as lever menu  
- Cost shopping / cutting `H=6` / floor edits / Regime re-checks inside T2  
- Switching E1 to ADV keep after Phase 1; inventing bounce/unfinished-downside screens  
- Hyperparam grid on A+B; Fold C locks; pooled Long+Short  
- Soft-promoting H4≥0 / TB+1≥15%; activating Precision WS2 / B1  
- Spending peek 2 after a clean H5 clear; stacking levers  

---

## Build sequence

1. **Dual-judge sign-off** → **DONE** (ACCEPT WITH REVISIONS; locks applied).  
2. **Phase 1** — label–gate / forensic / parsimony / ADVt diagnosis A+B (0 peeks). → **DONE**  
3. **Hard gate** — authorize O1 / P1 / E1 or STOP @ 0/2. → **STOP @ 0/2** (none authorized)  
4. **Peek 1** — skipped.  
5. **Peek 2** — skipped.  
6. **Stop-memo** — [horizon-short-ev-tb-bridge-stop-memo.md](horizon-short-ev-tb-bridge-stop-memo.md) — FAIL path: architecture; Precision / B1 stay blocked. Diagnostic harness **reverted** (no code merge).

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-short-ev-tb-bridge-stop-memo.md](horizon-short-ev-tb-bridge-stop-memo.md) | This ledger CLOSED — hard-stop @ 0/2 |
| [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | Short H5 FAIL @ `c*=20` baseline |
| [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md) | Short SEP FAIL; min-N convention |
| [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md) | Path-EV pivot; aux/path-room rejects |
| [horizon-tier2-v11-short-stop-memo.md](horizon-tier2-v11-short-stop-memo.md) | S1/S2 terminal; B1 inactive |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | Locked geometry |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Tier jobs |
| [precision-tier3-verdict.md](../precision-tier3-verdict.md) | Deferred until Horizon viable |
