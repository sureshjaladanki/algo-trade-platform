# Retail India desk — Execution Plan

| | |
|---|---|
| **Date** | 2026-09-05 |
| **Status** | BLUEPRINT Rev 1.0 / ACTIVE |
| **Review** | Claude Opus, 2026-09-05 |
| **Charter** | [india-equity-architecture-blueprint.md](india-equity-architecture-blueprint.md) |
| **Branch** | `in-equity` |

---

## How to read this plan

This is a **milestone map, not a peek charter.** Every milestone has four parts:

- **Why** — the question it answers. If you cannot state the question, do not start the milestone.
- **Build** — what code and documents exist when it is done.
- **Exit** — a numeric condition. Not "looks reasonable". A number.
- **Stop** — the condition under which the milestone fails, plus the STOP memo it writes to
  `docs/archive/`.

Rules that apply to every milestone:

1. **No milestone starts before its predecessors exit.** The dependency graph is in
   [Milestone map](#milestone-map).
2. **No book is looked at before H0 publishes its pre-registration.** Publishing n, σ, MDE and the
   pre-registered effect *after* seeing the data is not inference, it is decoration.
3. **A closed book is a completed milestone.** Write the STOP memo, delete the module, move on. Do
   not leave a failed book "paused" so a later agent can be tempted by it.
4. **Every number that cannot be sourced to an Indian statute, exchange circular or regulator
   document goes into the blueprint's working-numbers register** with the milestone that verifies it.
5. Poetry only. `poetry add` for runtime deps, `poetry add --group dev` for tooling, `poetry run`
   for everything. Both `pyproject.toml` and `poetry.lock` committed together. See
   [../repo-conventions.md](../repo-conventions.md).

---

## Non-negotiables (locks)

These are not preferences. A pull request that violates one of these is wrong regardless of what it
achieves.

**L1 — `costs` is the single source of Indian friction.**
STT (delivery 0.10% buy + 0.10% sell; intraday 0.025% sell; futures 0.05% sell; options 0.15% of
premium sell; exercise 0.15% of intrinsic, buyer; equity-oriented fund units 0.001% sell only),
stamp duty by product, exchange transaction charges by venue, SEBI turnover fee (₹10/crore), IPFT,
GST 18% on (brokerage + exchange + SEBI), brokerage with the **₹20-per-order floor**, and DP charge
**₹15.34 per ISIN per day of sale**. No book computes its own cost. No test hard-codes a bps number.

**L2 — `tax` is the single source of Indian tax.**
s.196 (STCG 20% → 20.8% with cess), s.198 (LTCG 12.5% above ₹1.25 lakh → 13.0%), s.66 (intraday
equity speculative, F&O non-speculative), slab + surcharge + 4% cess, 4-year versus 8-year carry
clocks kept separate, absolute-sum turnover for s.44AB, Tax Year boundaries under the Income-tax
Act 2025. STT is deductible against business income and **not** against capital gains — `costs` must
be told which book a trade belongs to before it can price it.

**L3 — Peak margin: no position is ever sized on notional.**
Every size comes from the broker's margin endpoint or margin calculator, plus a **25% buffer**. Never
a hard-coded leverage multiple. Peak margin has been 100% upfront since 1 September 2021 with four
random intraday snapshots and a penalty that applies even to positions closed before the close.

**L4 — SEBI algo rules are enforced in code, not in intent.**
Hard cap **8 orders/second** against the 10 OPS TOPS. Every order carries the exchange-issued algo
ID or it is not sent. Static-IP-whitelisted OAuth with 2FA, daily token renewal as an explicit
workflow step. The desk never offers a strategy to anyone outside self, spouse, dependent children
and dependent parents, and never becomes an algo provider, a Research Analyst or a PMS.

**L5 — Point-in-time for Indian listings, including the Indian-specific traps.**
Every panel row must be reconstructible as of its own date, honouring NSE and BSE **symbol changes,
ISIN changes, bonus issues, stock splits, rights issues, demergers, amalgamations and delistings**,
plus the **ESM/GSM stage** and **F&O ban-list state** on that date. Demergers are the trap: they
create a new ISIN and a price adjustment that naively adjusted close series get wrong. A name in ESM
Stage II on date *t* traded only in a ±2% periodic call auction — the panel must say so.

**L6 — The CAS regime break is a first-class column.**
`panel` carries `close_method ∈ {vwap_30min, cas_auction}`. The Closing Auction Session went live
**3 August 2026** for F&O-eligible stocks; the pre-open realignment lands **7 September 2026**. No
book may pool pre- and post-3-August-2026 closes for an F&O-eligible name without an explicit
declaration in its pre-registration.

**L7 — No live capital before L0 exits.** Not one rupee, not a "small test position".

**L8 — ₹0 paid data at P0, and no paid SKU before its book's ₹0 screen passes and its MDE is
published.** See the [spend ladder](#research-spend-ladder-inr).

**L9 — `pyproject.toml` contains no HMM, LightGBM, MLflow, Kaggle client or Polars at seed.**
Polars is added only when a `panel` milestone actually imports it.

**L10 — AI has two jobs and no others.** `ai.extract` may turn Indian results PDFs into typed
numbers; `ops` may have an LLM write a prose note about a run log. **No model output may enter a
return forecast, a signal, a weight or a position size.**

**L11 — Own capital only.** No client money, no pooled vehicle, no fee. Each of those changes the
regulatory perimeter.

**L12 — Every instruction list is manually executable.** A book that cannot be placed by hand from a
printed file is not permitted.

---

## Milestone map

```
P0 ──> U0 ──> H0 ──┬──> L1 ──> L2 ─────────┐
   cost/tax  PIT    │   ledger arithmetic   │
   posture  universe│                       ├──> L0 ──> X0
                    ├──> P1 ──> (M1) ───────┤   live    kill
                    │   packaged vs self    │   loop    review
                    ├──> S0 [gated: SEBI]   │
                    ├──> A0 [dated: 2027-08-31]
                    └──> R0 [closed at H0]
```

| ID | Milestone | Depends on | Status |
|---|---|---|---|
| **P0** | Cost, tax and posture lock | — | **DONE — 2026-09-05** |
| **U0** | India universe and point-in-time panel | P0 | **DONE (narrowed) — 2026-09-05.** **5,103** CM sessions in `data/cache/`. Membership is Nifty 50 + Next 50 (`docs/archive/u0-stop.md`). |
| **H0** | Hurdles, MDE and pre-registration | P0, U0 | **DONE — 2026-09-05.** Hurdles in `docs/next/h0-hurdles.md`. Six pre-registrations. STOP memos for R, option premium, event days, reconstitution. No book returns were read. |
| **L1** | Book L — the ledger arithmetic | H0 | **DONE — 2026-09-05.** ₹41,990 tax delta and ₹5,970 routing saving reproduced. Combined 95.92 bps at ₹50 lakh (kill is 50 bps). Core recommendation: direct Nifty 50 index fund at 4 turns/yr. |
| **L2** | Book L — realisation scheduler in `portfolio` | L1 | **DONE — 2026-09-05.** §6.1 limits fail at a ₹1 breach. Scheduler defers STCG across the 12-month line and harvests s.198 exemption in March. |
| **P1** | Book P — packaged versus self-run, ₹0 screen | H0, U0 | **STOPPED — 2026-09-05.** No PIT factor-index constituents; cannot reconcile self-run to published TRI within 50 bps/yr. Default packaged. `docs/archive/p1-stop.md`. |
| **M1** | Book M — self-run momentum | P1 **and** an H4 waiver that does not currently exist | **Closed.** `docs/archive/book-m-stop.md` |
| **R0** | Book R — results drift | — | **Closed at H0.** Write the STOP memo, do not build. |
| **A0** | Book A — CAS auction | Calendar | **Deferred to 2027-08-31.** Do not open early. |
| **S0** | Book B — SLBM lending yield | SEBI reformed-SLBM circular | Gated on a regulator publication |
| **L0** | Operating loop in IST | L2, P1 | **IN PROGRESS — 2026-09-05.** `execute` / `ops` / [l0-runbook.md](l0-runbook.md). Refusals and twenty in-process paper sessions tested. Calendar paper + live H1 still open. No live capital. |
| **X0** | Kill review | L0 + two quarters live | Pending |

**Critical path:** `P0 → U0 → H0 → L1 → L2 → P1 → L0` — cost and tax fidelity, then a
point-in-time Indian universe, then published hurdles, then the arithmetic book that carries the
desk's only measurable edge, then the one honest comparison against packaged Indian factor funds,
then a live once-a-day loop in IST. Everything predictive is closed at H0 and stays closed.

---

## Research spend ladder (INR)

| Tier | Ceiling | Unlocked by | What it buys |
|---|---|---|---|
| **0** | **₹0** | — | P0, U0, H0 and every book's public screen. NSE and BSE UDiFF bhavcopy, corporate filings, NSE monthly impact-cost file, SLB bhavcopy, index TRI history, AMFI TERs, SEBI circulars, RBI DBIE. **Everything through H0 is free.** |
| **1** | **₹6,000/yr** (~US$68) | **L0 exit only** | One broker API for execution and reconciliation: Kite Connect ₹500/month, or Dhan data ₹499/month, or Fyers / Angel / Upstox at ₹0 if the free tier meets L0. |
| **2** | **₹8,400 one-off** | A named exit criterion in a *specific* book's pre-registration that cannot be met from bhavcopy | Three months of minute bars: TrueData ₹1,440–2,796/month, or Global Datafeeds NimbleDataPro from ~₹225/exchange/month. **Three months, then decide.** No rolling subscription. |
| **3** | **₹35,000/yr** (~US$400) hard ceiling | Never exceeded before a book is live and after-tax profitable for two consecutive quarters | Everything above, plus a CA engagement for the s.44AB / s.44AA position. |
| **∞** | — | — | NSE Data & Analytics, CMOTS / Accord, LSEG India are institutional, quote-only and **outside the envelope. Do not contact them.** |

Total committed spend from today to a live loop: **₹0 until L0, then ₹6,000/yr.** All vendor prices
are **(working)** and re-checked on the day of purchase.

---

## P0 — Cost, tax and posture lock

### Why

Nothing else can be trusted until Indian friction and Indian tax are exact. Every closure in the
blueprint — index option premium selling, MTF, intraday, single-stock derivatives — is an
*arithmetic* closure. If `costs` is wrong by 2 bps, a closed book might not be closed and an open one
might not be open. P0 is also where the posture is written down so a later agent cannot quietly
re-scope the desk.

This milestone is implementable tomorrow with zero spend and zero data downloads.

### Build

1. **`src/costs.py`** — pure functions, `dataclass` inputs, no I/O, no globals.
   - `stt(product, side, value, premium=None, intrinsic=None) -> Decimal` covering: delivery
     (0.10% both legs), equity-oriented fund units (0.001% sell only, nil on purchase), intraday
     (0.025% sell), futures (0.05% sell), options (0.15% of premium, sell), exercised options
     (0.15% of intrinsic, purchaser).
   - `stamp_duty(product, buy_value)` — 0.015% delivery, 0.003% intraday, 0.002% futures, 0.003%
     options, buyer only.
   - `exchange_charge(venue, product, value)` — NSE cash 0.00297%, BSE cash 0.00375%, NSE futures
     0.00173%, BSE futures 0, NSE options 0.03553% of premium, BSE options 0.0325% of premium.
   - `sebi_turnover_fee(value)` = 0.0001%; `ipft(product, value)` = 0.0001% cash / 0.0005% F&O.
   - `brokerage(product, value, n_orders)` — ₹0 delivery; `min(0.03% × value, ₹20)` per executed
     order for intraday and futures; flat ₹20 per order for options. **The floor must be modelled per
     order, not averaged.**
   - `gst(brokerage, exchange_charge, sebi_fee)` = 18% of the sum. Not on STT, not on stamp duty.
   - `dp_charge(n_isins_sold)` = ₹15.34 per ISIN per day of sale; zero on buys, intraday and F&O.
   - `round_trip_bps(...)` — the composite, returning both bps and rupees.
   - `exercise_or_square_off(intrinsic, lot, n_lots)` — returns whichever is cheaper, comparing
     0.15%-of-intrinsic exercise STT against the round-trip cost of closing. This is a real Indian
     decision and it belongs in code, not in a trader's head.
2. **`src/tax.py`** — same discipline.
   - `stcg(gain)` = 20% × 1.04; `ltcg(gain, exemption_used)` = 12.5% × 1.04 on the excess over
     ₹1,25,000 aggregate per tax year; surcharge on capital gains capped at 15%.
   - `business_income(pnl, kind)` where `kind ∈ {speculative, non_speculative}`, at slab + surcharge
     + 4% cess, with **separate** carry-forward ledgers (4 years speculative, 8 years
     non-speculative) and speculative losses offsettable only against speculative income.
   - `audit_turnover(trades)` — the absolute sum of profits and losses, plus premium on options sold
     **(working, W10)** — and a flag when it crosses ₹1 crore and ₹10 crore.
   - `tax_year(date)` — 1 April to 31 March, per the Income-tax Act 2025.
3. **`docs/next/p0-posture.md`** — a short memo fixing, in writing:
   - Capital envelope **₹25 lakh – ₹1 crore**, design point **₹50 lakh**.
   - Broker choice and why; API tier and price.
   - **No leverage. No MTF. No single-stock derivatives. No naked short options.** (Blueprint §6.1.)
   - Order-rate cap 8/second; algo-ID assertion; static-IP OAuth + 2FA.
   - Every risk limit from blueprint §6.1, restated as the numbers the code will assert.
4. **`docs/next/p0-cost-verification.md`** — the contract-note reconciliation, showing the broker's
   line items beside `costs`' output for each of the six instrument types, with the residual in
   rupees.
5. Update the blueprint's working-numbers register for every W-item this milestone resolves
   (W1, W2, W3, W4, W5, W7, W8, W9, W10, W11, W12, W14).

### Exit

- `costs` reproduces **a real broker contract note to within ₹1 per trade** for: cash equity
  delivery, ETF delivery, cash equity intraday, index futures, index options, and an exercised index
  option. If no live account exists yet, use the broker's published brokerage calculator as the
  reference and record that substitution explicitly.
- `tax` reproduces **a hand-worked Tax Year 2026-27 computation to within ₹1** for a mixed book
  containing: a delivery position held 14 months, one held 5 months, an intraday loss, and an F&O
  loss — with the two carry-forward ledgers correct and separate.
- `p0-posture.md` exists, states the capital envelope and every limit as a number, and is referenced
  by the blueprint.
- Every W-item above is either resolved with a cited source or carries a named later milestone.
- `poetry run pytest` green; `poetry run ruff check src tests` clean; no new runtime dependency added
  (P0 needs only the standard library and `decimal`).

### Stop

If any statutory rate cannot be sourced to an NSE, BSE, SEBI or Finance Act document, it goes in
tagged **(working)** with a URL and a review date — or **P0 fails**. Do not guess a rate. Do not
average two blog posts. A cost model built on a guess makes every downstream closure unsafe, and the
whole design rests on arithmetic closures.

STOP memo: `docs/archive/p0-stop.md`.

---

## U0 — India universe and point-in-time panel

### Why

Every book needs to know what was tradable, at what price, under what surveillance state, on a given
Indian date. India's traps are specific: legacy bhavcopy was discontinued in July 2024 in favour of
UDiFF; ESM and GSM can put a name into a ±2% call auction for a month; the F&O ban list changes
overnight; demergers create new ISINs; and the closing-price mechanism itself changed on 3 August
2026. A panel that ignores any of these is not point-in-time.

### Build

1. **`src/panel.py`**
   - Fetcher for **NSE CM-UDiFF Common Bhavcopy Final (zip)** and **FO UDiFF bhavcopy**, plus BSE
     bhavcopy, ~2005 → present. Access discipline is part of the deliverable: session-cookie warm-up,
     browser user-agent, **≤ 1 request per 2 seconds**, exponential backoff, a **content-addressed
     local cache under `data/` so any given day is fetched exactly once, ever**, and a hard refusal
     to fetch between 09:00 and 16:15 IST.
   - Corporate-action spine from NSE and BSE filings: bonus, split, rights, demerger, amalgamation,
     delisting, symbol change, ISIN change. Adjusted and unadjusted series both retained; the
     adjustment factor is stored, not just applied.
   - `close_method` column per row per name (**L6**): `vwap_30min` before 2026-08-03 and for non-CAS
     names, `cas_auction` for F&O-eligible names from 2026-08-03.
   - Security-wise delivery position → the 20-day median **delivery** value series that H5 uses.
   - NSE monthly impact-cost file, joined by date and symbol (resolves **W6**).
2. **`src/universe.py`**
   - Nifty 50 / Next 50 / 100 / 200 / Midcap 150 / Smallcap 250 membership **as of a date**, from
     NSE index reconstitution press releases and factsheets.
   - Flags per name per date: `fno_eligible`, `cas_eligible`, `esm_stage`, `gsm_stage`,
     `price_band_pct`, `in_fno_ban`.
3. **`docs/next/u0-panel-verification.md`** — the four evidence tests below, with the actual names
   and dates used.

### Exit

- **≥ 5,000 sessions** of Nifty 500-breadth daily data available offline, from cache, with no
  network call needed to rebuild a panel.
- **Survivorship test passes**: a specific name delisted in, say, 2013 is present in the 2012 panel,
  absent after its delisting date, and its absence does not silently change a 2012 cross-sectional
  rank.
- **Demerger test passes**: one named Indian demerger between 2022 and 2026 is reconstructed
  correctly — parent price adjustment, new ISIN, and the combined holding value continuous across the
  record date to within 1%.
- **Look-ahead test passes**: a date-shift test proves zero forward-looking columns. Shift every
  input by one session and every derived column must change; any column that does not change is
  either constant or is reading the future.
- **Surveillance test passes**: at least one name that was in ESM Stage II is flagged as such on the
  correct dates, and `universe` refuses to include it in a tradable set.
- `close_method` is populated for every row and the 2026-08-03 transition is visible in a count by
  method by month.

### Stop

If point-in-time index membership history for the Nifty 200 cannot be assembled from free sources,
**drop the universe to Nifty 50 + Nifty Next 50** — both of which NSE publishes reconstitution
history for — and re-derive every book's capacity and σ at the narrower breadth. Record the
narrowing in the STOP memo; do not paper over it with a vendor purchase, which L8 forbids at this
stage anyway.

STOP memo: `docs/archive/u0-stop.md`.

---

## H0 — Hurdles, MDE and pre-registration

### Why

This is the milestone that makes the desk honest. Its output is a set of files that say, *before any
book is looked at*, what each book claims, how big the claim is, how much data exists, what the
minimum detectable effect is, and what number closes it. After H0 there is no room to negotiate a
hurdle downward because a result was disappointing.

H0 is also where most of this desk's books die, and that is the intended outcome.

### Build

1. **`src/harness.py`**
   - `mde(sigma_ann, years, alpha=0.05, power=0.80) -> float` implementing
     **MDE_ann = 2.80 × σ_ann / √T**.
   - `benchmark(capital, dates)` — Nifty 50 TRI net of 0.04% TER, taxed at 13.0% on realisation, on
     the same capital and cash-flow schedule as the sleeve under test. This is the single benchmark
     for H2, H3 and H7.
   - `PreRegistration` — a typed record holding: hypothesis, instrument, horizon, universe,
     `n`, `sigma_ann`, `T_years`, `mde_ann`, `E_net_hypothesised`, `half_E_net`, `passes_h4`, spec
     budget (5), specs used, and a SHA of the file at the moment of registration.
   - `spec_budget_guard` — refuses to run a sixth specification for a book.
   - `date_shift_test(panel, feature_fn)` — the look-ahead assertion, reusable by every book.
2. **`docs/next/h0-hurdles.md`** — H1 through H7 exactly as in blueprint §10, with the derivation of
   the 300 bps H2 number written out (23.8 bps friction + ~78 bps tax differential + ~40 bps impact
   = ~140 bps of self-inflicted drag, to be earned back twice over, and above the 30–34 bps TER of
   the packaged competitor by enough to pay for operational risk).
3. **One pre-registration file per book**, in `docs/next/`, committed *before* the book's first data
   access:
   - `h0-prereg-book-l.md` — arithmetic; no MDE; effect 95–130 bps/yr; kill at < 50 bps.
   - `h0-prereg-book-p.md` — deterministic comparison; no MDE; kill thresholds ±100 bps.
   - `h0-prereg-book-b.md` — σ 0.5%, T 5 yr, MDE 0.63%, E_net 25–60 bps, half 12–30 bps → marginal.
   - `h0-prereg-book-m.md` — σ 8%, T 20 yr, **MDE 5.01%**, E_net 2.0%, half 1.0% → **fails 5.0×**.
   - `h0-prereg-book-r.md` — σ 10%, T 15 yr, **MDE 7.23%**, E_net 1.9%, half 0.95% → **fails 7.6×**.
   - `h0-prereg-book-a.md` — σ 3.9%, T 0.09 yr, **MDE 36.4%**; records that T = 1 gives 10.9% and
     T = 20 gives 2.44%, and sets the review date **2027-08-31**.
4. **STOP memos written at H0, not later**, for every book that fails H4 on arrival:
   - `docs/archive/book-r-stop.md` — results drift. Must state: the anomaly's existence in the
     Indian literature (*Theoretical Economics Letters*, 2018; Nifty 500; 2002–2017; 64-day drift
     robust to beta, market cap, P/B, illiquidity, idiosyncratic volatility) is **not** in dispute;
     its retail implementability is. MDE 7.23% against ½ × 1.9%. Also record that India has no free
     point-in-time consensus dataset, so surprise must be seasonal-random-walk SUE from filed
     results, and that `ai.extract` — the desk's only legitimate AI use — dies with this book.
   - `docs/archive/book-option-premium-stop.md` — index option premium selling, with the three
     independent kills: friction ≈ VRP at India VIX 10.97; T < 6 months of the current regime;
     SEBI's FY26 evidence that ₹25,000 crore of the ₹91,685 crore individual loss was transaction
     cost, not transfer. Plus the full re-open condition so it cannot be reopened casually.
   - `docs/archive/book-event-day-stop.md` — Budget and MPC days. Must record the unusual reason:
     this is the **only** phenomenon on the list whose MDE arithmetic is comfortable (n = 140 events,
     MDE ≈ 2.5%/yr), and it is closed because trading it requires a directional forecast, which
     **L10** forbids. Closed on absence of an admissible signal, not on measurability.
   - `docs/archive/book-recon-stop.md` — index reconstitution: effective n ≈ 40 rebalances,
     MDE 1.77%/event against ~0.4%/yr net.

### Exit

- `h0-hurdles.md` exists with H1–H7 as numbers and the 300 bps derivation written out.
- A pre-registration file exists for **every** book named in the blueprint, committed with a SHA,
  and `harness` can load and validate each one.
- Every book failing H4 has its STOP memo in `docs/archive/` **before** any of its data was touched.
- `mde()` is unit-tested against the six values in blueprint §5.1 (0.63%, 5.01%, 7.23%, 36.4%,
  10.9%, 2.44%) to three significant figures.
- `date_shift_test` is unit-tested to catch a deliberately planted one-day look-ahead.

### Stop

If a book's pre-registration cannot state σ and T from the U0 panel — because the data does not
exist at that breadth or depth — **the book closes here, at H0, with a STOP memo**, and does not
get a "provisional look". A book that cannot say how much data it has cannot say what it found.

STOP memo: `docs/archive/h0-stop.md`.

---

## L1 / L2 — Book L, the holding-period and cost ledger

Rank 1. Zero research risk. This is the book that carries the desk.

### L1 Why

Quantify, exactly, the after-tax value of a realisation schedule on a ₹50 lakh Indian equity core:
the 20.8% → 13.0% conversion across the 12-month line, the use-it-or-lose-it ₹1.25 lakh s.198
exemption, the 0.001%-versus-0.10% STT gap between rebalancing in ETF units and rebalancing in
constituents, and the ETF-versus-direct-index-fund choice for the core. None of this requires an
alpha claim. All of it requires the arithmetic to be right.

### L1 Build

- `src/books/ledger.py`:
  - `realisation_schedule(lots, target_weights, as_of)` → the set of sells that reaches the target
    weights at minimum after-tax cost, respecting: 12-month acquisition dates per lot (FIFO per
    Indian practice), the remaining ₹1.25 lakh exemption for the tax year, and the 31 March boundary.
  - `etf_vs_constituents(turnover_value, etf_spread_bps)` → which venue a rebalance should route to,
    using the 20 bps STT gap against the day's quoted ETF spread.
  - `etf_vs_index_fund(capital, annual_turns, ter_etf, ter_fund, spread_bps, exit_load)` → the
    crossover, including the 1%-inside-15-days exit load some Indian index funds carry.
- `docs/next/l1-ledger-arithmetic.md` — the worked numbers at ₹25 lakh, ₹50 lakh and ₹1 crore, with
  the 1/capital decay of the exemption shown explicitly.

### L1 Exit

- The measured after-tax schedule delta at ₹50 lakh, at 60%/yr turnover on an 11% gross core,
  reproduces the blueprint's **₹41,990 (84 bps)** tax delta and **₹5,970 (12 bps)** routing saving
  to within ₹100 each.
- `etf_vs_constituents` correctly flips to constituents when the quoted ETF spread exceeds 20 bps.
- `etf_vs_index_fund` produces a crossover in annual turns, and the answer at ₹50 lakh and 4 turns
  a year is stated as a recommendation in `l1-ledger-arithmetic.md`.
- Every rupee figure traces to `costs` and `tax`; no arithmetic is duplicated in the book module.

### L1 Stop

If the measured schedule delta at ₹50 lakh is **under 50 bps/yr**, close Book L, run a plain direct
Nifty 50 index fund, and write `docs/archive/book-l-stop.md`. That would be a legitimate and
complete answer: it would mean the packaged vehicle already captures everything, and the desk's job
shrinks to choosing it and leaving it alone.

### L2 Why

Wire the schedule into `portfolio` so that no exit anywhere on the desk is taken without consulting
it. Book L is not a strategy that runs beside the others; it is a **constraint every other book's
exit must pass through**.

### L2 Build

- `src/portfolio.py`: weights subject to every blueprint §6.1 limit, asserted not assumed — gross
  ≤ 100%, active sleeve ≤ 40%, single name ≤ 6%, single sector ≤ 25%, zero naked short options, zero
  single-stock derivatives, single-position 4σ overnight loss ≤ 2% of equity.
- Sizing from the broker margin endpoint + 25% buffer (**L3**).
- Every proposed sell passes through `ledger.realisation_schedule`; if a sell would realise STCG that
  could become LTCG within *N* sessions, the order is deferred and the deferral is logged with the
  rupee value of the deferral.

### L2 Exit

- A simulated year of quarterly rebalancing on the U0 panel shows the scheduler deferring at least
  one sell across the 12-month line and consuming the ₹1.25 lakh exemption before 31 March, with the
  rupee saving logged per decision.
- Every §6.1 limit has a test that fails when the limit is breached by ₹1.
- The deferral log is human-readable, because at L0 a human reads it every morning.

### L2 Stop

If the scheduler's deferrals cause a tracking error against the target weights of more than **150
bps annualised**, the deferral window is too long: cap it and re-measure. If it cannot be capped
without losing the tax benefit, Book L reduces to the exemption and routing terms only, and that
reduction is recorded.

STOP memos: `docs/archive/book-l-stop.md`.

---

## P1 — Book P, packaged versus self-run Indian factor sleeves

Rank 2. Zero alpha claim. ₹0 of data spend. This is the milestone that decides how the 40% active
sleeve is filled.

### Why

India has cheap, direct-plan factor index funds and ETFs — Motilal Oswal Nifty 200 Momentum 30 ETF
at **0.30%**, its direct index fund at **0.34%**, UTI / Axis / Bandhan direct plans around
0.3–0.5% — which rebalance internally and defer the investor's tax event to redemption. A self-run
replication pays 23.8 bps of friction per turn and 20.8% STCG on realised rebalance gains. The
question of which wins is arithmetic on published data, and it retires or licenses an entire line of
research for free.

It is also live rather than rhetorical right now: the Nifty 200 Momentum 30 TRI has had a poor run
(one representative direct plan at −3.81% over the year to June 2026 against 13.42% over three
years), so the answer cannot be assumed from recent performance.

### Build

- `src/books/packaged.py`:
  - Load published TRI series for Nifty 200 Momentum 30, Nifty 500 Momentum 50, Nifty 100 Low
    Volatility 30 and Nifty Alpha 50 from NSE Indices, and scheme TERs and exit loads from AMFI.
  - `packaged_after_tax(tri, ter, exit_load, holding_years, capital)` — one tax event, at
    redemption, at 13.0%.
  - `self_run_after_tax(index_constituents_history, turnover, capital)` — replication through
    `panel` and `universe`, with `costs` on every rebalance leg, `tax` on every realised gain, and
    the NSE impact-cost file applied at 6× the actual order size per H5.
  - `crossover(...)` — the difference in bps/yr, by capital and by holding period.
- `docs/next/p1-packaged-vs-self.md` — the verdict, with the bps difference, the sensitivity to the
  tax term, and the recommended sleeve, weight and rebalance cadence.

### Exit

A verdict, with a number, in one of three forms:

1. **Packaged wins by > 100 bps/yr** → Book M closes permanently with
   `docs/archive/book-m-stop.md`; the 40% active sleeve is implemented in the named fund at the named
   weight and cadence. **This is a completed milestone, not a failure.**
2. **Self-run wins by > 100 bps/yr** → Book M opens, but only against its existing pre-registration,
   which already records an H4 failure of 5.0×. It gets five specs and its STOP memo is pre-written.
3. **Within ±100 bps** → buy the fund, because it carries no operational risk. Record the tie.

Additional exits: the self-run replication is reconciled against the published TRI to within **50
bps/yr** before costs, proving the replication is faithful and the difference measured is cost and
tax rather than tracking error. And the sensitivity of the verdict to the assumed self-run turnover
is tabulated at 20%, 30%, 50% and 100% per year.

### Stop

If the self-run replication cannot be reconciled to the published TRI within 50 bps/yr before costs,
the comparison is invalid — the replication is wrong, not the conclusion. Fix the replication or
close the milestone with `docs/archive/p1-stop.md` and default to the packaged vehicle, which is the
conservative and defensible choice.

---

## M1 — Book M, self-run momentum. Gated and expected to remain closed.

### Why

Only opens if P1 returns outcome 2. Its pre-registration already records **MDE 5.01%/yr against a
½ × 2.0% = 1.0% gate — a 5.0× failure of H4**. It exists on the plan so that a later agent finds a
closed door with a reason on it, rather than an unexamined idea.

### Build

Only on outcome 2: `src/books/momentum.py`, 12-month formation, 12-month minimum hold, annual
rebalance timed so exits land past the 12-month line, Nifty 200 universe, long-only, `costs` and
`tax` on every leg, five specifications maximum.

### Exit

Clear H2 (300 bps), H3 (Sharpe 0.40, and 0.30 in each half), H4 and H5 simultaneously. Given the
recorded MDE, the honest expectation is that H4 is not clearable and the milestone ends in a STOP
memo.

### Stop

Close on any of: P1 outcome 1 or 3; the fifth specification exhausted; H2 or H3 missed; or the
H4 failure standing. `docs/archive/book-m-stop.md` must state the MDE arithmetic and the required
gross effect (**g ≥ 12.1%/yr** at σ = 6% and T = 15 — not a credible claim for a publicly documented
Nifty 200 anomaly).

---

## A0 — Book A, CAS closing-auction dislocation. Deferred to 2027-08-31.

### Why

The Closing Auction Session is the one genuinely new and genuinely un-crowded piece of Indian
microstructure available to this desk: live since 3 August 2026, in a pool roughly **1% of
cash-market ADTO**, with documented end-of-day volatility, a regulator publicly committed to keeping
it, and SLBM reform being accelerated specifically to deepen it. Nobody has a long sample. Neither
do we.

### Build

**Nothing, before 2027-08-31.** The only deliverable now is a calendar item in `ops` with the review
date, and the pre-registration already written at H0.

At the review, the build is: a session-level study of the CAS equilibrium price against the 15:15
reference price for Nifty 200 CAS-eligible names, from `panel`'s `close_method = cas_auction` rows,
with five specifications and the MDE recomputed at the then-available T.

### Exit

At the review date, and only then: recompute MDE at the available T and apply H4. At T = 1 year the
MDE is **10.9%/yr** against a hypothesised 1.5% net — so the honest expectation is a further
deferral, not an opening. The book becomes viable on measurability only around T ≈ 20 years
(MDE 2.44%).

### Stop

**Opening this book before 2027-08-31 is a peek and is forbidden.** The review date is a hard
calendar item in `ops`, not a judgement call. If at any review the CAS mechanism has been materially
changed by SEBI, reset T to zero from the change date and re-defer.

---

## S0 — Book B, SLBM lending yield. Gated on a regulator publication.

### Why

Shares already held in the core can be lent for a fee without changing market exposure — genuinely
free money if the fee clears its friction. The market-wide fee pool grew from ₹425 crore in FY25 to
₹697 crore in FY26, with ₹346 crore in Q1 FY27 alone. But the new R3 three-day series (live
17 August 2026) has **no repay, recall or rollover**, so a lent share is genuinely locked, and SEBI's
chairman has said a reformed-SLBM consultation paper is imminent.

### Build

Two parts, in order:

1. **₹0 screen, buildable now**: `src/books/slbm.py` reads the free **NSE SLB bhavcopy** over five
   years and measures the realised, annualised lending fee on the specific Nifty 50 and Nifty 200
   names the core actually holds, along with fill probability and fee dispersion by name and by
   month. Output: `docs/next/s0-slb-fee-screen.md`.
2. **Live lending: blocked** until SEBI's reformed-SLBM circular is published *and* the tax treatment
   of the lending fee is settled in writing by a CA.

### Exit

- **Close if the median annualised lending fee on the desk's actual holdings is under 25 bps.** At
  that level the fee does not pay for the lock-in and the operational surface.
- Proceed to live lending only when: median fee ≥ 25 bps, SEBI's reformed circular is published and
  read, the tax treatment is in writing, and the lock-in is compatible with Book L's realisation
  schedule (a share lent across a planned 12-month crossing date is a scheduling conflict `portfolio`
  must refuse).

### Stop

Close on any of: median fee < 25 bps; the R3 lock-in incompatible with the realisation schedule;
tax treatment unresolved. `docs/archive/book-b-stop.md`.

---

## L0 — Operating loop in IST

### Why

A book that cannot be run every day, reconciled to the rupee, and executed by hand when the API
fails, is not a book. L0 is also the **only** milestone that unlocks paid data (₹500/month) and
live capital — both blocked until it exits (**L7**, **L8**).

### Build

The loop, in Indian time, with the 2026 session structure:

| Time (IST) | Step | Owner |
|---|---|---|
| **09:00** | Reconcile yesterday's fills against the broker ledger and contract note to ₹1. **If reconciliation fails, no instructions are emitted today.** | `ops` |
| 09:00–09:05 | Pre-open phase 1 — market and limit orders permitted | `execute` |
| 09:05–09:10 | Pre-open phase 2 — **limit orders only**; a market order here is rejected by the exchange | `execute` |
| 09:15 | Continuous trading opens; place the remainder of the instruction list as limit orders | `execute` |
| 15:20–15:25 | For CAS-eligible names only: place any close-referenced residual into the auction | `execute` |
| **16:15** | Run the desk: refresh `panel` from bhavcopy, recompute target weights, run the realisation scheduler, emit tomorrow's **instruction list** | all |
| 16:30 | LLM writes the "what changed, what looks wrong" note on the run log (**L10**) | `ops` |

Also built:

- `src/execute.py` — instruction-list generation and placement; hard 8 orders/second cap; exchange
  algo ID asserted on every order or the order is not sent; pre-open phase-2 and CAS-phase order-type
  rules encoded, not documented; static-IP OAuth with 2FA and daily token renewal as an explicit
  pre-run assertion.
- `src/ops.py` — reconciliation to ₹1; run log; kill-switch state; the Indian calendar: exchange
  holidays, **NSE expiry Tuesdays** and **BSE expiry Thursdays**, results season, Budget day, MPC
  dates, the 31 March tax-year boundary, the 31 August and 31 October filing deadlines, and Book A's
  **2027-08-31** review.
- `docs/next/l0-runbook.md` — the manual fallback (**L12**): how to place the same instruction list
  by hand, and the three failure modes that trigger it (API down, token failure, reconciliation
  mismatch).

### Exit

- **Twenty consecutive sessions** of paper running with **zero reconciliation breaks greater than
  ₹1** and zero missed 16:15 runs.
- The instruction list for at least one session is placed **entirely by hand** from the printed file,
  and the result reconciles to the automated path.
- `execute` demonstrably refuses: an untagged order, a market order in pre-open phase 2, a ninth
  order in the same clock second, an order in a name that is in the F&O ban list or ESM Stage II, and
  an order whose size exceeds any §6.1 limit.
- H1 re-verified against real contract notes now that live fills exist, still to ₹1.
- H6 satisfied: one machine, one broker, one run, ≤ 10 OPS, manual fallback documented and exercised.

### Stop

If twenty sessions cannot be completed without a reconciliation break, **stop and fix the
reconciliation** — do not proceed to live capital. If the loop needs a second machine, a second
broker, or a human watching the screen intraday, **stop and redesign** (H6). If the broker API
cannot be operated within the SEBI framework — algo ID unavailable, static IP not supported, TOPS
enforcement unclear — change broker before changing the design.

STOP memo: `docs/archive/l0-stop.md`.

---

## X0 — Kill review

### Why

To stop this desk from becoming a thing that exists because it exists.

### When

Two full quarters after L0 goes live with capital, and every two quarters after that. On the calendar
in `ops`, not at anyone's discretion.

### What is reviewed

1. **H7**: has the after-tax return trailed the Nifty 50 TRI by more than 600 bps in the tax year?
   If yes, halt every active sleeve, move to 100% core, and write the review.
2. **Book L's measured delta** against its L1 claim of 95–130 bps. If it has fallen below 50 bps —
   which will happen mechanically as capital grows past ₹1 crore — say so and act.
3. **Book P's verdict**, re-run. TERs move, exit loads move, and factor index composition is
   reconstituted semi-annually.
4. **Every closed book's re-open condition** from blueprint §8 and §12, checked as a list, not
   remembered: India VIX 30-day median, derivative STT rates, T+0 mandate status, single-stock
   derivative settlement, SEBI's reformed SLBM circular, post-CAS sample length, free Indian PIT
   consensus data, and capital crossing ₹1 crore.
5. **Spend against the ladder.** Actual rupees, against the ₹6,000/yr tier-1 and ₹35,000/yr ceiling.
6. **The working-numbers register.** Any W-item still unresolved past its milestone is either
   resolved or the dependent claim is withdrawn.

### Output

`docs/archive/x0-review-YYYY-MM.md`, containing the numbers, the decisions, and — if the desk is not
beating a NIFTYBEES-plus-Book-L baseline after tax — the recommendation to shut the active sleeves
and hold the core. **That recommendation is a legitimate outcome and the plan is written to make it
easy to take.**

---

## Calendar reality — the Indian dates this desk lives on

| Recurring | When | Why it matters |
|---|---|---|
| Pre-open auction | 09:00–09:15, two phases from 7 Sep 2026 | Market orders rejected in phase 2 |
| CAS for F&O-eligible names | continuous ends 15:15; auction 15:20–15:35 | The official close is an auction print, in a pool ~1% of cash ADTO |
| Derivatives close | 15:40 | Ten minutes later than cash |
| Post-close cash | 15:50–16:00 | Why the desk runs at 16:15 |
| NSE expiry | every Tuesday (weekly Nifty), last Tuesday (all else) | Delivery-margin ramp E−4 to E; ban-list churn |
| BSE expiry | every Thursday (weekly Sensex), last Thursday (all else) | Same |
| F&O ban list | published each morning pre-open | `universe` must refuse banned names |
| Price-band revision | upward daily, downward monthly | `universe` must carry the band as of the date |
| MWPL recomputation | quarterly, on free float and ADDV | The single-stock derivative universe moves — irrelevant here by design |
| Results season | ~Jan, Apr, Jul, Oct | Filing deadlines: 45 days quarterly, 60 days annual (mainboard) |
| Index reconstitution | semi-annual, March and September | Prints inside CAS now |
| Union Budget | 1 February | STT and capital-gains rates change here, and did in 2024 and 2026 |
| RBI MPC | six times a year | Index-level risk, no position taken |
| Tax year boundary | 31 March | Last date to consume the ₹1.25 lakh s.198 exemption |
| ITR filing | 31 August (no audit) / 31 October (audit) | **Missing it permanently forfeits loss carry-forward** |
| Advance tax | 15 Jun / 15 Sep / 15 Dec / 15 Mar | Business income, if any book ever generates it |
| **Book A review** | **2027-08-31** | Hard calendar item, not a judgement call |

---

## STOP memo template

Every STOP memo in `docs/archive/` uses this shape. It exists so a later agent can tell the
difference between "we tried and it failed" and "we never looked".

```markdown
# STOP — <book or milestone>

Date: YYYY-MM-DD
Closed at: <milestone ID>
Author: <agent / human>

## What was claimed
<hypothesis, instrument, horizon, universe, pre-registered E_net>

## What was measured
<n, sigma_ann, T_years, MDE_ann, half_E_net, specs used of 5>
<or: "nothing was measured; the book closed on arithmetic before any data access">

## Why it closed
<the binding hurdle: H1 / H2 / H3 / H4 / H5 / H6, with the number>
<the Indian reason, named: statute, circular, rate, or microstructure fact>

## What would re-open it
<a specific, checkable Indian change — a rate, a circular, a VIX level, a sample length,
 or a date. Not "more research".>

## What was deleted
<modules removed, dependencies dropped, calendar items retired>
```

---

*Charter: [india-equity-architecture-blueprint.md](india-equity-architecture-blueprint.md)*
