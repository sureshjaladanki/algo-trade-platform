# Retail India desk — Architecture Blueprint

**Market:** NSE India. The product is **not** Nifty-100 cash MIS, remaining-session straddles, same-session fade, or a home-built factor sort.  
**Status:** **BLUEPRINT Rev 2** — clean re-derivation after Horizon Successor STOP. Rev 1's three-book structure is **superseded** (§0.3). Not a dual-judge charter. Not a merge authority. Production cascade stays frozen.  
**Date:** 2026-08-18  
**Depends on (facts, not reopen):** [forced-flow-freeze-note.md](../archive/forced-flow-freeze-note.md), [horizon-successor-closed.md](../archive/horizon-successor-closed.md), [cascade-closed.md](../archive/cascade-closed.md), [fresh-closed.md](../archive/fresh-closed.md), [inherited-learnings.md](../archive/inherited-learnings.md)

**Implementation map:** [forced-flow-execution-plan.md](forced-flow-execution-plan.md)

---

## One-line

For Indian retail, the **tax wrapper and the capacity floor** decide what is viable before any alpha question. Both point away from home-built factor sorts and toward **forced-flow corporate events**: large effects, small capacity, low frequency, and no cheaper packaged substitute.

---

## 0. Derivation

### 0.1 What the prior programmes established

Recorded so it is not re-litigated. These are repository measurements, inherited on trust and not reproduced here (Appendix A).

| Programme | Question | Answer |
|---|---|---|
| Production cascade + Fresh | Can Top-K, 90-minute, 60/30 cash MIS pay 20 bps? | **No.** Selected horizon **−12…−19 bps**; unconditional \(EV_{net}\) **−20…−22**; selector IC **0.022** vs required **0.054**. |
| Fresh M4R | Does India continue or fade intraday? | **Fade**, by **+6–8 bps** — below cash friction and below the liquid-tail effective cost. |
| Successor P1 | Is remaining-session range incremental, and does it monetize? | Range **yes**; premium **no** (**+0.6 bps**, CI [−1.9, +3.1] with spread set to zero). |
| Successor P2 | Does the fade pay at futures friction? | Breakeven cost **4.5 bps** against forward friction above it — and April 2026 tripled futures STT. |
| Successor S6 | Same rule held to T+3? | **Inconclusive**, CI [−20.5, 0]. |

**The single transferable lesson** is the required-skill identity, \(\text{IC} \approx (c - \delta) / (\sigma \cdot \mathbb{E}[z \mid \text{selected}])\), published only after the failure it should have prevented. Every measured drift in this repository sat between 0 and 8 bps against costs of 10 to 20 bps. No model class fixes a negative numerator.

**Lock:** cash MIS directional, remaining-session index vol, and same-session fade are **closed**. Do not spend a peek on Stage C, geometry grids, Precision-as-bailout, name-option marks, or futures history to manufacture power.

### 0.2 The constraint ladder for Indian retail

The cascade optimized alpha and treated cost as a haircut. That is backwards. For a retail book in India the binding constraints, in order:

**1. Tax wrapper.** Determined by holding period and instrument, and it dominates most realistic alpha.

| Route | Effective rate | Note |
|---|---|---|
| Equity held > 12 months | **12.5%** above ₹1.25L/yr | The cheapest way to hold Indian equity risk |
| Equity held ≤ 12 months | **20%** + cess ≈ **20.8%** | §111A. Any monthly or weekly rebalance lands here |
| F&O | **Slab**, up to ~31.2% | Non-speculative business income. Worst rate for a high earner, though losses carry forward |
| **Inside a mutual fund or ETF** | **Zero on internal rebalancing** | The fund's own trades are not a taxable event for the unit holder |

That last row is the one the Rev 1 design missed, and it is decisive — see §0.3.

**2. Friction (April 2026 lock).** Finance Act 2026 raised derivatives STT effective 1 April 2026 and left cash untouched.

| Instrument | Statutory core | Working round trip |
|---|---|---|
| Equity delivery | STT 0.10% buy **and** 0.10% sell | **45 bps** |
| Equity intraday | STT 0.025% sell | 20 bps universe — **closed as a product** |
| Index futures | STT **0.05%** sell (was 0.02%) | **10–12 bps** |
| Stock futures | Same rate, wider spreads | 10–14 bps per leg |
| Options | STT **0.15%** of premium, sell side | No high-turnover premium book |

Policy has raised derivatives STT twice in eighteen months and cut weekly index expiries to one per exchange (NSE Nifty on Tuesday; Bank Nifty is monthly only). A retail edge built on many small derivative tickets is fighting the tax code deliberately.

**3. Capacity — and this one cuts in retail's favour.** A ₹25L–₹1Cr book can enter positions no fund can. Any effect that survives *because* it is too small to arbitrage at institutional size is a retail asset. Any effect available at scale is already packaged, cheaper, by someone else.

**4. Alpha.** Only now does the signal matter.

### 0.3 Why Rev 1's momentum book is withdrawn

Rev 1 made a monthly 12-1 momentum delivery sort the capital primary. Applying §0.2 kills it, and I am overruling my own earlier draft.

Indian momentum is real — published long-short estimates run near 17% annualized, and a long-only Nifty 100 top-decile construction has been reported at **+10.7% a year over the index**. But that same study reports turnover of about **32% per month**, roughly 3.8 round trips a year:

| Line | % of AUM / year |
|---|---|
| Published gross excess | +10.7 |
| Delivery friction at ~3.8 round trips | −1.7 |
| Impact on a concentrated book | −0.3 to −0.6 |
| **STCG at 20.8% on realized gains** | **−2 to −4** |
| Net | ≈ +4 to +7 |

Now compare against the packaged alternative. Momentum index funds on Nifty 200 Momentum 30 exist with several thousand crore of assets and expense ratios well under 1%. **The fund rebalances internally at no tax cost to the holder**, who pays 12.5% once, on redemption, after a year. The identical strategy run in a personal demat account pays 20.8% every year on realized gains.

So the do-it-yourself version starts **two to four percentage points a year behind the fund**, before operational risk, and must overcome that gap purely through a better sort. Meanwhile independent long-horizon work reports a **−70% drawdown with a 65-month recovery**, and finds the **liquid** momentum slice underperforming the Nifty 50 — precisely the slice a Nifty 100 book with an ADV mask is confined to.

**Conclusion I own:** the correct implementation of a retail momentum allocation is **to buy it, not to build it**. It becomes the benchmark and the beta core of this desk, not a research programme. Any future DIY factor sort must clear a bar of roughly **+2.5% a year over the corresponding index fund, after tax** — not merely beat the index. That bar is high enough that I decline to spend research days on it now.

The same logic retires Rev 1's FII-flow index overlay: a public, one-day-lagged, widely watched series with a thin causal story, on an instrument whose STT just tripled, competing with zero-cost index exposure. It is scope creep with a satellite label.

### 0.4 What that leaves

Strip out everything a fund does better, everything policy is taxing away, and everything already measured as dead, and one space survives: **discrete corporate events with forced or predictable flow**, where the move is measured in hundreds of basis points, capacity is genuinely limited, and no packaged product competes.

This is the inverse of the cascade in every dimension that mattered.

| Dimension | Cascade | This desk |
|---|---|---|
| Effect size | 5–8 bps | 100–400+ bps |
| Friction share of effect | 100%+ | 10–30% |
| Decisions per year | Thousands | Tens |
| Statistical power | MDE ≈ effect | MDE well under effect |
| Capacity | Institutional-competitive | Too small for funds |
| Live system | Feed, HMM, two rankers, 1m Precision | Calendar and a daily batch job |

---

## 1. Product architecture

**One research book. One passive core. Everything else is deferred.**

```
Passive core (capital, not research)
  Broad index and/or a momentum index fund
  Held > 12 months for 12.5% LTCG
  This is the benchmark every active rupee must beat AFTER tax

Book F — FORCED FLOW (research primary)
  F1  Index reconstitution: predict, then position
  F2  F&O universe entry and exit
  Delivery, days to weeks, event-dated

Book G — EARNINGS DRIFT (second, gated on data)
  Announcement-dated residual, 1 to 5 sessions
  Runs only if the calendar is free
```

Regime stays a frozen pre-open veto if a live book ever wants a hard flat. Precision is not a book. There is no intraday sleeve, no HMM router, no index overlay.

### 1.1 Book F — Forced flow (primary)

**Hypothesis.** Indian passive assets have grown large enough that index reconstitution forces mechanical, date-certain buying and selling. NSE publishes membership changes weeks before they take effect, and the tracking funds must transact near the close on the effective date. Positioning ahead of that flow, and fading its reversal afterwards, is a capacity-limited effect that institutions cannot fully arbitrage and no packaged product harvests.

**Why this is the right first test, on this desk's own rules:**

- **The kill-switch is in-repo.** Point-in-time index membership already exists in the repository, so historical change dates are derivable without buying anything. This satisfies the rule that a first test must fire on existing data within two machine-days.
- **It is well powered.** With an effect plausibly in the hundreds of basis points against event volatility near 600 bps, a few hundred events give a detectable effect far below the effect. Every prior programme failed the opposite way.
- **Friction is a rounding error.** 45 bps against a 200 bps candidate move is 20%, not 300%.
- **The prediction step is a legitimate quantitative problem.** NSE's selection rules are largely mechanical — free-float market capitalisation ranking with eligibility filters — so candidate additions and deletions can be ranked *before* announcement from data already held. That is where the durable edge sits, because the post-announcement trade is public information.

**Construction:**

1. **F1a — post-announcement.** On the announcement date, take a delivery position in additions and the opposite in deletions where shortable, exiting into the effective-date close. Report-only if it is fully public; it establishes whether the flow effect still exists at all.
2. **F1b — pre-announcement (the actual product).** Replicate the ranking rules, hold the top candidate additions ahead of the announcement window, and exit on announcement. Position sizing scaled by predicted inclusion probability.
3. **F1c — reversal.** Fade the post-effective-date reversion in additions. Documented globally; must be measured here, not assumed.
4. **F2 — F&O list changes.** Entry to and exit from the derivatives-eligible universe changes who can trade a name and how it is hedged. Same harness, separate event pool.

**Gates:**

| ID | Gate | Rule | If FAIL |
|---|---|---|---|
| **F0** | Event pool exists | Reconstitute historical change dates from point-in-time membership. Publish event counts by year and index family | Cannot build the pool in-repo → the whole programme's premise fails; stop before spending on data |
| **F1** | Effect exists, gross | Announcement-to-effective residual vs Nifty, pooled across folds, cost-free CI lower bound above zero, MDE published first | The Indian index effect has already decayed. Stop Book F. |
| **F2** | Net of friction and tax | Same at **45 bps** and then at **20.8%** short-term tax, against an after-tax passive hold | Effect existed, edge did not |
| **F3** | Predictability | Out-of-sample ranking of candidate additions beats a naive rank. Publish hit rate and the realized-vs-required skill line | No pre-announcement product; F1a alone is public information |
| **F4** | Decay | Effect by year. A monotone decline toward zero as passive assets grew is a **stop**, not a smoothing problem | The trade is being arbitraged away; do not fit it harder |
| **F5** | Capacity and reality | Circuit limits, delivery availability, borrow for the short leg, lot sizes, worst-case impact on the effective-date close | Untradeable at retail size in the names that carry the effect |

**Rejects:** trading the index rebalance intraday; using options to express it; adding a GBDT before F1 passes; expanding to every global index family to manufacture sample size.

### 1.2 Book G — Earnings drift (second)

**Hypothesis.** Results announcements produce residual moves of 100 to 400-plus basis points, so 45 bps of friction is a rounding error rather than the whole trade.

**Construction:** enter on the first close that provably contains the announcement, direction from the residual against Nifty, hold one to five sessions, disaster losses clipped rather than dropped. Skip the event when the overnight gap has already repriced it.

| ID | Gate | Rule | If FAIL |
|---|---|---|---|
| **G0** | Calendar | Announcement dates assembled from free sources | Needs a paid vendor → **defer Book G entirely**. Do not put data acquisition on the critical path of a first test. |
| **G1** | Drift, gross | T+3 residual authority, T+1 and T+5 companions, cost-free | Stop. Do not scan other event types in the same peek. |
| **G2** | Net | 45 bps then 20.8% tax | Edge below friction |
| **G3** | Gap-already-in | Restricted to events with a small overnight gap | If only the repriced tail works, there is no trade |

Language models may build and clean the calendar. They may not pick the side.

### 1.3 The passive core

Not a research project. Broad index exposure, and optionally a momentum index fund, held beyond twelve months. It exists to (a) hold the capital that Book F cannot deploy, since a low-frequency event book is idle most of the time, and (b) serve as the **after-tax benchmark** every active rupee is measured against.

**Lock:** no gate in this document is passed by beating a pre-tax index line. The comparator is an after-tax passive hold.

---

## 2. Where the surviving research assets go

| Asset | Role here |
|---|---|
| Remaining-session range head (Spearman ~0.61, incremental to VIX and HAR) | **Position sizing and event-day skip.** A volatility forecast need not beat implied to size a book. It never picks a side and never sells premium. |
| Purged folds, MDE, pooled statistics, three-way verdicts, disaster clip, real purge | The research operating system — reimplement from [inherited-learnings.md](../archive/inherited-learnings.md) |
| Point-in-time membership | **Primary data source** for Book F's event pool; rebuild from the daily panel |
| Effective-cost machinery | Reused in concept; delivery has its own schedule and must not silently inherit MIS costs |
| Cascade models (HMM, rankers, Precision) | Frozen. Not inputs, not features, not tie-breaks. |

---

## 3. Where AI belongs

| Use | Verdict |
|---|---|
| Ranking candidate index additions from mechanical eligibility rules | **Yes — the primary modelling job.** Structured, sizeable sample, verifiable out of sample |
| Quantile range head for sizing and skip decisions | Yes |
| Language models to assemble and clean event and results calendars | Yes, as data preparation |
| Conformal intervals on event outcomes for position sizing | Yes, after a gate passes |
| A meta-label model layered on Book F before F1 passes | No |
| Transformers on bars, headline sentiment as a side, any live language-model gate | No |

The discipline is unchanged: state required skill against the measured ceiling before fitting anything.

---

## 4. Platform

The honest consequence of an event-driven, low-frequency book is that **most of the live architecture is unnecessary**. A system that trades tens of times a year does not need a tick feed, an in-process bus, or a 1-minute inference kernel.

| Layer | Cadence | Owns |
|---|---|---|
| Event calendar | Daily batch, pre-open | Index announcement and effective dates, F&O list changes, results dates, corporate actions |
| Book F / G | On event dates | Candidate ranking, target positions, skip masks |
| Risk | Per intended order | Position cap, sector cap, event concentration, range-head sizing, total active weight vs the passive core |
| Execution | Scheduled window or closing auction | Delivery orders, algo-order tagging, audit record |

**Build only this in v1:** a daily batch job producing a dated instruction list, an append-only record of every instruction and fill, and broker reconciliation. Order placement may be human-confirmed at this frequency — that is a feature, not a shortcut.

**Do not build:** a websocket feed for 100 names, an in-process event bus, Redis, an options chain, a second broker, or paper-MIS infrastructure. If Book F passes and later demands automated closing-auction participation, that is one focused extension, not a high-frequency cascade. A tick-feed live architecture is not this desk's roadmap and is not present on this branch.

---

## 5. Capital and expectations

Book F fires on the order of tens of events a year, and cannot hold the whole book. Sizing must be stated honestly against the passive core.

| Capital | Structure |
|---|---|
| Under ₹25L | Passive core only. The fixed operational cost of a desk does not scale down. |
| ₹25L–₹1Cr | Passive core, plus Book F at a capped active weight, plus Book G if its calendar is free. |
| ₹1Cr+ | Same, larger per-event size, subject to F5 impact limits. Capacity, not ambition, sets the ceiling. |

If Book F clears its gates with, say, 200 bps net per event across 20 deployable events a year at a 25% active weight, that contributes roughly **1% a year over the passive core** — a real but modest number for one decision every few weeks. **Stating that before the peek is the point.** If the honest arithmetic cannot reach a number worth the operational risk, the correct answer is the passive core alone, and that is an allowed and respectable outcome.

---

## 6. Locks

| Lock | Rule |
|---|---|
| Production cascade | Frozen. No Top-K, 90-minute vertical, 60/30 barriers, or silent model swap |
| Closed products | Cash MIS directional, remaining-session vol, same-session fade, T+k of the intraday reject rule |
| April 2026 friction | Forward hurdle. Sample-era futures STT is a historical reprint only |
| Tax | Every authority gate is after-tax against an after-tax passive benchmark |
| DIY factor sorts | Must clear roughly +2.5% a year over the corresponding index fund after tax, or they are not a product |
| Instrument | Cash delivery. No options. No futures without a passing book and a written case |
| Tight stops | Forbidden as silent risk control on thin drift. Event books use disaster clips and position caps |
| Data acquisition | Earned by a cheap in-repo pass. Never the critical path of a first test |
| Gate validity | Passable by a correct model, inputs can carry the effect, MDE published, statistic matches the claim |
| Live language models in a gate | Forbidden |
| Cascade-ready claims | Forbidden from this document |

---

## 7. Capability sentences

| Path | Sentence |
|---|---|
| **PASS (F)** | The index-flow effect exists in the Indian sample, survives 45 bps and 20.8% tax against an after-tax passive hold, has not decayed to zero as passive assets grew, and candidate additions are predictable out of sample. |
| **FAIL (F)** | F1 or F2 fails, or F4 shows monotone decay — the effect has been arbitraged away. Stop. Do not fit it harder or widen to foreign index families. |
| **PASS (G)** | Earnings residual at T+3 clears cost and tax, and not only in the already-repriced tail. |
| **FAIL (G)** | Stop the event book. Do not substitute headline sentiment. |
| **FAIL (programme)** | Both fail on passable harnesses. The desk is then a passive core with an audit log — a correct outcome, arrived at in weeks instead of quarters. |

---

## 8. Out of scope

Dual-judge scoring and merge authority; remounting any closed ledger; the Precision execution bridge; options of any tenor; single-stock futures; intraday anything; selling signals without an investment-adviser or research-analyst registration.

---

## 9. Relation to existing docs

| Doc | Relationship |
|---|---|
| [forced-flow-execution-plan.md](forced-flow-execution-plan.md) | Milestone map for this blueprint |
| [forced-flow-freeze-note.md](../archive/forced-flow-freeze-note.md) | Working-set freeze: successor stopped, cascade frozen, momentum book withdrawn |
| [horizon-successor-closed.md](../archive/horizon-successor-closed.md) | Prior product hunt is over; range head is sizing only |
| [cascade-closed.md](../archive/cascade-closed.md) | Frozen production map, summarized; not a build plan |
| [fresh-closed.md](../archive/fresh-closed.md) | Cash-MIS event book closed |
| [inherited-learnings.md](../archive/inherited-learnings.md) | Pooled gates, MDE, purge, disaster clip — reimplement, do not import |

---

## Appendix A — Provenance

This document contains **no new measurement**. No code was run to produce it.

| Claim class | Source | Standing |
|---|---|---|
| Prior-programme failure numbers (§0.1) | [Closed-programme summaries](../archive/forced-flow-freeze-note.md) | **Inherited on trust**, not reproduced. Reprint from the original logs before using any as a hurdle. |
| Statutory rates, expiry structure, tax sections (§0.2) | NSE, the Income-tax Act, broker circulars, verified while writing | **Verified.** Re-check at each Finance Act. |
| Momentum estimates, turnover, drawdown, liquid-slice finding (§0.3) | External studies on other samples and universes | **Cited, not reproduced.** They inform the decision to *decline* that book, which is the conservative direction. |
| The constraint ladder, the withdrawal of the factor and overlay books, Book F's design and ordering, the platform reduction (§0.2–§4) | This blueprint | **Mine, and arguable.** The gates exist so it can be wrong cheaply. |
| Event-size, power, and capital sketches | Extrapolated | **Sketches.** Not results. F0 and F1 replace them with counts. |

---

## Appendix B — Symbols

| Symbol | Meaning |
|---|---|
| \(c\) | Instrument round trip: 45 bps delivery, 10–12 bps index futures, 20 bps cash MIS archive |
| \(\delta\) | Conditional drift over the book's hold |
| \(\sigma\) | Volatility of the traded object over that hold |
| F0–F5, G0–G3 | Gates in §1 |
| Range head | Remaining-session range forecast — sizing only, never side |
