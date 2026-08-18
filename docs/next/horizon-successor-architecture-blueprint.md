# Horizon Successor — Architecture Blueprint

**Market:** NSE India. Product is *not* assumed to be Nifty-100 cash MIS.  
**Status:** **BLUEPRINT Rev 3** — successor **STOPPED**. V2p-c PASS (range); last-trade V2 FAIL (report); S4-P1 waived; P2 STOP at `c_max` ≈ 4.5; S6 INCONCLUSIVE. Production cascade frozen. Not a dual-judge charter. Not a merge authority.  
**Date:** 2026-08-18 (Rev 3)  
**Depends on (facts, not reopen):** [horizon-fresh-architecture-blueprint.md](horizon-fresh-architecture-blueprint.md) Rev 3, [horizon-fresh-architecture-implementation-plan.md](horizon-fresh-architecture-implementation-plan.md) (post-M5 implementation review), [horizon-m9-range-monetization-charter.md](horizon-m9-range-monetization-charter.md), [horizon-m9-v1-memo.md](../archive/horizon-m9-v1-memo.md), [horizon-fresh-m4rb-stop-memo.md](../archive/horizon-fresh-m4rb-stop-memo.md), [horizon-ev-net-rebuild-stop-memo.md](../archive/horizon-ev-net-rebuild-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](../archive/rt-cost-realism-re-derivation-stop-memo.md), [regime-tier1-stop-memo.md](../archive/regime-tier1-stop-memo.md), production cascade map in [cascade-strategy-overview.md](../cascade-strategy-overview.md)

**Implementation map:** [horizon-successor-implementation-plan.md](horizon-successor-implementation-plan.md)

---

## One-line

Directional cash is closed. The range head is incremental (`b_q50` ≈ 0.60) and **V2p-c PASS**es as a short-premium *range* filter (pooled paired CI [+19.6, +32.6] bps). That did not print as 09:45–15:15 ATM straddle PnL (last-trade V2 **FAIL (report)**, [−1.9, +3.1] bps). Do **not** buy vendor quotes. P2 fade is real and bounded to `c < 4.5` bps, below forward SSF friction. S6 is **INCONCLUSIVE**. Production cascade stays frozen. Stop memo: [horizon-successor-stop-memo.md](../archive/horizon-successor-stop-memo.md).

---

## Verdict on Horizon Fresh Rev 3

**I do not fully buy the current research strategy.** The Fresh *science* (arithmetic, gate hygiene, M4R-b FAIL, the V-gate measurements) is earned and I inherit it. The Fresh *next spend* (name-option V2 / marks stub after name V1 PASS; Track B still blocked on SSF history; M6–M8 still sitting as blocked cascade cutover) is the wrong next programme for this desk.

| Layer | Buy-in |
|---|---|
| Governing arithmetic (§1), `c_eff` (§3.1), vertical-only for thin drift (§1.6) | **Full** |
| Stages A/B as infrastructure; K1/K2 PASS; range Spearman ~0.61 | **Full** |
| Directional cash MIS §14 FAIL (M4R-b F1+F2) | **Full** |
| Gate hygiene, MDE, three-way K4, pooled K5, one-rule/one-sleeve | **Full** |
| Forbidden remount of Top-K / H=6 / 60–30; Precision cannot launder Horizon | **Full** |
| M9 primary = sell *single-name* range in options (Rev 1: blocked on M9-0; now: V1 PASS → name V2) | **Reject** (still; see Rev 2) |
| V1-index as methodology rehearsal only | **Reject** — it is P1 V1, and it has **PASS**ed |
| Track B SSF ranked secondary *and* blocked on futures history before a cheap bound | **Reject** |
| Keep M6–M8 / Stage C–D cascade cutover as the latent architecture | **Reject** |
| Precision Execution Bridge still open as a 12–19 bps recovery hypothesis | **Reject as a research priority** |
| Treat name-level V1 PASS as Track A authority that unlocks name-option V2 | **Reject** — stale EOD control; wrong instrument |

The rest of this document is the replacement strategy. It does not reopen closed ledgers.

---

## Rev 2 — what landed after Rev 1 (2026-08-17)

Rev 1 ranked **in-repo kill-switches** (V1-index + nested HAR; C0 haircut) ahead of M9-0. Fresh ran M9-0 anyway, published V1-index, and recorded name-level V1 PASS. The ranking dissent **stands**. The coefficient ladder is why.

### Increment ladder (do not flatten these into one “V1 PASS”)

| Test | Instrument | Control | `b_q50` | `b_imp` | Read for *this* programme |
|---|---|---|---|---|---|
| **V0** names vs India VIX | 82 names | Common VIX | **≈ 1.0–1.1** | (VIX) | Idiosyncratic vol. Plumbing only. Not a product. |
| **V1-index** Nifty vs VIX | `^NSEI` | Same-session VIX, \(\kappa=1.6\) | **≈ 0.60 / 0.61** | (VIX) | **P1 V1 PASS.** Log `m9_v1_index.log`. **V1n PASS.** **V2p INCONCLUSIVE** (residual>0 thin). **V2p-c PASS** (short tercile). |
| **Name V1** vs lagged ATM | Names | T+1 EOD ATM (M9-0) | **+0.952 / +0.917** | **+0.153 / +0.127** | Fresh Track A PASS ([memo](../archive/horizon-m9-v1-memo.md)). For P1 this is **report-only**: the “implied” barely prices remaining-session range. Clock mismatch, not a live vol market. |

A head that looks incremental against a **stale** control is exactly the failure mode Rev 1 §2.1 named. The converse of “a FAIL may be staleness” is now measured: a PASS *was* staleness. `b_imp` ≈ 0.14 says lagged EOD ATM is not the option market Stage B would trade against.

**Lock:** name V1 PASS does **not** unlock S4 name-option marks, does **not** waive V1n/V2p, and does **not** make single-name options the primary product. Fresh’s next action (“V2 once mids/marks exist” on V1-selected *name* sessions, including `eval_horizon_m9_v2_stub.py`) is the wrong spend.

### What the Fresh implementation review changes (hygiene, not ranking)

Reviewed 2026-08-17 against blueprint Rev 3. Verdicts are implementation completeness on a closed directional product. Successor work **consumes the repaired library** and **does not reopen frozen ledgers**.

| Item | Review finding | Successor implication |
|---|---|---|
| **`k5_pooled`** | Correct, unit-tested, **no live caller** (M6 was the intended consumer and is blocked) | **S2 is the first production caller.** Do not reimplement pooled K5. |
| **M5P purge** | Was display-only (`train_end_disp`); now `apply_purge_date_filter` holds out the last 5 calendar days of the train year | S1/S2 must apply the real filter, not reprint a date. |
| **M4R-b disaster stop** | Dropped paths with drift < −500 bps (left-tail truncation, K4 biased up). Now clips to `−sl_floor`. FAIL still stands | S2 C0 uses the **clip**, never the drop. |
| **M6 harness** | Remounted M5 Stage C; now hard-exits 3. `admit.py` helpers kept | Stay archived. A future book gets instrument-specific D. |
| **M4R N-bar exhaustion** | Listed in Build, never coded. Frozen after pool STOP | Do not add it as a P2 companion. |
| **F2 residual** | Full M4R per-rule ledger was never reprinted on `c_eff`; R2017–R2022 were pre-registered and **not run** | C0 runs the 8-fold design. Per-rule `c_eff` reprint is a companion on the **frozen** sleeve family, not a new rule search. |
| **K3 conjunction** | ECE-only; now ECE **and** max-gap ≤ null p95 | P1 does not use K3. Leave the gate as repaired. |
| **Name V2 stub** | `eval_horizon_m9_v2_stub.py` + `v2_straddle.py` — EOD settle T→T+1 hold, clock-mismatched vs remaining-session; blocked on `option_marks_daily.parquet` | **Not** P1 V2. Do not acquire name marks to unblock it. |

Directional cash remains **CLOSED**. Stages A/B survive as infrastructure. M6–M8 stay scaffolding.

---

## 1. What the programme has actually established

Recorded so it is not re-litigated. Sources are dual-fold or 8-fold on harnesses that satisfy Fresh §10.4.

### 1.1 Closed products

| Product | Result | Source |
|---|---|---|
| Production Top-K + H=6 + 60/30 cash MIS | Relative rank can lift; selected H4 stays **−12…−19 bps** | Path-density, cost, MFE, admission, EV-net |
| Unconditional Long eligible \(EV_{net}\) under reachable geometries | **−20…−22 bps**, CI UB ≤ −17 | EV-net Step 0 |
| Horizon Fresh Stage C on cash events | Long continuation **negative gross**; best Short-fade **+6–8 bps** | M5R, M4R |
| Selector on the winning sleeve | IC **0.022** vs need **0.054** at flat 20; F1 FAIL | M4R-b |
| Liquid-tail `c_eff` (~7–8 bps median) | Still no dual-fold \(EV_{net}\) CI LB > 0; F2 FAIL | M4R-b |
| Regime as an *economic* index gate | I1 / I5 FAIL; A0 CLOSED — frozen soft overlay only | Regime A0 |

**Lock:** Nifty-100 *directional cash MIS* is not a Horizon product under this family’s hypotheses. Do not spend another peek on cash Stage C, geometry grids, or Precision-as-bailout.

### 1.2 Surviving assets (not products)

| Asset | Measured | What it is allowed to become |
|---|---|---|
| Remaining-session **range** forecast | Spearman **0.607–0.635** pooled, **0.617** within-clock (M3 K1) | A *vol* signal, if and only if it is incremental to **implied** on the instrument you can actually trade |
| Index increment vs VIX | V1-index `b_q50` **≈ 0.60 / 0.61** dual-fold (same-session VIX) | **P1 V1 PASS.** **V1n PASS.** V2p residual>0 **CLOSED**. **V2p-c PASS** (pooled paired CI [+19.6, +32.6] bps). |
| Name increment vs lagged ATM | Name V1 `b_q50` **+0.95 / +0.92**, `b_imp` **+0.15 / +0.13** | Report-only for P1. Confirms T+1 EOD is a weak control. Not a name-options charter. |
| Short **fade / reject** event drift | **+6.2 / +7.8 bps** (`prior_day_high_reject`), CI UB ≈ +16.8; two companion Short-fade rules same sign | A *directional* signal, if and only if friction of the **instrument** sits under that drift with a passable pooled test |
| Stage A `c_eff` | Median **7–8 bps** on the liquid tail vs universe-average 20 | A cost model, not a product |
| Validation harness | 8 rolling folds, K4 MDE **9.0–12.6 bps**, pooled K5 (library only), conformal helpers, real purge, disaster **clip** | Reuse; do not rebuild. First live `k5_pooled` caller is P2 C0. |

V0 (`range_q50` vs India VIX on *names*) printed `b_q50 ≈ 1.0–1.1`, p ≈ 0. That is **not** evidence of a tradable vol edge. India VIX is the same number for every name; a name-level range head *must* look incremental. V0 motivates nothing except “the OLS plumbing works.” V1-index + V1n show the head is incremental; V2p residual>0 never selected a passable session set.

### 1.3 The required-IC lesson (process, not just a number)

Fresh §15A is the right comparison and it arrived **after** M5. A production research desk publishes it *before* building a meta-label head:

\[
\text{required IC} \approx \frac{c - \delta}{\sigma \cdot \mathbb{E}[z \mid \text{selected}]}
\]

On this book: \(\delta \approx 7\) bps, \(c^* = 20\), \(\sigma \approx 137\) bps at 200/100 → need **0.054** to breakeven and **~0.10** for margin, against a measured directional ceiling of **~0.07**. That single line should have been the M4 exit, not an M5R post-mortem.

**Lock for every successor hypothesis:** the first page of the charter states instrument, friction of *that* instrument, measured \(\delta\) or forecast skill, required skill vs ceiling, and a kill-switch that can fire on **in-repo data** in ≤2 machine-days. Data acquisition is earned by a cheap PASS. It is never the critical path of the *first* test. Name V1 PASS does not satisfy this lock: the control was not the instrument’s live implied.

---

## 2. Where Fresh ranks the next work — and why I dissent

Fresh §15B ranking, as *executed* after the implementation review:

1. **Primary:** sell range in *single-name* options. M9-0 is **done**; name V1 dual-fold **PASS**; next Fresh action is **V2 on name sessions** blocked on option mids/marks (including a T→T+1 EOD straddle stub).  
2. **Secondary:** same fade signal on single-stock futures (still blocked on SSF history; C0 never run).  
3. Rejected: hedged cash, wider universe, multi-day cash delivery, more directional features.

The rejections are still correct. The ranking of (1) and (2) is still not. Rev 1 objected to putting M9-0 on the critical path; Rev 2 objects to treating the resulting stale-IV PASS as a product.

### 2.1 Single-name options as primary is the wrong Indian vol product

| Fact | Implication |
|---|---|
| The liquid vol market in India is **Nifty / BankNifty options**, not 88 cash names | If Stage B has vol information, the first place it can pay for itself is **index options** |
| M9-0 is **T+1-legal EOD ATM IV** joined onto an *intraday* remaining-range decision | Clock mismatch, now **measured**: name V1 `b_imp` ≈ 0.13–0.15 vs `b_q50` ≈ 0.92–0.95. The control did not price the object. |
| Name V1 PASS (Fresh authority) | Unlocks Fresh Track A V2 *as specified*. It does **not** pass P1. P1 V1 is V1-index, already PASS, still missing V1n/V2p. |
| Single-name option bid–ask is often a large fraction of premium; STT is on premium; lots are coarse | Name V3 will likely kill a real increment. Spending on `option_marks_daily.parquet` now learns microstructure on the wrong book. |
| V1-index dual-fold **PASS** on `^NSEI` + `^INDIAVIX` | That test **is** P1 V1. Fresh still writes that it “does not replace name-level V1.” For an index-vol product, name V1 is the rehearsal. |
| Live v1 ([live-architecture.md](../live-architecture.md)) is a cash-equity bar-cadence monolith | Index options are a bounded OMS extension (one underlying, SPAN). Single-name option execution is a different business |
| Name V2 stub holds T settle → T+1 settle | Even weaker clock than remaining-session. Not a proxy for P1 V2p or index-option V2. |

**Revised primary (unchanged):** index remaining-range vs India VIX / Nifty implied, monetized in **index options** (range-space V2p until marks exist). Single-name IV is a *capacity expansion* after index V2/V3, with **same-session** IV — not T−1 EOD as a production join, and not because name V1 already printed a PASS.

### 2.2 Track B is under-ranked and over-blocked

M4R-b F2 showed cash `c_eff` ≈ 7–8 bps still does not clear a dual-fold lower bound. That does **not** require downloading SSF history to ask the next question.

The winning sleeve’s *unconditional* drift is ~+7 bps. Futures round-trip on liquid F&O names is typically a few bps, not 20. The honest first test is:

> Reprint the M4R Short-fade pool, vertical-only, pooled across the **8 rolling folds already standing**, at haircut costs **3 / 5 / 8 bps**.

- FAIL at 3 bps (pooled K5 + sign test) → Track B is dead; do not acquire SSF.  
- PASS at 3, FAIL at 8 → SSF data is *earned*.  
- Dual-fold A+B was underpowered for a ~4 bps net; M5P already bought the 8-fold design for this.

M4R-b pre-registered R2017–R2022 as report-only and **did not run them**. That is a one-harness gap, not a new causal hypothesis.

### 2.3 Cascade cutover (M6–M8) is not a latent architecture

Stages C/D, conformal admit, Kelly, Precision-on-new-registry, and production cutover were the right *shape* for a cash directional book that never appeared. Keeping them “blocked” in the same plan is how previous charters leaked into the next one (EV-net → Fresh → M9 while M6 still remounted M5 Stage C).

**Lock:** archive Fresh M6–M8 as scaffolding. A future book gets an admit/sizing layer designed for *its* instrument (vega/gamma for options; lot and margin for SSF). Do not inherit `geometry_argmax` or Top-K.

### 2.4 Precision Execution Bridge is the bailout Fresh forbade

The bridge charter still asks whether 1m timing can recover **12–19 bps** on frozen production Top-K. Fresh §12’s own prior is **2–4 bps** of entry timing on a multi-hour hold. After M4R-b, the production book is a closed scientific dead end, not “H5 PASS, monetize it.”

**Lock:** do not dual-judge the Precision bridge as a Horizon-recovery programme. If it ever runs, it is a 2–4 bps measurement on a frozen registry with no cascade-ready language — and it is not on this successor’s critical path.

### 2.5 Do not remount Regime as “just trade Nifty futures”

I1 failed on the **index** vs a TOD-matched null (Regime A0). Index futures directional using the frozen triad HMM is not an unused free lunch. A new index-*direction* hypothesis would need a new causal story, not a cost haircut on a failed I1. This blueprint does **not** reopen Regime search.

---

## 3. Product-first architecture (replacement for Stages A–D as the system)

Horizon Fresh was a four-stage *subsystem* under Tier 2. That was the right test of “can cash directional work if we change clock, span, and admit?” The answer is no. The successor is not another subsystem. It is **two product lines sharing infrastructure**, each with its own economics.

```
Shared infrastructure (keep)
  Stage A  c_eff / tradability     — cost model; cash-only until SSF exists
  Stage B  remaining-range head    — K1/K2 already PASS on names
  Harness  purged 8-fold, MDE, pooled K5, session-block CI

Product P1  INDEX VOL                         Product P2  CHEAP-INSTRUMENT FADE
  residual = forecast − implied                 δ = event drift to MIS flatten
  instrument = Nifty options                    instrument = SSF (not earned)
  V1 / V1n / V2p-c PASS                         C0 PASS at 3; STOP at c_max ≈ 4.5
  S4-P1 marks earned → V2/V3                    S6 INCONCLUSIVE; no SSF download
```

Regime remains a frozen soft overlay where a cash or SSF sleeve still wants a session veto. It is not a PnL engine (A0). Precision is not in the successor until a product has a positive admitted book of its own.

### 3.1 Opportunity gate is product-specific (do not inherit 10c)

Stage B’s `q25 ≥ 200 bps` rule was sized for a **300 bps barrier span** that this programme no longer uses.

| Product | Gate |
|---|---|
| P1 index vol | Residual \(\widehat{R} - R^{\mathrm{imp}}\) exceeds a pre-registered threshold (and **V1n** PASS). High predicted range alone is not an edge — implied already knows high-vol days. |
| P2 fade | Event transition ∩ (optional) liquidity mask. Range gate is **not** required: fade drift was measured *inside* A∩B; S2 must also publish the ungated event pool so we do not bake Stage B into a directional product that no longer needs span. |

### 3.2 What “Stage C / D” means now

| Product | C (opinion) | D (book) |
|---|---|---|
| P1 | Sign of residual; optional magnitude threshold. **No** barrier-race head. | Vega cap, short-vol ban until V2 says otherwise, daily loss in premium points, expiry calendar |
| P2 | The primary *rule* is the opinion (M4R already showed ML did not concentrate: F1 admit **70% / 96%**). ML veto only if S2 PASS and a new IC gate is pre-registered. | Lot-size, F&O eligibility survivorship, concurrency, daily loss. Vertical-only + disaster stop. |

**Lock:** one rule, one sleeve, one head still applies if a veto model is ever fitted. F1’s near-full admit rate is evidence that a GBDT meta-label on this sleeve is not doing economic work.

---

## 4. Product P1 — Index vol (primary)

### 4.1 Hypothesis

Stage B predicts remaining-session range. India VIX (and Nifty implied) already prices a HAR-style forecast plus a variance risk premium. The tradable object is **realized remaining range − implied remaining range** on **Nifty**, not on 82 names vs a common VIX.

Instrument after a V2 PASS: Nifty ATM straddle / strangle (or calendar-safe equivalent) over the remaining cash session. **Default bias is short premium** — V2p-b showed `range_q50` sits below VIX-implied almost always, so the residual sign is nearly always negative (VRP + uncalibrated κ). Long premium is the opt-in that residual>0 already showed does not select. Short premium needs its own V2p-c gate, a hard daily premium-loss cap, and no new entries into a defined flatten window.

### 4.2 Why the remaining gates are still in-repo

V1 is already published (`eval_horizon_m9_v1_index.py`, folds A/B, no `volume_z`). Remaining P1 kill-switches use the same two files: `data/GOLDEN/^NSEI.csv`, `data/GOLDEN/^INDIAVIX.csv`.

India VIX is a **~30-day** IV. Converting it to remaining-session range via \(\kappa \cdot \sigma_{\mathrm{day}} \cdot \sqrt{f}\) (Fresh M9, \(\kappa=1.6\)) is a **model**. V1 PASS at \(\kappa=1.6\) does not prove the head beats a HAR that the option market already has. Nested controls exist so we do not PASS P1 for the wrong reason — the same lesson as name V1 vs stale ATM.

`incremental_range_ols` is still a two-regressor helper. V1n requires a 3+ column design; extend it, do not copy-paste a second OLS.

### 4.3 Gates (pre-register before the peek)

| ID | Gate | Rule | Status | If FAIL |
|---|---|---|---|---|
| **V1** | Incremental information (authority) | On **Nifty** remaining range: `range_q50` coef > 0, dual-fold, after controlling for VIX-implied remaining range | **PASS** 2026-08-17 (`b_q50` ≈ 0.60 / 0.61) | Stop P1; do not “try names” as a salvage |
| **V1n** | Nested HAR control (authority companion) | Same regression plus a causal Nifty HAR/Parkinson remaining-range baseline. `range_q50` must still be significant with the right sign | **PASS** 2026-08-17 (`b_q50` +0.57 / +0.62) | Head is redundant with HAR; option market already has this; stop P1 |
| **V1κ** | Conversion sensitivity (report-only) | Reprint V1 at \(\kappa \in \{1.4, 1.6, 1.8\}\). Authority stays at 1.6 | **PASS** all three (report-only) | Informs, does not waive V1 |
| **V2p** | Long residual>0 (retired) | residual > 0 at first bar, then 09:45 | **CLOSED** at both clocks (`s1_v2pb.log`). Empty set is the finding, not a clock bug. Do not scan 10:00 / q75 | — |
| **V2p-c** | Recalibrated **short** residual (authority remaining) | Fit `realized ~ implied` on **train**; select **bottom tercile** of standardized residual at 09:45. Statistic = paired difference: mean(`R_imp − R`) on selected **minus** all-session mean. Incremental to unconditional short vol | **PASS** 2026-08-18 (`s1_v2pc.log`). Range-space only | — |
| **V2** | Index option marks | Gross Nifty straddle/strangle PnL on the **same** V2p-c selection. **Same-session** chain, not EOD bhavcopy | **FAIL (report)** last-trade (`s1_v2_zenodo.log`). Quote V2 **waived** | Edge unsigned in premium space; stop P1 |
| **V3** | Net of option friction | V2 − premium spread − STT on premium − slippage (− delta-hedge if hedged) | **Not earned** | Edge below friction; stop P1 |

**V1-index is authority for P1**, not a rehearsal. Name-level V1 ran and PASSed against lagged EOD ATM; it remains **out of scope as P1 authority** (report-only). Phase-2 capacity after V3 needs **same-session** name IV — not T−1 EOD as a production join, and not `eval_horizon_m9_v2_stub.py`.

### 4.4 Explicit P1 rejects

| Reject | Why |
|---|---|
| Treat V0 name-vs-VIX incremental as encouragement | Tautological idiosyncratic vol |
| Treat name V1 PASS as P1 PASS or as a waiver of V1n | Stale control (`b_imp` ≈ 0.14); wrong instrument |
| Run the name V2 stub / acquire `option_marks_daily.parquet` as the next peek | Overnight EOD hold, name book, blocked on marks Fresh does not have. Not V2p and not index V2 |
| Short vol without V2p-c and a daily premium-loss cap | Gap/open + weekly pin; the *side* is measured, the *session product* is not |
| EOD FO bhavcopy as a remaining-session V2 mark | Same clock mismatch that made name V1 `b_imp` ≈ 0.14 |
| Claiming “Spearman 0.6 is an edge” | Forecast of realized is not forecast of realized−implied |

---

## 5. Product P2 — Cheap-instrument fade (parallel, cheap first)

### 5.1 Hypothesis

Indian single-name *intraday* fades rather than continues (M4R: every continuation rule tested was the wrong sign for Long). The effect is real and bounded: best CI UB ≈ **+17 bps** against cash `c* = 20`. Attack **\(c\)**, not \(\delta\). Do not reopen feature fishing (Fresh §15B rejection stands).

Sleeve (frozen): `prior_day_high_reject` Short as primary; companion report-only `vwap_loss` Short and `gap_fill_short` (same-sign family). **Do not** add the unimplemented M4R “N-bar exhaustion” rule — that would be a new pool peek after STOP.

Geometry: **vertical-only** to MIS flatten + wide disaster stop (Fresh §1.6). Barriers destroyed thin drift on M5R identical-row comparison.

### 5.2 Gates

| ID | Gate | Rule | If FAIL |
|---|---|---|---|
| **C0** | 8-fold cost bound at 3 bps | Unconditional sleeve pool. Pooled \(EV_{net}\) at **c = 3** with `k5_pooled` + sign ≥5/6 | Historical **PASS** (`s2_c0.log`). Bounds the sleeve, not the instrument |
| **C0-ladder** | Instrument bound (authority for “is SSF earned”) | Same harness; `k5_pooled` at **every** pre-registered haircut 3/5/8. `c_max` = haircut where pooled CI LB crosses 0. Forward SSF RT schedule published beside it | **P2 STOP** if LB ≤ 0 at c = 5. Do not download SSF. Arithmetic from c=3: `c_max` ≈ **4.5 bps** |
| **C1** | Power / MDE | Declare expected session count and MDE *before* the peek. Book-capped / ADV-restricted reprints with MDE ≥ the effect are unpassable — do not run them as authority | Repair harness; do not acquire data to “get a number” |
| **S0 / S1 / S2** | SSF panel | **STOP — not earned.** Forward SSF RT ≈ 5–10 bps (STT 0.02% sell-side post-Oct-2024 + spread + MIS exit) sits **above** `c_max` ≈ 4.5. Sample-era futures STT was half of today’s | Do not open S4-P2 |

F1 already showed a selector does not create the edge (IC 0.022, admit rate not sparse). C0 is a **pool** test. A later veto model is allowed only after C0 PASS and a new required-IC line at the *measured* S1 hurdle.

### 5.3 Why not make P2 primary

P2 fade is **real and bounded**. Pooled EV_net ≈ +5.2 bps at c = 3 (`c_max` ≈ 4.5 for LB > 0). A cheaper instrument at the **same** intraday horizon does not clear: forward SSF RT ≈ 5–10 bps. Attack **`c/σ`**, not `c` — a 2–10 session futures hold is the remaining lever. P2 as an *intraday* product is **stopped at forward friction**. Do not smuggle a multi-day hold into C0; that is a new family (S6).

---

## 6. Shared locks (inherit from Fresh, restated)

Inherited locks plus Rev 2 additions (name V1 / V2 stub / `k5_pooled`).

| Lock | Rule |
|---|---|
| `c* = 20` | Universe-average **cash** working assumption and stress reprint. Per-trade cash hurdle is `c_eff`. P1/P2 use **instrument** friction, not 20, in their own EV |
| Absolute labels | Unhedged products use absolute path − cost, not Nifty-excess, unless a hedge leg is funded |
| Vertical | Thin-drift directional sleeves: MIS flatten, not H=6 |
| Tight stops | Forbidden as silent risk control; justify with measured \(EV_{net}\) improvement on that sleeve |
| Top-K | Capacity only, never the economic gate |
| Production cascade | Frozen until an explicit ship decision on a **new** product. No silent swap of `predict_horizon_gbm` |
| Gate validity | Passable by a correct model; inputs can carry the effect; MDE published; statistic matches the claim (Fresh §10.4 + M4R checklist) |
| Geometry sweep | Still forbidden until a directional K4 PASS exists — and none does |
| More cash directional features | Forbidden (8 folds bound the effect) |
| Hedged cash / wider cash universe / cash delivery multi-day | Still rejected (Fresh §15B) |
| Name V1 | Report-only for this programme. Does not unlock name-option marks or waive V1n/V2p-c |
| Name V2 stub | Frozen. P1 V2 is Nifty options after V2p-c, remaining-session, not T→T+1 name straddles |
| `k5_pooled` | Live callers are P2 C0 / C0-ladder. Do not reimplement |
| Forward friction | Pre-register a **2026** instrument schedule; sample-era futures STT is not the forward hurdle |
| Book-capped C0 reprints | Unpassable at 1–4 fires/day (MDE 7–11 bps vs 3–5 bps effect). Capacity is sizing, not a gate |
| Option-mark clock | Must match the product clock. EOD bhavcopy is not a remaining-session V2 mark |

Diagnosis locks 1–17 in Fresh Appendix B carry forward unchanged.

---

## 7. Retrospective: how I would have run Fresh M0–M8

The M0–M3 path was high leverage (parquet, ceiling, Stage A, K1/K2). The waste was **Stage C complexity before product arithmetic**, and **successor ranking after FAIL**.

| What happened | What I would have done |
|---|---|
| M5 Long-continuation + geometry sweep before a drift-sign ledger | **M4R first.** Sleeve from evidence, not “Long-only to halve tests” |
| Geometry as a decision with invariant probabilities | Do not write a sweep until stacked geometry labels exist; after M5R evidence, default vertical-only *before* any sweep |
| Required-IC published in Rev 3 after M4R | Publish at M4 exit, as a sleeve-selection gate, not a memo insight |
| M6–M8 scaffolds while Stage C unproven | Do not build admit/Precision/cutover until K4 PASS. M6 later remounted broken M5 — that was predictable |
| M5 STOP invoked FAIL from an unpassable harness | The Rev 2 hygiene rules are correct; they should have been in Rev 1. I keep them |
| After M4R-b FAIL → M9-0 as critical path | After FAIL → **in-repo kill-switches** (V1-index + V1n + C0), then earn data |
| M9-0 + name V1 PASS (`b_imp` ≈ 0.14) treated as Track A authority | Publish V1-index as P1 V1 (done). Nested HAR next. Do not spend on name marks because a stale control printed incremental |
| Implementation review: M6 remount, purge display-only, disaster drop | Hygiene was the right post-mortem. Consume the repaired library; do not reopen frozen rules |

I would **not** have skipped Fresh. EV-net correctly forbade another H/TP/SL grid. Event clock + range gate + absolute admit was the right causal test of cash directional. I would have made that test smaller and sooner, and I would not have treated a four-stage cascade replacement as the company.

---

## 8. Capability sentences

| Path | Sentence |
|---|---|
| **PASS (P1)** | On Nifty, the range head is incremental to VIX-implied **and** to a causal HAR baseline; **V2p-c PASS** (short residual, incremental to unconditional short vol). V2/V3 on earned same-session index marks remain. |
| **FAIL (P1)** | V2p-c CI LB ≤ 0 on a passable harness — then Stage B is a filter, not a vol product. Residual>0 is already closed. Do not salvage with name V1. **Did not fire.** |
| **PASS (P2)** | *Intraday* SSF is **not** a PASS path at forward friction. Historical C0 PASS at 3 bps stands as a sleeve bound only. |
| **FAIL (P2)** | C0-ladder LB ≤ 0 at c = 5 **or** forward SSF RT floor ≥ `c_max` — stop the instrument change. Do not download SSF. **Fired** (`c_max` ≈ 4.5). |
| **FAIL (programme)** | V2p-c FAIL **and** multi-day fade (S6) FAIL on passable harnesses — **does not fire** (V2p-c PASS; S6 INCONCLUSIVE). |
| **INCONCLUSIVE** | S6 T+3 MDE 10.2 ≥ 6 bps — abort data spend; do not record S6 FAIL. |

---

## 9. Out of scope

- Dual-judge scores / peek IDs / merge authority  
- Live OMS redesign (index-option execution is a **follow-on** architecture note after V2p, not a v1 live-architecture rewrite)  
- Cost shopping on cash below the signed `c*=20` identity  
- Remounting CLOSED Admission / veto / TP-floor / path-density / EV-net / Fresh Stage C  
- Claiming cascade-ready from this document  
- Reopening Regime I1/I5 search  
- Adding event rules after M4R STOP (including the unimplemented N-bar exhaustion rule)  
- Acquiring name-option marks or running `eval_horizon_m9_v2_stub.py` as a P1 gate  

---

## 10. Relation to existing docs

| Doc | Relationship |
|---|---|
| [horizon-successor-implementation-plan.md](horizon-successor-implementation-plan.md) | Milestone map (S0–S6) Rev 3 for this blueprint |
| [horizon-fresh-architecture-blueprint.md](horizon-fresh-architecture-blueprint.md) | **ARCHIVE.** Closed cash-directional test. Arithmetic and hygiene inherit; ranking does not |
| [horizon-successor-s2-cost-ladder-memo.md](../archive/horizon-successor-s2-cost-ladder-memo.md) | C0-ladder: `c_max` ≈ 4.5; P2 STOP |
| [horizon-successor-s1-v2pc-preregistration.md](../archive/horizon-successor-s1-v2pc-preregistration.md) | P1 peek (locked) |
| [horizon-successor-s1-v2pc-memo.md](../archive/horizon-successor-s1-v2pc-memo.md) | V2p-c PASS |
| [horizon-successor-s6-multiday-fade-charter.md](horizon-successor-s6-multiday-fade-charter.md) | New family after P2 STOP |
| [horizon-successor-s6-multiday-fade-memo.md](../archive/horizon-successor-s6-multiday-fade-memo.md) | S6 T+3 INCONCLUSIVE |
| [horizon-successor-s4-p1-index-marks-charter.md](horizon-successor-s4-p1-index-marks-charter.md) | S4-P1 acquisition spec; **waived** |
| [horizon-successor-s1-v2-preregistration.md](../archive/horizon-successor-s1-v2-preregistration.md) | V2 locked before marks |
| [horizon-successor-s1-v2-zenodo-memo.md](../archive/horizon-successor-s1-v2-zenodo-memo.md) | Last-trade V2 FAIL (report) |
| [horizon-successor-stop-memo.md](../archive/horizon-successor-stop-memo.md) | Product hunt STOP |
| [horizon-fresh-architecture-implementation-plan.md](horizon-fresh-architecture-implementation-plan.md) | Historical M0–M9 map + 2026-08-17 implementation review (harness facts this programme consumes) |
| [horizon-m9-range-monetization-charter.md](horizon-m9-range-monetization-charter.md) | Open M9 charter. This blueprint **re-ranks**: V2p-c on Nifty; SSF not earned; name marks are not the door |
| [horizon-m9-v1-memo.md](../archive/horizon-m9-v1-memo.md) | Name V1 dual-fold PASS — **report-only** here (stale EOD ATM) |
| [horizon-m9-0-data-acquisition.md](horizon-m9-0-data-acquisition.md) | Store COMPLETE. Not P1 authority. Revisit only as Phase-2 (same-session name IV) after index V3 |
| [precision-execution-bridge-charter.md](precision-execution-bridge-charter.md) | Orthogonal; **not** on this successor’s critical path |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Live **production** map until an explicit ship of a *new* product |
| [live-architecture.md](../live-architecture.md) | Cash-equity v1 runtime; P1/P2 do not silently extend it |

---

## Appendix A — Symbols

| Symbol | Meaning |
|---|---|
| \(c^*\), `c*` | 20 bps universe-average **cash** working assumption |
| \(c_{\mathrm{eff}}\) | Row-level cash round-trip |
| \(\delta\) | Conditional drift over the hold (vertical-only) |
| \(R, \widehat{R}, R^{\mathrm{imp}}\) | Realized remaining range, Stage B q50, implied remaining range |
| V1 / V1n / V2p / V2p-c | P1 gates (incremental, nested HAR, residual>0 CLOSED, short residual **PASS**) |
| C0 / C0-ladder / `c_max` | P2 bound at 3 bps; instrument bound; haircut where pooled LB = 0 |

---

## Appendix B — Dissent map (Fresh Rev 3 → this document)

| Fresh claim | This document |
|---|---|
| M9 primary = single-name options; next = name V2 | P1 primary = **index** options; name IV is Phase-2 after index V3 |
| V1-index = methodology rehearsal; name V1 is authority | V1-index **is** P1 V1 (**PASS**). Remaining authority = V1n + V2p. Name V1 is report-only |
| Name V1 PASS unlocks name-option marks | Stale control (`b_imp` ≈ 0.14). Do not acquire `option_marks_daily.parquet` for this programme |
| Track B blocked on SSF data | C0 haircut on cash paths first (`k5_pooled`’s first live caller) |
| Stages A/B/D survive all successors; only C is at risk | A/B survive as **infra**. D is redesigned per product. C directional is discarded |
| M6–M8 blocked pending a book | Archived as scaffolding; review confirmed M6 remount was dangerous |
| Long-only until M7 (plan header residue) | Already superseded by Fresh §7; P2 is Short-fade by evidence |
| Precision re-measure on new registry (M7) | Only after a product PASS; not a Horizon recovery |
