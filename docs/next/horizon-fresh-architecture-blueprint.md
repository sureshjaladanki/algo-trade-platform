# Horizon Fresh Architecture — Blueprint

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Clean-sheet redesign of the Horizon engineering challenge under a single hard constraint  
**Constraint:** Round-trip cost `c* = 20 bps` (locked; not a design knob)  
**Goal:** Cascade only signals with positive expected net PnL — i.e. geometries and admissions where \(\mathbb{E}[\text{TP} - \text{SL} - \text{TO path}] > c^*\) after selection. Otherwise no strategy is economically viable.  
**Status:** **ARCHIVE / CLOSED** — §14 FAIL earned (M4R-b). §15B successor ranking is **SUPERSEDED** by [horizon-successor-architecture-blueprint.md](horizon-successor-architecture-blueprint.md) Rev 3. This file is the closed cash-directional test, not a live architecture.  
**Date:** 2026-08-16 (Rev 2 and Rev 3 same day, after the M5 and M4R post-mortems). Archive banner 2026-08-18.  
**Rev 2 changes:** K3 / K4 gate definitions corrected (§10.3–10.5); per-rule sleeve requirement (§5.2);
geometry-as-feature made a hard precondition (§5.3); sleeve order now driven by a drift-sign ledger (§7);
calibration and cross-sectional ranking promoted to locks (§8.2); label measurement bias added (§9.1).
Nothing in §1 (the governing arithmetic) changed.  
**Rev 3 changes (after M4R STOP):** \(\Delta p\) reframed as a barrier-race property with a vertical-only
default for thin-drift sleeves (§1.6); `c*` clarified as a universe average with row-level `c_eff`
required in EV arithmetic (§3.1); K5 changed to a pooled read with a fold sign test, plus the
selection-power tradeoff (§10.3); measured programme results and the governing IC comparison recorded
(§15A); successor product hypotheses ranked, with rejections (§15B).  
**Freedom assumed:** TP / SL / Long vs Short / models vs rules / n-layer vs simple — all open  
**Depends on (facts, not reopen):** [horizon-ev-net-rebuild-stop-memo.md](../archive/horizon-ev-net-rebuild-stop-memo.md), [cascade-strategy-overview.md](../cascade-strategy-overview.md), [rt-cost-realism-re-derivation-stop-memo.md](../archive/rt-cost-realism-re-derivation-stop-memo.md), production TB / Horizon / Precision contracts under `src/`

---

## One-line

At `c*=20`, Horizon must stop ranking every 15m bar under a 90-minute 60/30 barrier race and instead **gate on predicted session range, form opinions only on structural events, fit barriers to the predicted distribution, and admit only when a conformal lower bound on \(EV_{net}\) clears zero**.

---

## Why this blueprint exists

Prior Horizon ledgers (path-density, MFE-decay, TP-floor, admission, path-quality veto, EV-net rebuild) repeatedly showed:

| Fact | Implication |
|---|---|
| Long Top−Rest / H5 can lift while selected-book H4 stays ~−12…−19 bps | Relative ranking ≠ absolute economics |
| Unconditional Long eligible \(EV_{net}\) under reachable geometries ~−20…−22 bps (CI UB ≤ −17) | Pool itself is underwater after `c*`; scorer cannot invent edge that is not in the barrier span |
| Mean MFE ~43–54 bps with TP hit ~9–15% | Travel exists; it does not convert into barrier wins at current widths |
| EV-net STOP @ 0/3 forbids another H/TP/SL grid under the same contract | Fresh causal hypothesis required — not another ≤3 barrier redraw |

This document is that fresh hypothesis, captured as an architecture — not another peek ladder on frozen production floors.

---

## 1. The governing arithmetic

### 1.1 Barrier breakeven

For take-profit \(g\), stop \(s\), round-trip \(c\):

\[
p_{TP}\cdot g - p_{SL}\cdot s = c
\quad\Longrightarrow\quad
p^*_{TP} = \frac{c + s}{g + s}
\]

A driftless path hits TP first with probability \(s/(g+s)\) (gambler's ruin on absorbing barriers). The **probability edge required over a random walk** is therefore:

\[
\Delta p = \frac{c}{g + s}
\]

**Only the barrier span \(g+s\) and cost \(c\) matter.** Reward:risk ratio, horizon length, and model class do not appear in \(\Delta p\).

### 1.2 Span table at `c = 20` bps

| Geometry (TP / SL bps) | Span \(g+s\) | \(\Delta p\) over RW | Driftless \(P(TP)\) | Required \(P(TP)\) |
|---|---|---|---|---|
| 60 / 30 — production Long | 90 | **22.2 pp** | 33.3% | 55.6% |
| 50 / 30 — production Short | 80 | **25.0 pp** | 37.5% | 62.5% |
| 100 / 50 | 150 | 13.3 pp | 33.3% | 46.7% |
| 150 / 75 | 225 | 8.9 pp | 33.3% | 42.2% |
| **200 / 100** | **300** | **6.7 pp** | 33.3% | 40.0% |
| 300 / 150 | 450 | 4.4 pp | 33.3% | 37.8% |

Production geometry asks a LightGBM to beat a random walk by ~22 pp on 90-minute single-name equity moves. That is not a feature or calibration problem; it is a span problem: production Long span is **4.5× cost** (90/20) when the design needs about **15× cost** (300/20).

### 1.3 Timeout drag

At H=6 under EV-net G1, outcome mix was roughly **TP ~15% / SL ~44% / TO ~42%**. Full `c*` is paid on timeout paths that deliver ~0 gross. That is **~8.4 bps** of pure drag (\(0.42 \times 20\)) with no offsetting payoff, and it lands disproportionately against the far barrier — which is why realized TP rate sat *below* the driftless baseline.

**Timeout is the most expensive outcome per unit of information.** Architecture must keep timeout mass low (target ≤ ~20%), not treat it as a soft “no trade” label.

### 1.4 Dual feasibility bound

Two conditions must hold together:

1. **Span ≥ 15c = 300 bps** — so required edge is ~6–7 pp, not 20+.  
2. **Span ≤ ~1.5 σ_T** — so the barrier race resolves and timeout stays controlled.

Together: **expected move over the holding window ≳ 2%**.

Rough vol back-of-envelope from measured MFE (~50 bps / 90m):

- \(\sigma_{90m} \approx 62\) bps  
- \(\sigma_{15m} \approx 25\) bps  
- \(\sigma_{day} \approx 1.25\%\)

A 2% expected session move is roughly a **1.6× vol day** — on the order of the top ~20–25% of (name, day) cells in Nifty 100.

### 1.5 Immediate architectural consequences

| Consequence | Design lock |
|---|---|
| Vertical barrier | **MIS square-off**, not a fixed 90m H=6 |
| Why not H=6 | H=6 is the **worst available choice** — too long to be a scalp with a tight stop, too short to capture a trend-day move at 300 bps span |
| Eligibility | **Volatility / range forecast**, not a fixed TB bps floor alone |
| Decision clock | **Event clock** (structural breaks), not every 15m bar |
| Trade count | **~1–4 fires/day across ~88 names** is correct economics, not a coverage failure |
| Cascade gate | **Absolute \(EV_{net}\) admit**, not Top-K relative rank |

### 1.6 The \(\Delta p\) requirement is a property of barrier races, not of trading (Revision 3)

Everything in §1.1–1.5 assumes you have chosen to race two horizontal barriers. Drop them and the
requirement disappears: holding to the MIS vertical gives

\[
EV_{net} = \delta - c
\]

where \(\delta\) is realized conditional drift over the hold. There is no \(\Delta p\), no span
table, and no reward:risk geometry to optimize — only "is the drift bigger than the cost."

This matters because the measured evidence now says barriers are **destroying** edge at these signal
strengths. On identical rows, M5R read barrier-race gross return of −10.6 / −5.3 bps against
barrier-free drift to flatten of −5.3 / +4.7 bps. With session \(\sigma \approx 125\) bps a 100 bps
stop sits well inside noise, so it is triggered by randomness rather than by information, and each
such trigger converts a live position into a realized loss.

| Regime | Right exit structure |
|---|---|
| Strong signal, drift ≫ noise over the hold | Barrier race is fine; the span table applies |
| **Thin drift, \(\delta\) of order 10 bps against \(\sigma\) of order 125 bps** | **Vertical-only exit** plus a wide disaster stop; manage risk with Stage D **sizing**, not with a tight stop |

**Lock:** for any sleeve whose measured drift is small relative to session \(\sigma\), the default
geometry is vertical-only. A tight stop must be justified by evidence that it improves \(EV_{net}\)
on that sleeve, not assumed as risk control. Risk control lives in §6.2.

---

## 2. Tier ownership (fresh split)

Regime (Tier 1) stays the market-state gate. Horizon is redesigned as a **four-stage subsystem** (A–D) under Tier 2. Precision (Tier 3) keeps fill timing / exit execution — but is no longer asked to recover a 12–19 bps Horizon deficit.

```
Regime (unchanged role)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  HORIZON (fresh)                                            │
│                                                             │
│  Stage A  Tradability filter        (deterministic)         │
│  Stage B  Opportunity / range gate   (quantile ML)           │
│  Stage C  Direction + geometry EV    (primary rule + ML)     │
│  Stage D  Absolute admission + book (conformal EV + Kelly)  │
└─────────────────────────────────────────────────────────────┘
        │  only if conformal LB(EV_net) > 0
        ▼
Precision (1m fill / skip / inherited exits) — monetize, do not bail out
```

| Stage | Owns | Does **not** own |
|---|---|---|
| **A Tradability** | Where 20 bps is actually achievable (spread / tick / impact) | Direction, barriers |
| **B Opportunity** | Whether remaining-session range clears economic span | Side selection |
| **C Direction + EV** | Primary-rule side + meta-label worth-it + geometry argmax | Force-K emissions |
| **D Admission / book** | Conformal absolute admit, sizing, concurrency / sector caps | Rewriting Regime |
| **Precision** | 1m entry timing, skip selectivity, frozen exits | Re-ranking; salvaging negative Horizon books |

**Forbidden claim even on PASS:** “Precision recovered Horizon economics.” Entry timing on a multi-hour hold is worth maybe **2–4 bps**, not a 12–19 bps deficit bridge.

---

## 3. Stage A — Tradability (deterministic)

Accounting cost is locked at 20 bps, but **effective** cost varies by name:

\[
c_{\text{eff}} \approx \text{statutory} + 2\times\text{half-spread} + \text{tick drag} + \text{impact}
\]

Sketch magnitudes: statutory ~**4 bps**, plus spread / tick / impact. NSE ₹0.05 tick is ~2.5 bps on a ₹200 name and ~0.1 bps on a ₹5,000 name. Spread is a large fraction of a 20 bps budget.

**Rule:** Drop (name, session) cells where working `c*=20` is not realistically achievable. The constraint becomes a **filter on where** you trade, not only a flat tax paid everywhere.

### 3.1 `c_eff` must reach the EV arithmetic, not just the mask (Revision 3)

`c*=20` is the **universe-average working assumption**, not a per-name floor. Statutory cost is only
~4 bps of it; the remaining ~16 bps is spread, tick and impact, and those vary by an order of
magnitude across the Nifty 100. A book that fires 1–4 times a day can confine itself to the liquid
tail, where achievable round-trip is materially below 20.

The M2 implementation computed `c_eff_bps` per row, kept only the boolean `c_eff ≤ 20`, and then let
every downstream EV computation use the flat `C_STAR`. That discards the entire point of Stage A.

**Locks:**

| Lock | Rule |
|---|---|
| EV arithmetic | \(EV_{net}\) uses **row-level `c_eff`**, never the flat constant, wherever Stage A has run |
| `c*` role | Charter-level average for sizing the design problem (§1) and for stress reporting — not the per-trade hurdle |
| Mask | `tradable_ok` remains, but as a sanity bound on the tail, not as the cost model |
| Reporting | Every K4 / K5 ledger publishes the realized `c_eff` distribution of the admitted set alongside the flat-`c*` reprint, so the two are never confused |

A gate that clears on row-level `c_eff` but fails at a flat 20 bps is a **liquidity-tail product**,
which is a legitimate outcome — provided the capacity that tail supports is stated.

**Inputs to prefer over current `(H−L)/close` spread proxy:**

- Corwin–Schultz or Abdi–Ranaldo high-low spread estimators  
- ADV / ADV-rank (already present as Horizon features)  
- Optional: impact proxy from recent participation

---

## 4. Stage B — Opportunity gate (new Tier 2a)

### 4.1 Why this stage is highest leverage

Direction on single-name intraday equity has very low R² (order **~0.005**). **Range is far more predictable** (often R² ~0.4–0.6 with HAR-style features). Current stack spends modeling capital almost entirely on the unpredictable quantity and almost none on the quantity that sets the cost ratio.

### 4.2 Model

- **Family:** quantile LightGBM (or equivalent GBDT quantile) on **log remaining-session range**  
- **Target:** remaining range from decision time → MIS flatten  
- **Admit rule:** 25th percentile of predicted remaining range **≥ 10c** (200 bps at `c*=20`) — lower quantile, not mean, so the gate is conservative  

### 4.3 Feature sketch (HAR / Corsi-style)

| Family | Examples |
|---|---|
| Opening structure | Opening 30m range, gap |
| Vol state | VIX level / change, 5d realized vol, TOD-normalized RV |
| Cross-section | Sector index range, relative volume z |
| Calendar | Event-day / earnings flag (data gap today — see §9) |

### 4.4 Output contract

Per eligible (symbol, clock):

- `range_q25`, `range_q50`, `range_q75` (or equivalent)  
- `opportunity_ok` Bool — clears 10c on q25  

If Stage B fails OOS, **stop the cascade redesign** — nothing downstream can create span that is not in the data.

---

## 5. Stage C — Direction and EV (Tier 2b)

### 5.1 Event clock (not bar clock)

Form opinions only when a **structural event** fires, e.g.:

- ORB break with volume confirmation  
- VWAP reclaim after N bars on the opposite side  
- Prior-day high / low break  
- Range expansion above 2× TOD-normalized median  

**Effect:** Collapse the decision pool from tens of thousands of 15m rows per fold to a few thousand rows where a causal story for conditional drift can exist. This is the “different entry clock” named as legitimate grounds for a fresh charter in the EV-net stop memo.

### 5.2 Primary rule owns the side; ML only vetoes

Classic **meta-labeling**:

1. Primary rule proposes **Long** or **Short** from the event definition.  
2. ML answers only: *is this instance of the primary signal worth paying 20 bps?*  
3. ML does **not** pick direction.

Removes a large overfitting surface and yields a balanced, well-posed label.

#### One rule, one sleeve, one head (added Revision 2)

“The primary rule owns the side” means **each** rule owns its own side. Rules must not be pooled
into a single head with rule identity as a feature, because a GBDT will spend its splits on
whatever varies most — in the M5 run the four rule one-hots received ~1% of the splits while
volatility features took the rest, so the model could not express per-rule direction even in
principle.

The M5R drift ledger shows why this matters. Barrier-free drift from the event bar to MIS flatten,
by rule, dual-fold (fold A / fold B):

| Rule | Kind | Drift A | Drift B | Sign |
|---|---|---|---|---|
| `vwap_reclaim` | fade / reversion | **+11.1 bps** | **+17.9 bps** | consistently **with** Long |
| `range_expand_2x` | volatility | −7.1 bps | +12.5 bps | inconsistent |
| `orb_break_vol` | continuation | −9.8 bps | −5.5 bps | consistently **against** Long |
| `prior_day_high` | continuation | −13.1 bps | −31.2 bps | consistently **against** Long |

Individually none of these clears its own CI (±25–40 bps), so this is a direction-of-research
signal, not an established edge. But the **sign disagreement is structural**: pooling a fade rule
with two continuation rules of the opposite sign into one Long head averages the signal toward
zero, which is close to what K4 measured. Pre-register a per-rule sleeve, or drop the rule.

**Corollary — the “Long-only first” lock in §7 is not sleeve-neutral.** It presumes continuation.
The two continuation rules carry the wrong sign for Long in both folds, so “Long-only” selected
against the evidence. See §7 Revision 2.

### 5.3 Geometry as a decision variable

Do **not** freeze production floors (60/50/30) or H=6 as the economic design.

Train:

- **Calibrated multiclass head** on \(P(\text{TP first})\), \(P(\text{SL first})\), \(P(\text{timeout})\), with geometry multipliers **passed in as features** so one model spans the grid.  
- **Quantile / conditional head** for \(\mathbb{E}[r \mid \text{timeout}]\).

At inference, for each event instance:

1. Sweep a coarse grid of `(tp_mult, sl_mult)` as fractions of Stage B predicted range.  
2. Compute \(EV_{net}(g,s)\) under calibrated probabilities and `c*=20`.  
3. Choose \(g^* = \arg\max EV_{net}\).  

Every signal gets barriers fitted to its own predicted distribution. Vertical barrier = **MIS square-off** (with sleeve-specific last-entry cutoffs so the race has time to resolve).

#### The sweep is only meaningful if probabilities are geometry-conditional (added Revision 2)

“Geometry multipliers passed in as features” is a **hard requirement**, not a convenience. With
geometry-invariant probabilities, \(EV_{net} = p_{TP}g - p_{SL}s + p_{TO}\mathbb{E}[r|TO] - c\)
rises monotonically in \(g\) and falls monotonically in \(s\), so the argmax returns the widest
target and the tightest stop on **every** row regardless of the data — a constant dressed as a
decision. The M5 implementation did exactly this and reported \(g^*/s^*=3.0\) (the grid corners)
on every instance, with a \(g^*+s^*\) span of ~188 bps that was never the 300 bps span the labels
were built on.

Implementing this correctly requires the labeler to accept **per-row barrier widths** and the
training set to be **stacked over several geometries** so `(tp_mult, sl_mult)` genuinely vary
against outcomes. Until that exists, do not run or report a geometry sweep.

**Ordering lock:** geometry optimization comes *after* K4. Optimizing barriers on a decision set
with no established directional edge is a search for a lucky corner of the grid, which is what the
EV-net stop memo forbade.

### 5.4 Absolute vs excess labels

Production today trains on **Nifty-excess** path EV while trading an **unhedged cash** book. That is a label/product mismatch.

| Choice | When |
|---|---|
| **Absolute path return − c\*** | Default for unhedged MIS cash (matches EV-net probe) |
| Nifty-excess | Only if a Nifty futures hedge leg is funded and its own ~5 bps RT is justified |

**Lock for this blueprint:** absolute \(EV_{net}\) unless a hedge product is explicitly added.

---

## 6. Stage D — Admission and book (Tier 2c)

### 6.1 Absolute admit (replaces Top-K)

Admit if:

\[
\text{conformal lower bound of } EV_{net}(g^*) > 0
\]

| Property | Top-K (production) | Absolute EV admit (this blueprint) |
|---|---|---|
| Fires when book is bad | Always K names | Can fire **zero** |
| Selects relative vs absolute | Relative | Absolute |
| Matches goal “only positive PnL signals” | No | Yes |

Top-K remains useful as a **capacity / concurrency cap** after absolute admit — never as the sole economic gate.

### 6.2 Sizing and risk

- Size ∝ fractional Kelly on predicted EV / variance  
- Sector caps  
- Concurrency cap across names  
- Daily loss limit  

Trade count floating to ~1–4/day is an intended outcome of Stages B–D, not a defect to “fix” with lower thresholds.

---

## 7. Long vs Short posture

| Decision | Lock |
|---|---|
| Build order | ~~**Long-only first**, then Short as a straight refit~~ — **superseded, see Revision 2** |
| Why | Halves multiple-testing burden; Short sleeve already disabled in production cascade |
| Short coupling | High-range days are disproportionately down days — Stage B naturally steers short opportunity mass |
| Short asymmetries | Wider stop vs target (squeeze risk); never carry shorts into the 15:00–15:20 MIS flatten / cover window |
| Afternoon | Preserve / strengthen afternoon cover rules (existing `afternoon_cover_risk` in Precision); do not invent short entries into flatten |

Do not activate Short from Long PASS language alone — require a Short-specific K-gate reprint after Long clears.

### Revision 2 — sleeve order follows the drift sign, not convention

“Long-only first” was chosen to halve the multiple-testing burden, and that reasoning is still
sound *as a way to limit how many sleeves are tested at once*. It was wrong as a way to choose
**which** sleeve to test first, because it silently presumed continuation.

Two facts now point the other way:

1. The two continuation rules carry negative drift for Long in **both** folds (§5.2), while the one
   fade rule carries positive drift in both.
2. This blueprint's own note above — high-range days are disproportionately **down** days — says
   Stage B's range gate steers opportunity mass toward sessions where the Short side is the natural
   product. Stage B was then wired to a Long-only Stage C, so the gate and the sleeve were pulling
   in opposite directions.

**Revised lock:** the first sleeve is chosen by a pre-registered **drift-sign ledger** on the event
pool (§5.2 table), not by convention. Still one sleeve at a time. On current evidence the ordering
is: reversion/fade rules first (either side), then continuation rules only if a fold-consistent
positive drift sign appears.

The Short asymmetries and afternoon-cover rules above stand unchanged and apply the moment a Short
sleeve is activated.

---

## 8. Models

### 8.1 Keep GBDT as the workhorse

Effective sample size is **sessions**, not bars:

- ~11 years × ~250 days ≈ 2,800 sessions  
- Cross-sectional correlation within a day → ~88 names may contribute only a few effective observations  
- Rough independent sample order: ~8,000  

That caps honest complexity near current depth (3–4). A transformer on full 1m history will memorize sessions.

### 8.2 Change the loss

| Current | Problem | Replacement |
|---|---|---|
| Huber regressor on path EV | Wrong loss for trimodal TP/SL/TO; shrinks the payoff tail | **Multiclass log-loss** on first-hit outcome + calibrated probabilities |
| Isotonic on purged val | Keep | Keep — EV arithmetic is only as good as honest probs |

**Isotonic is load-bearing, not optional polish.** M5 shipped no calibrator and read K3 on raw
LightGBM margins: mean predicted \(P(TP)\) was 0.230 against a realized 0.337, a −11 pp systematic
bias, and K3 printed 16–24 pp max decile gaps. Adding per-class isotonic on a purged validation
slice carved out of train (last 20% of train sessions, one-session embargo) brought ECE to 2.4 pp
(fold B, PASS) and 4.6 pp (fold A, marginal) with max gaps inside their own bootstrap null bands.
Calibration was never the obstacle; its absence was.

**Feature levels do not transfer across folds.** The same run showed the head extrapolating vol
*levels* in the wrong direction between a 2018 test year and a 2019 one. Prefer **within-bar
cross-sectional ranks** of vol-state features over raw levels; ranks are immune to regime level
shift and cost nothing to compute.

### 8.3 Phase-2 path model (only after tabular clears)

First-passage is a path-shape problem. After the tabular Stage C baseline clears the edge test (K4 below), a small temporal CNN / GRU on the raw 1m bar tensor for the barrier-first-hit head is the legitimate upgrade. Do **not** start there.

---

## 9. Data gaps (fix before / alongside modeling)

| Gap | Why it matters | Action |
|---|---|---|
| `(H−L)/close` as “spread” | Range proxy, not spread; spread is 30–50% of 20 bps budget | Corwin–Schultz / Abdi–Ranaldo |
| No earnings / corporate-action calendar | Highest-vol days poorly identified ex ante | Cheap calendar join → Stage B |
| No options / OI / skew | Among better intraday directional / vol predictors in India | Phase-2 feature family |
| 5.4 GB CSV under `data/GOLDEN` | Throttles walk-forward iteration | Parquet + lazy Polars scans (~**order-of-magnitude** faster experiment loops) |
| First-hit resolved on 15m high/low | A 300 bps span race judged on 15m bars is ambiguous whenever one bar touches both barriers, and the current labeler breaks those ties to **SL** | Resolve first-hit on **1m** bars (the parquet store exists for this) |
| TP trigger asymmetry | TP fires at `tp_w + 2 bps` penetration but SL fires at exactly `sl_w`, so the target is measurably harder to reach than the stop — this biases K4 downward | Make penetration symmetric, or charge it to both barriers and report the shift |

Experiment turnaround (honest peeks per week) is higher leverage than model class choice.

### 9.1 Measurement bias is a first-class risk at 20 bps

The three items above are not hygiene — they are the difference between a −5 bps and a 0 bps read on
a cost-free skill gate, and K4 is decided in exactly that range. In the M5R run the barrier-race
gross return (−10.6 / −5.3 bps) sat below the barrier-free drift (−5.3 / +4.7 bps) on the same rows.
Some of that gap is genuine path shape, but the penetration asymmetry and the tie-break-to-SL rule
push in the same direction, so the gap cannot be attributed until first-hit is resolved on 1m bars.

**Rule:** before any K4 reading is treated as authority, publish (a) the share of rows where a single
bar touches both barriers, and (b) the K4 point estimate with penetration set symmetric.

---

## 10. Validation redesign

### 10.1 Keep

- Purged walk-forward with embargo  
- Session-block bootstrap CIs  
- Pre-registered peek budgets and hard-stops  
- Dual-fold A+B discipline  

### 10.2 Correct the EV-net Step 0 mistake

EV-net Step 0 required the **unconditional eligible pool** CI UB > −10 bps. A driftless pool has \(EV_{net} = -c = -20\) bps **by construction**. Measuring −20…−22 bps was the expected arithmetic outcome. The gate could only pass if the raw universe were profitable *before selection* — in which case Horizon would be unnecessary.

The informative diagnostic in that run was **oracle positive-mass ~27–30%**, marked report-only. **Selection is the job.** Do not gate on the pre-selection pool mean.

### 10.3 Pre-registered gates (K1–K5)

**Revision 2 (2026-08-16), after the M5 post-mortem.** The original K3 and K4 rules were not
testable as written; see §10.5. Definitions below supersede them.

| ID | Gate | Rule (dual-fold) | If FAIL |
|---|---|---|---|
| **K1** Range head | OOS Spearman(pred, realized remaining range) ≥ 0.45, **and** within-clock Spearman ≥ 0.40 | Data / Stage B broken — stop |
| **K2** Gate efficacy | Post-gate mean realized \|move\| over trade window ≥ 8c | Opportunity filter not creating span |
| **K3** Calibration | n-weighted **ECE** of \(P(\text{TP first})\) ≤ 3 pp on purged holdout, **and** max decile gap ≤ its own bootstrap null p95 | Do not trust EV arithmetic |
| **K4** Edge test | Mean **gross** path return (martingale residual); session-block CI LB > 0. Companion: \(P(\text{TP}\mid\text{resolved}) - s/(g+s)\) | See three-way rule below |
| **K5** Economics | **Pooled** admitted-set mean \(EV_{net}\) CI LB > 0 on row-level `c_eff`, **and** positive point estimate in ≥ 6 of 8 folds (sign test); flat-`c*` and c=30 reprints published | Skill exists but not enough vs friction |

**K4 is cost-free** — \(c\) does not appear. It separates “do we have directional skill?” from
“is skill larger than friction?” Prior ledgers conflated those questions.

#### Why K4 is a gross-return test, not a \(P(TP)\) test

Under the driftless null the entry price is a martingale, so optional stopping forces
\(\mathbb{E}[\text{path ret}] = 0\) **at any barrier pair and any timeout mass**. That makes gross
return the cleanest cost-free statistic available: it needs no \(s/(g+s)\) algebra, it survives an
MIS vertical, and it does not move when geometry varies row to row.

The original rule compared unconditional realized \(P(TP)\) to \(s/(g+s)\). That formula is the
gambler's-ruin probability for a race with **no time limit**. Once a vertical barrier exists,
\(P(TP) + P(SL) < 1\), so unconditional \(P(TP)\) sits below \(s/(g+s)\) by roughly
\(P(TO)\cdot s/(g+s)\) even for a driftless walk — a built-in penalty of ~1–3 pp at the timeout
rates M5 observed. Compare \(P(TP \mid \text{resolved})\) if a probability reading is wanted.

#### K4 is a three-way decision, not PASS/FAIL

Every K-gate must publish its **minimum detectable effect** (half-width of the session-block CI).
With two single-year folds the MDE on gross return is ~11–15 bps — wider than the entire 20 bps
cost budget. A point estimate near zero is therefore ambiguous, and the M5 ledger read that
ambiguity as a falsification. Decision rule:

| Reading | Verdict |
|---|---|
| CI LB > 0 | **PASS** — directional skill established; proceed to K5 |
| CI UB < \(c^*\) | **FAIL** — skill cannot reach friction; K5 is unreachable, stop |
| Otherwise | **INCONCLUSIVE** — do not stop and do not proceed; buy power first (more folds / sessions), then re-read |

An INCONCLUSIVE reading is a validation-design problem, not evidence about the market.

#### Why K5 is a pooled read (Revision 3)

A per-fold lower bound is **arithmetically incompatible** with the sparse book this blueprint asks for.
At the 200/100 geometry, per-trade gross dispersion is

\[
\sigma \approx \sqrt{0.30\cdot200^2 + 0.68\cdot100^2 - (-8)^2} \approx 137 \text{ bps}
\]

To put a 95% lower bound above zero on a true \(EV_{net}\) of +10 bps you need \(SE < 5.1\) bps, i.e.
~720 independent trades, or ~1,150 once intra-session clustering is allowed for — roughly **4.6 fires
per session**. The design target is 1–4 fires per *day across ~88 names* (§6.2), an order of magnitude
fewer. So a genuinely profitable sparse book would fail per-fold K5 by construction.

Pooling the 8 rolling folds gives ~2,000 sessions, which is ample. Fold-consistency is then tested
separately and more honestly as a **sign test** on the per-fold point estimates, which is what
"dual-fold discipline" was always trying to buy. Keep publishing per-fold point estimates and MDEs;
just do not gate on per-fold lower bounds.

#### The selection-power tradeoff

Selectivity and power move against each other. Top-decile selection cuts \(N\) tenfold and widens the
CI by ~3.2×, so a selector that genuinely lifts \(EV_{net}\) can still produce an unpassable gate. Any
admission threshold must be chosen with its resulting MDE in view — state the expected admit count
*before* running the peek.

### 10.4 Gate hygiene (added Revision 2)

Each rule below was violated at least once in M0–M5.

| Rule | Why |
|---|---|
| A gate must be passable by a correct model | K3's “max decile gap ≤ 3 pp” has a null p95 of ~6–9 pp at realistic bin counts. A max over 10 bins is not centred on zero; at ~200 rows per bin and \(p\approx0.33\) the per-bin binomial SE alone is ~3.3 pp. Use ECE, or compare the max to its own bootstrap null. |
| A gate must test the thing it names | K3 names calibration but was evaluated on raw GBDT margins with no calibrator fitted, so it measured the missing isotonic step. |
| A skill gate needs skill-bearing inputs | K4 names directional skill but was fed only volatility/range features, which are symmetric in the barrier race and raise \(P(TP)\) and \(P(SL)\) together. |
| Publish MDE with every gate | Otherwise “no edge” and “no power” are indistinguishable. |
| Ceiling diagnostics measure the pool, gates measure the model | A ceiling lift (M3/M4) says selection room exists; it never implies a selector can find it. |

### 10.5 Correct the K1 clock control

Remaining-session range falls mechanically as the session runs out, and `bars_to_mis` is a Stage B
feature, so a range head can score well by learning the clock. K1 must therefore publish the
**within-clock** Spearman (computed inside each bar-of-day, then n-weighted) alongside the pooled
value. Measured on fold A: pooled 0.635, within-clock 0.617, clock alone −0.095 — Stage B's skill
is genuine cross-sectional range prediction, not a time-of-day artefact. Keep publishing the
control so that stays true.

### 10.6 Selection-ceiling diagnostic (report-only, always publish)

Rank the post-gate pool by *realized* \(EV_{net}\) (oracle) and report top-decile mean.

| Ceiling reading | Diagnosis |
|---|---|
| Ceiling high (+80 bps) but model recovers ~0 / negative | Features / selector problem |
| Ceiling itself thin | Geometry / opportunity problem — do not spend peeks on scorers |

One afternoon of this diagnostic would have clarified months of relative-rank ledgers.

---

## 11. Explicit deletes (do not remount as defaults)

| Delete | Why |
|---|---|
| Top-K as the **sole** cascade economic gate | Relative; fires on bad books |
| Huber path-EV as primary loss | Trimodal outcomes; tail shrink |
| Nifty-excess labels on unhedged cash | Label ≠ product |
| Fixed H=6 as the economic vertical | Too short for 300 bps span; timeout factory |
| Fixed bps floors 60/50/30 as the only geometry | Span too small vs `c*` |
| Uniform 15m decision clock for every name-bar | Dilutes causal mass; inflates TO |

Individually each item was reasonable under older charters. Collectively they are fatal at 20 bps.

---

## 12. Precision boundary (anti-bailout)

| Allowed | Forbidden |
|---|---|
| 1m fill timing / skip on an already absolute-EV+ book | Claiming Horizon-path PASS from Precision P3 |
| Inherited barriers frozen at Horizon decision | Recomputing TB widths from 1m post-decision |
| Measuring whether Precision adds a few bps | Using Precision to bridge a 12–19 bps Horizon H4 deficit as the primary recovery plan |
| Short companion report-only | Activating Short from Long Precision PASS |

The Precision Execution Bridge charter remains a **falsification** of monetization on the *frozen production* Top-K book. This blueprint is a **separate** redesign of that book. Do not mix their success language.

---

## 13. Build order (suggested)

1. **Diagnostics first (no model ship):** selection-ceiling on current and on Stage-B-gated pools; Corwin–Schultz spread panel; absolute vs excess label reprint.  
2. **Stage A** tradability filter — deterministic, unit-testable. **Then actually apply it downstream.**  
3. **Stage B** range head → clear **K1 / K2** (with the within-clock control) or STOP.  
4. **Event clock + primary rules** — emit *transitions*, one row per (symbol, bar); publish the per-rule drift-sign ledger and pick the sleeve from it (§5.2, §7).  
5. **Validation power check** — confirm the K4 MDE is narrower than \(c^*\) before spending the peek.  
6. **Stage C** multiclass with directional features + calibration → clear **K3 / K4** or STOP.  
7. **Geometry as a decision variable** — only after K4 PASS (§5.3 ordering lock).  
8. **Stage D** conformal absolute admit + Kelly caps → clear **K5**.  
9. **Precision** re-measure on the *new* admitted registry (not production Top-K=5).  
10. **Second sleeve** only after the first clears K5 and a sleeve-specific charter exists.

Steps 4, 5 and 7 are Rev 2 insertions; step 2's second sentence is there because M2 built the Stage A
mask and M5 never called it, despite M4's own exit note requiring A∩B before Stage C.

Peek budgets, dual-judge text, and hard-stop OR cuts belong in a **follow-on charter** derived from this blueprint — not in this document.

**Implementation map:** [horizon-fresh-architecture-implementation-plan.md](horizon-fresh-architecture-implementation-plan.md) — milestone plan (M0–M8) including cleanup/refactor scheduled with each build step.

---

## 14. Capability sentences (design intent)

| Path | Sentence |
|---|---|
| **PASS (architecture)** | Under locked `c*=20`, a Horizon that gates on predicted session range, decides on an event clock with meta-label veto, fits barriers to the predicted distribution, and admits only on conformal \(EV_{net}>0\) can cascade a sparse book with dual-fold absolute expectancy above friction. |
| **FAIL (architecture)** | Even with range gating and absolute admit, admitted-set edge (K4) or economics (K5) fail dual-fold **on a harness whose gates are passable and whose inputs can carry the effect being tested** — then Nifty-100 MIS cash under 20 bps is not a viable Horizon product with this hypothesis; do not return to Top-K / H=6 / 60–30 grids; next requires a different product definition (hedged book, different universe, or different session product). |
| **INCONCLUSIVE (new, Rev 2)** | A gate reads near zero with an MDE wider than the effect it must detect, or the harness could not have produced a PASS regardless of the truth. This is **not** a FAIL and does not license the FAIL sentence. Repair the harness or buy statistical power, then re-read. |

The qualifier in the FAIL row is Rev 2's main addition. The M5 stop invoked the FAIL sentence from a
run whose Stage C had no directional input, no calibrator, no Stage A mask, a scrambled clock feature,
and an event pool that was 73% restatements of persisting state. Under those conditions a FAIL was the
only reachable outcome, so the result carried no information about the market. **A capability FAIL
requires a harness that could have passed.**

---

## 15. Relation to existing cascade docs

| Doc | Relationship |
|---|---|
| [horizon-fresh-architecture-implementation-plan.md](horizon-fresh-architecture-implementation-plan.md) | Step-by-step M0–M8 build + cleanup/refactor map derived from this blueprint |
| [horizon-m9-range-monetization-charter.md](horizon-m9-range-monetization-charter.md) | Successor charter after directional §14 FAIL (Track A options / Track B SSF) |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Still the live map of **production** Regime → Horizon → Precision; this blueprint proposes a **replacement Horizon subsystem**, not a silent edit of that map |
| [horizon-ev-net-rebuild-stop-memo.md](../archive/horizon-ev-net-rebuild-stop-memo.md) | Closed barrier-grid ledger; this blueprint is the “new causal hypothesis” that memo required |
| [horizon-fresh-m5-stop-memo.md](../archive/horizon-fresh-m5-stop-memo.md) | M5 STOP and the addendum vacating it — source of the Rev 2 gate corrections |
| [horizon-fresh-m4r-stop-memo.md](../archive/horizon-fresh-m4r-stop-memo.md) | M4R STOP, narrowed to the unconditional rule pool — source of the Rev 3 changes |
| [precision-execution-bridge-charter.md](precision-execution-bridge-charter.md) | Orthogonal falsification on **frozen** Top-K; must not claim cascade-ready from Precision alone; does not authorize this redesign |
| Production `src/horizon/**`, `src/labels/triple_barrier.py` | Unchanged until a charter derived from this blueprint is dual-judged and built |

---

## 15A. What the directional programme has established (Revision 3)

Recorded so it is not re-litigated. All readings are dual-fold or 8-fold, on harnesses that satisfy
the §10.4 hygiene rules and with MDE published.

| Quantity | Measured | Source |
|---|---|---|
| Range predictability | Spearman **0.607–0.635** pooled, **0.617** within-clock | M3 K1, §10.5 control |
| Directional predictability | IC ≈ **0.07** ceiling (R² ~0.005) | §4.1, consistent with every ledger since |
| Best fold-consistent event drift | **+6.2 / +7.8 bps** (`prior_day_high_reject` Short), CI UB ≈ **+16.8** | M4R drift ledger |
| Validation power | K4 MDE **9.0–12.6 bps** on 8/8 folds | M5P |
| Long continuation | **negative** gross, dual-fold | M5R |
| Timeout control under MIS vertical | 1.8–2.3% | M5R |

### The governing comparison

Required directional IC to carry the best sleeve from +7 bps to breakeven at a 20 bps hurdle is
about **0.054**; for a 30 bps gross book with margin, about **0.10**. Measured achievable IC is
**~0.07**. Breakeven sits just below the ceiling; margin sits above it. That is the whole story of
this programme in two numbers, and it is why the directional product has no headroom.

Against that, the **range** head measures Spearman 0.6 — an order of magnitude more signal — and has
been used only as a filter for the directional bet that cannot pay its own friction.

## 15B. Successor product hypotheses (if the directional FAIL is earned)

Ranked. Each is a **new charter**, not an extension of this one. Stages A, B and D survive all of
them; only Stage C's directional head is at risk.

### Primary — sell range, not direction

Monetize the Stage B forecast directly in options rather than using it as a gate.

**The honest caveat first:** Spearman 0.6 against *realized* range is not an edge. Implied vol already
embeds a HAR-style forecast plus a variance risk premium. The tradable quantity is
**realized minus implied**, so the first gate is whether the range head carries *incremental*
information over implied — a cheap, decisive test that kills the hypothesis in an afternoon if the
incremental coefficient is null.

| Gate | Rule |
|---|---|
| **V1** Incremental information | Regress realized remaining range on (implied range, `range_q50`); the head's incremental coefficient must be significant with the right sign, dual-fold |
| **V2** Sign economics | Mean gross straddle / strangle PnL on V1-selected sessions; martingale-residual style, cost-free |
| **V3** Net economics | V2 after option friction (premium spread, STT on premium, delta-hedge slippage if hedged) |

Data prerequisite: NSE implied vol / OI history — already logged as a gap in §9. This is the real cost
of the pivot, and it is a data-acquisition project rather than a modelling one.

**Opened:** [horizon-m9-range-monetization-charter.md](horizon-m9-range-monetization-charter.md) after
M4R-b §14 FAIL. India VIX is in-repo (`^INDIAVIX.csv`) and supports report-only **V0**; authority **V1**
still requires single-name IV.

### Secondary — keep the signal, change the instrument

Attack \(c\) instead of \(\delta\): run the same event/drift signal on **single-stock futures** over
the liquid F&O subset, where round-trip is materially below cash-intraday. Composes with §3.1.
Constraints to design for: lot-size granularity against a sparse book, and a changing F&O eligibility
list (survivorship).

### Rejected, with reasons

| Option | Why it fails |
|---|---|
| Hedged / market-neutral cash book | Reduces \(\sigma\), not \(EV\), and adds a second round trip. Makes the gate easier to pass at an expectancy that is still negative. |
| Wider universe (mid / small cap) | \(c_{\text{eff}}\) and idiosyncratic dispersion move together, so the ratio barely improves while capacity worsens. |
| Multi-day **cash delivery** hold | Worse in India, not better: delivery STT is charged on both sides, versus sell-side only for intraday. If a multi-day hold is wanted, use futures. |
| More directional feature engineering | 8 folds across multiple sleeves now bound event drift at CI UB ≈ +17 bps. The constraint is the signal, not the feature set. |

---

## 16. Out of scope (this blueprint)

- Dual-judge scores / peek IDs / merge authority  
- Live execution / OMS redesign ([live-architecture.md](../live-architecture.md) stays separate)  
- Cost shopping below 20 bps  
- Remounting CLOSED Admission / P(SL) veto / TP50 / E1–E2 / path-room as “free peeks” under the old Top-K book  
- Claiming production cascade-ready from this document alone  

---

## Appendix A — Symbols (quick reference)

| Symbol | Meaning |
|---|---|
| \(c^*\), `c*` | Round-trip cost = 20 bps (0.0020) — the **universe-average** working assumption used to size the design problem and to stress-report. Not a per-name floor; see §3.1 |
| \(c_{\text{eff}}\) | Row-level achievable round-trip = statutory + 2×half-spread + tick drag + impact. **This is the hurdle used in \(EV_{net}\)** wherever Stage A has run |
| \(\delta\) | Realized conditional drift over the hold — the quantity a vertical-only sleeve monetizes (§1.6) |
| \(g\), \(s\) | Take-profit / stop widths |
| \(EV_{net}\) | Path return − \(c^*\) (absolute unless hedge exists) |
| \(\Delta p\) | Required \(P(TP)\) edge over driftless \(s/(g+s)\) |
| H | Vertical barrier; blueprint default = MIS flatten, not fixed 6×15m |
| K1–K5 | Pre-registered validation gates for a future charter |

---

## Appendix B — Diagnosis lock carried forward

1. **Pool economics before scorer peeks.** Relative Top−Rest with negative selected nets is not a ship signal.  
2. **Travel ≠ TP mass.** MFE without barrier conversion does not clear friction.  
3. **Do not gate on unconditional pool mean under driftless null** — that null is −c by construction.  
4. **Do not redraw another ≤3 H/TP/SL grid** under the EV-net contract; change eligibility, entry clock, or product definition instead.  
5. **Precision cannot launder Horizon failure** into cascade-ready language.

Added Revision 2, from the M5 post-mortem:

6. **A gate must be passable by a correct model, and must be fed inputs that can carry the effect it tests.** Otherwise a FAIL measures the harness.  
7. **Publish the minimum detectable effect with every gate.** “No edge” and “no power” look identical without it.  
8. **`s/(g+s)` is a no-time-limit formula.** Do not compare it to unconditional \(P(TP)\) once a vertical barrier exists; prefer the martingale residual on gross return.  
9. **A geometry argmax over geometry-invariant probabilities is a constant.** It always returns the grid corner.  
10. **One rule, one sleeve, one head.** Rules with opposite conditional drift cannot share a meta-label model.  
11. **Cross-sectional ranks over raw levels** for anything whose distribution shifts between folds.  
12. **Silent integer overflow is a real failure mode in Polars.** `dt.hour()` and `dt.minute()` return `Int8`; `hour * 60` wraps. Cast before arithmetic on datetime parts.

Added Revision 3, from the M4R post-mortem:

13. **The §10.2 error generalizes — do not gate on any unconditional pool mean.** M4R stopped on unconditional *per-rule* drift, which is the same mistake as EV-net Step 0 one level up: the architecture's claim is that Stage C selection creates the edge, so the gate that can refute it is K4 on the **admitted** set, at the stage the architecture names. Rule-level drift bounds the pool, not the product.
14. **A tight stop is not risk control when drift is thin.** Compare barrier-race gross return against barrier-free drift on identical rows before assuming barriers help. Risk belongs in sizing (§6.2).
15. **If Stage A computes a per-row cost, spend it.** A `c_eff` column that only feeds a boolean is a discarded measurement, and it silently overstates the hurdle for a liquid-tail book.
16. **Check that the gate is passable by the *book*, not only by the model.** K5's per-fold lower bound was incompatible with the 1–4 fires/day target at any plausible expectancy. Sparsity and statistical power trade against each other; price that in before pre-registering a threshold.
17. **Report required-IC alongside every drift reading.** "Drift is +7 bps, hurdle is 20" is not actionable; "required selector IC is 0.054 against a measured ceiling of 0.07" is.
