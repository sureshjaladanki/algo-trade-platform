# Retail India desk — Architecture Blueprint

**Market:** NSE India. The product is **not** Nifty-100 cash MIS, remaining-session straddles, same-session fade, or a home-built factor sort.  
**Status:** **BLUEPRINT Rev 3** — F0/F1/C2 measured. Public reconstitution residual **closed** (economic FAIL). Predicted-basket leftover **STOP** (+205 bps vs 300 hurdle). Ranking retained. **G0 PASS. G1 PASS** (+33.5 bps). **G2 INCONCLUSIVE / economic FAIL** (gross 33.5 < 45). G3 not opened. Book G closed. Desk is a passive core plus an audit log. Rev 2's "well powered" sketch is **falsified** (§0.5). Not a dual-judge charter. Not a merge authority. Production cascade stays frozen.  
**Date:** 2026-08-19  
**Review:** [forced-flow-architect-review.md](../archive/forced-flow-architect-review.md)  
**Depends on (facts, not reopen):** [forced-flow-freeze-note.md](../archive/forced-flow-freeze-note.md), [horizon-successor-closed.md](../archive/horizon-successor-closed.md), [cascade-closed.md](../archive/cascade-closed.md), [fresh-closed.md](../archive/fresh-closed.md), [inherited-learnings.md](../archive/inherited-learnings.md)

**Implementation map:** [forced-flow-execution-plan.md](forced-flow-execution-plan.md)

---

## One-line

For Indian retail, the **tax wrapper and the inference budget** decide what is viable before any alpha question. Low-frequency reconstitution leftovers cannot clear 45 bps. Ranking of Next 50 is a research asset. Earnings drift exists at T+3 (+33.5 bps) and **does not clear 45 bps delivery**. The desk is a passive core.

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

**2. Event count (inference budget).** A book with tens of decisions a year cannot establish an edge at any effect size below several hundred basis points. MDE ≈ 2.8 σ / √n. At n=27 and σ=600 bps that is **323 bps**. If the product needs ~300 bps gross to clear 45 bps and 20.8% at a 25% active weight, the harness is sized to see a product and will not see a 50 bps leftover. Low frequency solves friction and creates an unsolvable inference problem. The viable zone is hundreds to thousands of events a year with effects well above 45 bps.

**3. Friction (April 2026 lock).** Finance Act 2026 raised derivatives STT effective 1 April 2026 and left cash untouched.

| Instrument | Statutory core | Working round trip |
|---|---|---|
| Equity delivery | STT 0.10% buy **and** 0.10% sell | **45 bps** |
| Equity intraday | STT 0.025% sell | 20 bps universe — **closed as a product** |
| Index futures | STT **0.05%** sell (was 0.02%) | **10–12 bps** |
| Stock futures | Same rate, wider spreads | 10–14 bps per leg |
| Options | STT **0.15%** of premium, sell side | No high-turnover premium book |

Policy has raised derivatives STT twice in eighteen months and cut weekly index expiries to one per exchange (NSE Nifty on Tuesday; Bank Nifty is monthly only). A retail edge built on many small derivative tickets is fighting the tax code deliberately.

**4. Capacity.** A ₹25L–₹1Cr cash book in Next 50 names is a rounding error against ADV. Capacity is not the binding constraint on this desk. It starts to bind above roughly **₹1Cr**. Effects that survive only because funds cannot hold them remain a retail asset; effects available at scale are already packaged.

**5. Alpha.** Only now does the signal matter.

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
| Effect size | 5–8 bps | Public Nifty 50 window measured at **+26 to +52 bps** (additions) |
| Friction share of effect | 100%+ | 45 bps ≥ leftover on the public window |
| Decisions per year | Thousands | **Tens — a liability.** MDE 323 bps at n=27 |
| Statistical power | MDE ≈ effect | **MDE ≥ required product** on Book F public legs |
| Capacity | Institutional-competitive | Not binding below ~₹1Cr |
| Live system | Feed, HMM, two rankers, 1m Precision | Calendar and a daily batch job |

### 0.5 What Book F taught

Measured 2026-08-19. Pack: [forced-flow-status.md](forced-flow-status.md). Review: [forced-flow-architect-review.md](../archive/forced-flow-architect-review.md).

The cascade died because friction ≥ effect at thousands of decisions. Book F died the mirror death: **MDE ≥ effect at tens of decisions.**

net bps = 0.792 × (gross − 45)

Two cycles a year, 25% of the book per cycle, targeting ~1%/yr: **net ~200 bps so gross ≈300 bps per event.** F1 MDE was 323 bps. The harness was sized to see a product and did not. Addition centres of +26 bps (T−20→T) and +52 bps (announcement→T) cannot clear delivery. **C1 (public window) is closed: INCONCLUSIVE on existence, FAIL on economics.**

T−20 sits inside the announcement window (NSE ≥ four weeks' notice). F1-effective was a subset of F1a.

The T−40→T−20 companion on *actual* additions printed +538 bps (look-ahead; locked). Combined with +52 bps post-announcement, most of that move is pre-PR. Ranking (F3-SKILL) PASS: Next 50 6-month FF mcap top-k 66.7% vs 4.1% naive. The ex-ante basket on that private window (C2 / F3-RESIDUAL) printed **+205 bps vs a 300 bps hurdle — STOP**.

**Lock:** a gate whose MDE exceeds the pre-registered economic hurdle is not a valid existence gate. Either do not run it, or pre-register INCONCLUSIVE → STOP for capital.

---

## 1. Product architecture

**One research primary, now closed. Ranking retained. No Book F residual capital. No Book G residual capital.**

```
Passive core (capital, not research)
  Broad index and/or a momentum index fund
  Held > 12 months for 12.5% LTCG
  After-tax benchmark

Book G — EARNINGS DRIFT (closed)
  G0 PASS — 3,586 quarterly filings
  G1 PASS — T+3 +33.5 bps, n=3543, MDE 28.2
  G2 INCONCLUSIVE / economic FAIL — net −9.1; gross 33.5 < 45
  G3 not opened

Book F — FORCED FLOW (ranking retained; residual capital closed)
  C2  Predicted Next 50 top-3 — STOP (+205 vs 300)
  C1  Public announcement→effective — CLOSED
  C3  Post-effective fade — additions closed; deletion companion locked
  C4  F&O list changes — deferred
```

Regime stays a frozen pre-open veto if a live book ever wants a hard flat. Precision is not a book. There is no intraday sleeve, no HMM router, no index overlay.

### 1.1 Book F — Forced flow (ranking retained; residual capital closed)

**Hypothesis.** NSE reconstitution forces mechanical buying. The *public* window (announcement → effective close) is professionally crowded: trackers print at T, arb desks use single-stock futures at 10–14 bps. A retail cash book at 45 bps plus 20.8% is the worst-positioned participant there. The *private* window is cut-off → announcement, holding a probabilistic Next 50 basket at a size no fund can put in a tracking-error budget. Ranking skill is verified. The residual on an ex-ante basket is **STOP**: +205 bps against a 300 bps hurdle.

**What was measured (do not re-peek):**

- **C1** public residual INCONCLUSIVE on existence, **FAIL on economics.** Closed.
- **F3-SKILL** Next 50 6-month FF mcap top-k **PASS** (66.7% vs 4.1% naive).
- **C3** additions fade INCONCLUSIVE. Deletion bounce prior-σ PASS at sample-scale INCONCLUSIVE — locked companion. Next 50 offset muddles deletions (a name leaving Nifty 50 usually enters Next 50).
- T−40→T−20 on *actual* additions is look-ahead. Locked.

**Construction (C-numbers; gates keep F-numbers):**

| ID | Construction | Status |
|---|---|---|
| **C1** | Post-announcement, actual names, exit T | **CLOSED** |
| **C2** | Ex-ante top-3 Next 50, first session of Feb/Aug → session after PR, equal weight. Charter: [f3-residual-charter.md](f3-residual-charter.md). Memo: [f3-residual.md](../archive/f3-residual.md) | **STOP** — +205 bps vs 300 hurdle |
| **C3** | T→T+20 fade | Additions closed; deletion companion locked |
| **C4** | F&O list entry/exit | **Deferred.** C2 did not GO |

C2 used **equal weight, fixed k = 3**. Probability-weighted sizing is forbidden.

**Gates:**

| ID | Gate | Status |
|---|---|---|
| **F0** | Event pool | **Done.** 68 events, 43 tradable |
| **F1** | Public residual | **Closed.** INCONCLUSIVE existence, economic FAIL |
| **F2-NET** | 45 bps then 20.8% vs after-tax passive | **Closed-not-applicable.** C1 and C2 both closed |
| **F3-SKILL** | OOS rank vs naive | **PASS** |
| **F3-RESIDUAL** | C2 basket vs Next 50 ranks 21–50 | **STOP** (+205 vs 300). Book F capital closed |
| **F4** | Decay | Folded into F3-RESIDUAL as 2015–19 vs 2020–25. Not a standalone peek |
| **F5** | Tradability | Not opened |

**Rejects:** re-running any peeked F1 or C2 window; promoting locked companions; GBDT/meta-label; foreign index families for sample size; PIT F&O list or full-NSE panel to rescue C2; options; probability-weighted sizing.

### 1.2 Book G — Earnings drift (closed)

**Hypothesis.** Results announcements produce residual moves of 100 to 400-plus basis points, so 45 bps of friction is a rounding error rather than the whole trade. On the existing 100-name panel, ~44 quarters give on the order of **thousands** of events. MDE at n≈3,543 and σ=600 is 28 bps — the only book on this desk where power sat below the candidate effect.

F1 and C2 have verdicts. **G0 PASS.** **G1 PASS** (+33.5 bps). **G2 INCONCLUSIVE / economic FAIL.** G3 not opened. Working sample 2015 through early 2025. Do not buy a vendor to fill 2025. Do not promote T+5.

**Construction (measured):** enter on the first close that provably contains the announcement, direction = sign of T−1→T residual vs Nifty, hold T→T+3, disaster losses clipped rather than dropped.

| ID | Gate | Rule | Verdict |
|---|---|---|---|
| **G0** | Calendar | 3,586 first-broadcast quarterly filings on 95 of 100 GOLDEN names | **PASS.** Closed. |
| **G1** | Drift, gross | T+3 residual authority, T+1 and T+5 companions, cost-free | **PASS** +33.5 bps, CI [22.6, 45.8], n=3543. T+5 companion +47.2 — do not promote. |
| **G2** | Net | 45 bps then 20.8% tax | **INCONCLUSIVE / economic FAIL.** Net −9.1, CI [−17.8, 0.6]. Gross 33.5 < 45. |
| **G3** | Gap-already-in | Restricted to events with a small overnight gap | **Not opened.** |

Language models may build and clean the calendar. They may not pick the side.

### 1.3 The passive core

Not a research project. Broad index exposure, and optionally a momentum index fund, held beyond twelve months. It exists to (a) hold the capital that active books cannot deploy, and (b) serve as the **after-tax benchmark** every active rupee is measured against.

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
| Ranking candidate index additions from mechanical eligibility rules | **Done (F3-SKILL PASS).** Do not fit a richer ranker. C2 is STOP |
| Quantile range head for sizing and skip decisions | Yes |
| Language models to assemble and clean event and results calendars | Yes, as data preparation — G0 |
| Conformal intervals on event outcomes for position sizing | Yes, after a gate passes |
| A meta-label model layered on Book F | No |
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

Active books cannot hold the whole book. Sizing is after-tax against the passive core.

net bps = 0.792 × (gross − 45)

C2 economic hurdle was **300 bps gross** per cycle-basket. The peek printed +205. Capital on this construction is closed.

| Capital | Structure |
|---|---|
| Under ₹25L | Passive core only. The fixed operational cost of a desk does not scale down. |
| ₹25L–₹1Cr | Passive core only. Book G did not clear delivery. No C2 residual. |
| ₹1Cr+ | Passive core only. |

If the honest arithmetic cannot reach a number worth the operational risk, the correct answer is the passive core alone, and that is an allowed and respectable outcome.

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
| Gate validity | Passable by a correct model, inputs can carry the effect, MDE published, statistic matches the claim. **If MDE exceeds the pre-registered economic hurdle, either do not run the gate or pre-register INCONCLUSIVE → STOP** |
| Residual charters | Every residual charter prints the economic hurdle beside the MDE, before the peek |
| C1 public window | Permanently closed. Do not re-run F1 / F1a / F1c additions |
| G1 / G2 | Permanently closed. Do not re-run. Do not promote T+5. Do not open G3 |
| Live language models in a gate | Forbidden |
| Cascade-ready claims | Forbidden from this document |

---

## 7. Capability sentences

| Path | Sentence |
|---|---|
| **PASS (F)** | Not reached. Ranking already PASS. C2 did not GO. |
| **FAIL (F)** | C1 closed on economics. C2 STOP. Do not fit it harder or widen to foreign index families. |
| **PASS (G)** | Not reached. G1 existed; G2 did not clear 45 bps. |
| **FAIL (G)** | G2 INCONCLUSIVE / economic FAIL. Stop the earnings book. Do not substitute headline sentiment. Do not promote T+5. |
| **FAIL (programme)** | **Invoked.** C2 stopped. G failed on a passable harness. The desk is a passive core with an audit log. |

---

## 8. Out of scope

Dual-judge scoring and merge authority; remounting any closed ledger; the Precision execution bridge; options of any tenor; single-stock futures; intraday anything; selling signals without an investment-adviser or research-analyst registration.

---

## 9. Relation to existing docs

| Doc | Relationship |
|---|---|
| [forced-flow-execution-plan.md](forced-flow-execution-plan.md) | Milestone map for this blueprint |
| [forced-flow-status.md](forced-flow-status.md) | Measured pack, 2026-08-19 |
| [forced-flow-architect-review.md](../archive/forced-flow-architect-review.md) | Rev 3 unblock |
| [f3-residual-charter.md](f3-residual-charter.md) | C2 peek, written before the run |
| [f3-residual.md](../archive/f3-residual.md) | C2 STOP memo |
| [g0-charter.md](g0-charter.md) | G0, written before the hunt |
| [g0-calendar.md](../archive/g0-calendar.md) | G0 PASS memo |
| [g1-charter.md](g1-charter.md) | G1, written before the peek |
| [g1-earnings-drift.md](../archive/g1-earnings-drift.md) | G1 PASS memo |
| [g2-charter.md](g2-charter.md) | G2, written before the G1 peek |
| [g2-net.md](../archive/g2-net.md) | G2 INCONCLUSIVE / economic FAIL |
| [g3-charter.md](g3-charter.md) | G3, written before the G1 peek; not opened |
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
| Event-size, power, and capital sketches | Rev 2 Appendix A | **Falsified by F0/F1.** "Well powered" and "hundreds of events" do not hold. Required gross ≈300 bps; MDE was 323 at n=27. |

---

## Appendix B — Symbols

| Symbol | Meaning |
|---|---|
| \(c\) | Instrument round trip: 45 bps delivery, 10–12 bps index futures, 20 bps cash MIS archive |
| \(\delta\) | Conditional drift over the book's hold |
| \(\sigma\) | Volatility of the traded object over that hold |
| F0–F5, G0–G3 | Gates in §1. F2 is **F2-NET** (costs/tax). F&O list changes are **C4**, not F2 |
| C1–C4 | Book F constructions. C1 closed; C2 STOP; C3 locked companion; C4 deferred |
| Range head | Remaining-session range forecast — sizing only, never side |
