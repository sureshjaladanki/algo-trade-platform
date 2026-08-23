# Retail US desk — Execution Plan

**Authority:** Implements [us-equity-architecture-blueprint.md](us-equity-architecture-blueprint.md) **Rev 1.1**  
**Status:** **ACTIVE** — measured through 2026-08-22. H0, C1, A0, A0.5, B0, B0.5 complete at $0. **A1 STOP:** spliced 2012–present (OptionsDX + ThetaData FREE) IV−RV 4.91 vol pts vs spread cost 4.14 (**1.19×** < 2×). Book A closed. A2/A3 not run. B1 is not certified.  
**Date:** 2026-08-22  
**Revision:** Spend-deferral. Claude Opus review 2026-08-21. Vendor purchases moved off P0; discovery ceiling **$700**.  
**Goal:** Establish whether any economically viable algo trading book exists for a $25k–$500k US retail desk after cost and after tax versus an after-tax VTI hold, and if so, operate it.  
**Constraint:** After-cost, after-tax excess vs an after-tax VTI hold. Cost and tax constants are **working** until P0 calibrates them.

---

## How to read this plan

This is a **milestone map, not a peek charter.** No milestone authorizes a look at a strategy result unless its Exit condition names the statistic in advance. Each milestone has four fields:

- **Why** — the question it answers
- **Build** — the artefacts, and nothing beyond them
- **Exit** — the numeric condition to proceed
- **Stop** — the condition that closes the branch and produces a STOP memo in `docs/archive/`

Milestones run in sequence except where this plan names a background or $0 parallel track (C2, A0.5, B0.5). A book's *certified* milestones may not begin before P0 software, U0 listed-panel tests, and H0 are green. A STOP memo is a completed milestone, not a failure. $0 screens (A0, B0) and $0 kill-ladders (A0.5, B0.5) are not certified exits.

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
| 7 | **No live capital before L0**, except P0's tiny calibration fills and C2's passive-core shadow year. Paper 60 sessions, then 10% size for 60 sessions. |
| 8 | No short stock, no naked short options, no leverage above 1.0× in v1. |
| 9 | No vendor data purchase unless a **later** milestone explicitly authorizes the SKU. P0 authorizes **$0** paid data. Public, broker, and free-tier data first. Discovery vendor spend is capped at **$700** before L0. Do not buy Book A tape and Book B panel in the same month. |
| 10 | No HMM, LightGBM, MLflow, or Kaggle client enters `pyproject.toml`. If a milestone appears to need one, the milestone design is wrong. |
| 11 | AI produces features from text and runs ops checks. AI does not forecast returns. |
| 12 | Own capital only. No third-party money, no advertised performance. |

---

## Milestone map

| ID | Name | Status | Hard stop if… |
|---|---|---|---|
| **P0** | Posture and cost lock | Software green; 200 broker fills outstanding; **$0 paid data** | Modelled costs cannot be pinned within 3 bps / 0.3% of premium against real broker fills |
| **U0** | Universe (listed PIT) | Fixture + listed-panel tests green; delisted *prices* deferred to B1 | Delisted *prices* unavailable at acceptable cost → Book B closes; A and C proceed |
| **H0** | Hurdle and inference design | **Complete** | Every candidate book's MDE exceeds 0.5 × its hypothesized effect → programme stops at H0 |
| **C1** | Book C — tax and location accounting proof | **Complete** (35.5 bps/yr, 0 washes, representative lots) | After-tax excess vs static VTI < 25 bps/yr → harvest module dropped, location/bands kept |
| **C2** | Book C — shadow year | Not started (audit, not a data purchase) | Realized after-tax excess < 15 bps or any wash-sale violation reaches a filing |
| **A0** | Book A — $0 VIX–RV / PUT screen | **Complete** (2.91 vol pts net, sign 5/5; 1256 wedge 98 bps at full sleeve) | Screen only. A miss would have skipped CBOE; a hit is not A1 |
| **A0.5** | Book A — $0 spread construction | **Complete** — 62.2% credit retained (n=37/54); A1 dump authorized. H3 still closes certification. | Spread round-trip eats the 25% credit-retention hypothesis, or H3 closes even the short window as a *certification* (it does) — this milestone may only *kill* |
| **A1** | Book A — VRP existence | **STOP** (1.39× < 2×; n=139; sign 5/5 net) | Mean implied-minus-realized in the 20–25 delta bucket ≤ modelled *spread* round-trip cost |
| **A2** | Book A — economics and ETF benchmark | **Not run** (A1 closed the book) | After-tax sleeve fails to beat PUTW-equivalent by 75 bps/yr, or sleeve Sharpe < 0.4, or sleeve max DD > 25% of sleeve notional, or 20% blend dilutes Book C |
| **A3** | Book A — tradability | **Not run** (A1 closed the book) | Paper fills worse than modelled by > 0.3% of premium, or fill rate at target limits < 80% |
| **B0** | Book B — $0 listed PEAD | **Complete** (80.9 bps mid-cap net, n=17,143; survivorship-biased) | Screen only. A miss would have skipped the panel; a hit is not B1 |
| **B0.5** | Book B — $0 bound and Item 2.02 | **Complete** (Item 2.02 mid 82.3 bps, n=13,907; w=12.9% after free stitch; bound 71.7 bps) | Item 2.02 listed mid-cap net drift < 40 bps → Book B closes, no vendor |
| **B1** | Book B — PEAD existence | Not started; **Norgate trial, then Platinum 6-mo if trial is complete** | Pooled net-of-cost drift < 40 bps/event on ≥ 6,000 clustered events, or effect lives only below $20M ADV |
| **B2** | Book B — economics and AI increment | Not started | IRA capacity insufficient to house the sleeve, or LLM text features add < 10 bps over numeric surprise → AI removed |
| **B3** | Book B — tradability | Not started | Realized mid-cap round-trip cost exceeds 25 bps, or closing-auction fills degrade the drift by > 15 bps |
| **L0** | Operating loop | Not started | No book has passed its H5 minimum → global STOP, 100% passive posture |
| **X0** | Kill review | Not started | Standing quarterly gate; any live book that misses its H5 minimum over four rolling quarters is retired |

**Critical path:** P0 (software + fills, $0 data) → U0 listed → (H0 and C1 already green) → C2 in the background ∥ A0.5 → A1 **STOP (Book A closed)** ∥ B0.5 → B1 → B2 → B3 → L0. Do not buy A-tape. B1 remains after the A1 month. L0 is built only after a book passes. X0 is standing once live.

---

## Research spend ladder (Rev 1.1)

Discovery purchases exist to *kill or certify*. They are not infrastructure. Working ceiling **$700** before L0 (one CBOE SPX dump + one Norgate Platinum 6-month). Expected spend through the first kill gate: **$0** if A0.5 or B0.5 stops a book, else **$25–35** for the A1 dump.

| Step | Book | Spend | What it answers | Authorizes next |
|---|---|---|---|---|
| Done | C1, H0, A0, A0.5, A1 STOP, B0, B0.5 | $0 | C1 35.5 bps; A0 VIX–RV 2.91 vol pts; A0.5 spread retains 62.2% of credit; A1 spliced IV−RV 4.91 vs cost 4.14 (1.19×); B0 listed PEAD 80.9 bps; B0.5 Item 2.02 82.3 bps, w=12.9% (bound 71.7) after Tiingo+successor stitch | Book A closed; B1 after this month |
| First dollar | A1 | **Not spent.** Cboe cart $580 tripped the $100 stop. OptionsDX 2012–2023 + ThetaData FREE 2024–present at $0. A1 closed the book (1.19×). | 20–25Δ, 30–45 DTE implied-minus-realized net of *spread* cost | A2 not authorized |
| Later dollar | B1 | Norgate US Platinum **3-week trial**, then **$346.50 / 6 months** dump-and-cancel if the trial panel is complete | Delisted PIT + historical constituents, 2010–2026 | B2 only if B1 passes |
| Closed at discovery | — | Full-market OPRA ($300–420/mo), CGI license (≥$1k/mo), Polygon Developer ($79/mo, 10y — too short for B1), Polygon Advanced ($199/mo, delisted spotty), Sharadar before B1, Databento, CRSP, 2005–2011 Optsum | — | Do not buy |

A0 cannot certify A1: VIX minus subsequent RV is not a 20–25 delta put-spread. ThetaData FREE cannot certify A1 either: ~38 cycles, MDE 68.1 bps, ratio 0.59, **H3 closes certification**. B0 cannot certify B1: Lock 5, listed-only, current S&P 400 membership. Say “cannot certify” rather than dressing Yahoo VIX or a listed panel as the milestone.

---

## P0 — Posture and cost lock

### Why

Nothing downstream is interpretable until the desk knows what a trade costs and what a gain is taxed at. Rungs 1 and 2 of the ladder become code here.

### Build

1. `costs`: bid-ask and effective half-spread by product bucket, Section 31 (**working** ~$27.80/$1M of sell proceeds), FINRA TAF ($0.000166/share, $8.30 cap), OCC $0.02/contract, exchange ORF, broker per-contract, borrow rate stub (set to "prohibited" in v1), futures round-turn. Unit-tested per bucket against the table in Blueprint §0.2.
2. `tax`: ST 40% / LT 20% / 1256 blend 28% (**working**, configurable), qualified-dividend test, wash-sale window arithmetic across joint accounts, IRA-destruction case, FIFO/specific-lot accounting, December 1256 mark. Unit-tested against hand-worked examples.
3. **After-tax VTI benchmark series**, 2005–2026: total return, dividends taxed at 20% on the qualified-dividend schedule, 3 bps ER. This series is the denominator of every later claim.
4. PDT state machine and Reg T / portfolio-margin thresholds as constants.
5. Broker account opened; API keys; 200 real fills logged in tiny size across SPY, one large cap, one mid cap, and one SPX spread, purely to calibrate `costs`. These fills are operational, not a vendor SKU.
6. **Data decision, $0 paid:** Yahoo / Vanguard (after-tax VTI, VIX, SPX, listed bars), SEC EDGAR, FRED, IBKR delayed/historical included with the account, ThetaData **FREE** tier for A0.5. **No Polygon. No CBOE. No Norgate. No Sharadar.** Those SKUs are authorized only at A1 or B1 as named below, and only after the $0 kill-ladder for that book is green. See [p0-data-decision.md](p0-data-decision.md).

### Exit

All cost and tax unit tests pass; modelled cost matches the 200 calibration fills within 3 bps (equities) and 0.3% of premium (options); after-tax VTI series reproduces published VTI total return within 5 bps/yr before tax.

### Stop

Costs cannot be pinned within tolerance → the desk cannot evaluate any book and the programme stops here.

---

## U0 — Universe and point-in-time panel (listed)

### Why

Survivorship bias is the single most common cause of a fake equity backtest. This milestone makes the *listed* panel honest and the leakage tests real. Delisted *prices* are the B1 purchase, not a P0/U0 purchase: Book B cannot be certified without them (Lock 5), but Books A and C do not need them, and buying the panel before B0.5 is spending before the next certified test exists.

### Build

PIT *identifier* panel for US common stock and ETFs, 2005–2026: listed tickers from EDGAR company tickers plus Wikipedia/current-index snapshots; delisted and renamed *names* from EDGAR Form 25/15 with effective dates even when prices are missing. Split and dividend adjustment from one canonical *listed* source, unit-tested against six known corporate actions. Daily $ADV and a liquidity bucket per name-date on names Yahoo still serves. EDGAR filing index keyed by accession number and **filing timestamp**. Panels typed, `df in → df out`. **No vendor dump.**

### Exit

Listed panel round-trips a known index membership snapshot; leakage test: no future information reachable from any row's knowledge date. Delisted *identifiers* are present even if their price series are empty.

### Stop

Delisted *prices* later unobtainable at acceptable cost (B1 SKU above the $700 discovery ceiling, or trial panel unusable) → Book B closes; Books A and C proceed (neither needs single-name history).

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

Confirm the accounting result survives contact with a real broker and a real tax year. This is calendar time, not a data vendor. C2 runs in the background while A0.5 / B0.5 execute at $0.

### C2 Build

Run C1 live on the passive core only (no active sleeve), with the instruction list and reconciliation from L0's ops module in minimal form. One full tax year. Reconcile the lot ledger to the broker's 1099-B.

### C2 Exit

Realized after-tax excess ≥ 15 bps; lot ledger agrees with broker 1099-B on every lot; zero wash-sale violations.

### C2 Stop

Any wash-sale violation that reaches a filing → harvest module disabled permanently. The tax risk dominates the 30 bps.

---

## A0 / A0.5 / A1 / A2 / A3 — Book A, index VRP

### A0 Why (complete, $0)

Establish that a *coarse* volatility risk premium is still visible in public data, net of expensive-end SPX ATM cost, before any option-tape dollar. VIX minus subsequent 21-day SPX RV is **not** the 20–25 delta put-spread. A green A0 is permission to attempt A0.5, not to buy CBOE.

### A0 result (2026-08-21)

n=259 non-overlapping windows. Mean raw VIX–RV 3.29 vol pts; net of mid cost 3.00; net of expensive-end cost **2.91**; sign stable in **5/5** sub-periods. Stress raw: 2018 +0.25, 2020 **−0.23**, 2024 +2.78. Packaged path used `^PUT` (PUTW Yahoo history unusable): 2016-02-24 – 2026-08-20 after-tax PUT 5.08% vs after-tax VTI 15.19%; DIY 1256 marked 6.07%; **1256 vs ordinary wedge 98 bps/yr at full sleeve ≈ 20 bps at 20% weight**, below Book C’s measured 35.5 bps. The tax advantage alone no longer carries Book A. Detail: [a0-public-vrp-screen.md](../a0-public-vrp-screen.md).

### A0.5 Why

`costs` has no bucket for the *vertical put spread* A1 actually trades (short 20–25Δ, long 50–100 points lower). Every Book A cost figure to date is ATM-single-leg and therefore biased low. ThetaData FREE (EOD US index options from 2023-06-01, ~38 cycles) **cannot certify A1**: MDE = 2.8 × 150 / √38 = **68.1 bps**, ratio 0.59 vs 116 bps hypothesized, **H3 closes certification**. It can still *kill* the book if the spread’s own round-trip already consumes the 25% credit-retention hypothesis.

### A0.5 result (2026-08-21)

MDE printed first: n=38, MDE=68.1 bps, ratio=0.59. **H3 closes A1 certification** on the FREE window, as pre-registered. Cost peek ran on the official `thetadata` Python client (no Java terminal): 37 of 54 monthlies reconstructed, mean credit 6.86, mean all-in 37.8% of credit, **62.2% retained** vs 25% hurdle. Not sparse. **A1 CBOE dump authorized.** This is not A1. Detail: [a05-spread-cost-screen.md](../a05-spread-cost-screen.md).

### A0.5 Build

Free ThetaData account and official Python client (`thetadata`, API key in `.env`). SPX EOD chains 2023-06-01 → present. Reconstruct 30–45 DTE, short-leg ~20–25 delta, 50–100 point width put *spreads*. Publish: mean credit, mean bid–ask as % of credit on both legs, all-in round-trip vs the ATM `costs` bucket, and whether 25% of credit remains after that round-trip. MDE printed first; the peek is a kill screen, not A1.

### A0.5 Exit

Spread round-trip published. If mean all-in cost of the traded spread leaves ≥ 25% of mean credit after cost, A1’s CBOE dump is authorized. If not, Book A closes at $0.

### A0.5 Stop

Spread round-trip eats the 25% retention hypothesis, or chains are too sparse/wide to build the pre-registered structure → Book A closes. Do not buy CBOE.

### A1 result (2026-08-22)

MDE printed first: n=173, MDE=31.9 bps, ratio=0.28. Tape: OptionsDX SPX EOD through 2023 spliced to ThetaData FREE from expiry 2024-01-01 (completes the pre-registered 2012–present window, including the named 2024 stress year; not 2005–2011). 169 of 174 monthlies in the 20–25Δ / 30–45 DTE bucket. Mean IV−RV **4.91** vol pts; mean spread round-trip **4.14** vol pts; **1.19×** vs hurdle 2×. Net of cost positive in **4/5** sub-periods (last window 2021-09–2026-12 goes to −0.55 after the tail). Stress raw: 2018 +1.54, 2020 +2.06, **2024 +1.44**. OptionsDX-only (already published, dump ended 2023) was 1.39×. **Book A STOP.** A2/A3 not run. Do not search other delta buckets; do not extend to 2005–2011. Detail: [a1-vrp-existence.md](../a1-vrp-existence.md). STOP memo: [book-a-stop.md](../archive/book-a-stop.md).

### A1 Why

Establish that the premium exists in the specific delta bucket and tenor the desk can actually trade, and that it is larger than the cost of trading the *spread* (the A0.5 number, not the ATM bucket).

### A1 Build

**SKU (only if A0.5 green):** CBOE DataShop Option EOD Summary, underlying **SPX only**, historical **2012-01-01 → present**, **calcs excluded**, CGI **unlicensed**. Dump-and-cancel. Working ceiling **$25–35**; if the cart exceeds **$100**, stop and re-quote. Reconstruct IV and delta from bid/ask + SPX close (Yahoo `^GSPC`). Do **not** buy full-market OPRA, a CGI license, or 2005–2011 Optsum: 2012–present is ~175 monthly cycles, MDE 2.8 × 150 / √175 = **31.7 bps**, ratio 0.27, inside H3, and contains 2018 / 2020 / 2024. Implied volatility minus subsequent realized volatility by delta bucket (10/15/20/25/30) and tenor (7/14/30/45 DTE). Sub-period breakdown including those stress windows. All figures net of the A0.5 spread round-trip, falling back to the ATM bucket only if A0.5 could not measure a leg. Explicitly include a 0DTE and 7DTE row to document the Blueprint’s closure of 0DTE with this desk’s own numbers. This dump **is** the A2 tape; do not purchase twice.

### A1 Exit

Mean implied-minus-realized in the 20–25 delta, 30–45 DTE bucket exceeds modelled *spread* round-trip cost by ≥ 2×, and the sign is stable in at least 4 of 5 non-overlapping sub-periods of the 2012–present window.

### A1 Stop

Premium ≤ cost, or sign unstable → Book A closes. Do not search other delta buckets beyond the pre-registered five; that is spec mining. Do not extend the sample to 2005–2011 to rescue a fail.

### A2 Why

A premium is not a book. Test the sleeve after cost, after tax, against the packaged ETF alternative — which is the real competitor. **A2 arithmetic fix, pre-registered 2026-08-21, before any CBOE dollar:** total-book excess is the identity `w × (sleeve − VTI) + (1−w) × C`. At w = 20% with C = 0, “total-book ≥ 200 bps” demands the sleeve beat after-tax VTI by **1,000 bps**. No defined-risk short put spread does that; A0’s PUT vs VTI (5.08% vs 15.19%) already shows the cash-secured cousin does not. That clause was a drafting error that conflated H1 (L0 programme gate) with a single-sleeve identity. It is removed here, dated, and not a goalpost move after seeing tape — the tape has not been bought. H1 and H5 are unchanged.

### A2 Build

Walk-forward simulation of the pre-registered rule (short 20–25 delta put spread, 30–45 DTE, 50–100 point width, close at 50% credit or 7–14 DTE), sized to the 8%-of-equity max-loss limit, with the 28% Section 1256 blend applied and the December mark modelled. Benchmark: PUTW-equivalent held in the taxable account with ordinary-income distributions. Second benchmark: after-tax VTI, reported honestly (A0 says the sleeve will lose this comparison in a bull window; that is not an A2 kill). Blend the sleeve with the Book C core at 15%, 20%, and 25% weights. **Same CBOE files as A1.**

### A2 Exit

Sleeve after-tax return beats the ETF equivalent by ≥ 75 bps/yr, sleeve Sharpe ≥ 0.4, sleeve max drawdown ≤ 25% of sleeve notional, and at 20% weight the blended book’s after-tax excess vs VTI is at least Book C’s measured **35.5 bps/yr** (the sleeve must not dilute the accounting engine). H1 (≥ 200 bps total-book) remains an L0 programme gate across all passing books.

### A2 Stop

Any of those four A2 exits fails → Book A closes. Do not re-optimize width or exit rule outside the trial budget.

### A3 Why

Options backtests lie about fills. Find out by how much before risking money.

### A3 Build

60 sessions of paper trading the exact rule with the exact limit-price policy (mid + 25% of spread cap, no chasing). Log intended vs achieved price per leg. Feed realized slippage back into `costs` and re-run A2 with the calibrated number.

### A3 Exit

Realized slippage within 0.3% of premium of model; fill rate at target limits ≥ 80%; A2 still passes on recalibrated costs.

### A3 Stop

Fills degrade the edge below the A2 exit → Book A closes.

---

## B0 / B0.5 / B1 / B2 / B3 — Book B, PEAD

### B0 Why (complete, $0)

Test whether listed-only mid-cap PEAD is already dead, which would skip every later dollar. Survivorship can only *help* a long-only drift. A miss kills the panel purchase. A hit is not B1.

### B0 result (2026-08-21)

MDE printed first: n=17,143, n_eff=3,428.6, MDE=38.3 bps, ratio 0.38. Current S&P 400 listed names, 2010–2026, long-only, all 8-Ks (not Item 2.02 only). Mid-cap ($20–100M ADV) mean net-of-cost 20-day drift **80.9 bps** (kill 40), working cost 25 bps. Gate was “buy Polygon PIT panel”; Rev 1.1 replaces that SKU. Detail: [b0-public-pead-screen.md](../b0-public-pead-screen.md).

### B0.5 Why

B0 filtered on *current index membership*, not mere survival, so the missing mass is larger than ordinary delisting. Zero-drift bound: combined = (1−w) × 80.9. Setting combined = 40 bps gives **w = 50.6%**. Above that, a delisted cohort with literally zero drift kills B1 unaided and B0 carries no decision weight. `w` is measurable from free EDGAR Form 25/15. B0 also used all 8-Ks; Item 2.02 is the earnings-relevant subset. Widen from ~400 index names to ~1,500 liquid listed names. None of this is a vendor.

### B0.5 result (2026-08-21)

MDE printed first: n=13,907, n_eff=2,781.4, MDE=42.5 bps, ratio=0.42. Listed names with $ADV > $20M (S&P 1500 candidates, 1,349 after the ADV cut), Item 2.02 only, long-only, mid-cap 20-day net **82.3 bps** (kill 40). Current S&P 400 N_listed=399. Free stitch (Tiingo usable EOD + Yahoo/Tiingo successors) cut unrecovered leavers from 316 to **N_missing=59**; **w=12.9%** (< 50.6%). Membership missing mass (promoted/demoted/delisted) 62.1%. Zero-drift bound (1−w)×82.3 = **71.7 bps**. Dirty identity (AHL, SIVB, CHK) stays in N_missing. Form 25/15 unique CIKs 11,912. Gate: B0 still informs B1. Still not Lock 5. Detail: [b05-item-202-bound.md](../b05-item-202-bound.md), [b075-tiingo-coverage.md](../b075-tiingo-coverage.md).

### B0.5 Build

1. Filter the existing EDGAR cache to Item 2.02. Re-run the listed mid-cap 20-day net-of-cost mean. MDE printed first.
2. Universe: listed US names with $ADV > $20M that Yahoo still serves, top ~1,500 by ADV, not only current S&P 400.
3. EDGAR Form 25/15: count names that left the mid-cap / S&P 400 band over 2010–2026. Publish `w` = N_missing / (N_listed + N_missing).
4. Publish the bound: if delisted mean = 0, combined = (1−w) × listed Item 2.02 mean; compare to 40 bps.

### B0.5 Exit

Item 2.02 listed mid-cap net ≥ 40 bps; `w` published. If `w` < 50.6% and the bound stays ≥ 40, B0 still *informs* B1 but does not certify it. If `w` ≥ 50.6%, B0’s “buy panel” gate is revoked; B1’s trial remains the only honest test (Lock 5).

### B0.5 Stop

Item 2.02 listed mid-cap net < 40 bps → Book B closes. No Norgate, no Polygon, no Sharadar.

### B1 Why

The only book with an inference budget that supports genuine discovery. Also the most likely to be already arbitraged. Test the existence claim on numeric data alone, before spending a dollar on AI or fundamentals vendors. **Cannot certify at $0:** Lock 5, listed-only Yahoo does not keep delisted quotes.

### B1 Build

**SKU (only if B0.5 green):** Norgate US Stocks **Platinum**, 3-week free trial first. If the trial panel is complete (delisted EOD + historical index constituents, Python-usable, 2010–2026), subscribe **6 months at $346.50**, dump, cancel. Do **not** default to Polygon: Developer is 10 years against B1’s 16-year window; Advanced is $199/mo and delisted coverage is spotty. Polygon or EODHD only if the Norgate trial cannot deliver. Event panel from EDGAR filing timestamps (8-K Item 2.02) joined to that PIT price panel, 2010–2026, $ADV > $20M. Surprise proxy from the announcement-window return only (no vendor consensus). Pooled forward returns at 5/10/20/40 days, net of modelled cost, with date and sector clustering, purged walk-forward, and controls for momentum and size. MDE printed first.

### B1 Exit

Net-of-cost drift ≥ 40 bps per event, present in the $20–100M ADV band (not only in the illiquid tail), stable in sign across walk-forward folds.

### B1 Stop

Below 40 bps, or effect concentrated below $20M ADV → Book B closes. No vendor fundamentals are purchased.

### B2 Why

Establish that the sleeve is housable (IRA capacity) and that text-derived features earn their complexity.

### B2 Build

Only now, if B1 passed: authorize a PIT fundamentals/consensus subscription. Build `ai.extract` for guidance-change and call-language features with strict pre-timestamp inputs, cached and versioned. Report the sleeve three ways: numeric surprise only, numeric + text, and text only. Model the IRA-versus-taxable placement explicitly.

### B2 Exit

Sleeve is fully housable in the IRA at ≥ 20% of total equity; text features add ≥ 10 bps per event over numeric surprise on held-out folds; sleeve after-tax excess vs after-tax VTI ≥ **800 bps/yr** at the 25% target weight (arithmetically 200 bps at book level; this is a restatement of the same identity, dated 2026-08-21, not a reduction). H1 itself remains an L0 programme gate.

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

P0 is still the interpretability gate — cost model, tax model, after-tax VTI — but it is **not** a procurement gate. P0 buys $0 of paid data; its remaining work is 200 tiny broker fills. U0 listed runs next at $0 (leakage, corp-action fixtures, EDGAR index). H0 and C1 are already green. C2 is calendar time and runs in the background: a funded IBKR year plus 1099-B, not a vendor.

The remaining research path is a kill-ladder, cheapest first. A0.5 (ThetaData FREE) did not kill Book A: spread round-trip leaves **62.2%** of credit. A1 on OptionsDX 2012–2023 plus ThetaData FREE 2024–present ($0) after the Cboe cart tripped $100: mean IV−RV **4.91** vol pts vs spread cost **4.14** (1.19× < 2×). **Book A is closed.** A2/A3 are not run. B0.5 published Item 2.02 mid-cap net **82.3 bps** and **w=12.9%** after the free stitch (bound 71.7 bps); Book B is not closed. B1 is a Norgate Platinum *trial* after this month, then a 6-month dump-and-cancel at $346.50 — not Polygon Advanced at $199/mo. Sharadar stays closed until B1 passes.

Book A is no longer sequenced on the 1256 tax wedge alone: A0 measured that wedge at 98 bps at full sleeve ≈ 20 bps at 20% weight, below C1’s 35.5 bps. A1 then showed the defined-risk 20–25Δ spread’s implied-minus-realized does not cover twice the spread round-trip. Book B remains because it is the expensive branch and the most likely to be already in the price.

L0 is built only after a book passes, never before. The single largest scheduling risk is the temptation to build L0 early because it feels like progress; the plan forbids it. The single largest *spend* risk is buying Polygon or full-market OPRA because a milestone name used to say so; Rev 1.1 forbids that too.
