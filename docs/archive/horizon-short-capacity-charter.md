# Horizon Short Capacity / Regularization — Nifty-100 MIS v1

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Test whether **pre-registered Short LightGBM capacity / regularization** changes — under locked `SHORT_FEATURES`, path-EV label, `c*=20` / `H=6` / floors / K=3 — clear dual-fold Short H5, or whether **more** regularization (not less) is what the TB bridge needs  
**Status:** **CLOSED — STOP @ 0/2** ([stop-memo](horizon-short-capacity-stop-memo.md)); dual-judge ACCEPT WITH REVISIONS landed; Phase 1 authorized **[]**  
**Authority (prior):** Short architecture STOP ([stop-memo](horizon-short-architecture-stop-memo.md)) closed architecture classes and pointed **Long-only cascade economics** as next cascade residual. This charter is an **owner reopen** of a **distinct untested lever class**: v1 Short hyperparam starting points were never dual-judge peeks after measured post-filter `TREND_DOWN` mass (see [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) production constraint #5). It does **not** remount architecture / EV–TB / travel / feature reject lists.  
**Judges (this charter):** Gemini Flash · Claude Sonnet (2026-08-15)  
**Date:** 2026-08-14 · dual-judge 2026-08-15 · Phase 1 STOP 2026-08-15  
**Depends on:** [horizon-short-architecture-stop-memo.md](horizon-short-architecture-stop-memo.md), [horizon-short-ev-tb-bridge-stop-memo.md](horizon-short-ev-tb-bridge-stop-memo.md), [horizon-short-travel-separation-stop-memo.md](horizon-short-travel-separation-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-tier2-verdict.md](../horizon-tier2-verdict.md), [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md), [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [cascade-strategy-overview.md](../cascade-strategy-overview.md)  
**Does not reopen:** Cost ladder · Regime · Precision WS2 / B1 · primary `H=6` · floors / vol multiples · path-room · Short aux-excess · chase demote · S1 / S2 · C1 merge · hybrid λ · O1 `lambdarank` · A1/A2/A3 architecture remount · Long L1/E1/E2 / Long TP50 · unnamed novel features · free hyperparam grid on A+B · K retune

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | Architecture FAIL path disabled Short pending Long-only economics, but left an **orthogonal** residual: Short `min_child_samples=400` vs Long `300` on a sleeve that is already ~½ Long mass — v1 called this out and deferred retune after measuring counts; O8 forbade A+B grids, so capacity was **never** a dual-judge peek |
| Diagnosis to test | Either (a) Short is **capacity-starved** (underfit) under tighter-than-Long leaf floors, so H2 PASS / H5 FAIL is partly a capacity artifact; or (b) **regularization helps H5** — easing capacity lifts H1/H2 noise without Top−Rest TB=+1, and/or tightening further is the only authorized direction |
| Single degree of freedom | **Short LightGBM capacity / regularization only** — one pre-registered param slice per peek. Features / label / geometry / K frozen |
| Tier ownership | **Horizon owns Short path EV + TB bridge via capacity.** Precision blocked; B1 inactive until Short dual-fold H5 |
| Sleeve posture | **Short-only peeks**; Long = companion report-only (no Long param spend) |
| Peek budget | **Max 2** Short Fold A+B; Phase 1 mandatory; immediate stop on first H5 clear |
| Vs architecture STOP | Fresh ledger — **cannot** borrow architecture 1/2. Short sleeve may be **temporarily re-enabled for this charter’s peeks only**; live/paper stays flat until merge |
| Precision | **Out of scope** — no bailout |
| Build posture | **CLOSED** — Phase 1 hard-stop @ 0/2; see [stop-memo](horizon-short-capacity-stop-memo.md) |

**One-line:** Ask whether Short H5 needs **more capacity** (underfit) or **more regularization** under locked physics — or stop and return to Long-only cascade economics without another Short remount.

---

## Dual-judge scores (charter design) — 2026-08-15

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | 9/10 | 8.5/10 | **8.5** |
| Scope / freeze | 10/10 | 9/10 | **9.5** |
| Phase 1 design | 9/10 | 7.5/10 | **8** — Claude MUST_FIX on val-cut noise |
| Lever ladder / budget | 9/10 | 7/10 | **8** — ladder narrower than full Short-vs-Long capacity gap |
| Gate design | 9/10 | 8/10 | **8.5** |
| Capability / FAIL path | 9/10 | 8.5/10 | **8.5** |
| Overall | 9/10 | 8/10 | **8.5 → ACCEPT WITH REVISIONS** |

**Judge one-liners**

- Gemini: Mathematically sound, highly disciplined charter that validly isolates an un-peeked capacity residual from v1 constraint #5 under strict 0-peek Phase 1 numeric authorization.  
- Claude: A well-scoped, properly falsification-oriented reopen of a genuinely untested lever, weakened only by unbounded-noise Phase‑1 val cuts and a capacity ladder narrower than its own stated diagnosis.

**Owner critical Q consensus (judges)**

| Q | Consensus | Lock |
|---|---|---|
| Q1 — Could Short hyperparams underfit? | **Plausible / untested** (Gemini YES·HIGH; Claude CONDITIONAL·MED) | Phase 1 must separate EV-IC underfit vs TB-bridge underfit; val H5-proxy already +3.3/+3.5 pp under baseline → not gross EV underfit |
| Q2 — Could underfitting be from features? | **NO — CLOSED remount** (both HIGH) | `SHORT_FEATURES` stay frozen; travel / EV–TB / architecture already closed feature-adjacent levers |
| Q3 — Raise `K_Short` 3→5? | **NO** (both HIGH) | Hard-lock K=3; raising K dilutes Top−Rest, confounds capacity DoF, soft-gates abs TB+1 / fills (Precision concern) |

**MUST_FIX (land before Phase 1)**

1. Add a **minimum val-sample-size floor** and a **robustness check** (bootstrap CI or two-seed stability) to Phase 1 U1/U2/R1 numeric cuts before they authorize a peek — bare +0.010 / +0.015 point deltas on a single thin `TREND_DOWN` val split can mis-spend the only 2 peeks.

**NICE_TO_HAVE (optional)**

1. Report-only val H5-proxy under `max_depth` / `n_estimators` counterfactuals (no peek spend) so FAIL capability sentence can note whether those axes remain live.  
2. Worked example of U2 conditional-authorize branch.  
3. State whether Phase 1 last-fold val is the same split later used for isotonic calibration.  
4. Log leaf utilization under mcs=400 vs 300; confirm `n_train_Short` = post-filter `TREND_DOWN` bars on matching calendar windows.

**Design intent for judges (locked — satisfied)**

1. **No free grid on holdout** — Phase 1 train/val authorize only; ≤2 peeks; one param-slice per peek.  
2. **Both hypotheses pre-registered** — underfit ease **and** tighten-reg must be falsifiable; do not only ease.  
3. **Numeric Phase 1 cuts** — no qualitative “looks underfit.”  
4. **Relative capacity metric** — compare Short leaf floor to Short train mass vs Long leaf floor to Long train mass (same fold calendar).  
5. **FAIL path** returns to architecture STOP posture (Long-only economics; Short flat) — not Precision / feature remount.

---

## Why this is allowed after architecture STOP

| Architecture STOP lock | This charter’s answer |
|---|---|
| Short H5 not recoverable via **architecture classes tested** | Capacity / regularization was **not** an architecture class; A1/A2/A3 frozen out |
| Next = Long-only cascade economics | Still the **cascade** default if this ledger FAILs; this is an optional **owner reopen** of v1 constraint #5 |
| Short sleeve disabled / flat | Holds for live/paper; peeks are **eval-only** unless stop-memo merges |
| No another Short-only remount of closed levers | Features / objective family / universe / K / floors stay frozen — **params only** |

**v1 authority (binding cite):** [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) Short table locks `min_child_samples=400` as “**Higher than Long relative to dataset size**” and production constraint #5: *“Retune Short `min_child_samples` / `num_leaves` after measuring actual post-filter `TREND_DOWN` bar counts.”* That measurement→retune never became a gated A+B peek under path-EV + `c*=20`.

---

## Authority from prior Short ledgers (do not re-litigate)

| Fact | Implication |
|---|---|
| Holdout Short H5 **FAIL/FAIL**; H2 **PASS/PASS** @ `c*=20` | Residual unchanged — capacity peeks must beat this reprint |
| Travel C1 ρ~0.30 cleared; H5/H2 failed as ranking lever | **Not** a feature charter |
| EV–TB Phase 1 authorized **[]** @ 0/2 | **Not** an objective-swap charter |
| Architecture A2 FAIL; A1/A3 not authorized | **Not** an architecture remount |
| Absolute Short Top-K TB+1 ~13% > Long ~9–13% often | Absolute density ≠ Top−Rest H5; do not soft-gate on abs TB+1 |

**Capability sentence inherited:** single path-EV LightGBM under **current** Short feature physics + **current** `SHORT_PARAMS` is insufficient for Short H5. This charter asks whether **params alone** change that sentence.

---

## Rejected-levers registry (carry-forward)

| Lever | Ledger | Outcome |
|---|---|---|
| Path-room · aux-excess · chase demote | v2 | Demoted / H5-A FAIL |
| S1 / S2 | v1.1 Short | FAIL / cut would hurt |
| C1 merge · C2 · S1a · S-K | short-travel | No-merge / unauthorized |
| Hybrid λ · F1 · O1/P1/E1 | EV–TB | Rejected / struck / 0-authorize |
| A1 / A2 / A3 | architecture | A2 FAIL; A1/A3 not authorized |
| Long L1/E1/E2 · Long TP50 · cost · Precision/B1 | cross-charter | Forbidden |
| Free hyperparam / K grid on A+B | O8 / eval anti-pattern #5 | **Forbidden** — this charter’s discrete ladder is the only licensed exception |

---

## Tier responsibility lock (hard)

| Tier | Owns | Does **not** own |
|---|---|---|
| **1 Regime** | Sleeve open/close | Stock pick / Short capacity |
| **2 Horizon + TB** | Short name rank + path EV **and** TB=+1 via **capacity / reg** under frozen geometry | Precision bailout; feature/objective remount; floor/H/cost edits |
| **3 Precision** | 1m fill on a **shipped** Short Top-K | Recovering Short H5 via B1 |

**Anti-goal:** Precision/B1 bridges Short H5 · silent feature add · holdout param fishing → **FAIL charter intent**.

---

## Carry-forward locks

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors | Long TP **60** / Short TP **50** / SL **30** |
| Vol multiples | Long `2.5/1.0`; Short `2.0/0.9` |
| Primary H | **H=6 / 90m** |
| K | Short **3** — **hard-locked** |
| Features / label | Current `SHORT_FEATURES` + path-EV; aux=0; C1 flag-only |
| Baseline params | Current `SHORT_PARAMS` (`min_child_samples=400`, `max_depth=3`, `num_leaves=15`, `n_estimators=600`, …) |
| Long / Regime / Precision | Frozen companion / CLOSED / blocked |

---

## Process locks

| Lock | Rule |
|---|---|
| Dual-judge gate | **Required** before Phase 1 |
| Phase 1 | Capacity diagnosis — **0 peeks**; train/val + numeric cuts; holdout H5 = frozen reprint |
| Peek budget | **Max 2** Short-only Fold A+B |
| Single-variable | One pre-registered **param slice** per peek (may touch ≤3 named keys if the slice is locked as one atomic bundle) |
| Sequential | Peek *n* fails H5 → peek *n+1* may try next **authorized** lever. Any H5 clear without H1/H2/H3 regression → **STOP** (no stacking) |
| Immediate win-stop | Clean Short H5 hold ends the ledger |
| Multiplicity | **New ledger** — cannot borrow architecture / EV–TB peek slots |
| Stop | Exhaust 2 **or** hard-stop @ 0 **or** first H5 clear → stop-memo |

---

## Gates

| Role | Metric | Rule |
|---|---|---|
| **Primary (peek)** | Short H5 (Top−Rest StockTB+1) | Dual-fold CI LB > 0 |
| **Companion** | Short H1/H2/H3 | No regression vs cost peek-1 Short |
| **Anti-goal** | Break H5/H2 for report-only abs TB+1 / H4 | **FAIL** |
| Report-only | Abs TB+1, H4@20, H4arch@30, ADVt lo, Phase-1 capacity diagnostics | Never soft-promote H4≥0 / TB+1≥15% |
| Long companion | Long H5/H1–H4 vs cost peek-1 Long | Report-only |

---

## Phase 1 — Capacity diagnosis (0 peeks)

**Required before any peek.** Short primary. Folds A+B.  
Holdout H5/H2/ADVt = **frozen reprint** (cost peek-1 / architecture Phase 1). Authorization = **last-fold train/val only**.

### Publish (both folds)

| Diagnostic | What to publish |
|---|---|
| **Baseline reprint** | Holdout Short H5 FAIL / H2 PASS; min-N; ADVt lo |
| **Sample mass** | Train bars Short vs Long (same calendar windows); ratio `n_S / n_L`; sessions / episodes via `sleeve_sample_diagnostics` |
| **Relative leaf floor** | `ρ_leaf = min_child_samples / n_train_bars` for Short @400 and Long @300; also Short@400 vs counterfactual Short@300 and Short@200 |
| **Fit gap** | Val Spearman(score, path-EV) − train Spearman (same last-fold fit); large positive gap → overfit signal; near-zero + weak val H5-proxy → underfit-compatible |
| **Val H5-proxy** | Top−Rest StockTB=+1 on val under baseline `SHORT_PARAMS` |
| **Capacity counterfactuals (val only)** | Refit path-EV on train with **U-slice** and **R-slice** below; publish val H5-proxy + val H2-proxy + fit gap — **no holdout peek** |
| **Leaf occupancy (report)** | Mean / P10 samples per leaf on train under baseline (if cheap to extract; else skip with note) |

### Phase 1 decision gate (numeric — locked)

Define per fold:

- `ratio = n_train_Short / n_train_Long`
- `rel400 = 400 / n_train_Short`
- `rel300_L = 300 / n_train_Long`
- `gap = IC_ev_train − IC_ev_val` (Spearman; **positive** ⇒ train ≫ val = overfit-shaped)
- `H5v0` = val Top−Rest TB=+1 under baseline params  
- `H5v_U` = val Top−Rest TB=+1 under **U1** params (below)  
- `H5v_R` = val Top−Rest TB=+1 under **R1** params (below)  
- `H2v_*` = val H2-proxy (Top−Rest raw excess) under that fit

| Authorize | Dual-fold rule |
|---|---|
| **U1** (ease toward Long absolute) | `ratio ≤ 0.60` **both** folds **and** `rel400 ≥ 1.25 × rel300_L` both **and** `gap ≤ 0.05` both **and** `H5v_U − H5v0 ≥ +0.010` both **and** `H2v_U > 0` both |
| **U2** (scale leaf floor to ~½ mass) | U1 numeric CLEAR **or** (`ratio ≤ 0.55` both **and** `H5v` under U2 params − `H5v0 ≥ +0.015` both **and** `H2v_U2 > 0` both). U2 may peek **only if** U1 authorized **or** U1 fails authorization solely on the `+0.010` cut while U2 clears `+0.015` |
| **R1** (tighten reg) | `gap ≥ 0.08` both **or** (`H5v_R − H5v0 ≥ +0.010` both **and** `H2v_R > 0` both). R1 is the **“regularization helps H5”** lane |
| **None** | **STOP @ 0/2** → restore architecture FAIL posture (Long-only economics; Short flat) |

**Hard-stop @ 0 peeks:** no U1/U2/R1 CLEAR → STOP (do not invent peeks).

**Tie-break if multiple authorize:** **U1 → U2 → R1** (test underfit before tighten; U2 only after U1 slot rules above).

**MUST_FIX (dual-judge 2026-08-15) — land before Phase 1 authorize:**
- Publish val bars / sessions for the last-fold Short val window; require a pre-registered **min val-N** (floor TBD from Phase 1 sample-mass print; default candidate ≥150 bars / ≥10 sessions mirroring holdout min-N spirit).
- For each `H5v_* − H5v0` cut, require either (a) **bootstrap CI LB > 0** on the val Top−Rest delta, or (b) **two-seed stability** (same sign and Δ ≥ cut under `random_state ∈ {42, 7}`). Point-estimate-only authorize is forbidden.

---

## Pre-registered Short capacity ladder

Spend ≤**2** peeks. Atomic slices (do **not** mix U and R in one peek).

| ID | Hypothesis | Locked param slice (only these keys change) |
|---|---|---|
| **U1** | Underfit — leaf floor too high vs mass | `min_child_samples: 400 → 300` (match Long absolute). All other `SHORT_PARAMS` unchanged |
| **U2** | Underfit — scale to ~½ Long mass | `min_child_samples: 400 → 200`. All other unchanged |
| **R1** | Regularization helps H5 | `min_child_samples: 400 → 500` **and** `reg_lambda: 8.0 → 10.0` (atomic bundle). Depth/leaves/estimators unchanged |

**Peek plan:**

| Slot | Content |
|---|---|
| Peek 1 | First authorized of U1 → U2 → R1 |
| Peek 2 | Next authorized **only if** Peek 1 fails H5 |
| On any H5 clear | **STOP** → PASS path |
| Both fail / hard-stop | **STOP** → FAIL path |

**Peek semantics:** retrain Short path-EV on train with the slice; isotonic on val as today; evaluate holdout A+B under frozen geometry. Long companion unchanged.

**Peek gates:** Short only; baseline = cost peek-1 Short @ `c*=20`; H5 dual-fold CI LB > 0; no H1/H2/H3 regression; merge via stop-memo only; H5 ≠ cascade-ready.

---

## Phase 3 — Capability verdict

| Path | Lock |
|---|---|
| **PASS** | Dual-fold Short H5 + no H1/H2/H3 regression → merge winning slice into `SHORT_PARAMS`; unlocks Short Precision remeasure charter only — **not** cascade-ready |
| **FAIL** | Authorized peeks fail or hard-stop → lock: **Short H5 is not recoverable via the capacity / regularization slices tested this ledger** (name authorized-but-untested IDs). Next = **Long-only cascade economics** (architecture STOP posture). Short stays **disabled / flat**. **Not** feature remount, **not** Precision bailout, **not** another free param grid |

---

## Forbidden moves

- Holdout param fishing / grids beyond U1/U2/R1  
- Changing features, label, K, floors, H, cost, Regime  
- Remounting path-room, aux, chase, S1/S2, C1, architecture A1–A3, O1 `lambdarank`  
- Mixing U-slice and R-slice in one peek  
- Soft-promoting H4≥0 / TB+1≥15%; Precision WS2 / B1 activate  
- Claiming live Short enabled without stop-memo merge  
- Stacking peeks after a clean H5 clear  

---

## Build sequence

1. **Dual-judge sign-off** → **ACCEPT WITH REVISIONS** (2026-08-15); MUST_FIX val-cut robustness landed in harness.  
2. **Phase 1** — **DONE** A+B (`logs/horizon_short_capacity_phase1_ab.txt`); authorized **[]**.  
3. **Hard gate** — **STOP @ 0/2** (U1/U2/R1 all FAIL dual-fold).  
4. **Peek 1 / Peek 2** — unused.  
5. **Stop-memo** — [horizon-short-capacity-stop-memo.md](horizon-short-capacity-stop-memo.md); FAIL → Long-only economics + Short flat; Precision / B1 stay blocked.

**Proposed harness:** `python -m src.experiments.analyze_horizon_short_capacity --folds A,B`  
**Proposed logs:** `logs/horizon_short_capacity_phase1_ab.txt`, `logs/horizon_short_capacity_peek*_ab.txt`

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) | v1 Short params; constraint #5 retune-after-measure |
| [horizon-short-architecture-stop-memo.md](horizon-short-architecture-stop-memo.md) | Prior CLOSED — Short flat; Long-only next |
| [horizon-short-ev-tb-bridge-stop-memo.md](horizon-short-ev-tb-bridge-stop-memo.md) | Objective-swap refused @ 0/2 |
| [horizon-short-travel-separation-stop-memo.md](horizon-short-travel-separation-stop-memo.md) | C1 ≠ H5 lever |
| [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | Short H5 FAIL @ `c*=20` baseline |
| [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md) | H5/H2 gates; anti-pattern #5 |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | Locked geometry |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Tier jobs |
| [precision-execution-bridge-charter.md](precision-execution-bridge-charter.md) | Parallel Long Precision draft — Short stays out until H5 |
