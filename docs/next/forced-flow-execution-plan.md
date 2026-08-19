# Retail India desk — Execution Plan

**Authority:** Implements [forced-flow-architecture-blueprint.md](forced-flow-architecture-blueprint.md) Rev 2  
**Status:** **ACTIVE** — Horizon Successor product hunt is **STOPPED**. Production cascade frozen. Rev 1's momentum and overlay milestones are **withdrawn** (blueprint §0.3).  
**Date:** 2026-08-18  
**Constraint:** Delivery **45 bps** round trip, short-term gains **20.8%**, benchmarked against an **after-tax** passive hold.

---

## How to read this plan

A milestone map, not a peek charter. Each milestone states why it exists, what to build, what ends it, and what stops it. Peek budgets belong in a follow-on charter derived from a pass.

- Production Regime → Horizon → Precision stays **frozen**. That tree is not on this branch.
- Rebuild pooled session-block CI + fold sign test, the real purge filter, and the disaster clip from [inherited-learnings.md](../archive/inherited-learnings.md) under `src/events/` when F1 needs them. Do not import a cascade package.
- The range head is a sizing/skip tool after a passing book, not a research track. Rebuild it only if Book F/G asks.
- No vendor data anywhere in this plan.

---

## Non-negotiables

| Lock | Rule |
|---|---|
| Do not remount | Anything from the closed cash-directional, remaining-session vol, or same-session fade ledgers |
| In-repo first | F0 and F1 run entirely on point-in-time membership already held |
| After tax | Every authority gate charges 20.8% and compares to an after-tax passive hold |
| Instrument | Cash delivery only. No options, no futures |
| MDE | Printed before every peek, beside the point estimate |
| No factor sorts | A do-it-yourself factor book must clear roughly +2.5% a year over the matching index fund after tax. Not attempted in this plan |
| Production | No cascade cutover. No live automation before a passing book |

### Global STOP language

If **F1** fails, or **F4** shows the effect decaying monotonically toward zero, stop Book F. Do not widen to foreign index families or fit the residual harder.  
If **G0** shows the results calendar needs a paid vendor, defer Book G rather than buying data.  
If Book F and Book G both fail on passable harnesses, the desk is a passive core plus an audit log. Record it and stop.

Before invoking FAIL: the gate must be passable by a correct model, the inputs must be able to carry the effect, the MDE must be published, the pipeline must be wired, the statistic must match the claim, and the hurdle must be the instrument's own.

---

## Milestone map

| ID | Name | Primary outcome | Hard stop if… |
|---|---|---|---|
| **P0** | Posture and cost lock | Successor frozen in the working set; delivery and tax constants; daily panel | Cost or tax constants disputed after gates start |
| **F0** | Event pool | Historical index membership changes reconstructed, counted by year and family | The pool cannot be built from in-repo membership |
| **F1** | Effect exists | Announcement-to-effective residual vs Nifty, cost-free | No effect, or MDE exceeds it |
| **F2** | Net of friction and tax | 45 bps then 20.8%, against an after-tax passive hold | Effect existed, edge did not |
| **F3** | Predictability | Out-of-sample ranking of candidate additions | Only the public post-announcement trade works |
| **F4** | Decay | Effect by year against passive-asset growth | Monotone decline toward zero |
| **F5** | Tradability | Circuits, borrow, lots, effective-date impact | Untradeable at retail size where the effect lives |
| **G0–G3** | Earnings drift | Calendar, then gross, net, and gap-restricted | Calendar needs a vendor, or drift fails |
| **L0** | Operating loop | Dated instruction list, audit record, reconciliation | Any drift toward tick feeds or intraday logic |

**P0 → F0 → F1 is the critical path.** Book G runs only in parallel if its calendar turns out to be free. There is no third book.

---

## P0 — Posture, cost lock, panel

### Why

The working tree still presents the closed programmes as gravity, and every gate below is denominated in constants that must be agreed before anyone sees a result.

### Build

1. A short freeze note: successor stopped, cascade frozen, this plan is the next spend, Rev 1's momentum and overlay books withdrawn with the reason.
2. Constants, unit-tested: delivery round trip 45 bps, short-term gains 20.8%, long-term 12.5%, index futures 10–12 bps recorded for reference only.
3. A daily panel from existing bars — symbol, date, open, high, low, close, volume, index-membership flag, Nifty close join. Corporate actions must fail loudly if absent rather than silently producing unadjusted returns.
4. An after-tax passive benchmark series: buy and hold, long-term rate applied on exit, so every later gate has a comparator.

### Exit

Constants tested, panel covering the years the existing folds cover, benchmark series reproducible.

### Stop

If the panel cannot be built from in-repo bars, say so and stop. Do not interpolate closes.

---

## F0 — Event pool

### Why

Everything downstream depends on whether a usable event history can be reconstructed for free. This is the milestone that decides whether Book F is a programme or an idea.

### Build

1. Reconstruct index membership changes by differencing point-in-time membership across dates, for every index family the repository covers.
2. Separate **announcement** dates from **effective** dates. Where only effective dates are recoverable, record that explicitly — it constrains which sub-gates can run, since F3 needs the announcement date.
3. Classify each event: addition or deletion, index family, and whether the name remains in the tradable universe.
4. Publish counts by year and family, and the implied sample size for F1.

### Exit

An event table with counts, plus a written statement of which of F1a, F1b, and F1c the available dates can actually support.

### Stop

Fewer events than the power calculation needs, or announcement dates unrecoverable and unobtainable free. Then Book F reduces to whatever the effective dates alone can test, or stops. Do not buy an event calendar to rescue this.

---

## F1 — Does the effect exist

### Why

The global index effect has decayed markedly in developed markets as it became well known. Whether it survives in India, where passive assets grew later and faster, is an empirical question and the first thing worth knowing.

### Build

1. Charter on one page: instrument, friction, the event window, the statistic, the required effect, and the MDE — before the peek.
2. Residual return against Nifty across the event window, purged folds, pooled statistic with a fold sign test, disaster losses clipped.
3. Run additions and deletions **separately**. They are different trades with different borrow and shortability constraints, and pooling them hides a one-sided result.
4. Companions, clearly labelled: the pre-announcement window and the post-effective reversal window.

### Exit

A three-way verdict with the effect size, interval, MDE, and event count printed together.

### Stop

FAIL, or MDE at or above the effect. In the latter case the verdict is inconclusive and the repair is more event history from the existing panel — never a data purchase, and never a re-run with a different window after seeing the result.

---

## F2 — Net of friction and tax

### Why

An event book realises gains inside twelve months, so the passive core's 12.5% deferred rate is the comparator, not a pre-tax index line.

### Build

Charge 45 bps round trip per event leg, then 20.8% on realized gains, and compare against the after-tax passive series from P0. Publish the per-event net in basis points and the annual contribution implied by the F0 event count at a stated active weight.

### Exit

Net lower bound above zero against the after-tax benchmark, plus that annual contribution figure.

### Stop

FAIL, or an annual contribution too small to justify the operational risk. The second case is a legitimate stop even when the statistics pass, and it should be judged against the number written down in the blueprint before the peek.

---

## F3 — Predictability

### Why

Trading after the announcement is public information. The durable version of this book predicts membership changes from the published, largely mechanical eligibility rules before they are announced.

### Build

1. Replicate the ranking rules — free-float market capitalisation and eligibility filters — as of each pre-announcement cut-off, using only data available then.
2. Rank candidates and evaluate out of sample: hit rate, rank correlation with actual changes, and the realized-versus-required skill line.
3. Only then, size positions by predicted inclusion probability and reprint F2 on the pre-announcement window.

### Exit

Out-of-sample ranking beats a naive baseline and the pre-announcement window clears F2, or Book F is limited to whatever F1a supports.

### Stop

Do not fit a large model here before the simple rule replication is evaluated. If the rules cannot be replicated from available fields, say so and keep the public version only.

---

## F4 — Decay

### Why

A trade that worked in 2015 and not since is a museum piece. This gate exists to catch that before capital is committed, and it is the one most likely to end the book.

### Build

Effect by year, with event counts, plotted against the growth of passive assets tracking the affected indices. Pre-register what counts as decay before looking.

### Exit

No monotone decline toward zero, or a clear stop.

### Stop

Do not smooth, pool, or reweight the sample to hide a downward trend. That is the geometry sweep in a slower costume.

---

## F5 — Tradability

### Why

Effects concentrate in exactly the names that are hardest to trade: small additions, circuit-limited moves, and deletions that cannot be shorted in cash.

### Build

Apply circuit-limit exclusions, delivery availability, lot and rounding constraints, and borrow availability for any short leg. Estimate impact for a retail-sized order at the effective-date close. Reprint F2 on the tradable subset.

### Exit

The tradable subset still clears F2, or the book stops with the reason recorded.

### Stop

Do not drop the tradability mask to recover a result. If the effect lives only where it cannot be traded, that is the finding.

---

## G0–G3 — Earnings drift

### Why

The second-best use of the same harness, and the only other place where the move plausibly dwarfs friction.

### Build

1. **G0:** assemble announcement dates from free sources. If that fails, defer the book. Book F is unaffected.
2. **G1:** residual against Nifty, entry at the first close provably containing the announcement, T+3 as authority with T+1 and T+5 as companions, cost-free, disaster clipped.
3. **G2:** 45 bps then 20.8% tax against the after-tax benchmark.
4. **G3:** restricted to events whose overnight gap sits below a pre-registered percentile.

### Stop

G1 FAIL stops the book. If G3 shows the edge exists only where the gap already repriced the news, there is no trade. Do not add guidance or sentiment models in the same milestone.

---

## L0 — Operating loop

### Why

A book that trades tens of times a year needs a calendar and a record, not a trading platform.

### Build

1. A daily batch job producing a dated instruction list: event, name, direction, size, and the window to execute in.
2. Risk checks applied to that list: position cap, sector cap, event concentration, range-head sizing, and total active weight against the passive core.
3. An append-only record of every instruction, fill, and skip, with reasons.
4. Broker reconciliation as the source of truth.
5. Human-confirmed order placement, executed in a scheduled window or the closing auction, with algo-order tagging.
6. Shadow-run the loop over past events, then run it live at a fraction of the intended size.

### Stop

If the build starts adding a tick feed, an event bus, or intraday logic, stop the build rather than the research. Automating the closing auction is a later, focused extension justified only by measured slippage.

---

## Suggested calendar

| Elapsed | Work |
|---|---|
| Days 1–2 | P0 constants, panel, after-tax benchmark, freeze note |
| Days 3–4 | F0 event pool and counts; decide which sub-gates are supportable |
| Days 5–6 | F1 charter and peek, additions and deletions separately |
| Day 7 | F2 net of friction and tax, with the annual contribution figure |
| Days 8–10 | F3 rule replication and out-of-sample ranking |
| Days 11–12 | F4 decay, F5 tradability |
| Parallel | G0 calendar hunt; G1–G3 only if free |
| After a pass | L0 shadow run, then fractional live size |

Do not start L0 before F2. Do not open Book G before F1 has a verdict.

---

## Forbidden in this plan

Any closed ledger; factor sorts; index or single-stock futures; options; intraday logic of any kind; buying an event or results calendar; widening to foreign index families for sample size; fitting a model before the mechanical rule replication in F3; treating an inconclusive verdict as a pass; sample-era friction; cascade-ready claims.

---

## Expected artifacts

| Path | Role |
|---|---|
| `src/events/` | Event pool construction, ranking rules, cost and tax constants — created at P0 |
| `docs/archive/` | One memo per gate verdict, written after the peek |
| `logs/` | Fold outputs, following existing convention |

Peeks live under `src/events/` and `src/experiments/` if needed. There is no `src/horizon/` on this branch.

---

## Relation to existing docs

| Doc | Role |
|---|---|
| [forced-flow-architecture-blueprint.md](forced-flow-architecture-blueprint.md) | Authority |
| [forced-flow-freeze-note.md](../archive/forced-flow-freeze-note.md) | Working-set freeze |
| [horizon-successor-closed.md](../archive/horizon-successor-closed.md) | Prior programme stop |
| [cascade-closed.md](../archive/cascade-closed.md) | Frozen production map, summarized |
| [inherited-learnings.md](../archive/inherited-learnings.md) | Gate machinery to reimplement |
