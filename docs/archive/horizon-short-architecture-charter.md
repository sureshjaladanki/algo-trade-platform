# Horizon Short Architecture — Nifty-100 MIS v1

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Test whether a **pre-registered architecture change** — jointly-trained **two-head**, **true listwise redesign**, or **coarser Short universe** — can clear dual-fold Short H5 under locked `c*=20` / `H=6` / floors after the EV–TB bridge hard-stopped at **0/2**  
**Status:** **CLOSED** — Phase 1 authorized **A2 only**; Peek 1 A2 FAIL Short H5 (and H1/H2 regression); Peek 2 unused; stop-memo written; Short sleeve disabled pending Long-only economics  
**Authority (prior):** EV–TB bridge STOP ([stop-memo](horizon-short-ev-tb-bridge-stop-memo.md)); short-travel / Long density / MFE-decay / TP-floor / cost ledgers **CLOSED**  
**Judges (this charter):** [Claude Sonnet](66f9081c-0ba3-485a-8511-434f7d1dfb44), [Gemini Flash](c53f01a5-2974-4248-93fc-2c704f460823)  
**Date:** 2026-08-14  
**Depends on:** [horizon-short-ev-tb-bridge-stop-memo.md](horizon-short-ev-tb-bridge-stop-memo.md), [horizon-short-ev-tb-bridge-charter.md](horizon-short-ev-tb-bridge-charter.md), [horizon-short-travel-separation-stop-memo.md](horizon-short-travel-separation-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md), [horizon-tier2-v11-short-stop-memo.md](horizon-tier2-v11-short-stop-memo.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [cascade-strategy-overview.md](../cascade-strategy-overview.md)  
**Does not reopen:** Cost ladder · Regime · Precision WS2 / B1 · primary `H=6` · floors / vol multiples · path-room · Short aux-excess · chase demote · S1 / S2 · C1 merge · hybrid λ label blend · O1/P1/E1 holdout peeks · closed O1 `lambdarank` remount · Long L1/E1/E2 / Long TP50 · travel-separation S1a / S-K / C2 · unnamed novel features · A3 K-tuning

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | EV–TB bridge Phase 1 hard-stop @ **0/2**: same-family rank-loss / parsimony / P25 keep **not** authorized. Residual is a **generalization / architecture** gap, not a licensed train/val objective-swap |
| Diagnosis to test | Which architecture class (if any) clears dual-fold Short H5 under **numeric** Phase-1 cuts — without remounting closed levers |
| Single degree of freedom | One pre-registered **architecture** lever per peek (two-head **or** true listwise **or** coarser universe) |
| Tier ownership | **Horizon owns Short path EV + TB bridge via architecture.** Precision blocked; B1 inactive until Short dual-fold H5 |
| Sleeve posture | **Short-only peeks**; Long = companion report-only |
| Peek budget | **Max 2** Short Fold A+B; Phase 1 mandatory; immediate stop on first H5 clear |
| Closed O1 | LightGBM `lambdarank` toward TB exit order — **forbidden remount**; A2 must use a **different** listwise objective |
| Precision | **Out of scope** — no bailout |

**One-line:** Ask whether Short H5 needs a **new model/universe architecture** after objective-swap peeks were refused — or stop and escalate to Long-only cascade economics, not Precision.

---

## Dual-judge scores (charter design) — 2026-08-14

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | 9.5/10 | 8.5/10 | **ACCEPT** — architecture escalate is the right residual after EV–TB 0/2 |
| Scope / freeze | 8.5/10 | 9/10 | **ACCEPT** — reject registry + no O1 remount; close K loophole |
| Phase 1 design | 6.5/10 | 5.5/10 | **REVISE→LOCK** — numeric A1/A2/A3 cuts (qualitative bars rejected) |
| Lever ladder / budget | 7.5/10 | 6/10 | **REVISE→LOCK** — A2 ≠ closed `lambdarank`; A1 w=1.0; A3 mask tie-break; keep max **2** with FAIL scoped to **tested** classes |
| Gate design | 9.5/10 | 9/10 | **ACCEPT** — H5 primary; no H1/H2/H3 regression |
| Capability / FAIL path | 9.5/10 | 8/10 | **REVISE→LOCK** — Long-only economics + Short sleeve disabled on FAIL |
| Overall | ACCEPT WITH REVISIONS | ACCEPT WITH REVISIONS | **ACCEPT WITH REVISIONS → OPEN** |

**Judge one-liners**

- Gemini: Faithful architecture escalate; inject numeric Phase-1 cuts; stop A2→O1 collapse; lock A1 loss weight; close A3 K/mask loopholes.  
- Claude: Right residual and FAIL pivot; Phase-1 bars too qualitative; A2 distinctness must be evidenced; scope FAIL to classes tested; Short sleeve disable on FAIL.

**Revisions applied (MUST_FIX consensus)**

1. **Numeric Phase-1 cuts** for A1 / A2 / A3 (tables below) — no qualitative “low overlap / improves / beats null.”  
2. **A2 ≠ closed O1:** bar-level groups + grades TP=2/TO=1/SL=0 + `eval_at=[3]` + `label_gain=[0,1,3]` + objective **`yetirank` or `approx_ndcg` only** — **forbid** `objective: lambdarank` and binary 0/1 targets.  
3. **A1 loss:** `loss_total = loss_path_EV + w·loss_TB` with **w=1.0** locked; shared trunk = current `SHORT_FEATURES` only (no feature expansion).  
4. **K=3 hard-locked** all peeks; A3 min-N miss → **STOP A3** (no K cut).  
5. **A3 mask rule:** evaluate PIT Nifty-50 **and** train ADV≥P50; if both CLEAR, peek the mask with **higher** val Top−Rest TB=+1 delta (ties → Nifty-50).  
6. Peek budget **kept at 2**; FAIL sentence scoped to **architecture classes tested this ledger**; authorized-but-untested classes named in stop-memo.  
7. On FAIL: Short momentum sleeve stays **disabled / flat** in live or paper cascade pending Long-only economics charter.  
8. Publish reused TB-probe val IC_tb beside A1 overlap (Fold A probe was −0.025 — do not mistake noise for complementarity).

---

## Authority from EV–TB bridge STOP (binding — do not re-litigate)

From [stop-memo](horizon-short-ev-tb-bridge-stop-memo.md) + `logs/horizon_ev_tb_bridge_phase1_ab.txt`:

| Fact | Implication |
|---|---|
| Holdout Short H5 **FAIL/FAIL**; H2 **PASS/PASS** (cost peek-1 reprint) | Residual unchanged |
| Min-N CLEAR (788/921 bars; 125/133 sess); train TB=+1 5556/5568 | Not a sample-size excuse for O1 |
| Val IC_ev **0.19 / 0.29**; val IC_tb **0.06 / 0.16**; Top−Rest TP-share **+3pp** both | Path-EV **already** ranks some TB/travel on val |
| Full TB-ranker (`lambdarank`) val IC_tb **−0.025 / +0.016** vs path-EV **+0.064 / +0.157** | Closed O1 family **loses** to path-EV — do not remount |
| P1: no common N; E1: Top already travels | Not authorized |
| Authorized ladder | **[]** — hard-stop @ 0/2 |

**Capability lock (already written):** single path-EV LightGBM under current Short feature physics is **insufficient for Short H5**. This charter is the pre-registered next step.

**Closed O1 spec (cite for A2 distinctness):** EV–TB O1 = same Short tree family, LightGBM **`objective: lambdarank`** toward StockTB=+1 / TB exit order; path-EV independent. A2 may **not** re-run that contract.

---

## Rejected-levers registry (carry-forward)

| Lever | Ledger | Outcome |
|---|---|---|
| Path-room · aux-excess · chase demote | v2 | Demoted / H5-A FAIL |
| S1 / S2 | v1.1 Short | FAIL / cut would hurt |
| C1 merge · C2 · S1a · S-K | short-travel | No-merge / unauthorized |
| Hybrid λ · unnamed F1 | EV–TB | Rejected / struck |
| O1 `lambdarank` · P1 · E1 | EV–TB Phase 1 | **Not authorized** — closed @ 0/2 |
| Long L1/E1/E2 · Long TP50 · cost · Precision/B1 bailout | cross-charter | Forbidden |

---

## Tier responsibility lock (hard)

| Tier | Owns | Does **not** own |
|---|---|---|
| **1 Regime** | Sleeve open/close | Stock pick / Short architecture |
| **2 Horizon + TB** | Short name rank + path EV **and** TB=+1 via architecture / universe coarsening under frozen geometry | Precision bailout; Regime-inside-T2; barrier/H/cost edits; O1 remount; A3 K-tune |
| **3 Precision** | 1m fill on a **shipped** Short Top-K | Recovering Short H5 / H4; early B1 |

**Anti-goal:** Precision/B1 bridges Short H5 · silent O1 · Regime-inside-Horizon → **FAIL charter intent**.

---

## Carry-forward locks

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors | Long TP **60** / Short TP **50** / SL **30** |
| Vol multiples | Long `2.5/1.0`; Short `2.0/0.9` |
| Primary H | **H=6 / 90m** |
| K | Short **3** — **hard-locked**; never cut under A3 |
| Defaults until merge | Current `SHORT_FEATURES` + path-EV single-head; aux=0; C1 flag-only |
| Long / Regime / Precision | Frozen companion / CLOSED / blocked |

---

## Process locks

| Lock | Rule |
|---|---|
| Dual-judge gate | **DONE** — ACCEPT WITH REVISIONS applied; Phase 1 unlocked |
| Phase 1 | Architecture-class diagnosis — **0 peeks**; numeric cuts only; holdout H5 = frozen reprint |
| Peek budget | **Max 2** Short-only Fold A+B |
| Single-variable | One architecture lever per peek; no grid; no pooled Long+Short |
| Sequential | Peek *n* fails H5 → peek *n+1* may try next **authorized** lever. Any H5 clear without H1/H2/H3 regression → **STOP** (no stacking) |
| Immediate win-stop | Clean Short H5 hold ends the ledger |
| Multiplicity | **New ledger** — cannot borrow EV–TB 0/2 |
| Stop | Exhaust 2 **or** hard-stop @ 0 **or** first H5 clear → stop-memo |

---

## Gates

| Role | Metric | Rule |
|---|---|---|
| **Primary (peek)** | Short H5 (Top−Rest StockTB+1) | Dual-fold CI LB > 0 |
| **Companion** | Short H1/H2/H3 | No regression vs cost peek-1 Short |
| **Anti-goal** | Break H5/H2 for report-only abs TB+1 / H4 | **FAIL** |
| Report-only | Abs TB+1, H4@20, H4arch@30, ADVt lo, Phase-1 architecture diagnostics | Never soft-promote H4≥0 / TB+1≥15% |
| Long companion | Long H5/H1–H4 vs cost peek-1 Long | Report-only |

---

## Phase 1 — Architecture-class diagnosis (0 peeks)

**Required before any peek.** Short primary. Folds A+B.  
Holdout H5/H2/SEP/ADVt = **frozen reprint**. Authorization = **train/val** + numeric cuts below.

| Diagnostic | What to publish |
|---|---|
| **Baseline reprint** | Holdout H5/H2 FAIL/PASS; min-N; ADVt lo (~33%) — cite EV–TB STOP |
| **Complementarity** | Val Top-K Jaccard(path-EV, TB-probe); TB=+1 hit rates in EV-only / TB-only / both / neither; **TB-probe val IC_tb** (expect weak / Fold A negative) |
| **Generalization gap** | Val H5-proxy vs holdout H5 reprint — report-only |
| **Listwise geometry** | Mean eligible names/bar; grade mass TP/TO/SL; path-EV val NDCG@3 vs shuffled null under TP=2/TO=1/SL=0 |
| **Universe stress** | ADVt lo; val TB / H2-proxy by ADV tercile; **both** coarse masks: PIT Nifty-50 (historical membership) **and** train ADV≥P50 — val Top−Rest TB=+1 Δ + H2-proxy |
| **Min-N under masks** | Holdout bars/sessions per mask vs ≥150 / ≥30 |

### Phase 1 decision gate (numeric — locked)

| Authorize | Dual-fold rule (both folds unless noted) |
|---|---|
| **A1** | Val Top-K Jaccard(path-EV, TB-probe) **&lt; 0.40** **and** TB-only Top-K TB=+1 hit rate ≥ EV-only + **2.0 pp** **and** neither head alone clears val H5-proxy (Top−Rest TB=+1 ≤ 0). Publish probe IC_tb. |
| **A2** | Mean eligible names/bar ≥ **50** **and** non-degenerate grade mass (all of TP/TO/SL present) **and** path-EV val NDCG@3 − shuffled null ≥ **+0.030** **and** holdout H5 reprint remains FAIL. |
| **A3** | Chosen mask: val Top−Rest TB=+1 Δ ≥ **+0.020** vs full-universe path-EV baseline **and** val H2-proxy &gt; 0 **and** holdout min-N CLEAR (≥150 bars / ≥30 sess) under that mask. |
| **None** | **STOP @ 0/2** → Long-only cascade economics; Short sleeve disabled |

**A3 mask selection (if A3 authorized):** if exactly one mask CLEARs → that mask; if both CLEAR → peek the mask with **higher** val Top−Rest TB=+1 Δ; tie → **PIT Nifty-50**.

**Hard-stop @ 0 peeks:** no A1/A2/A3 numeric CLEAR → STOP (do not invent peeks).

---

## Pre-registered Short architecture ladder

Spend ≤**2** peeks. **Tie-break if multiple authorize:** **A1 → A2 → A3**.

| ID | Lever | Single variable (locked) | Phase 1 |
|---|---|---|---|
| **A1** | Jointly-trained **two-head** | Shared trunk on current `SHORT_FEATURES` only; path-EV head + TB head; `loss = L_EV + 1.0·L_TB`; **Top-K rank = TB head only**; path-EV diagnostic/report-only. No hybrid λ label; no feature add; no loss-weight grid | A1 numeric CLEAR |
| **A2** | **True listwise redesign** | Bar-level groups (`group` = eligible count at timestamp); grades **TP=2 / TO=1 / SL=0**; optimize NDCG@3 with `label_gain=[0,1,3]`; objective ∈ {**`yetirank`**, **`approx_ndcg`**} only. **Forbid** `lambdarank`, binary targets, ungrouped fits | A2 numeric CLEAR |
| **A3** | **Coarser Short universe** | Exactly one mask from Phase-1 rule (PIT Nifty-50 **or** train ADV≥P50). Geometry / **K=3** unchanged. Min-N miss → STOP A3 | A3 numeric CLEAR |

**Peek plan:**

| Slot | Content |
|---|---|
| Peek 1 | First authorized of A1→A2→A3 |
| Peek 2 | Next authorized **only if** Peek 1 fails H5 |
| On any H5 clear | **STOP** → PASS path |
| Both fail / hard-stop | **STOP** → FAIL path (below) |

**Peek gates:** Short only; baseline = cost peek-1 Short @ `c*=20`; H5 dual-fold CI LB > 0; no H1/H2/H3 regression; merge via stop-memo only; H5 ≠ cascade-ready.

---

## Phase 3 — Capability verdict

| Path | Lock |
|---|---|
| **PASS** | Dual-fold Short H5 + no H1/H2/H3 regression → unlocks **Short Precision remeasure** charter only — **not** cascade-ready |
| **FAIL** | Authorized peeks fail or hard-stop → lock: **Short H5 is not recoverable via the architecture classes tested this ledger** (name any authorized-but-untested class in the stop-memo). Next = **Long-only cascade economics re-check**. Short momentum sleeve stays **disabled / flat** in live/paper cascade. **Not** another Short-only remount, **not** Regime-inside-Horizon, **not** Precision bailout |

---

## Phase 4 — Cascade hygiene (only after Short H5)

- Re-measure Precision Phase 1 Short book only after Short H5 dual-fold clears.  
- Holistic PnL only after Long soft-H3 / Short H5 residuals dual-judge clear — **H5 alone ≠ book net ≥ 0**.

---

## Forbidden moves

- Remounting path-room, aux, chase, S1, S2, C1, C2, S1a, S-K, Long L1/E1/E2, Long TP50  
- Hybrid λ; O1/P1/E1 after EV–TB 0-authorize; A2 as `lambdarank` remount  
- Feature expansion under A1; loss-weight grid; K cut under A3  
- Mid-charter A3 mask switch; inventing a third universe rule  
- Cost / H / floor / Regime-inside-T2 edits  
- Soft-promoting H4≥0 / TB+1≥15%; Precision WS2 / B1 activate  
- Stacking architecture levers; peek 2 after a clean H5 clear  

---

## Build sequence

1. **Dual-judge sign-off** → **DONE** (ACCEPT WITH REVISIONS; locks applied).  
2. **Phase 1** — complementarity / listwise geometry / coarse-mask diagnosis A+B (0 peeks). → **DONE** (A2 only)  
3. **Hard gate** — authorize A1 / A2 / A3 or STOP @ 0/2. → **A2 authorized**; A1/A3 FAIL  
4. **Peek 1** — A2 true listwise (`rank_xendcg`). → **H5 FAIL/FAIL; H1/H2 regress**  
5. **Peek 2** — skipped (no next authorized class).  
6. **Stop-memo** — [horizon-short-architecture-stop-memo.md](horizon-short-architecture-stop-memo.md) — FAIL path: Long-only cascade economics; Short sleeve disabled; Precision / B1 stay blocked. A2 **not** merged into defaults.

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-short-architecture-stop-memo.md](horizon-short-architecture-stop-memo.md) | This ledger CLOSED — A2 FAIL @ 1/2 |
| [horizon-short-ev-tb-bridge-stop-memo.md](horizon-short-ev-tb-bridge-stop-memo.md) | Prior CLOSED — hard-stop @ 0/2 |
| [horizon-short-ev-tb-bridge-charter.md](horizon-short-ev-tb-bridge-charter.md) | O1/P1/E1 refused; capability sentence |
| [horizon-short-travel-separation-stop-memo.md](horizon-short-travel-separation-stop-memo.md) | C1 no-merge; SEP FAIL |
| [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | Short H5 FAIL @ `c*=20` baseline |
| [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md) | Path-EV pivot; aux/path-room rejects |
| [horizon-tier2-v11-short-stop-memo.md](horizon-tier2-v11-short-stop-memo.md) | S1/S2 terminal; B1 inactive |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | Locked geometry |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Tier jobs |
| [precision-tier3-verdict.md](../precision-tier3-verdict.md) | Deferred until Horizon viable |
