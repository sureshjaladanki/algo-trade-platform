# Horizon Fresh Architecture — Implementation Plan

**Market:** NSE India, Nifty 100, intraday MIS cash  
**Constraint:** Round-trip `c* = 20 bps` — **universe-average** working assumption; row-level `c_eff` is the per-trade hurdle (blueprint §3.1)  
**Authority:** Implements [horizon-fresh-architecture-blueprint.md](horizon-fresh-architecture-blueprint.md) (Revision 3)  
**Status:** M0–M4 COMPLETE · M5 VACATED→INCONCLUSIVE · M5R / M5R-b / M5P / M5P-b COMPLETE ·
**M4R STOP (pool)** · **M4R-b STOP — §14 capability FAIL** · **M6–M8 BLOCKED** (harness hard-exit) ·
**M9 OPEN** (V0 + V1-index + **V1 name dual-fold PASS** 2026-08-17; V2 blocked on option marks)  
**Date:** 2026-08-17 (post-M5 implementation review)

> **Where the programme stands.** Directional Nifty-100 MIS cash is **closed** (M4R-b).
> Stages A/B survive. **M9** is open: [horizon-m9-range-monetization-charter.md](horizon-m9-range-monetization-charter.md).
> Immediate work: **V2** (gross option PnL) once mids/marks exist. Do not remount Top-K / H=6 / 60–30.

---

## Post-M5 implementation review (2026-08-17)

Reviewed code vs blueprint Rev 3 and this plan for **M5R → M9** (M0–M5 already reviewed).
Verdicts below are about *implementation completeness*, not a re-litigation of the
directional FAIL.

| ID | Plan claim | Review | Action this pass |
|---|---|---|---|
| **M5R** | Seven harness defects fixed; K3/K4 re-read | **COMPLETE** with two code bugs | K3 `passed` now requires ECE **and** max-gap ≤ null p95 (was ECE-only). M5 ledger `geometry_argmax` call restored (signature lock had made the M5 harness unrunnable). |
| **M5R-b** | 1m first-hit + symmetric penetration | **COMPLETE** | No change. Dual-touch share + K4 reprint match §9.1. |
| **M5P** | Rolling folds + purge + MDE < c\* | **COMPLETE** with a real purge gap | Purge was **display-only** (`train_end_disp`); `filter_by_period` is year-based and cannot express a 5-day December embargo. `apply_purge_date_filter` now actually holds out those days on Stage B train. |
| **M4R** | Per-rule drift ledger → one sleeve | **STOP stands** | N-bar exhaustion-into-band-edge was listed in Build and **never implemented**. Frozen — do not add a rule after the pool STOP. Per-family heads were never built because no sleeve cleared the selection rule. |
| **M5P-b** | Pooled K5, `c_eff` array, vertical-only, admit-power | **COMPLETE** | `k5_pooled` is unit-tested but was never wired into a live harness (M6 was the intended consumer). Library is correct. |
| **M4R-b** | F1 selector + F2 `c_eff`; both FAIL | **COMPLETE FAIL** with one measurement bug | Disaster stop **dropped** paths with drift < −500 bps instead of realizing the stop — left-tail truncation biased K4 upward. Now clips to `−sl_floor`. Verdict still FAIL (bias was against FAIL). Residual: F2 did not reprint the **full M4R per-rule** ledger on `c_eff` (only the F1 admit set); R2017–R2022 report-only folds were pre-registered and not run. |
| **M6** | K5 on absolute admit | **BLOCKED — scaffold was dangerous** | Harness remounted M5 Stage C (rule one-hots, no directional block, no calibration, invariant geometry sweep) and called `geometry_argmax` with the pre-lock 4-float signature (`TypeError`). Now **hard-exits 3**. Conformal residual LB + sector / daily-loss caps added as library helpers for a future M9 registry. |
| **M7 / M8** | Precision / cutover | **Scaffold only** (correct) | `precision_bridge.py` / `cutover.py` are contracts, not peeks. Leave frozen. |
| **M9** | Range monetization | **OPEN** | V0 + **V1-index dual-fold PASS**; authority V1 blocked on M9-0 |

### Bugs fixed this review

1. **K3 conjunction** — blueprint requires ECE ≤ 3 pp *and* max decile gap ≤ bootstrap null p95. `k3_calibration_ece.passed` previously used ECE only.
2. **M5P purge not applied** — embargo printed, train still included 27–31 Dec of the train year.
3. **M4R-b disaster filter** — `.filter(side_drift > −500 bps)` dropped disasters; now `max(drift, −sl_floor)`.
4. **M5 `geometry_argmax` replay** — M5R signature lock broke the M5 ledger harness; replay uses an explicit invariant callable so the defect remains reproducible.
5. **M6 authority path** — withdrawn. Stage D helpers (conformal residual quantile, sector cap, daily-loss cap) implemented and unit-tested without an authority peek.

### Frozen / do-not-fix (would reopen a closed ledger)

- M4R **N-bar exhaustion** rule — adding it now is a new pool peek after STOP.
- M5R pooled Long head with rule one-hots — M5 ledger; M4R forbade pooling *going forward*, then stopped before a sleeve existed.
- Geometry sweep as a decision — still forbidden until a K4 PASS (none exists).
- M4R-b `fill_null(0)` on missing directional lookbacks — documented thin-sleeve workaround; changing it is a feature change after F1.

### Residual gaps (not authority, still true)

- `k5_pooled` has no production caller until M9 produces an admitted book.
- F2 never reprinted the M4R *per-rule* drift ledger against row-level `c_eff` (preregistration field). Sleeve-level F1/F2 FAIL is still sufficient for §14.
- V1-index dual-fold published (`eval_horizon_m9_v1_index.py`; no `volume_z`)
- K1 within-clock Spearman still lives in the M3 memo, not in `gates.py` (M3 already reviewed; leftover).

> **M5 post-mortem summary.** The M5 STOP was procedurally correct but evidentially void: the Stage C
> harness could not have produced a K4 PASS regardless of whether edge existed. Five implementation
> defects and two gate-definition defects are listed in [M5R](#m5r--stage-c-harness-repair-k3-k4-re-read).
> After repair, K3 essentially passes (fold B 2.38 pp PASS, fold A 4.6 pp marginal with the max gap
> inside its own null band) and K4 reads a fold-consistent **negative** gross return of −5 to −11 bps
> with CI upper bounds of +1 to +11 bps — which rejects the +20 bps that K5 would require. The stop
> verdict therefore survives for the current *Long-continuation* decision set, but the diagnosis is
> different and it points at a specific next hypothesis rather than at product abandonment.
> See [horizon-fresh-m5-stop-memo.md](../archive/horizon-fresh-m5-stop-memo.md) (addendum).

---

## How to read this plan

This is a **milestone map**, not a peek charter.

- Each milestone has a **why**, **what to build**, **cleanup/refactor that travels with it**, **exit criteria**, and a **stop** if the evidence fails.
- Work proceeds **Long-only** until M7. Short is a separate refit, not a parallel ship track.
- Production Regime → Horizon → Precision stays **frozen** until a milestone explicitly cuts over. Until then, fresh code lives beside production under clear module boundaries.
- Cleanup is not a separate “someday” project — it is **scheduled inside each milestone**, so we do not rebuild on top of dead contracts.

---

## The essence (why this plan exists)

At 20 bps round-trip, Horizon’s job is not “rank every 15m bar and emit Top-K.” Its job is:

> **Only cascade signals whose expected net PnL is positive after cost.**

The blueprint’s governing fact is arithmetic, not taste:

\[
\Delta p = \frac{c}{g + s}
\]

Required edge over a random walk depends only on **cost ÷ barrier span**. Production Long 60/30 has span 90 bps → needs ~**22 pp** of edge. A 200/100 geometry needs ~**7 pp**. That is the difference between “almost never works” and “might work if we pick the right days and events.”

### Facts that already support this (do not re-litigate)

| Fact | Source | What it means for the plan |
|---|---|---|
| Unconditional Long eligible \(EV_{net}\) ~**−20…−22 bps** (CI UB ≤ −17) on G1–G3 | [EV-net STOP](../archive/horizon-ev-net-rebuild-stop-memo.md) | Do **not** start with another H/TP/SL grid. Change eligibility, clock, and admit. |
| Mean MFE ~**43–54 bps** with TP hit only ~**9–15%** | Same | Travel exists; conversion does not. Range/opportunity first. |
| Oracle positive-mass ~**27–30%** inside a still-negative pool | Same (report-only) | Selection room exists — but only after a sane pool definition. |
| Long H4 still ~**−12…−19 bps** after path-density / MFE / TP-floor ledgers | Path-density & companions | Relative Top−Rest ≠ absolute economics. |
| Production span is **4.5× cost**; design needs ~**15× cost** | Blueprint §1.2 | Fixed 60/30 + H=6 is the wrong product shape. |
| Driftless pool mean \(EV_{net} = -c\) by construction | Blueprint §10.2 | Never gate a redesign on “unconditional pool > −10 bps.” |

### What we are building instead (four Horizon stages)

```
Regime (keep)
    → A Tradability        where 20 bps is actually achievable
    → B Opportunity        predicted remaining range clears span
    → C Direction + EV     event clock + meta-label + geometry argmax
    → D Absolute admit     conformal EV_net > 0 + book caps
    → Precision            monetize an already-positive book (do not bail it out)
```

Expected trade count of **~1–4 fires/day** across ~88 names is a **success condition**, not a coverage bug.

---

## Non-negotiables

| Lock | Rule |
|---|---|
| Cost | `c* = 20` is the **universe average**; the per-trade hurdle in \(EV_{net}\) is row-level `c_eff` wherever Stage A has run. Flat 20 and archive 30 become stress reprints (blueprint §3.1) |
| Geometry default | **Vertical-only** to MIS flatten for any sleeve whose drift is thin relative to session σ; a tight stop must be justified by measured \(EV_{net}\) improvement, not assumed as risk control (blueprint §1.6) |
| Risk control | Sizing / concurrency / daily-loss caps in Stage D — **not** a tight stop |
| Economics gate | K5 is a **pooled** read across folds plus a fold sign test; per-fold lower bounds are not passable by a 1–4 fires/day book |
| STOP scope | A stop on an **unconditional pool mean** bounds the pool, not the product (blueprint §10.2 generalized) |
| Labels | Prefer **absolute** path − c\* for unhedged cash (not Nifty-excess) until a hedge product exists |
| Vertical | Prefer **MIS flatten**, not fixed H=6, once Stage C geometry is live |
| Gate | **Absolute EV admit** owns economics; Top-K is capacity-only after admit |
| Sleeve | ~~Long-first~~ → **one sleeve at a time, chosen by the drift-sign ledger** (blueprint §7 Rev 2) |
| Precision | Never claim Horizon recovery from Precision P3 |
| Production cutover | Explicit milestone gate — no silent swap of `predict_horizon_gbm` / Top-K registry |
| Gate validity | A gate must be **passable by a correct model** and fed inputs that can carry the effect it tests |
| Power | Every gate publishes its **minimum detectable effect** next to the point estimate |
| Geometry | No geometry sweep before K4 PASS, and none at all with geometry-invariant probabilities |

### Global STOP language

If **K1 / K2** fail → Stage B is broken; stop the redesign.  
If **K4** fails → no directional skill after opportunity gating; stop (do not spend on geometry knobs or Precision).  
If **K5** fails after K4 PASS → skill exists but not enough vs friction; next is product definition change, not Top-K/H=6 remount.

(K1–K5 definitions: blueprint §10.3.)

### Before invoking any STOP (added Rev 2)

A STOP is a claim about the market, so it carries a burden of proof about the harness. Confirm all four:

1. **The gate could have passed.** Compare the threshold to its own null distribution (blueprint §10.4).
2. **The inputs could carry the effect.** A directional gate needs directional features; check univariate association and model split share, not just the presence of a feature list.
3. **The test had power.** Publish the MDE. If the MDE exceeds the effect size the design targets, the reading is **INCONCLUSIVE**, not FAIL.
4. **The pipeline ran as designed.** Confirm every upstream stage the milestone claims to consume is actually wired in, and that no feature is silently degenerate.

Added after the M4R review:

5. **The statistic is the one the architecture named.** A stop on an unconditional pool mean cannot refute a design whose claim is that *selection* creates the edge.
6. **The hurdle is the one the design uses.** If Stage A computes row-level `c_eff`, the gate must use it.
7. **The gate is passable by the intended book**, not only by the model — check the admit count and resulting MDE against the sparsity target.
8. **Required-IC is published next to the drift reading**, so "short of the hurdle" is quantified rather than asserted.

M5 failed items 1–4. M4R passed 1–4 and failed 5–6. Treat this checklist as the price of admission for
the FAIL sentence.

---

## Two tracks that run together

Every milestone below has both:

1. **Build** — new fresh-architecture capability  
2. **Cleanup / refactor** — remove, quarantine, or isolate production contracts that would otherwise poison the new path

### Cleanup principles

- **Do not delete production Horizon until cutover.** Quarantine and stop *depending* on it for fresh work.
- Prefer **new modules** (`src/horizon/fresh/` or clearly named packages) over editing `triple_barrier.py` floors in place mid-experiment.
- Archive CLOSED peek harnesses as **audit-only**; do not keep growing them.
- One concern per module; match [coding conventions](../coding-conventions.md): small pure transforms, fail fast, no speculative config layers.

### Production surface that will eventually move or shrink

| Area today | Problem for fresh arch | Plan posture |
|---|---|---|
| `src/labels/triple_barrier.py` — floors 60/50/30, H=6, Nifty-excess | Wrong span + wrong label for unhedged book | Keep as **production/legacy**; add absolute/MIS-vertical label path beside it |
| `src/horizon/horizon_model.py` — Huber path-EV + Top-K rank | Wrong loss; relative gate | New Stage C model; leave ship model frozen |
| `src/features/horizon_precision.py` — `horizon_rank ≤ K` | Economic gate is relative | New registry builder on absolute admit |
| `src/precision/session.py` — `LONG_TOP_K=5` | Capacity constant mistaken for edge | Keep constant as **post-admit cap** only after cutover |
| `src/horizon/eval/*` peek ledgers (admission, veto, TP-floor, MFE, EV-net, …) | CLOSED science; noise for implementers | Quarantine folder / docs pointers; no new peeks on old book |
| `data/GOLDEN` CSV (~5.4 GB) | Slow walk-forward | Parquet migration early (M0/M1) |
| `(H−L)/close` as spread in Precision | Range proxy, not spread | Corwin–Schultz / Abdi–Ranaldo in Stage A |

---

## Milestone map (at a glance)

| ID | Name | Primary outcome | Hard stop if… |
|---|---|---|---|
| **M0** | Foundation & quarantine | Workspace ready; legacy isolated | Cannot reproduce EV-net / selection-ceiling baselines |
| **M1** | Truth diagnostics | Selection ceiling + spread + absolute-label reprint | Ceiling thin *and* no Stage-B hypothesis left |
| **M2** | Stage A tradability | Deterministic name/session filter | Filter empties universe with no liquidity story |
| **M3** | Stage B range gate | K1 + K2 | K1 or K2 dual-fold FAIL |
| **M4** | Event clock + primary rules | Sparse Long decision set | Events have no oracle mass above ceiling |
| **M5** | Stage C EV + geometry | K3 + K4 | K4 FAIL |
| **M5R** | **Stage C harness repair** | Gates become passable; K3/K4 re-read | K4 UB < c\* on a repaired harness |
| **M5P** | **Validation power** | K4 MDE < c\* before authority peeks | Cannot reach MDE < c\* on available history |
| **M4R** | **Primary-rule redesign** | Per-rule drift ledger → sleeve choice | No rule has fold-consistent drift ≥ c\* |
| **M5P-b** | **Gate repairs** | Pooled K5 + `c_eff` hurdle + admit-count pre-declaration | none (correctness milestone) |
| **M4R-b** | **Two falsifications** | Selector on winning sleeve; row-level `c_eff` reprint | Both FAIL → §14 capability FAIL earned |
| **M9** | **Successor charter** (contingent) | Range-in-options, or futures instrument | V1 incremental-information FAIL |
| **M6** | Stage D admit + book | K5 | K5 FAIL |
| **M7** | Precision on new registry | Monetization measure (not bailout) | P0 broken / thin; or language claims Horizon PASS |
| **M8** | Cutover / Short charter | Production swap **or** explicit no-ship | Only after M6 PASS + review |

Suggested sequence is **strict for M0→M6**. M7 can start scaffolding earlier but must not gate M5/M6.

**Revised sequence after the M5 post-mortem:** M5R → M5P → M4R → M5 re-read → M6. M5R comes first
because until the harness is trustworthy no reading from it can direct anything else. M5P comes before
M4R so the sleeve decision is made with a test that can resolve it.

**Revised again after the M4R review (Rev 3):** … → M4R (STOP, narrowed) → **M5P-b → M4R-b** → either
M5 re-read → M6, or **M9**. M5P-b precedes M4R-b because M4R-b F2 reads K5 economics, and K5 must be
correct before it is cited.

---

## M0 — Foundation & quarantine

### Why

You cannot implement a clean-sheet Horizon on a desk full of CLOSED peeks and a slow CSV store. First make the workspace honest.

### Build

1. Create a **fresh package boundary**, e.g. `src/horizon/fresh/` (or equivalent) with empty `__init__` and a short README pointing at the blueprint.
2. Add a **single friction constant import path** for fresh work (`c*=20` / archive 30) — do not fork cost.
3. Stand up **Parquet (or equivalent) materialization** of `data/GOLDEN` 1m → analysis tables (lazy Polars). Keep CSV as source of truth until validated.
4. Document folds A/B and purge/embargo rules reused from existing purged CV (`GBMHorizonModel` windows stay the validation *spirit*; fresh models get their own trainers later).

### Cleanup / refactor

| Action | Detail |
|---|---|
| Quarantine CLOSED Horizon peek code | Mark `src/horizon/eval/{admission,path_quality_veto,tp_floor,mfe_decay,ev_net_rebuild,short_travel,capacity,architecture,…}` and matching `src/experiments/analyze_horizon_*` / peek scripts as **audit-only** (module docstring + index in this plan or `docs/archive/`) |
| Freeze production cutover | Comment / doc lock: do not change `LONG_TOP_K`, production TB floors, or `predict_horizon_gbm` ship path in M0–M6 |
| Deduplicate doc drift | Ensure `docs/next/` points to blueprint + this plan; EV-net charter remains archived STOP |
| Kill dead experiment churn | No new peeks on production Top-K book under “fresh” naming |

### Exit criteria

- [x] Fresh package exists and is importable (`src/horizon/fresh/`)  
- [x] Parquet (or agreed store) round-trips a smoke symbol with matching row counts vs CSV  
- [x] Quarantine index written (what is audit-only vs live) — `docs/archive/horizon-fresh-quarantine-index.md`  
- [x] Can reprint EV-net Step 0 summary numbers from log or harness without editing production labels (`eval_horizon_fresh_m0_baseline.py` → audit harness) 

### Stop

Cannot establish a reproducible baseline environment → fix infra before any model work.

---

## M1 — Truth diagnostics (no model ship)

### Why

The blueprint’s highest-value afternoon is the **selection-ceiling** diagnostic: oracle top-decile \(EV_{net}\) on a defined pool. That tells you whether the problem is geometry/opportunity or features/selector — before you write Stage C.

Also close the label/product mismatch early: production trains **Nifty-excess**; the book is **unhedged cash**.

### Build

1. **Selection-ceiling harness** (report-only):  
   - Pool definitions: (a) production-eligible Long, (b) later Stage-B-gated (stub until M3).  
   - Rank by realized absolute \(EV_{net}\); publish top-decile mean, pos-mass, TP/SL/TO mix.  
2. **Spread panel:** Corwin–Schultz and/or Abdi–Ranaldo vs current `(H−L)/close` proxy; distribution by price bucket / ADV.  
3. **Absolute vs excess reprint:** same paths, `path_ret - c*` vs excess − c\*; show how often signs disagree.

### Cleanup / refactor

| Action | Detail |
|---|---|
| Extract shared bootstrap CI | Session-block bootstrap used in EV-net / gates — pull to a small shared util if duplicated, rather than copy-paste into fresh harnesses |
| Stop using range-as-spread in *new* code | Precision can keep proxy until cutover; fresh Stage A must not call `(H−L)/close` “spread” |
| Label naming clarity | Introduce explicit column names in fresh labels: `ev_net_abs`, `ev_net_excess` — never overload `tb_excess_ret_*` silently |

### Exit criteria

- [x] Ceiling report dual-fold for production-eligible Long pool *(fold A smoke; fold B + full universe pending)*  
- [x] Spread estimator panel reviewed (median bps by ADV/price) *(CS by price bucket; AR needs tune)*  
- [x] Absolute vs excess disagreement rate published *(~6% on fold A smoke)*  
- [x] Written one-paragraph diagnosis — see `docs/archive/horizon-fresh-m0-m1-checkpoint.md`

### Stop

If oracle ceiling is thin under *any* reasonable MIS-vertical / wider-span probe **and** Stage B cannot enlarge span by construction, escalate to product-definition discussion (hedge / universe / session) — do not proceed to deep Stage C.

---

## M2 — Stage A: Tradability filter

### Why

Accounting cost is 20 bps everywhere; **effective** cost is not. Tick drag alone is ~2.5 bps on a ₹200 name vs ~0.1 bps on a ₹5,000 name. Spread is a large share of the budget. Stage A makes the constraint a **where** filter.

### Build

1. Deterministic `c_eff` sketch: statutory (~4 bps) + 2× half-spread + tick drag + optional impact.  
2. Filter `(symbol, session)` where working 20 bps is not achievable.  
3. Unit tests: known price/tick examples; monotonicity (worse spread → likelier reject).

### Cleanup / refactor

| Action | Detail |
|---|---|
| Shared microstructure helpers | Put spread estimators + tick helpers under `src/features/` or `src/horizon/fresh/microstructure.py` — one place |
| Precision later | Plan a follow-on to replace Precision `spread_proxy_bps` with the same estimator at cutover (do not dual-maintain forever) |

### Exit criteria

- [x] Tradability mask joins cleanly onto 15m/1m panels  
- [x] Rejection mass explained (price bucket / spread / ADV) — not a silent black hole  
- [x] Tests green  

### Stop

Filter removes almost all liquid names without a coherent microstructure story → revisit estimator, not Stage B.

---

## M3 — Stage B: Opportunity / range gate (K1, K2)

### Why

Direction R² on single-name intraday is tiny (~0.005). Range is far more predictable (~0.4–0.6 class). **This is the highest-leverage new module.** If Stage B fails, the redesign stops — no scorer can invent span.

Target: admit when **q25(predicted remaining session range) ≥ 10c** (200 bps at `c*=20`). Vertical context is remaining time to MIS flatten.

### Build

1. Features: opening 30m range, gap, VIX level/Δ, 5d RV, sector range, volume z (**equities only**), TOD structure; earnings/event flag if calendar available (else explicit TODO). Cash-index symbols (`^NSEI`) have **no usable volume** — see M9 V1-index note.  
2. Quantile GBDT on log remaining range.  
3. `opportunity_ok` mask.  
4. Eval harness for **K1** (Spearman ≥ 0.45 dual-fold) and **K2** (post-gate mean \|move\| ≥ 8c dual-fold).  
5. Re-run selection-ceiling **on opportunity_ok** pool.

### Cleanup / refactor

| Action | Detail |
|---|---|
| Do not bolt range head onto `GBMHorizonModel` | Separate trainer — production Huber model stays untouched |
| Feature hygiene | Reuse `src/features/core.py` primitives; avoid copy-paste of VWAP/RV helpers |
| Regime join | Consume existing daily/intraday regime columns; do not re-fit HMM here |

### Exit criteria

- [x] **K1 PASS** dual-fold *(full trade universe 82 names A+B)* — **holds under the Rev 2 clock control**: pooled Spearman 0.635, within-clock 0.617, clock alone −0.095, so this is genuine cross-sectional range skill and not a time-of-day artefact  
- [x] **K2 PASS** dual-fold *(full trade universe 82 names A+B)*  
- [ ] Re-run K1/K2 with the `bars_to_mis` overflow fixed (Stage B trained on a scrambled clock feature and still passed; the fix should only help)  
- [x] Post-gate ceiling report published (oracle mass rises vs ungated; top10% +~70 bps; TO ↓)  
- [x] Timeout/TO discussion updated: gate biases toward days where span can resolve (TO 47%→41% A, 48%→43% B)  

### Stop

**K1 or K2 FAIL dual-fold → STOP redesign.** Blueprint capability FAIL path applies.

---

## M4 — Event clock + Long primary rules

### Why

Uniform 15m decisions dilute causal mass and inflate timeouts. The EV-net stop memo explicitly named a **different entry clock** as legitimate grounds for a fresh charter. Meta-labeling only works if the primary rule proposes a side.

### Build

1. Implement Long event set (start minimal, pre-register):  
   - ORB break + volume confirmation  
   - VWAP reclaim after N opposite bars  
   - Prior-day high break  
   - Range expansion > 2× TOD median  
2. Emit event rows only (not every bar): `event_id`, `symbol`, `clock`, `side=long`, `rule_id`.  
3. Apply Stage A ∩ Stage B ∩ Regime soft overlay on events.  
4. Oracle ceiling on **event pool** (should be denser than bar pool).

### Cleanup / refactor

| Action | Detail |
|---|---|
| Retire “score every bar” assumption in fresh path | Fresh pipeline must not call production `predict_horizon_gbm` for its decision set |
| Session helpers | Reuse `src/horizon/session.py` MIS cutoffs; extend for MIS-vertical last-entry consistent with remaining-range race (document times) |
| Flag-gated path-room / L1 features | Leave production flags off; do not port rejected features into event rules |

### Exit criteria

- [x] Event panel builds idempotently  
- [x] Counts: events/day, symbols/day, overlap with opportunity_ok  
- [x] Oracle pos-mass / top-decile on event pool published *(raw events ≈ bar; **A∩B** lifts top10% +66–85 bps and cuts TO)*  
- [x] Written rule dictionary (what fires, causality, no look-ahead)  
- [x] **Rev 2:** event freshness measured — only **27.1%** of emitted rows were transitions; the rest restated a live condition, so the "event clock" was close to the bar clock. Fixed by `transition_events` + `collapse_to_bar`.  
- [ ] **Rev 2:** per-rule drift-sign ledger → carried into M4R as the sleeve-selection input  

**Note:** Raw event pool alone does not beat bar ceiling — Stage A∩B overlay on events is required before Stage C. Not a stop (improvement appears once opportunity-gated). **M5 then did not apply Stage A** — see M5R defect 4. When a milestone's exit note states a precondition for the next milestone, the next milestone's harness must assert it.

### Stop

Event pool has **no** selection ceiling improvement vs bar pool → rules are noise; redesign rules before Stage C ML.

---

## M5 — Stage C: Direction EV + geometry-as-decision (K3, K4)

### Why

Huber regression on path EV shrinks the payoff tail and fights a trimodal TP/SL/TO outcome. The blueprint replaces it with:

- Primary rule owns side  
- ML meta-label / multiclass first-hit probabilities  
- Geometry multipliers as **features**; at inference, sweep `(tp_mult, sl_mult)` as fractions of Stage B range and pick \(\arg\max EV_{net}\)

Vertical barrier: **MIS flatten** (with last-entry so the race can resolve). Timeout target mass ≤ ~20%.

### Build

1. **Fresh labeler** (beside production TB): absolute path, parameterized geometry, MIS vertical, first-hit outcomes + \(EV_{net}\).  
2. Multiclass head \(P(TP), P(SL), P(TO)\) + isotonic (or equivalent) calibration on purged val.  
3. Optional \(\mathbb{E}[r \mid TO]\) head.  
4. Inference geometry sweep → `g*`, `s*`, `ev_net_hat`.  
5. Gates **K3** (calibration) and **K4** (realized \(P(TP) - s/(g+s)\); CI LB > 0).  

### Cleanup / refactor

| Action | Detail |
|---|---|
| Do not edit production floors in `triple_barrier.py` as the experiment vehicle | New module e.g. `src/labels/fresh_barrier.py` (name flexible) |
| Loss / model split | New `FreshHorizonModel` (or Stage-C trainer); production `GBMHorizonModel` remains for Precision bridge / legacy eval |
| Drop Nifty-excess as default in fresh labels | Excess may remain as report-only companion |
| Eval vocabulary | Fresh gates named K1–K5; do not overload H1–H5 ship language |

### Exit criteria

- [x] **K3** evaluated — FAIL dual-fold (max calib gap ≫ 3 pp) — **void: no calibrator was fitted and the threshold was below its own null (§M5R defects 2, 6)**  
- [x] **K4** evaluated — FAIL dual-fold (CI LB < 0) — **void: no directional features, no Stage A, scrambled clock, TO-biased null (§M5R defects 1, 3, 4, 7)**  
- [x] Timeout mass on admitted geometries reported *(~9–11% all / ~3–5% admit — TO OK)*  
- [x] ~~Geometry distribution sane (not collapsed) — unique g* ~180–200~~ — **void: the sweep used geometry-invariant probabilities, so it returned the grid corner (`tp_mult`=0.6, `sl_mult`=0.2 → g\*/s\* = 3.0) on every row, and the reported ~188 bps span was never the 300 bps span the labels used**  

### Stop

**K4 FAIL → STOP.** Triggered 2026-08-16, then **VACATED** the same day by the M5R post-mortem: the
harness could not have passed. Reclassified **INCONCLUSIVE** per blueprint §14.  
Memo: [horizon-fresh-m5-stop-memo.md](../archive/horizon-fresh-m5-stop-memo.md) + addendum.  
The forbidden-next-steps list still stands: no geometry grid search, no Precision peeks, no Stage D
soft thresholds. Repairing a defective harness is none of those things.

---

## M5R — Stage C harness repair (K3, K4 re-read)

### Why

M5 reported `0/4 gate-fold cells passed` and invoked the blueprint FAIL sentence. A post-mortem of the
harness found seven defects, of which the first alone makes the K4 reading uninterpretable.

| # | Defect | Evidence | Consequence |
|---|---|---|---|
| 1 | **Stage C had no directional feature.** All 11 inputs were volatility / range / rule-identity. | Univariate \|Spearman(feature, TP-first)\| ≤ 0.065; strongest was `rv_5d` at **−0.065**. Rule one-hots took 10–141 LightGBM splits vs 3,500–4,800 for vol features. | Vol features are symmetric in the barrier race — they raise P(TP) and P(SL) together. K4 tested a head that could not express direction. |
| 2 | **No calibrator was ever fitted.** Blueprint §8.2 requires isotonic on purged val; `FreshHorizonModel` had no calibration step. | Mean predicted P(TP) 0.230 vs realized 0.337 (−11 pp bias); train→test P(TP) base rate shifted 0.283→0.337. | K3 measured the missing isotonic step, not the model. |
| 3 | **`bars_to_mis` was scrambled by silent Int8 overflow.** `dt.hour()` returns `Int8`, so `hour * 60` wraps. | 15:00 mapped to −124 and 10:45 to −123; values ran 53–69 instead of 0–23, colliding pairs of unrelated bar times. | The clock feature was noise in **both** Stage B and Stage C. Fixed in `opportunity.py`; regression test added. |
| 4 | **Stage A was never applied.** M5 filtered on `tb_eligible & entry_ok & opportunity_ok` only. | `eval_horizon_fresh_m5_stage_c.py` imports no tradability module. | Contradicts M4's own exit note that A∩B is required before Stage C. |
| 5 | **The event pool was 73% restatements.** Rules re-fired on every bar the condition stayed true. | Fresh-rate by rule: `prior_day_high` 10.3%, `orb_break_vol` 28.2%, `range_expand_2x` 31.2%, `vwap_reclaim` 75.3%. 1.30 rows per (symbol, bar). | The "event clock" was close to the bar clock, and duplicated rows differing only in a one-hot are near-duplicates to a GBDT. |
| 6 | **K3's threshold was unreachable.** Max gap over 10 deciles compared to a flat 3 pp. | Bootstrap null p95 of the max gap is 6.0–9.4 pp on these samples. | A perfectly calibrated head fails almost surely. |
| 7 | **K4's null ignored timeout dilution.** `s/(g+s)` is a no-time-limit formula. | TO mass 8.9% / 11.4% all, 3.4% / 4.7% admit → ~1–3 pp built-in penalty. | Biased against passing by roughly the TO mass. |

Defect 1 is decisive on its own: **a FAIL from that harness carried no information about the market.**

### Build

1. Directional feature block — signed, ATR-normalized, causal (`src/horizon/fresh/direction.py`).
2. Cross-sectional rank versions of vol-state features (level shift immunity).
3. Event `transition_events` + `collapse_to_bar` — false→true transitions, one row per (symbol, bar), multi-hot rules.
4. Apply the Stage A tradability mask (Corwin–Schultz spread → `c_eff` ≤ 20 bps).
5. Per-class isotonic calibration on a purged val slice (last 20% of train sessions, one-session embargo).
6. Gate repairs: `k3_calibration_ece` (ECE + bootstrap null band), `k4_martingale_residual` (gross return), `k4_edge_over_driftless(resolved=…)`.
7. Barrier-free **drift compass** per rule — the direction ledger blueprint §5.2 now requires.
8. **M5R-b (done):** resolve first-hit on 1m bars and make TP penetration symmetric (blueprint §9.1).
   Harness: `eval_horizon_fresh_m5rb_stage_c.py`.

### Cleanup / refactor

| Action | Detail |
|---|---|
| Keep the M5 harness reproducible | `eval_horizon_fresh_m5_stage_c.py` and `k3_tp_calibration` stay as the M5 ledger; marked superseded, not deleted |
| `geometry_argmax` signature | Now requires a geometry-**conditional** probability callable, so the degenerate invariant sweep cannot be written by accident |
| Forensics harness | `diagnose_horizon_fresh_m5_forensics.py` — audit-only, keeps the post-mortem numbers reproducible |
| Regression test for the overflow | `test_bars_to_mis_is_monotone_and_positive` |

### Results (fold A / fold B, 82 names, `m5r_full_run.log`)

| Reading | M5 | M5R |
|---|---|---|
| K3 | 16.1 / 24.4 pp max gap — FAIL | **ECE 4.64 pp / 2.38 pp**; fold B **PASS**, fold A marginal; max gaps 9.16 vs null 9.35 and 3.92 vs null 5.96 — both **inside the null band** |
| K4 gross (all events) | not measured | −10.55 / −5.29 bps, CI \[−21.6, +1.2\] / \[−18.7, +7.7\] |
| K4 gross (admit) | not measured | −4.71 bps / admit set empty |
| K4 P(TP\|resolved) − driftless | −0.8 / −5.1 pp (unadjusted) | −3.46 / −1.79 pp |
| Realized P(TP) | — | 0.293 / 0.308 vs driftless 0.333 |
| Mean predicted P(TP) | 0.230 (vs realized 0.337) | 0.339 / 0.284 (vs realized 0.293 / 0.308) |
| TO mass | 8.9% / 11.4% | 1.8% / 2.3% |
| MDE on K4 | not published | 11.4 / 13.2 bps |

Fold B's admit set is **empty**: calibrated P(TP) never exceeded the driftless 1/3. That is Stage D
behaving as designed — a day with no admissible instance should fire zero trades.

### Results M5R-b (1m first-hit + symmetric penetration; report-only)

| Reading | M5R (15m, TP-only pen) | M5R-b (1m, symmetric 2 bps) |
|---|---|---|
| Dual-touch share (15m first-hit bar) | not published | **0.19% / 0.21%** (train/test fold A test year; fold B similar) |
| Dual-touch share (1m) | — | **0.000%** both folds |
| K4 gross (all events) | −10.55 / −5.29 bps | **−7.46 / −2.70 bps**, CI \[−18.8, +4.5\] / \[−16.6, +10.3\] |
| K4 gross (admit) | −4.71 bps / empty | **−1.26 bps** / empty |
| Realized P(TP) | 0.293 / 0.308 | **0.303 / 0.316** |
| MDE on K4 | 11.4 / 13.2 bps | 11.6 / 13.5 bps |

Measurement bias was real (~**+3 bps** on all-events K4) but does not change the sleeve
verdict: both folds still have CI UB ≪ \(c^*\). Log: `data/GOLDEN_PARQUET/m5rb_full_run.log`.

### Exit criteria

- [x] All seven defects fixed or explicitly deferred with a reason
- [x] K3 re-read with a passable metric — dual-fold, full universe
- [x] K4 re-read as a martingale residual with MDE published
- [x] Per-rule drift ledger published (feeds M4R)
- [x] Tests green (`tests/horizon/fresh`)
- [x] M5R-b: 1m first-hit resolution + symmetric penetration, K4 reprinted
  (report-only; re-declare authority after review — do not inherit peek budget)
- [x] **Review 2026-08-17:** K3 `passed` now ANDs max-gap ≤ null p95 (was ECE-only).
  M5 ledger harness `geometry_argmax` replay restored after the callable signature lock.

### Stop

The repaired harness **still fails K4 for Long continuation**, and the CI upper bounds (+1.2 / +7.7 bps
all-events) sit well below the +20 bps K5 would need. Under the blueprint §10.3 three-way rule this is
**FAIL for this decision set** — not INCONCLUSIVE, because the UB rejects reaching \(c^*\).

That is a verdict on *Long continuation on 15m breakout rules*, not on the architecture. M4R follows.

---

## M4R — Primary-rule redesign (drift-sign ledger)

### Why

The four M5 rules carry **opposite and fold-consistent** drift signs, and were pooled into one Long
head that gave rule identity ~1% of its splits. Barrier-free drift from the event bar to MIS flatten:

| Rule | Kind | Drift A | Drift B | Read |
|---|---|---|---|---|
| `vwap_reclaim` | fade / reversion | **+11.1 bps** | **+17.9 bps** | consistently with Long |
| `range_expand_2x` | volatility | −7.1 bps | +12.5 bps | inconsistent |
| `orb_break_vol` | continuation | −9.8 bps | −5.5 bps | consistently against Long |
| `prior_day_high` | continuation | −13.1 bps | −31.2 bps | consistently against Long |

No single CI excludes zero (±25–40 bps), so this is a **direction-of-research** signal, not an edge.
But it says clearly that the Long-continuation sleeve — three of four rules — was the least promising
quadrant available, and that "Long-only first" chose it by convention rather than evidence.

This is the "different entry clock **and** different side" that the EV-net stop memo named as
legitimate grounds for a fresh hypothesis. It is not a barrier redraw.

### Build

1. Split the rule set into **reversion** and **continuation** families; one head per family per side.
2. Add reversion primary rules for both sides: VWAP loss/reclaim, opening-range fade, prior-day-high **rejection**, gap-fill, N-bar exhaustion into a band edge.
3. Publish the drift-sign ledger for every candidate rule **before** any Stage C fit — pre-registered, dual-fold, report-only.
4. Select **one** sleeve to carry to Stage C: the rule family whose drift sign is fold-consistent and whose magnitude has a plausible route past \(c^*\).
5. Short sleeve is now **in scope** (blueprint §7 Rev 2), subject to the existing Short asymmetries: wider stop vs target, no carry into the 15:00–15:20 flatten.

### Cleanup / refactor

| Action | Detail |
|---|---|
| Rule registry | One module owning `rule_id → (family, side, description, causality)`; drop the four-way one-hot pattern |
| Short session helpers | Reuse `short_entry_ok_expr` / `SHORT_LAST_ENTRY`; do not fork MIS constants |
| Retire pooled-head code path | Once per-family heads exist, the single Long head becomes M5 ledger only |

### Exit criteria

- [x] Drift-sign ledger for all candidate rules, dual-fold, pre-registered
  — log: `data/GOLDEN_PARQUET/m4r_drift_ledger.log`
- [x] Rule registry with family + side, unit-tested for causality (no look-ahead)
- [ ] One sleeve selected with a written rationale — **not met**
- [ ] Selection-ceiling reprint on the selected sleeve's event pool — **n/a (STOP)**
- [x] **Review 2026-08-17:** Build item "N-bar exhaustion into a band edge" was **never coded**.
  Frozen — do not add a candidate after the pool STOP. Registry covers VWAP loss/reclaim,
  ORB fade, PDH/PDL reject, gap-fill, plus the M5 continuation set.

### Stop

**No rule family has fold-consistent drift with a credible route to \(c^*\) → STOP**, and this time the
blueprint §14 FAIL sentence applies for real: the product definition must change (hedged book,
different universe, or a different session product), because the failure is then in the causal
hypothesis rather than in the harness.

**Triggered 2026-08-16.** Several rules are fold-consistent in sign (e.g. `prior_day_high_reject`
Short +6.2 / +7.8 bps; `vwap_loss` Short +3.2 / +5.2; `gap_fill_short` +6.8 / +4.4), but **no**
rule's session-block CI upper bound reaches \(c^*=20\) bps (best UB ≈ +16.8). Under the
pre-registered selection rule (consistent sign **and** CI UB ≥ \(c^*\) on ≥1 fold) there is no
sleeve with a credible route past friction. Do **not** proceed to M5 re-read / M6 / geometry.

### Stop scope — narrowed by review (Rev 3)

The ledger is sound and the sleeve-selection rule was applied as pre-registered. Two corrections to
what the stop is entitled to conclude:

1. **It bounds the pool, not the product.** Blueprint §10.2 is explicit that a pre-selection mean is
   not the gate, because *selection is the job*. Gating on unconditional per-rule drift is the EV-net
   Step 0 error one level up. The statistic that can refute the architecture is K4 on the **admitted**
   set after Stage C, which was never run on the winning sleeve.
2. **The hurdle used was the flat `c*`.** Stage A computes row-level `c_eff` and the pipeline discards
   it (blueprint §3.1). A +7 bps sleeve against a liquid-tail `c_eff` is a different comparison from
   +7 against a universe-average 20.

The required-IC arithmetic says neither correction is a formality: carrying +7 bps to breakeven at a
20 bps hurdle needs a selector IC of ~**0.054**, against a measured achievable ceiling of ~**0.07**
(blueprint §15A). Breakeven is below the ceiling; margin (~0.10) is above it.

**Revised status: M4R STOP stands for the *unconditional rule pool*.** Escalation to a product change
is gated on **M4R-b**, two pre-registered falsifications that close the two gaps above. The
forbidden-next-steps list is unchanged: no geometry search, no Precision peeks, no Top-K remount.

---

## M4R-b — Two falsifications before escalating

**Prerequisite: M5P-b must land first** — F2 reads K5 economics, and K5 must be correct before it is
cited. Document order here follows lineage (M4R → M4R-b); execution order is M5P-b → M4R-b.

**Pre-registration (locked before authority runs):**
[horizon-fresh-m4rb-preregistration.md](../archive/horizon-fresh-m4rb-preregistration.md)

**Harness:** `src/experiments/eval_horizon_fresh_m4rb_falsify.py`

### Why

M5 recorded a FAIL from a harness that could not have passed; the four-point checklist above exists to
prevent a repeat. M4R is a better ledger, but its stop rests on a statistic the architecture never
claimed would clear \(c^*\), evaluated against a hurdle the architecture said not to use. Both gaps are
closable with existing code and one peek each. Both are pre-registered as **expected FAIL** — a PASS is
the surprise, which is what makes them falsifications rather than a search for a lucky reading.

### Build

**F1 — Stage C selector on the winning sleeve.**

1. Sleeve: `prior_day_high_reject` Short (best fold-consistent drift), Stage A ∩ Stage B, transition events.
2. Geometry: **vertical-only** to MIS flatten per blueprint §1.6, with a wide disaster stop only. Do not race 200/100 — the M5R evidence says a tight stop destroys thin drift.
3. Stage C multiclass / meta-label head with the M5R directional features and isotonic calibration.
4. Read K4 on the **admitted** set with the three-way rule, and publish the realized selector IC next to the required IC (0.054 breakeven, 0.10 margin).
5. State the expected admit count **before** the run, so the resulting MDE is known in advance (blueprint §10.3 selection-power tradeoff).

**F2 — Row-level `c_eff` reprint.**

1. Carry `c_eff_bps` into `expected_ev_net` and the K4 / K5 arithmetic in place of the flat `C_STAR`.
2. Restrict to the liquid tail the sparse book would actually trade; publish the realized `c_eff` distribution of that subset.
3. Reprint the M4R drift ledger and F1's K4 against row-level `c_eff`, with the flat-`c*` and c=30 columns alongside.
4. Publish the **capacity** the liquid tail supports — a tail-only product must state its size limit.

### Cleanup / refactor

| Action | Detail |
|---|---|
| Single cost entry point | `expected_ev_net` / gates take a cost **array**, defaulting to `C_STAR` only when Stage A has not run |
| Delete flat-cost assumptions in fresh code | Grep for `C_STAR` in EV paths; each remaining use must be a stress reprint, not a hurdle |
| Vertical-only geometry | Add it as a named `FreshLongGeometry` / short equivalent rather than a special case in a harness |
| Keep M4R ledger intact | `m4r_drift_ledger.log` stays the authority for the unconditional pool |

### Exit criteria

- [x] F1 pre-registration written (sleeve, geometry, expected admit count, expected outcome) **before** the run
  — `docs/archive/horizon-fresh-m4rb-preregistration.md`
- [x] F1 K4 on the admitted set, three-way verdict, realized vs required IC published
  — IC ≈ +0.022 / +0.023 vs need 0.054; F1 **FAIL** (`m4rb_full_run.log`)
- [x] F2 row-level `c_eff` wired into EV arithmetic; `c_eff` distribution and capacity published
  — median c_eff ~7–8 bps; EV_net CI LB never > 0 dual-fold; F2 **FAIL**
- [x] Combined verdict written against the four-point STOP checklist
  — [horizon-fresh-m4rb-stop-memo.md](../archive/horizon-fresh-m4rb-stop-memo.md)
- [x] **Review 2026-08-17:** disaster stop now **clips** to `−sl_floor` instead of dropping
  the left tail (K4 was biased upward; FAIL still stands). Residual: F2 did not reprint
  the full M4R per-rule ledger on `c_eff`; R2017–R2022 report-only folds were not run.

### Stop

**Both F1 and F2 FAIL → the blueprint §14 capability FAIL is earned.** Recorded 2026-08-16.
Open the successor charter (**M9**). The failure is in the causal hypothesis, not the harness:
directional event drift on Nifty-100 intraday remains thin, and no selector reaches the required IC
even at a liquidity-tail `c_eff` hurdle.

---

## M5P — Validation power

### Why

M5's K4 required a session-block CI lower bound above zero on a quantity whose MDE is **11–15 bps** —
comparable to the entire 20 bps cost budget. A strategy sitting exactly at the design target could not
have been distinguished from one sitting at zero. Two single-year test folds (~220 sessions each) are
not enough resolution for the decision being made.

### Build

1. Publish MDE for K2 / K4 / K5 on the current fold design.
2. Extend to a rolling walk-forward with more, shorter test windows (target ≥ 6 folds) instead of two single-year holdouts, keeping purge/embargo discipline.
3. Report the effective sample size honestly: cross-sectional correlation within a session means ~82 names contribute far fewer than 82 independent observations. Session-block bootstrap already respects this — say so in the ledger.
4. Add a formal purge/embargo between train and test in `folds.py` (currently adjacent calendar years with no gap).
5. Pre-register the three-way K4 decision rule (PASS / FAIL / INCONCLUSIVE) with its thresholds.

### Exit criteria

- [x] MDE < \(c^*\) for K4 on the chosen fold design, or a written statement that available history cannot support the gate
  — **8/8 folds** (A/B + R2017–R2022) have K4 MDE in **9.0–12.6 bps** (< 20). Log: `m5p_full_run.log`.
- [x] Fold definitions include explicit purge/embargo — `ROLLING_FOLDS` + `DEFAULT_PURGE_CALENDAR_DAYS=5`
- [x] Every gate result prints MDE alongside the point estimate — K2/K4/K5 via `GateResult.mde`; K4 three-way pre-registered
- [x] **Review 2026-08-17:** purge is applied to Stage B *train rows* via `apply_purge_date_filter`
  (previously only printed as `train_end_disp`; year-based `filter_by_period` cannot hold out 27–31 Dec)

### Stop

Available history cannot deliver MDE < \(c^*\) → the gate cannot decide the question. Escalate to product
definition rather than running underpowered peeks and reading their noise.

**Not triggered.** M5P EXIT → proceed to M4R.

---

## M5P-b — Gate repairs from the M4R review

### Why

M5P bought power for K4 and succeeded (MDE 9.0–12.6 bps on 8/8 folds). The M4R review then found that
**K5** has the opposite problem: it is not underpowered, it is *unpassable by the intended book*.

At the 200/100 geometry per-trade gross dispersion is σ ≈ 137 bps. A 95% lower bound above zero on a
true \(EV_{net}\) of +10 bps needs SE < 5.1 bps → ~720 independent trades, or ~1,150 with intra-session
clustering, i.e. ~4.6 fires per session. The design target is 1–4 fires per **day across ~88 names**.
A genuinely profitable sparse book therefore fails per-fold K5 by construction.

### Build

1. **K5 becomes a pooled read** across the 8 rolling folds (~2,000 sessions), with fold-consistency tested separately as a **sign test** (positive point estimate in ≥ 6 of 8 folds). Keep publishing per-fold points and MDEs; stop gating on per-fold lower bounds.
2. K5 hurdle uses **row-level `c_eff`**; flat-`c*` and c=30 reprints become companions.
3. Every admission threshold declares its **expected admit count and resulting MDE before the run** (selection-power tradeoff, blueprint §10.3).
4. Add a **vertical-only** geometry as a first-class option, and a check that any tight stop is justified by measured \(EV_{net}\) improvement on that sleeve rather than assumed.

### Exit criteria

- [x] Pooled K5 + fold sign test implemented and unit-tested
  — `k5_pooled` / `k5_economics` (report-only); `tests/horizon/fresh/test_m5pb_gates.py`
- [x] `c_eff` array threaded through the EV / gate arithmetic
  — `expected_ev_net(..., cost=)` and `path_ev_net(path, cost)` accept scalar or array
- [x] Admit-count / MDE pre-declaration is part of the harness output, not a convention
  — `declare_admit_power` → `AdmitPowerPlan`
- [x] Vertical-only geometry available and covered by tests
  — `MIS_VERTICAL_ONLY_LONG_GEOMETRY` / `_SHORT_GEOMETRY` in `fresh_barrier.py`
- [x] **Review 2026-08-17:** `k5_pooled` is correct and unit-tested; no live harness calls it
  (M6 was the intended consumer and is blocked). Leave unwired until an M9 book exists.

### Stop

None — this is a gate-correctness milestone. It must land **before** any K5 reading is treated as
authority, including inside M4R-b F2.

**EXIT PASS (2026-08-16).** Proceed to M4R-b.

---

## M9 — Successor charter (OPEN after M4R-b)

**Charter:** [horizon-m9-range-monetization-charter.md](horizon-m9-range-monetization-charter.md)  
**Code:** `src/horizon/m9/`, `src/experiments/eval_horizon_m9_v0_vix_bridge.py`,
`src/experiments/eval_horizon_m9_v1_index.py`, `src/experiments/eval_horizon_m9_v1.py`,
`src/scripts/build_atm_iv_daily.py`

### Why

M4R-b earned the blueprint §14 capability FAIL for directional cash MIS. Ranked hypotheses and
rejections are in blueprint §15B. Stages A, B and D survive; Stage C directional is discarded.

### Primary hypothesis — sell range, not direction

| Gate | Rule | Status |
|---|---|---|
| **V0** | India VIX bridge OLS (report-only) | Dual-fold published — not authority |
| **V1-index** | Nifty remaining range vs India VIX + index `range_q50` | Dual-fold **PASS** (log `m9_v1_index.log`) |
| **V1** | Incremental info vs **single-name** implied | Dual-fold **PASS** (`m9_v1_full.log`) |
| **V2** | Gross option PnL on V1 sessions | After V1 PASS |
| **V3** | Net of option friction | After V2 PASS |

### Index volume (locked)

Cash-index feeds (`data/GOLDEN/^NSEI.csv`) ship **volume ≡ 0** — participation is unavailable,
not missing-at-random. Align with Regime Tier-1:

- **V1-index / any index-only Stage B reprint:** **drop `volume_z`** from the feature set
  (`INDEX_OPPORTUNITY_FEATURES` in `eval_horizon_m9_v1_index.py`). Do **not** invent volume from
  range/`|r|` (collinear with RV).
- **Stock Stage B (M3 / name panels):** keep `volume_z`; real equity volume remains valid.
- **Location on index:** use TWAP semantics where VWAP would have been (Regime `vwap_dist`);
  revisit participation only with rollover-clean **Nifty futures volume**.

### Secondary — SSF cost cut

Blocked on futures history (**S0**). Do not reopen cash Stage C feature fishing.

### Data audit (2026-08-16)

| Asset | Present? |
|---|---|
| `data/GOLDEN/^INDIAVIX.csv` (1m) | **Yes** → enables V0 / V1-index |
| `data/GOLDEN/^NSEI.csv` (1m) | **Yes**, but **volume unavailable** (≡ 0) → drop `volume_z` on index-only |
| Single-name IV / option chains | **Yes** (EOD ATM IV parquet, 2015–2019) → unblocks V1 after pre-registration |
| Single-stock futures OHLCV | **No** → blocks Track B |

### Exit criteria

- [x] Written §14 capability FAIL for the directional product, with the M4R-b evidence
  — [horizon-fresh-m4rb-stop-memo.md](../archive/horizon-fresh-m4rb-stop-memo.md)
- [x] One successor hypothesis selected, with the rejections from blueprint §15B restated
  — Track A primary (options); Track B secondary (SSF); rejections in M9 charter
- [x] Data prerequisites secured before any **authority** gate is run — **M9-0 store + coverage COMPLETE**
  (`atm_iv_daily.parquet`, folds A/B coverage 79.8% / 78.4%)
- [x] New charter document created; this plan's status line points at it
  — [horizon-m9-range-monetization-charter.md](horizon-m9-range-monetization-charter.md)
- [x] V0 report-only dual-fold published (`m9_v0_vix_bridge.log`)
  — dual-fold INCREMENTAL vs India VIX (b_q50≈1.0–1.1, p≈0); **not** authority V1
- [x] V1-index dual-fold published (`eval_horizon_m9_v1_index.py`; no `volume_z`)
  — fold A/B **PASS** `b_q50`≈0.60/0.61, p≪0.05; log `data/GOLDEN_PARQUET/m9_v1_index.log`.
  Methodology kill-switch does **not** replace name-level V1.
- [x] V1 authority after M9-0
  — pre-reg [horizon-m9-v1-preregistration.md](../archive/horizon-m9-v1-preregistration.md);
  dual-fold **PASS** (`m9_v1_full.log`); memo [horizon-m9-v1-memo.md](../archive/horizon-m9-v1-memo.md)

### Next actions (ordered)

1. **V2** — Gross option PnL on V1-selected sessions (needs mids/marks; not in GOLDEN today).  
2. **V3** — Only after V2 PASS, net of option friction.  
3. Optionally start SSF data acquisition for Track B in parallel — not a substitute for V2.

---

## M6 — Stage D: Absolute admit + book (K5)

> **Blocked.** M6–M8 remain closed while the directional product is FAIL. The previous
> `eval_horizon_fresh_m6_admit.py` remounted M5 Stage C and is now a **hard exit (code 3)**.
> If M9 Track A or B produces an absolute-EV positive book, revisit M6 against *that*
> registry — not production Top-K, and not the M5 Long-continuation head.
> Library helpers in `src/horizon/fresh/admit.py` (conformal residual LB, concurrency /
> sector / daily-loss caps, Kelly) are ready for that revisit.

### Why

Top-K always fires K names, even on bad days. Absolute conformal lower bound on \(EV_{net}(g^*) > 0\) is the gate that matches the product goal. Kelly / sector / concurrency / daily loss caps keep a sparse book alive.

### Build

1. Conformal (or purged-calibration) lower bound on \(EV_{net}\).  
2. Admit mask; optional post-admit **capacity** Top-K (not economic gate).  
3. Sizing: fractional Kelly on EV/variance; sector cap; concurrency cap; daily loss limit.  
4. Gate **K5** (Rev 3): **pooled** admitted-set mean \(EV_{net}\) CI LB > 0 on **row-level `c_eff`**, plus a fold sign test (positive point in ≥ 6 of 8 folds). Flat-`c*` and c=30 reprints published as companions. Per-fold lower bounds are **not** the gate — see M5P-b for why.  

### Cleanup / refactor

| Action | Detail |
|---|---|
| New registry builder | Parallel to `calculate_horizon_precision_features` — e.g. absolute-admit registry with frozen `g*,s*` at decision |
| Deprecate Top-K-as-edge in docs | Update draft notes; production overview unchanged until M8 |
| Rank columns | If rank retained, document as capacity sort key only |

### Exit criteria

- [ ] **K5 PASS** pooled + fold sign test (blueprint §10.3 Rev 3) — **blocked, no book**
- [ ] Fires/day distribution published (~1–4 is expected)
- [ ] Zero-fire days exist and are accepted
- [x] Book risk caps unit-tested — concurrency, sector, daily-loss, conformal residual LB
  (`tests/horizon/fresh/test_admit.py`). Authority K5 still blocked.
- [x] M6 harness hard-blocked (`eval_horizon_fresh_m6_admit.py` exits 3)  

### Stop

**K5 FAIL after K4 PASS** → skill without economics; next work is product definition (hedge, universe, session), **not** remounting Top-K / H=6 / 60–30.

---

## M7 — Precision on the new registry

### Why

Precision’s honest job is to shave **~2–4 bps** of entry timing / skip toxicity on an already positive-EV book. It cannot bridge a 12–19 bps Horizon deficit. Re-measure on the **fresh admitted registry**, not production Top-K=5.

### Build

1. Wire Precision feature/join path to fresh registry (frozen barriers from Stage C).  
2. Phase-1 rules baseline on Long fires (P0–P3 style metrics, adapted to new upstream).  
3. Report Δ vs naive decision-close on the same admitted set.  

### Cleanup / refactor

| Action | Detail |
|---|---|
| Keep Precision Execution Bridge charter orthogonal | That charter falsifies monetization on **frozen production** Top-K; do not merge success language |
| Share session / MIS flatten constants | One source (`horizon/session.py`) |
| Avoid feeding Precision fills into Horizon K-gates | Same anti-pattern as H5 lock |

### Exit criteria

- [ ] P0 causality/MIS/fill checklist PASS  
- [ ] Publish P1/P2/P3 (or fresh equivalents) on new registry  
- [ ] Explicit statement: Precision result ≠ Horizon K4/K5  

### Stop

Harness broken / thin → fix infra.  
If Precision is used rhetorically to “save” failed K5 → charter FAIL intent.

---

## M8 — Cutover decision & Short track

### Why

Only after Long K5 (and a sober Precision read) should production cascade wiring change. Short is a **refit**, with wider stops and no carry into 15:00–15:20 flatten (existing `afternoon_cover_risk` intuition).

### Build / decision

**Option Ship:**  
- Point `precision_pipeline` / registry to fresh admit path  
- Update [cascade-strategy-overview.md](../cascade-strategy-overview.md) Horizon section  
- Freeze legacy Top-K path behind a legacy flag for audit replay  

**Option No-ship:**  
- Leave production unchanged  
- Archive fresh package as research with capability FAIL sentence from blueprint §14  

**Short (only if Ship or explicit Short charter):**  
- Refit Stages B–D with Short primary rules  
- Asymmetries: wider SL vs TP; afternoon cover hard rules  

### Cleanup / refactor (cutover checklist)

| Action | Detail |
|---|---|
| Delete or archive dead peeks | Move CLOSED analyze scripts under `src/experiments/archive/` or docs-only pointers |
| Single label entrypoint | Production either calls fresh labeler or remains on legacy — no dual silent defaults |
| MLflow naming | New experiment names (`Horizon_Fresh_*`) vs `Horizon_Pipeline` |
| Config | No speculative mega-config; sleeve constants in one module |
| Docs | Overview, verdicts, and this plan’s status line updated in one PR |

### Exit criteria

- [ ] Written ship / no-ship decision with K1–K5 reprint  
- [ ] If ship: one integration test from Regime → fresh Horizon → Precision smoke  
- [ ] If Short starts: separate charter linked from this plan  

---

## Refactor backlog (cross-cutting)

These items appear inside milestones above; collected here so nothing is lost.

| Item | When | Notes |
|---|---|---|
| Parquet materialization of GOLDEN | M0 | Order-of-magnitude iteration speed |
| Quarantine CLOSED Horizon peek modules | M0 | Audit-only |
| Shared session-block bootstrap util | M1 | Stop copy-paste CIs |
| Microstructure spread estimators | M1–M2 | Replace range-as-spread in fresh path |
| Explicit `ev_net_abs` vs excess columns | M1 / M5 | Label honesty |
| Fresh package vs production `GBMHorizonModel` | M3–M5 | No in-place Huber rewrite |
| Fresh barrier labeler vs `triple_barrier.py` | M5 | Leave production floors frozen until M8 |
| Absolute-admit registry vs Top-K registry | M6 | Capacity Top-K optional after admit |
| Precision spread proxy alignment | M7–M8 | Same estimator as Stage A |
| Cascade overview rewrite | M8 only | Avoid doc/code skew earlier |
| Earnings / corporate-action calendar | M3 if available, else M3 TODO → M5 | Stage B lift |
| Options/OI/skew features | After M6 PASS | Phase-2 only |
| Temporal CNN/GRU first-hit head | After K4 PASS | Blueprint phase-2; not before tabular |
| **Directional feature block** | M5R | `src/horizon/fresh/direction.py` — signed, ATR-normalized, causal |
| **Cross-sectional rank features** | M5R | Vol *levels* do not transfer across folds; within-bar ranks do |
| **Isotonic calibration + purged val split** | M5R | Was specified in blueprint §8.2 and never built |
| **`bars_to_mis` Int8 overflow fix** | M5R | Cast datetime parts before arithmetic; regression test added |
| **Event transition semantics** | M5R | `transition_events` / `collapse_to_bar`; one row per (symbol, bar) |
| **Gate validity + MDE reporting** | M5R / M5P | `k3_calibration_ece`, `k4_martingale_residual` |
| **1m first-hit resolution + symmetric penetration** | M5R-b | A 300 bps race judged on 15m bars with ties broken to SL biases K4 down |
| **Geometry stacked over multipliers** | After K4 PASS | Labeler must accept per-row barrier widths; otherwise no sweep |
| **Purge / embargo in `folds.py`** | M5P | `apply_purge_date_filter` holds out the last 5 calendar days of the train year (year-based `filter_by_period` cannot). Applied in the M5P Stage B train fit as of 2026-08-17. |
| **K3 ECE ∧ max-gap vs null** | M5R / review | `k3_calibration_ece.passed` now matches blueprint §10.3 conjunction |
| **M6 harness withdrawn** | M6 | Hard-exit; do not remount M5 Stage C. `admit.py` helpers kept for M9. |
| **Rule registry (family + side)** | M4R | Replaces the four-way one-hot; enables per-sleeve heads |
| **Row-level `c_eff` threaded into EV / gates** | M5P-b / M4R-b | `expected_ev_net` and K4/K5 take a cost array; flat `C_STAR` becomes a stress reprint only |
| **Pooled K5 + fold sign test** | M5P-b | Per-fold LB is unpassable at 1–4 fires/day |
| **Vertical-only geometry as a named option** | M5P-b | Thin-drift sleeves; stop tight stops from being the silent default |
| **Admit-count / MDE pre-declaration in harness output** | M5P-b | Selection-power tradeoff must be visible before the peek |
| **Capacity statement for liquid-tail books** | M4R-b F2 | A tail-only product must state its size limit |
| **NSE implied vol / OI history** | M9 prerequisite | Blocks the V1 incremental-information gate |

---

## Human checkpoints (recommended)

After each milestone, write a **short memo** (½–1 page) with:

1. What changed in code (modules touched)  
2. Numbers that matter (K-gates, ceiling, fires/day)  
3. Cleanup done vs deferred  
4. Go / Stop / Rework decision  

Do not wait for a giant dual-judge document to record a Stop — the blueprint already defines the language.

---

## What “done” looks like

**Architecture PASS:** the selected sleeve clears K1–K5 dual-fold under `c*=20`; registry is absolute-EV; Precision is re-measured on that book; production either cut over deliberately or explicitly declined.

**Architecture FAIL:** Stop at M3/M4R/M5/M6 per gates, **on a harness that satisfies the four-point checklist above**; do **not** return to Top-K + H=6 + 60/30 as the recovery plan; next hypothesis must change product definition (hedge, universe, or session product).

**Architecture INCONCLUSIVE:** a gate reads near zero with an MDE wider than the effect it targets, or the harness could not have passed. Repair or buy power; do not record a FAIL. This is the state M5 was actually in.

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-fresh-architecture-blueprint.md](horizon-fresh-architecture-blueprint.md) | Design authority (arithmetic, stages, K-gates) |
| [horizon-fresh-m5-stop-memo.md](../archive/horizon-fresh-m5-stop-memo.md) | M5 STOP + addendum vacating it (harness defects) |
| [horizon-fresh-m4r-stop-memo.md](../archive/horizon-fresh-m4r-stop-memo.md) | M4R STOP, narrowed scope, required-IC arithmetic |
| [horizon-fresh-m4rb-preregistration.md](../archive/horizon-fresh-m4rb-preregistration.md) | M4R-b F1/F2 locked before authority runs |
| [horizon-fresh-m4rb-stop-memo.md](../archive/horizon-fresh-m4rb-stop-memo.md) | M4R-b F1+F2 FAIL → §14 capability FAIL |
| [horizon-m9-range-monetization-charter.md](horizon-m9-range-monetization-charter.md) | M9 successor charter (open; V1 PASS) |
| [horizon-m9-v1-preregistration.md](../archive/horizon-m9-v1-preregistration.md) | V1 locked before authority run |
| [horizon-m9-v1-memo.md](../archive/horizon-m9-v1-memo.md) | V1 dual-fold PASS |
| [horizon-ev-net-rebuild-stop-memo.md](../archive/horizon-ev-net-rebuild-stop-memo.md) | Why another barrier grid is forbidden |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Live production map until M8 |
| [precision-execution-bridge-charter.md](precision-execution-bridge-charter.md) | Orthogonal falsification on frozen Top-K |
| [coding-conventions.md](../coding-conventions.md) | How to write the code as you go |

---

## Appendix — Milestone → blueprint map

| Milestone | Blueprint sections |
|---|---|
| M0–M1 | §9 data gaps, §10.2 / §10.6 diagnostics, §13 step 1 |
| M2 | §3 Stage A |
| M3 | §4 Stage B, K1–K2, §10.5 clock control |
| M4 | §5.1–5.2 event clock + meta-label primary |
| M5 | §5.3–5.4, §8 models, K3–K4 |
| **M5R** | §8.2 calibration + ranks, §9.1 measurement bias, §10.3–10.4 gate repair |
| **M4R** | §5.2 one rule / one sleeve / one head, §7 Rev 2 sleeve order |
| **M5P** | §10.3 three-way K4 rule, §10.4 MDE reporting |
| **M5P-b** | §1.6 vertical-only, §3.1 `c_eff` hurdle, §10.3 pooled K5 + selection-power |
| **M4R-b** | §10.2 selection is the job, §3.1 `c_eff`, §15A required-IC arithmetic |
| **M9** | §15A what was established, §15B successor hypotheses + rejections |
| M6 | §6 Stage D, K5 |
| M7 | §12 Precision boundary |
| M8 | §7 second sleeve, §14 capability sentences, §15 production relation |
