# Retail India desk — Execution Plan

**Authority:** Implements [forced-flow-architecture-blueprint.md](forced-flow-architecture-blueprint.md) **Rev 3**  
**Status:** **ACTIVE** — Book F capital closed (C1 economic FAIL; C2 STOP). Ranking retained. Book G is the research primary. Horizon Successor **STOPPED**. Production cascade frozen.  
**Date:** 2026-08-19  
**Constraint:** Delivery **45 bps** round trip, short-term gains **20.8%**, benchmarked against an **after-tax** passive hold.  
**Review:** [forced-flow-architect-review.md](../archive/forced-flow-architect-review.md). **Pack:** [forced-flow-status.md](forced-flow-status.md).

---

## How to read this plan

A milestone map, not a peek charter. Each milestone states why it exists, what to build, what ends it, and what stops it. Peek budgets belong in a follow-on charter derived from a pass.

- Production Regime → Horizon → Precision stays **frozen**. That tree is not on this branch.
- Pooled session-block CI, fold sign test, purge filter, and disaster clip live under `src/events/` (F1 used them). Reuse for F3-RESIDUAL and G1. Do not import a cascade package.
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

If **F3-RESIDUAL** STOPs (including INCONCLUSIVE→STOP) **and** Book G fails on a passable harness, the desk is a passive core plus an audit log. Record it and stop.  
C1 (announcement→effective) is already closed. Do not re-open it. Do not widen to foreign index families or fit the residual harder.  
If **G0** shows the results calendar needs a paid vendor, defer Book G rather than buying data.

Before invoking FAIL: the gate must be passable by a correct model, the inputs must be able to carry the effect, the MDE must be published, the pipeline must be wired, the statistic must match the claim, and the hurdle must be the instrument's own.

---

## Milestone map

| ID | Name | Status | Hard stop if… |
|---|---|---|---|
| **P0** | Posture and cost lock | **Done** | Cost or tax constants disputed after gates start |
| **F0** | Event pool | **Done** | 68 events, 43 tradable |
| **F1** | Public residual (C1) | **Closed** | INCONCLUSIVE existence, economic FAIL. Do not re-run |
| **F2-NET** | 45 bps then 20.8% | **Closed-N/A** | C1 and C2 both closed |
| **F3-SKILL** | Next 50 FF rank | **PASS** | 66.7% vs 4.1% naive |
| **F3-RESIDUAL** | C2 predicted top-3 basket | **STOP** | Point +205 < 300 hurdle. Capital closed |
| **F4** | Decay | **Folded** into F3-RESIDUAL era split | Not a standalone peek at n≈22 |
| **F5** | Tradability | **Not opened** | C2 was STOP |
| **G0–G3** | Earnings drift | **G0 open now** | Calendar needs a vendor, or drift fails |
| **L0** | Operating loop | Not opened | Any drift toward tick feeds or intraday logic |

**Critical path:** **G0 → G1 → G2 → G3.** Book G is the main line. Book F capital is closed. Do not start L0 before F2-NET on a passing book.

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

### Verdict (2026-08-19)

**Closed.** Additions +26.3 bps (T−20→T) and +51.8 bps (announce→T) against MDE 323.5 bps. INCONCLUSIVE on existence. Economic FAIL: the centre cannot clear 45 bps delivery, and MDE ≈ the ~300 bps gross hurdle, so a product-sized effect would have been seen.

**Windows permanently closed:** T−20→T, announcement→T, T→T+20 additions. Do not re-run with a new estimator, clip, or universe. T−40→T−20 actual-addition companion and F1c deletion companion stay locked.

T−20 sits inside the announcement window. F1-effective was a subset of F1a.

---

## F2-NET — Net of friction and tax

### Why

An event book realises gains inside twelve months, so the passive core's 12.5% deferred rate is the comparator, not a pre-tax index line.

**F2 keeps this meaning.** Blueprint F&O list changes are construction **C4**, not F2.

### Build

Charge 45 bps round trip per event leg, then 20.8% on realized gains, and compare against the after-tax passive series from P0. Publish the per-event net in basis points and the annual contribution implied by event count at a stated active weight.

### Status

**Closed-not-applicable.** C1 closed on economics. C2 STOP. F2-NET does not re-open on reconstitution.

### Stop

FAIL, or an annual contribution too small to justify the operational risk.

---

## F3-SKILL — Predictability (done)

### Verdict

**PASS.** NSE MCWB Next 50 6-month average FF mcap; top-k hit rate 66.7% CI [47.8%, 85.5%] vs naive 4.1%; mean rank 2.67; n=24 scored. 2015–19 76.9%; 2020–25 54.5%. Charter: [f1b-charter.md](f1b-charter.md). Memo: [f1b-pre-announcement.md](../archive/f1b-pre-announcement.md).

Do not fit a richer ranker. C2 equal-weight peek is done (STOP). The F1b memo's "do not open a pre-announcement residual until F1a/F2" is **superseded**.

---

## F3-RESIDUAL — C2 predicted basket (done)

### Why

Ranking is an input. The product is a hold of *predicted* names from a PIT-safe entry to the session after the PR. That window had never been measured with an ex-ante label.

### Verdict (2026-08-19)

**STOP.** Authority (top-3 minus Next 50 ranks 21–50) +204.8 bps, CI [54.6, 353.1], n=22, prior MDE 448, hurdle 300, GO bar 450. Both eras positive (+154 / +247). CI lower bound > 0. Point below the economic hurdle. Companion vs Nifty +236.4. Sensitivity (coverage ≥ 2/3) +175.8. Memo: [f3-residual.md](../archive/f3-residual.md).

Book F capital stops. Do not open F2-NET or F5. Ranking (F3-SKILL) retained.

---

## F4 — Decay

Folded into F3-RESIDUAL as 2015–19 vs 2020–25. A standalone peek at n≈22 is not a valid gate.

---

## F5 — Tradability

Not opened. F3-RESIDUAL was STOP.

---

## G0–G3 — Earnings drift (research primary)

### Why

The only book on this desk where MDE sits below the candidate effect. Existing 100-name panel × ~44 quarters ≈ thousands of events; MDE ≈ 25 bps at σ=600 vs 100–400 bps candidate moves. F1 and C2 have verdicts. **G0 is unblocked.**

### Build

1. **G0 (open now, three-day cap):** assemble results dates from free NSE corporate-announcement archives. If not free in three days, defer per the existing rule. Do not buy a vendor. The 100-name panel is the universe — no expansion.
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
| Days 1–3 | G0 calendar hunt |
| Days 4+ | G1 if the calendar is free; else the desk is a passive core plus ranking research and the audit log |
| After a C2 GO | — not reached |
| After a G2 pass | L0 shadow run, then fractional live size |

Do not start L0 before F2-NET on a passing book. P0–F3-RESIDUAL are done; do not repeat them.

---

## Forbidden in this plan

Any closed ledger; factor sorts; index or single-stock futures; options; intraday logic of any kind; buying an event or results calendar; widening to foreign index families for sample size; fitting a model on Book F; treating an inconclusive F1 residual as a pass; sample-era friction; cascade-ready claims; re-running any peeked F1 or C2 window with a new estimator; promoting either locked companion; building the PIT F&O list or a full-NSE panel to rescue C2; any standalone F4 peek.

---

## Expected artifacts

| Path | Role |
|---|---|
| `src/events/` | Event pool, ranking, residual, stats — created at P0 |
| `docs/next/forced-flow-status.md` | Measured pack |
| `docs/archive/forced-flow-architect-review.md` | Unblock review |
| `docs/next/f3-residual-charter.md` | C2, written before peek |
| `docs/archive/` | One memo per gate verdict, written after the peek |
| `logs/` | Fold outputs, following existing convention |

Peeks live under `src/events/` and `src/experiments/` if needed. There is no `src/horizon/` on this branch.

---

## Relation to existing docs

| Doc | Role |
|---|---|
| [forced-flow-architecture-blueprint.md](forced-flow-architecture-blueprint.md) | Authority, Rev 3 |
| [forced-flow-status.md](forced-flow-status.md) | Measured pack |
| [forced-flow-architect-review.md](../archive/forced-flow-architect-review.md) | Unblock review |
| [f3-residual-charter.md](f3-residual-charter.md) | C2, written before peek |
| [f3-residual.md](../archive/f3-residual.md) | C2 STOP memo |
| [forced-flow-freeze-note.md](../archive/forced-flow-freeze-note.md) | Working-set freeze |
| [horizon-successor-closed.md](../archive/horizon-successor-closed.md) | Prior programme stop |
| [cascade-closed.md](../archive/cascade-closed.md) | Frozen production map, summarized |
| [inherited-learnings.md](../archive/inherited-learnings.md) | Gate machinery to reimplement |
