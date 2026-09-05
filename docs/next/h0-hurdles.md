# H0 — Hurdles H1–H7

Date: 2026-09-05
Milestone: H0
Charter: [india-equity-architecture-blueprint.md](india-equity-architecture-blueprint.md) §10

These numbers are locked **before any book is looked at**. A later disappointing result is not a
reason to lower a hurdle.

**Benchmark for H2, H3 and H7:** Nifty 50 TRI, net of **0.04% TER**, taxed at **13.0% on
realisation**, on the same capital and the same cash-flow schedule as the sleeve under test. That is
NIFTYBEES, priced honestly. Implemented as `src.harness.benchmark`.

| # | Hurdle | Number | STOP |
|---|---|---|---|
| **H1** | Cost and tax fidelity | `costs` reproduces a real broker contract note to **₹1 per trade**, and `tax` reproduces a hand-worked Tax Year 2026-27 computation for a mixed delivery + intraday + F&O book to **₹1**, across cash delivery, ETF delivery, cash intraday, index futures, index options and exercise STT, plus DP charges | If either fails, **the platform stops.** No book proceeds on an unverified cost model. |
| **H2** | After-cost after-tax excess | Any active sleeve must beat the benchmark by **≥ 300 bps/yr** over the full PIT sample | Below 300 bps, the sleeve closes and its weight goes to the packaged vehicle or the core. |
| **H3** | Risk-adjusted | Active Sharpe versus the benchmark **≥ 0.40** after cost and tax, and **≥ 0.30 in each of two non-overlapping halves** | Fails either leg → close. |
| **H4** | Measurability | **MDE_ann = 2.80 σ/√T ≤ ½ × E_net**, with n, σ, MDE and E_net published in a pre-registration file **before the first peek**. Budget: **5 specifications per book.** | A book whose MDE exceeds half its pre-registered effect **closes at H0, before any data is looked at.** After the fifth spec, the book closes regardless of result. |
| **H5** | Capacity | Clears H2 at ₹50 lakh with impact cost from the NSE monthly file at **6× the actual order size**, and no single order exceeds **10% of the name's 20-day median delivery value** (delivery, not traded — MWPL is now 65× ADDV) | Fails → reduce breadth or close. |
| **H6** | Operability | One machine, one broker, one ~16:15 IST run, **≤ 10 orders/second**, exchange algo ID on every order, reconciled to the broker ledger to ₹1 the next morning before pre-open, with a documented manual fallback | If the loop needs a second machine, a second broker, or intraday supervision, **stop and redesign.** |
| **H7** | Whole-desk | After-tax return trails the Nifty 50 TRI by more than **600 bps in a tax year** | Halt all active sleeves, move to 100% core, and write an X0 review. |

## Why H2 is 300 bps

A 100%-turnover cash-delivery sleeve inflicts drag on itself that a NIFTYBEES core does not:

| Piece | Approx. |
|---|---|
| Statutory + broker friction on a ₹1 lakh delivery round trip (`costs`, P0) | **23.8 bps** |
| Tax differential: realising as s.196 STCG (20.8%) instead of s.198 LTCG (13.0%) on an ~11%/yr TRI assumption | **~78 bps** |
| Impact, using the NSE monthly impact-cost file rather than a quoted spread | **~40 bps** |
| **Self-inflicted drag** | **~140 bps** |

H2 requires that drag to be earned back **twice over** (~280 bps). The packaged competitor's TER is
**30–34 bps** (direct/ETF factor vehicles in Book P). Three hundred basis points sits above 280 and
above that TER by enough to pay for operational risk (one machine, one broker, instruction lists,
reconciliation). It is not a round number chosen after seeing a backtest.

Book L's hypothesised 95–130 bps is **schedule delta versus a naive realisation**, not H2 excess
versus the TRI. L is arithmetic and is not required to clear 300 bps of active alpha. Active sleeves
(anything that takes security-selection or timing risk against the benchmark) are.

## H4 arithmetic

At α = 0.05 two-sided and 80% power, \(z_{1-α/2} + z_{1-β} = 1.96 + 0.84 = 2.80\).

**MDE_ann = 2.80 × σ_ann / √T**, where σ_ann is the annualised standard deviation of the **sleeve
versus the benchmark**, not of an academic anomaly. Gate: **MDE_ann ≤ ½ × E_net**.

`src.harness.mde` implements the formula. Unit tests pin the six blueprint §5.1 values: 0.63%,
5.01%, 7.23%, 36.4%, 10.9%, 2.44%.

## Pre-registration files

Committed under `docs/next/h0-prereg-book-*.md` **before** any book's first data access. `harness`
loads them, hashes the file bytes, and checks MDE and H4 against the formula. Specification budget
is 5; `spec_budget_guard` refuses a sixth.

W17 (Book L): the 11%/yr Nifty 50 TRI figure used in the 95–130 bps schedule arithmetic is an
**assumption, not a forecast**. The *delta* between schedules is insensitive to the level.

## Closed at H0 (STOP memos, no peek)

| Phenomenon | Memo |
|---|---|
| Book R — results-season drift | [book-r-stop.md](../archive/book-r-stop.md) |
| Index option premium selling | [book-option-premium-stop.md](../archive/book-option-premium-stop.md) |
| Budget / MPC event days | [book-event-day-stop.md](../archive/book-event-day-stop.md) |
| Index reconstitution / passive flow | [book-recon-stop.md](../archive/book-recon-stop.md) |

Book M fails H4 5.0× and stays gated behind Book P; it is not opened. Book A fails H4 today and is
deferred to **2027-08-31**. Book B is H4-marginal and stays gated on SEBI's reformed-SLBM circular.
