# Retail US desk — Execution Plan

**Authority:** Implements [us-equity-architecture-blueprint.md](us-equity-architecture-blueprint.md) **Rev 1**  
**Status:** **DRAFT** — unmeasured. Fresh start. No measurements exist.  
**Date:** 2026-08-20  
**Goal:** Establish whether any economically viable algo trading book exists for a $25k–$500k US retail desk after cost and after tax versus an after-tax VTI hold, and if so, operate it.  
**Constraint:** After-cost, after-tax excess vs an after-tax VTI hold. Cost and tax constants are **working** until P0 calibrates them.

---

## How to read this plan

This is a **milestone map, not a peek charter.** No milestone authorizes a look at a strategy result unless its Exit condition names the statistic in advance. Each milestone has four fields:

- **Why** — the question it answers
- **Build** — the artefacts, and nothing beyond them
- **Exit** — the numeric condition to proceed
- **Stop** — the condition that closes the branch and produces a STOP memo in `docs/archive/`

Milestones run in sequence. A book's milestones may not begin before P0, U0, and H0 are all green. A STOP memo is a completed milestone, not a failure.

---

## Non-negotiables (locks)

| # | Lock |
|---|---|
| 1 | Constraint order is fixed: **tax wrapper → friction → inference → capacity → alpha.** Alpha work before rung 4 is complete is out of scope. |
| 2 | Every result is reported **after cost and after tax**, against an **after-tax VTI hold**. Gross-only results are not results. |
| 3 | **MDE is printed before every peek.** MDE > 0.5 × hypothesized effect closes the book without a peek. |
| 4 | `costs` and `tax` are single, unit-tested modules. No backtest may re-implement either. |
| 5 | Point-in-time or it does not exist. Delisted tickers present; no survivorship. |
| 6 | Trial budget 5 pre-registered specs per book, α = 0.01, logged including abandonments. |
| 7 | **No live capital before L0.** Paper 60 sessions, then 10% size for 60 sessions. |
| 8 | No short stock, no naked short options, no leverage above 1.0× in v1. |
| 9 | No vendor data purchase unless P0 or a later milestone explicitly authorizes it. Public and broker data first. |
| 10 | No HMM, LightGBM, MLflow, or Kaggle client enters `pyproject.toml`. If a milestone appears to need one, the milestone design is wrong. |
| 11 | AI produces features from text and runs ops checks. AI does not forecast returns. |
| 12 | Own capital only. No third-party money, no advertised performance. |

---

## Milestone map

| ID | Name | Status | Hard stop if… |
|---|---|---|---|
| **P0** | Posture and cost lock | Software green; 200 broker fills outstanding | Modelled costs cannot be pinned within 3 bps / 0.3% of premium against real broker fills |
| **U0** | Universe and point-in-time panel | Fixture panel + tests green; Polygon dump outstanding | Delisted coverage is unavailable at acceptable cost → equity single-name books close |
| **H0** | Hurdle and inference design | **Complete** | Every candidate book's MDE exceeds 0.5 × its hypothesized effect → programme stops at H0 |
| **C1** | Book C — tax and location accounting proof | **Complete** (35.5 bps/yr, 0 washes, representative lots) | After-tax excess vs static VTI < 25 bps/yr → harvest module dropped, location/bands kept |
| **C2** | Book C — shadow year | Not started | Realized after-tax excess < 15 bps or any wash-sale violation reaches a filing |
| **A1** | Book A — VRP existence | Not started | Mean implied-minus-realized in the 20–25 delta bucket ≤ modelled round-trip cost |
| **A2** | Book A — economics and ETF benchmark | Not started | After-tax sleeve fails to beat PUTW-equivalent by 75 bps/yr, or sleeve Sharpe < 0.4, or sleeve max DD > 25% of sleeve notional |
| **A3** | Book A — tradability | Not started | Paper fills worse than modelled by > 0.3% of premium, or fill rate at target limits < 80% |
| **B1** | Book B — PEAD existence | Not started | Pooled net-of-cost drift < 40 bps/event on ≥ 6,000 clustered events, or effect lives only below $20M ADV |
| **B2** | Book B — economics and AI increment | Not started | IRA capacity insufficient to house the sleeve, or LLM text features add < 10 bps over numeric surprise → AI removed |
| **B3** | Book B — tradability | Not started | Realized mid-cap round-trip cost exceeds 25 bps, or closing-auction fills degrade the drift by > 15 bps |
| **L0** | Operating loop | Not started | No book has passed its H5 minimum → global STOP, 100% passive posture |
| **X0** | Kill review | Not started | Standing quarterly gate; any live book that misses its H5 minimum over four rolling quarters is retired |

**Critical path:** P0 → U0 → H0 → C1 (then C2 in the background) → A1 → A2 → A3 → B1 → B2 → B3 → L0. L0 is built only after a book passes. X0 is standing once live.

---

## P0 — Posture and cost lock

### Why

Nothing downstream is interpretable until the desk knows what a trade costs and what a gain is taxed at. Rungs 1 and 2 of the ladder become code here.

### Build

1. `costs`: bid-ask and effective half-spread by product bucket, Section 31 (**working** ~$27.80/$1M of sell proceeds), FINRA TAF ($0.000166/share, $8.30 cap), OCC $0.02/contract, exchange ORF, broker per-contract, borrow rate stub (set to "prohibited" in v1), futures round-turn. Unit-tested per bucket against the table in Blueprint §0.2.
2. `tax`: ST 40% / LT 20% / 1256 blend 28% (**working**, configurable), qualified-dividend test, wash-sale window arithmetic across joint accounts, IRA-destruction case, FIFO/specific-lot accounting, December 1256 mark. Unit-tested against hand-worked examples.
3. **After-tax VTI benchmark series**, 2005–2026: total return, dividends taxed at 20% on the qualified-dividend schedule, 3 bps ER. This series is the denominator of every later claim.
4. PDT state machine and Reg T / portfolio-margin thresholds as constants.
5. Broker account opened; API keys; 200 real fills logged in tiny size across SPY, one large cap, one mid cap, and one SPX spread, purely to calibrate `costs`.
6. **Data decision, minimal:** Polygon Developer tier (adjusted daily bars, corporate actions, delisted tickers) and CBOE SPX EOD option history for the years A1 requires. Nothing else. Fundamentals vendor deferred to B2.

### Exit

All cost and tax unit tests pass; modelled cost matches the 200 calibration fills within 3 bps (equities) and 0.3% of premium (options); after-tax VTI series reproduces published VTI total return within 5 bps/yr before tax.

### Stop

Costs cannot be pinned within tolerance → the desk cannot evaluate any book and the programme stops here.

---

## U0 — Universe and point-in-time panel

### Why

Survivorship bias is the single most common cause of a fake equity backtest. This milestone makes the panel honest or closes the single-name branch.

### Build

PIT listing panel for US common stock and ETFs, 2005–2026, including delisted, acquired, and renamed tickers with effective dates. Split and dividend adjustment from one canonical source, unit-tested against six known corporate actions. Daily $ADV and a liquidity bucket per name-date. EDGAR filing index keyed by accession number and **filing timestamp**. Panels in Polars, typed, `df in → df out`.

### Exit

Panel round-trips a known index membership snapshot; delisted names are present and their final prices are sane; no future information reachable from any row's knowledge date (verified by an automated leakage test).

### Stop

Delisted coverage unobtainable → Book B closes; Books A and C proceed (neither needs single-name history).

---

## H0 — Hurdle and inference design

### Why

Decide what is measurable **before** looking. This is the milestone that prevents three years of wasted work.

### Build

For each candidate book: the bet definition, n per year, estimated σ per observation, the clustering haircut, and **MDE = 2.8σ/√n**, published in `docs/`. Purged and embargoed walk-forward splits per book. Trial ledger with pre-registered specifications. Deflated-Sharpe implementation. A `harness` guard that raises unless n, σ, and MDE have been printed for the current test.

### Exit

MDE published for all three books; at least one book has MDE ≤ 0.5 × its hypothesized effect; harness guard demonstrably blocks an un-declared test.

### Stop

No book clears the MDE ratio → **programme stops at H0 with zero data-mining risk incurred.** This is a legitimate and inexpensive outcome.

---

## C1 / C2 — Book C, tax and location engine

### C1 Why

The highest-certainty return in the document. It is an accounting result, not a statistical one, so it can be proven quickly and cheaply.

### C1 Build

Asset-location optimizer (which holding in which wrapper, given IRA capacity); rebalance-band logic with MES beta adjustment so drift is corrected without realizing gains; harvest engine over a whitelisted, non-substantially-identical substitute set with a 31-day joint-account quarantine; five-year retrospective simulation on the desk's actual (or representative) lot structure, priced through `costs` and `tax`.

### C1 Exit

Simulated after-tax excess vs a static VTI hold ≥ 25 bps/yr, with zero wash-sale violations in the simulation and a full audit trail of every harvest decision.

### C1 Stop

< 25 bps → drop harvesting; keep location and bands, which cost nothing and are retained regardless.

### C2 Why

Confirm the accounting result survives contact with a real broker and a real tax year.

### C2 Build

Run C1 live on the passive core only (no active sleeve), with the instruction list and reconciliation from L0's ops module in minimal form. One full tax year. Reconcile the lot ledger to the broker's 1099-B.

### C2 Exit

Realized after-tax excess ≥ 15 bps; lot ledger agrees with broker 1099-B on every lot; zero wash-sale violations.

### C2 Stop

Any wash-sale violation that reaches a filing → harvest module disabled permanently. The tax risk dominates the 30 bps.

---

## A1 / A2 / A3 — Book A, index VRP

### A1 Why

Establish that the premium exists in the specific delta bucket and tenor the desk can actually trade, and that it is larger than the cost of trading it.

### A1 Build

SPX EOD option panel 2005–2026. Implied volatility minus subsequent realized volatility by delta bucket (10/15/20/25/30) and tenor (7/14/30/45 DTE). Sub-period breakdown, including 2018, 2020, and 2024 stress windows. All figures net of the modelled round-trip cost from `costs`. Explicitly include a 0DTE and 7DTE row to document the Blueprint's closure of 0DTE with this desk's own numbers.

### A1 Exit

Mean implied-minus-realized in the 20–25 delta, 30–45 DTE bucket exceeds modelled round-trip cost by ≥ 2×, and the sign is stable in at least 4 of 5 non-overlapping sub-periods.

### A1 Stop

Premium ≤ cost, or sign unstable → Book A closes. Do not search other delta buckets beyond the pre-registered five; that is spec mining.

### A2 Why

A premium is not a book. Test the sleeve after cost, after tax, against the packaged ETF alternative — which is the real competitor.

### A2 Build

Walk-forward simulation of the pre-registered rule (short 20–25 delta put spread, 30–45 DTE, 50–100 point width, close at 50% credit or 7–14 DTE), sized to the 8%-of-equity max-loss limit, with the 28% Section 1256 blend applied and the December mark modelled. Benchmark: PUTW-equivalent held in the taxable account with ordinary-income distributions. Second benchmark: after-tax VTI. Blend the sleeve with the passive core at 15%, 20%, and 25% weights.

### A2 Exit

Sleeve after-tax return beats the ETF equivalent by ≥ 75 bps/yr, sleeve Sharpe ≥ 0.4, sleeve max drawdown ≤ 25% of sleeve notional, and total-book after-tax excess vs VTI ≥ 200 bps with total-book max drawdown not exceeding the benchmark's.

### A2 Stop

Any of those four fails → Book A closes. Do not re-optimize width or exit rule outside the trial budget.

### A3 Why

Options backtests lie about fills. Find out by how much before risking money.

### A3 Build

60 sessions of paper trading the exact rule with the exact limit-price policy (mid + 25% of spread cap, no chasing). Log intended vs achieved price per leg. Feed realized slippage back into `costs` and re-run A2 with the calibrated number.

### A3 Exit

Realized slippage within 0.3% of premium of model; fill rate at target limits ≥ 80%; A2 still passes on recalibrated costs.

### A3 Stop

Fills degrade the edge below the A2 exit → Book A closes.

---

## B1 / B2 / B3 — Book B, PEAD

### B1 Why

The only book with an inference budget that supports genuine discovery. Also the most likely to be already arbitraged. Test the existence claim on numeric data alone, before spending a dollar on AI or fundamentals vendors.

### B1 Build

Event panel from EDGAR filing timestamps (8-K earnings releases) joined to the U0 price panel, 2010–2026, $ADV > $20M. Surprise proxy from the announcement-window return only (no vendor consensus needed at this stage). Pooled forward returns at 5/10/20/40 days, net of modelled cost, with date and sector clustering, purged walk-forward, and controls for momentum and size. MDE printed first.

### B1 Exit

Net-of-cost drift ≥ 40 bps per event, present in the $20–100M ADV band (not only in the illiquid tail), stable in sign across walk-forward folds.

### B1 Stop

Below 40 bps, or effect concentrated below $20M ADV → Book B closes. No vendor fundamentals are purchased.

### B2 Why

Establish that the sleeve is housable (IRA capacity) and that text-derived features earn their complexity.

### B2 Build

Only now, if B1 passed: authorize a PIT fundamentals/consensus subscription. Build `ai.extract` for guidance-change and call-language features with strict pre-timestamp inputs, cached and versioned. Report the sleeve three ways: numeric surprise only, numeric + text, and text only. Model the IRA-versus-taxable placement explicitly.

### B2 Exit

Sleeve is fully housable in the IRA at ≥ 20% of total equity; text features add ≥ 10 bps per event over numeric surprise on held-out folds; total-book after-tax excess ≥ 200 bps.

### B2 Stop

Text adds < 10 bps → remove the AI layer and re-test numeric-only against the same exit. IRA capacity insufficient → apply the 40% tax haircut; if the sleeve then fails, Book B closes.

### B3 Why

Mid-cap fills are where PEAD backtests die.

### B3 Build

60 sessions of paper trading via the closing auction (MOC/LOC) at target size. Measure realized round-trip cost per name bucket and the decay of the drift caused by entry timing.

### B3 Exit

Realized round-trip cost ≤ 25 bps in the traded bucket; auction-timed entry preserves ≥ 85% of the modelled drift; B2 still passes on recalibrated costs.

### B3 Stop

Either fails → Book B closes.

---

## L0 — Operating loop

### Why

Build the operating machinery only for books that have already passed. Ops before alpha is how retail desks spend two years building infrastructure for a strategy that never existed.

### Build

Daily instruction-list generator (dry-run first, diffed against live positions); IBKR order adapter with limit/MOC/LOC and the kill switch; PDT counter and margin pre-check; fill audit of intended versus actual; daily P&L reconciliation against broker statements; tax-lot ledger with wash-sale flags; after-tax attribution report versus the P0 benchmark series. Deploy at 10% of target size for 60 sessions, then full size.

### Exit

60 consecutive sessions with zero unexplained reconciliation breaks, zero PDT or locate violations, kill switch verified in a drill, and live after-cost tracking within 30 bps/yr of the A2/B2 model.

### Stop

No book passed → **global STOP.** Post the STOP memo, hold 100% passive core plus IRA factor ETFs plus Book C location and bands. Reopen only with new data.

---

## X0 — Kill review

Standing quarterly gate once live. Any book missing its H5 minimum over four rolling quarters is retired and its capital returns to the passive core. Retirement is automatic and does not require a new debate.

---

## Critical path

P0 is the gate on everything: without a calibrated cost model, a tested tax model, and an after-tax VTI benchmark, no later result can be interpreted, so P0 is worked to completion first and no strategy code is written during it. U0 runs next and can proceed in parallel with the tail of P0 since it shares only the corporate-action tests. H0 immediately follows and is the cheapest possible programme-killer — if no book's MDE clears half its hypothesized effect, the programme ends there having spent weeks rather than years. Book C then runs first among the books because it is an accounting proof rather than a statistical one and it delivers the only near-certain return in the plan, and its C2 shadow year can run in the background while Book A is researched. Book A follows because A1 is a single, cheap, high-information test on one purchased dataset and because Section 1256 gives it a structural tax advantage no ETF can match. Book B runs last despite having the best inference budget, because it is the most expensive branch (fundamentals subscription, LLM extraction pipeline, mid-cap fill risk) and the most likely to be already in the price — so it is gated behind a numeric-only existence test that costs nothing but EDGAR and the U0 panel. L0 is built only after a book passes, never before. The single largest scheduling risk is the temptation to build L0 early because it feels like progress; the plan forbids it.
