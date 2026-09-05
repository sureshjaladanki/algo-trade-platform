# Retail India desk — Architecture Blueprint

| | |
|---|---|
| **Date** | 2026-09-05 |
| **Status** | BLUEPRINT Rev 1.0 / ACTIVE |
| **Review** | Claude Opus, 2026-09-05 |
| **Scope** | Listed Indian equity and equity derivatives (NSE / BSE). Own capital only. |
| **Companion** | [india-equity-execution-plan.md](india-equity-execution-plan.md) |
| **P0 posture** | [p0-posture.md](p0-posture.md) |

This is the charter. The execution plan turns it into milestones. Nothing in this document is a
translation of a US desk; where a number is not sourced to an Indian statute, exchange circular or
regulator document as of September 2026, it is tagged **(working)** and listed in
[Appendix A](#appendix-a--working-numbers-register) with a verification owner.

---

## One-line thesis

Indian statutory friction is levied on **turnover** — and from 1 April 2026 futures STT is
2.5× the prior rate (options premium STT 1.5×) — while free Indian data is only ~20 years deep, so at ₹25 lakh–₹1 crore of own capital
the high-turnover books die on cost and the low-turnover books die on measurability: **this desk's
viable edge is arithmetic, not predictive**, and the algo's job is to compute cost, STT and
holding-period exactly, choose packaged-versus-self honestly, and execute against a NIFTYBEES hurdle
without error.

---

## 0. Derivation — India's own constraint ladder

A US retail desk derives from tax location first (IRA / Roth / Section 1256) because the US gives a
retail trader a container in which turnover is invisible to the tax authority. **India gives no such
container.** So India's ladder is not the US ladder re-ordered; it is a different ladder, and the
rungs bind in a different direction.

### 0.1 Rung 1 — There is no wrapper, so holding period is the only tax lever

India has no self-directed, tax-deferred, turnover-tolerant account. What it does have:

| Vehicle | Can it hold a self-directed algo book? | Why not |
|---|---|---|
| ELSS | No | Equity mutual fund. You buy units; the AMC trades. 3-year lock-in per instalment. 80C only, capped ₹1.5 lakh, and **not available at all under the new default regime**. |
| NPS (Tier I / Tier II) | No | Pension scheme. Fund-manager-managed, capped equity allocation, withdrawal restrictions to age 60 on Tier I. No security selection, no orders. |
| PPF / Sukanya / SSY | No | Debt, sovereign-rate, ₹1.5 lakh/yr cap, 15-year tenor. |
| PMS / AIF | No | ₹50 lakh and ₹1 crore minimums, and they make *you* the client of a registered manager, not the manager. Tax is pass-through anyway — no shelter. |
| Demat + trading account | Yes — and this is the only option | Fully taxable, every year, at your own rate. |

Consequence: **every rupee of realised gain is taxed in the tax year it is realised.** The only lever
is *classification and holding period*:

| Classification | Statute (Income-tax Act, 2025, in force 1 Apr 2026) | Rate |
|---|---|---|
| Listed equity held > 12 months | s.198 (old s.112A) | 12.5% above ₹1.25 lakh aggregate per tax year, no indexation → **13.0%** with 4% cess |
| Listed equity held ≤ 12 months | s.196 (old s.111A) | 20% flat, no exemption → **20.8%** with cess |
| Intraday equity (no delivery) | s.66 (old s.43(5)) — **speculative business** | Slab, up to **31.2%** effective (30% + cess); losses only against speculative income, carry 4 years |
| F&O on a recognised exchange | s.66 exception — **non-speculative business** | Slab, up to **31.2%**; losses against any head except salary, carry 8 years |

The spread between 13.0% and 20.8% is 780 bps of realised gain, and the spread between 13.0% and
31.2% is 1,820 bps. **On a retail Indian book, moving a realised gain across the 12-month line is
worth more than most alphas a retail trader can measure.** That is the first-rung finding, and it is
arithmetic — no inference required.

The ₹1.25 lakh s.198 exemption is a *fixed rupee* benefit, so its value in basis points falls with
capital. This is the single most important reason this desk is designed for ₹25 lakh–₹1 crore and
not for ₹10 crore:

| Capital | ₹1.25 lakh exemption saved at 13% | As bps of capital |
|---|---|---|
| ₹25 lakh | ₹16,250 | 65 bps |
| ₹50 lakh | ₹16,250 | 33 bps |
| ₹1 crore | ₹16,250 | 16 bps |
| ₹10 crore | ₹16,250 | 1.6 bps |

### 0.2 Rung 2 — Friction is charged on notional, and Budget 2026 doubled it on derivatives

STT is not a fee on profit. It is a fee on the size of the trade. The Finance Act, 2026 (Presidential
assent 30 March 2026, effective 1 April 2026) raised:

- futures: sale-side STT **0.02% → 0.05%**
- options: sale-side STT on premium **0.10% → 0.15%**
- exercised options: **0.125% → 0.15%** of intrinsic value, payable by the purchaser

Delivery (0.10% both legs), intraday (0.025% sell) and equity-oriented fund units (0.001% sell) were
left unchanged. **The 2026 hike is aimed exactly at the products a retail algo desk would reach for
first.** Worked round trips are in [§4](#4-friction--the-real-indian-cost-stack); the headline is
that index-futures round-trip friction went from ~3.1 bps to ~6.1 bps of notional overnight, and
NSE's own August 2026 volumes fell 22.6% month-on-month with index-options premium turnover down
28.6%.

### 0.3 Rung 3 — Inference budget, and why it points the opposite way from Rung 2

Free, PIT-reconstructible Indian daily data runs ~2005–2026 for a clean Nifty 500 universe (~21
years, ~5,150 sessions). Corporate filings good enough for a machine-readable results calendar run
from ~2011 (~15 years). The current derivatives regime — one weekly per exchange, Tuesday/Thursday
expiry, January 2026 lot sizes, April 2026 STT, August 2026 closing auction — is **months old**.

The minimum detectable effect for an annual active return, at α = 0.05 two-sided and 80% power, is

> **MDE_ann = 2.80 × σ_ann / √T**

where σ_ann is the annualised standard deviation of the sleeve's return *against the benchmark* and
T is years of usable point-in-time history.

Rung 2 kills every high-turnover book. Rung 3 kills every low-turnover book, because a low-turnover
book has a large σ per unit of T. **The two rungs close the statistical-alpha space from opposite
ends.** The per-book arithmetic is in [§5](#5-inference--n-σ-mde-and-the-gate) and it is the reason
this blueprint ranks two arithmetic books above every predictive one.

### 0.4 Rung 4 — Capacity is not the constraint; it is slack

At ₹50 lakh, a 6%-of-equity maximum position is ₹3 lakh. NSE's published monthly impact-cost file
puts a Nifty 50 name at 2–6 bps and a Nifty Midcap 150 name at 8–20 bps for a ₹1 lakh order
**(working)**. A ₹3 lakh order in a Nifty 200 name is a fraction of a percent of that name's 20-day
median *delivery* value. Headroom to the H5 limit is roughly three orders of magnitude. Capacity
binds somewhere above ₹5 crore, which is outside the envelope. Say it plainly: **this desk is not
capacity-constrained, it is friction- and measurability-constrained**, and any design that trades
capacity for turnover is trading away the only thing that is not scarce.

### 0.5 Rung 5 — Alpha, only now

See [§7](#7-alpha-last--indian-phenomena-versus-retail-viability). Every Indian phenomenon is graded
against the four rungs above, and most of them fail on Rung 2 or Rung 3 before their statistical
existence is even in question.

---

## 1. Market structure as of 5 September 2026

### 1.1 Venues

| | NSE | BSE | MSEI |
|---|---|---|---|
| Cash market share | >90% | <10% | negligible |
| Index options premium share (Aug 2026) | ~65% | 34.7% | — |
| Derivatives expiry day | **Tuesday** (all contracts) | **Thursday** (all contracts) | — |
| Weekly index option | Nifty 50 only | Sensex only | — |
| Futures transaction charge | 0.00173–0.00183% | **0** | — |
| Cash transaction charge | 0.00297–0.00307% | 0.00375% | — |

NSE has filed for an IPO; its own filing shows options generated ~₹10,000 crore of transaction
charges in FY26, about 60% of revenue from operations. **The exchange's incentive is to defend
derivative volume; SEBI's stated incentive since October 2024 has been to compress it.** That policy
tension is a standing risk to any derivative book and a reason to hold the derivative sleeve at zero
by default (§8).

### 1.2 Session — and the two 2026 changes that break every close-based backtest

The trading day changed twice in 2026. SEBI circular
`HO/47/11/11(3)2025-MRD-POD2/I/2765/2026` dated 16 January 2026 introduced a **Closing Auction
Session (CAS)**, live **3 August 2026** for F&O-eligible stocks, and realigned the pre-open session
from **7 September 2026** — two days after this document's date.

Current and imminent timetable (IST):

| Phase | Time | Notes |
|---|---|---|
| Pre-open order entry, phase 1 | 09:00–09:05 | Market **and** limit orders (new, from 7 Sep 2026) |
| Pre-open order entry, phase 2 | 09:05–09:10 | **Limit orders only**; market orders rejected; random close 09:08–09:10 |
| Pre-open matching / confirmation | 09:10–09:12 | |
| Buffer | 09:12–09:15 | |
| Continuous trading | 09:15 → | |
| Continuous ends, **CAS stocks** | **15:15** | F&O-eligible stocks (>200 names) |
| CAS transition | 15:15–15:20 | Reference price fixed; ±3% band locked |
| CAS order entry, open | 15:20–15:25 | Market and limit |
| CAS order entry, restricted | 15:25–15:30 | Limit only; random close 15:28–15:30 |
| CAS matching → **official close** | 15:30–15:35 | Equilibrium price *is* the closing price |
| Continuous ends, non-CAS stocks | 15:30 | Old 30-minute VWAP close retained |
| Derivatives close | **15:40** | Extended by 10 minutes |
| Post-close (cash) | 15:50–16:00 | Trades at the official closing price |

Three consequences the platform must encode:

1. **There are now two closing-price mechanisms in the same market on the same day.** `panel` must
   carry a `close_method` column ∈ {`vwap_30min`, `cas_auction`} and no book may pool pre- and
   post-3-August-2026 closes for an F&O-eligible name without declaring the break.
2. **The CAS pool is thin.** Jefferies (2 September 2026) put the auction pool at roughly **1% of
   cash-market ADTO**, with greater end-of-day volatility as a result. SEBI's chairman has said CAS
   will not be rolled back and that SLBM reform is being accelerated to deepen it. A close-referenced
   order is now exposed to a shallow auction, not to a 30-minute average.
3. **The desk's own run window moves to ~16:15 IST**, after the post-close session settles, because
   before 16:00 the official close of an F&O-eligible name does not exist yet.

### 1.3 Settlement

T+1 rolling settlement for cash equity. Optional T+0 exists in beta for a limited set of scrips, but
SEBI has **postponed the broader rollout indefinitely** (deadlines of 1 May 2025 and 1 November 2025
both lapsed; the October 2025 circular declined to set a new date, citing QSB readiness). T+0 also
requires execution by 13:30 and funds by 16:30 and excludes institutional and custodian clients.
**Design assumption: T+1 only.** T+0 changes nothing for this desk and must not appear in any cash
projection.

### 1.4 Tick size, price bands, surveillance

Tick size (NSE, from 15 April 2025, applied to cash and stock derivatives) **(working)**:

| Security price | Tick |
|---|---|
| < ₹250 | ₹0.01 |
| ₹250 – ₹1,000 | ₹0.05 |
| ₹1,001 – ₹5,000 | ₹0.10 |
| ₹5,001 – ₹10,000 | ₹0.50 |
| ₹10,001 – ₹20,000 | ₹1.00 |
| > ₹20,001 | ₹5.00 |

Index futures: ₹0.05 below 15,000; ₹0.10 for 15,000–30,000; ₹0.20 above 30,000. At Nifty ≈ 23,873
the futures tick is ₹0.10, or **₹6.50 per lot per tick** — against a round-trip friction of ~14.4
Nifty points (§4). A "one-tick edge" is 144× too small to pay for itself.

Price bands: individual stocks carry 2% / 5% / 10% / 20% daily bands; derivatives-eligible stocks
carry no band but a 10% daily operating range. NSE's 8 April 2026 revision covered 3,162 securities
— 23 at 2%, 367 at 5%, 170 at 10%, 213 with no band, 2,386 at 20%, 3 at 40%. Market-wide breakers
halt the whole equity and derivative market at Nifty 50 or Sensex moves of 10% / 15% / 20%.

Surveillance is the hard reason smallcaps are closed to a systematic book. Under the July 2025 ESM
framework, a Stage I name gets 100% margin from T+2, trade-for-trade settlement and a 5% (or 2%)
band; a **Stage II name trades only in a periodic call auction with a ±2% band** and must stay there
a minimum of one month. GSM adds its own escalating margin and auction-only stages. A backtest that
assumes continuous trading in a name that was in ESM Stage II on that date is not a backtest.

### 1.5 Derivatives structure — what actually exists

Following SEBI's October 2024 index-derivatives package and the 26 May 2025 expiry circular:

- **One weekly benchmark index option per exchange.** Nifty 50 on NSE (Tuesday), Sensex on BSE
  (Thursday). That is the entire weekly universe.
- **Everything else is minimum one-month tenor**: all index futures, all non-benchmark index options
  (Bank Nifty, FinNifty, Midcap Select, Next 50, Bankex), and all single-stock futures and options.
  Expiry is the last Tuesday (NSE) / last Thursday (BSE).
- Option premium is collected upfront from buyers; the calendar-spread margin benefit is **withdrawn
  on expiry day** for contracts expiring that day; an additional 2% ELM applies to short options on
  expiry day **(working)**.
- Non-benchmark index derivatives face new eligibility norms from 3 November 2025, and a derivatives
  pre-open and post-close session was introduced from 6 December 2025.

Lot sizes, effective January 2026 contracts (NSE circular `NSE/FAOP/70616`, SEBI
`SEBI/HO/MRD-PoD2/CIR/P/2024/00181`):

| Underlying | Lot | Level, 4 Sep 2026 | Notional / lot |
|---|---|---|---|
| Nifty 50 | 65 (was 75) | 23,873 | **₹15.52 lakh** |
| Nifty Bank | 30 (was 35) | ~57,500 | ₹17.25 lakh |
| Nifty Financial Services | 60 (was 65) | — | ~₹15 lakh (working) |
| Nifty Mid Select | 120 (was 140) | — | ~₹15 lakh (working) |
| Nifty Next 50 | 25 (unchanged) | — | ~₹19 lakh (working) |
| BSE Sensex | 20 | ~78,000 (working) | ~₹15.6 lakh |

**One index lot is 31% of a ₹50 lakh book by notional.** Position sizing in Indian index derivatives
is not continuous; it is a step function with a ₹15 lakh step.

### 1.6 MWPL and the ban period

From 1 October 2025 the market-wide position limit for a single stock is the **lower of 15% of
free float or 65× average daily delivery value (ADDV)**, with a 10%-free-float floor, recalculated
quarterly. From 8 December 2025 compliance is measured on **delta-based Future-Equivalent open
interest (FutEq OI)**, not contract counts, and is checked at random intervals *during* the session,
not only at end of day.

- **Ban entry**: market-wide FutEq OI crosses **95%** of MWPL.
- **Ban exit**: aggregate FutEq OI falls below **80%**.
- **During a ban**: no trade may increase your net delta or flip its sign relative to the base
  recorded on day 1 of the ban. Deltas are taken from the clearing corporation's 14:00 marks.
- **Penalty**: 1% of the violation value, minimum ₹5,000, maximum ₹1,00,000 per stock per day, plus
  GST, repeating daily until corrected.
- Individual entity limit in a single stock: **10% of MWPL**.

The ban list is published each morning before the open. A stock derivatives book therefore has a
tradable universe that changes overnight, a hedge that may become illegal to adjust, and a penalty
regime that punishes the *mechanically correct* action of unwinding one leg of a hedge.

### 1.7 Margin

Peak margin has been at 100% upfront since 1 September 2021. The clearing corporation takes four
random intraday snapshots; the broker must have collected the full VaR+ELM (cash) or SPAN+Exposure
(F&O) at peak utilisation, and the penalty applies even if the position was closed before the close.
Practical ceilings:

| Position | Margin posted | Effective leverage |
|---|---|---|
| Cash delivery | 100% | 1× |
| Cash intraday (MIS) | ~20% VaR+ELM | ~5× max |
| Delivery via MTF | 25–50% | 2–4× |
| Nifty index future, 1 lot | SPAN+Exposure ≈ ₹1.1–1.4 lakh **(working)** | ~11× on margin |
| Short index option, 1 lot | SPAN+Exposure ≈ ₹1.1–1.5 lakh **(working)** | loss unbounded |

Position sizing in this platform is **always** computed from the broker's own margin endpoint plus a
25% buffer, never from a hard-coded percentage. See lock L3.

### 1.8 Physical settlement of stock derivatives

All single-stock futures and options have been physically settled since October 2019. Delivery
margin ramps through expiry week (broker schedules differ; Zerodha's is representative):

| Day | Long ITM option | Stock future / short option |
|---|---|---|
| E−4 | 10% of VaR+ELM+adhoc | normal |
| E−3 | 25% | normal |
| E−2 | 45% | normal |
| E−1 | 25% of **contract value** | normal |
| E | 50% of contract value (long ITM); 25% (long OTM) | 50% of contract value or 1.5× NRML, lower |

If margin is short, long ITM options are squared off around 12:00 and short options around 14:30 on
expiry day. Under ICICI's schedule the ramp reaches **100% of VaR+ELM+adhoc** on expiry day with
full contract value or free shares required by 11:00.

The India-specific operational rule that follows: **square off a long ITM option before expiry
whenever the 0.15%-of-intrinsic exercise STT exceeds the round-trip cost of closing the position.**
For a Nifty option 200 points in the money, exercise STT is 0.15% × 200 × 65 = ₹19.50 against ~₹30
to close — so let it exercise. At 1,000 points ITM it is ₹97.50 against the same ~₹30 — so close it.
`costs` owns this comparison; no book decides it by hand.

### 1.9 SLBM and MTF

**SLBM.** Market-wide lending fees were ₹697 crore in FY26 (₹425 crore in FY25), and ₹346 crore in
Q1 FY27 — growing fast off a small base. NSE Clearing and BSE Clearing introduced a shorter **R3
series with a three-day cycle from 17 August 2026** (first leg T+1, reverse leg T+3), available only
for F&O-eligible stocks, with no repay, recall or rollover. Retail sits on the lending side with a
negligible share; borrowing is dominated by proprietary arbitrage. SEBI's chairman has said a
consultation paper on a reformed SLBM framework is imminent, covering a wider eligible universe, net
settlement within SLB and against the cash market, and inter-exchange interoperability. **The rules
are about to change**, which is why the SLBM book is gated rather than opened (§8).

**MTF.** Roughly 2–4× on ~1,700 stocks. Dhan's slab rates are 12.49% p.a. up to ₹5 lakh funded,
rising to 15.49% above ₹25 lakh. Zerodha does not offer MTF. SEBI's 2026 framework adds income
(≥ ₹5 lakh) and net-worth (≥ ₹25 lakh) eligibility and stricter disclosure **(working)**. The
arithmetic is fatal and is dealt with in §2.

### 1.10 Retail API versus co-location

| | Retail broker API | NSE co-location |
|---|---|---|
| Access | Any client with a demat account | Trading members only |
| Cost | ₹0–₹500/month | Lakhs/month rack + connectivity |
| Order rate ceiling | **10 orders/second** (SEBI TOPS) | Effectively unbounded |
| Kite Connect documented limits | 1 quote req/s, 3 historical req/s, 10 order placements/s, 200 orders/min, 3,000–5,000 orders/day | — |
| Round-trip latency | 50–500 ms | single-digit microseconds |

**Any book whose edge decays inside one second is unavailable to this desk by construction.** That
single line closes scalping, expiry-day gamma, order-book imbalance and every latency-adjacent idea
without needing a backtest, and it is the honest reason a one-machine retail desk should not be in
the same trade as a co-located prop algo.

### 1.11 The SEBI retail algo framework — binding, not aspirational

SEBI circular of **4 February 2025**, "Safer participation of retail investors in Algorithmic
trading", with NSE implementation standards of 5 May 2025 (`NSE/INVG/67858`) and extensions of
29 July 2025 and 30 September 2025 (`SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/132`). Non-compliant brokers
were barred from onboarding new retail API-algo clients from 5 January 2026, and the framework became
**applicable to all stock brokers from 1 April 2026**. It is in force today.

What binds this desk:

- **TOPS = 10 orders per second per exchange per segment**, measured on the broker server's calendar
  clock second. Below it, a self-written algo needs no client-level registration; a **generic
  exchange algo ID** is issued and the algo must still satisfy the RMS conditions. Above it, the
  client must register the algorithm with **each** exchange through the broker.
- **Every algo order — above and below the threshold — must carry the exchange-issued unique
  identifier.** There is no untagged automated order.
- A registered retail algo may be used for **self, spouse, dependent children and dependent parents
  only**. Not for anyone else, ever.
- **The broker is the principal**; an algo provider or vendor is its agent. Open, unauthenticated
  APIs are no longer permitted: static IP whitelisting, OAuth and 2FA are mandatory, with daily
  session-token renewal.
- **White box** (disclosed, replicable logic) versus **black box** (opaque). A black-box provider
  must hold a SEBI Research Analyst licence and publish periodic performance, now connected to the
  PaRRVA performance-verification regime live since May 2026 **(working)**.

Design consequences, and they are hard locks: this desk stays under 10 OPS by design; it never offers
a strategy to anyone outside the statutory family definition; it never becomes an algo provider, an
RA or a PMS, because each of those three changes the regulatory perimeter and the audit surface.

---

## 2. Products — Intraday versus Multiday

This is the first-class section. Verdict is one of **viable** (a book may be built on it),
**candidate-gate** (a ₹0 screen with a pre-committed kill number decides), or **closed** (do not
revisit without the named Indian change).

| Product | Intraday | Multiday | Verdict | Binding Indian reason |
|---|---|---|---|---|
| Cash equity delivery | — | ✅ | **VIABLE** | Only product reaching 13.0% LTCG with a ₹1.25 lakh exemption; 23.8 bps round trip is small against a 12-month hold |
| Equity ETF (NIFTYBEES class) | — | ✅ | **VIABLE — core and hurdle** | STT on sale is **0.001%, not 0.10%**; total statutory round trip 3.9 bps versus 23.8 bps for a stock |
| Cash equity intraday (MIS) | ✅ | — | **CLOSED** | 8.3 bps statutory round trip at ₹1 lakh clips + spread; **speculative** business income at slab, losses ring-fenced, 4-year carry; peak margin caps leverage ~5× |
| Index futures (Nifty / Bank Nifty / Sensex / FinNifty / Midcap Select / Next 50) | ❌ | ⚠️ | **CANDIDATE-GATE — hedge overlay only** | Cash-settled (their one advantage over stock F&O), but 6.1 bps round trip × daily = 15%/yr; one lot = 31% of a ₹50 lakh book; monthly tenor only |
| Index options — weekly and expiry-day | ❌ | ❌ | **CLOSED** | Only Nifty (Tue) and Sensex (Thu) have weeklies — two maximally crowded venues; India VIX 10.97; friction ≈ 1.0% of premium ≈ the entire VRP |
| Index options — monthly | ❌ | ❌ | **CLOSED** | Same friction, worse liquidity away from the weekly strikes |
| Stock futures | ❌ | ❌ | **CLOSED** | Compulsory physical settlement; delivery-margin ramp to 100%; ban period on delta-based FutEq with intraday checks and ₹5,000–₹1,00,000/day penalties; MWPL universe moves quarterly; STT 0.05% on full notional |
| Stock options | ❌ | ❌ | **CLOSED** | Same physical settlement; forced square-off at 12:00 / 14:30 on expiry; premium spreads 5–20% outside the top ~15 names; monthly tenor only |
| Sector / thematic ETFs (BANKBEES etc.) | ❌ | ❌ | **CLOSED** | Higher TER, wider spreads, and concentration that 4/5 risk does not license |
| MTF as leverage | — | ❌ | **CLOSED** | Borrowing at 12.49–15.49% p.a. against a ~11% expected-return asset is negative carry; MTF interest is not deductible against capital gains |
| SLBM as a strategy | — | ⚠️ | **CANDIDATE-GATE — deferred** | ₹697 crore FY26 market-wide fee pool; new R3 3-day series has no repay/recall/rollover; SEBI reform consultation imminent |
| SGB | — | ❌ | **CLOSED** | No new tranches since 2024; issuance discontinued; secondary-market buyers lost the maturity exemption from 1 Apr 2026 **(working)**; thin, discounted secondary market |
| G-sec (RBI Retail Direct / NSE goBID) | — | ❌ | **CLOSED as a book** | Slab-taxed interest, no algo content; a liquid fund or sweep FD is a simpler cash sleeve |
| Currency / commodity derivatives | — | — | **OUT OF CHARTER** | Charter is Indian *equity* markets |

### 2.1 Why cash equity delivery is the spine

At 23.8 bps per ₹1 lakh round trip (of which STT is 84%) plus ₹15.34 DP per ISIN per day of sale,
delivery is the only Indian product whose friction is small compared to the holding period it
implies. A sleeve turning over 60%/yr pays ~14 bps in statutory friction and reaches the 13.0% LTCG
rate. The same sleeve run intraday pays ~21%/yr in friction and 31.2% in tax. There is no contest.

### 2.2 Why the ETF STT asymmetry is the most under-exploited fact in Indian retail

STT on the sale of a unit of an equity-oriented fund is **0.001%**. STT on the sale of an equity
share is **0.10%** — 100× more. There is no STT at all on the *purchase* of equity-oriented fund
units. So:

| ₹1 lakh round trip, NSE, Zerodha-class, delivery | Stock | NIFTYBEES |
|---|---|---|
| STT | ₹200.00 | ₹1.00 |
| Stamp duty (buy, 0.015%) | ₹15.00 | ₹15.00 |
| Exchange transaction (0.00297% × 2) | ₹5.94 | ₹5.94 |
| SEBI turnover fee (₹10/crore × 2) | ₹0.20 | ₹0.20 |
| IPFT (0.0001% × 2) | ₹0.20 | ₹0.20 |
| Brokerage | ₹0 | ₹0 |
| GST 18% on (brokerage + exchange + SEBI) | ₹1.14 | ₹1.14 |
| DP charge (1 ISIN, 1 sell day) | ₹15.34 | ₹15.34 |
| **Total** | **₹237.82 = 23.8 bps** | **₹38.82 = 3.9 bps** |

**Rebalancing the core through NIFTYBEES rather than through constituents saves ~20 bps per turn.**
The offsetting cost is the quoted spread: NIFTYBEES shows ~0.11% quoted spread against ~₹272 last
traded, TER 0.04%, AUM ₹66,777 crore (31 July 2026), average daily volume ~72 lakh units. A direct
Nifty 50 index fund has no spread and no DP charge but 2–16 bps more TER and, in some schemes, an
exit load inside 15 days. The decision is capital- and cadence-dependent, it is fully determined by
published numbers, and it belongs to Book L. Peers worth pricing: ICICI Prudential Nifty 50 ETF
(TER 0.03%), Kotak (0.04%), SBI Nifty 50 ETF (0.04%, AUM ~₹2.16 lakh crore — largely EPFO-driven
**(working)**), Mirae (0.05–0.07%).

### 2.3 Why index futures survive only as a hedge

Nifty futures, 1 lot, ₹15.52 lakh notional, round trip:

| Line | Amount |
|---|---|
| STT 0.05% on sale | ₹776.00 |
| Stamp 0.002% on buy | ₹31.04 |
| Exchange 0.00173% × ₹31.04 lakh | ₹53.70 |
| SEBI 0.0001% × ₹31.04 lakh | ₹3.10 |
| IPFT 0.0005% × ₹31.04 lakh | ₹15.52 |
| Brokerage ₹20 × 2 | ₹40.00 |
| GST 18% on (40 + 53.70 + 3.10 + 15.52) | ₹20.22 |
| **Total** | **₹939.58 = 6.05 bps = 14.4 Nifty points** |

Before 1 April 2026 the STT line was ₹310.40 and the total ₹474 — **3.05 bps, or 7.3 points. The
Budget 2026 hike doubled index-futures round-trip friction.** Cadence decides everything:

| Overlay cadence | Annual friction on notional |
|---|---|
| Daily | 15.1% |
| Weekly | 3.1% |
| Monthly | 0.73% |
| Quarterly | 0.24% |

A monthly or quarterly hedge overlay is affordable. A daily one is not. The gate: an index-futures
overlay is permitted only when a live book's H2 surplus exceeds **2×** the annual overlay friction,
and never more than one lot per ₹50 lakh of equity.

### 2.4 Why index option premium selling is closed — the arithmetic, not the opinion

This is what most Indian retail algo desks do, so it gets the full computation rather than a
dismissal.

Nifty weekly ATM straddle, 1 lot, sold at 90 points each leg, bought back at 45 points each leg:

| Line | Amount |
|---|---|
| STT 0.15% on premium sold (₹11,700) | ₹17.55 |
| Exchange 0.03553% on total premium traded (₹17,550) | ₹6.24 |
| Stamp 0.003% on buy-back premium | ₹0.18 |
| SEBI + IPFT | ₹0.11 |
| Brokerage ₹20 × 4 orders | ₹80.00 |
| GST 18% on (80 + 6.24 + 0.11) | ₹15.54 |
| **Total** | **₹119.62 ≈ 1.02% of premium sold** |

Now the payoff. India VIX closed at **10.97 on 4 September 2026** (52-week range 8.72–28.91).
Weekly σ = 11%/√52 = **1.53%**. Premium received on the straddle = 180 points = **0.75% of
notional**. The volatility risk premium at VIX 11 in a realised-vol regime of 9–11 is 0–2 vol
points, worth perhaps 5–10% of the premium: **1.0–2.3 bps of notional per week, or 0.5–1.2%/yr
gross.** Round-trip friction is 1.02% of premium = 0.77 bps of notional per week = **0.40%/yr** —
*the same order of magnitude as the entire premium being harvested.*

And the tail. A 4σ weekly move is 6.1% = 1,456 Nifty points. Loss on a short straddle net of premium
= 1,276 points × 65 = **₹82,940 = 1.66% of ₹50 lakh, from one lot, in one week.**

Three independent kills:

1. **Economics.** Friction ≈ gross VRP at VIX 11.
2. **Measurability.** The current regime — one weekly per exchange (Nov 2024), Tuesday expiry
   (Sep 2025), January 2026 lot sizes, April 2026 STT, August 2026 CAS — is under 6 months old.
   MDE_ann at σ = 8% and T = 0.43 yr is **>30%/yr** against a hypothesised 0.5–1.2%. There is no
   sample.
3. **Counterparty.** SEBI's study released 20 August 2026: in FY26, **87.7% of individual equity
   derivatives traders lost money**; aggregate net loss **₹91,685 crore** (FY25: ₹1,11,788 crore);
   **options were 92% of aggregate losses**; average loss among losers ₹1.47 lakh against average
   profit among winners ₹1.22 lakh; **transaction costs alone were ₹25,000 crore** in FY26 and
   ~₹1 lakh crore cumulatively over FY22–FY26. Active individuals fell 18% to ~78.6 lakh, new
   entrants fell 40%, exits rose 76%.

Read the third one carefully, because it is usually misread as an invitation. **A third of the
individual loss is friction paid to the exchange and the exchequer, not to a counterparty.** The
residual is captured by co-located proprietary and FPI algos, not by a one-machine desk on a
500 ms API. And the pool is draining — index options premium ADTO fell 20% MoM in August 2026 to
₹53,900 crore, the lowest since February 2025, with contracts traded down 30%. This is a negative-sum
game with a shrinking loser pool and a rising toll.

**Re-open condition, stated once so it cannot be negotiated later:** India VIX 30-day median
sustained above **18** for a full quarter, **and** a defined-risk structure whose maximum loss per
lot is under 2% of equity, **and** at least 12 months of history under a stable STT / expiry / lot
regime, **and** after-cost expectancy clearing H3.

### 2.5 Why MTF is closed on one line of arithmetic

Dhan's MTF slab is 12.49% p.a. up to ₹5 lakh funded, 13.49% to ₹10 lakh, 14.49% to ₹25 lakh, 15.49%
above. The Nifty's 12-month forward earnings yield at P/E 18.4× is **5.4%**; long-run Nifty 50 TRI is
~11–12%. Borrowing at 12.5–15.5% to hold an asset with an 11% expected return is negative carry
before any drawdown, and the interest is deductible only against business income, not against the
capital gains the position generates. **A leveraged long is a fee paid to be more wrong.**

---

## 3. Tax and economics that actually exist in India

### 3.1 The regime in force

The **Income-tax Act, 2025** replaced the 1961 Act on **1 April 2026**, replacing the
Financial Year / Assessment Year pair with a single **Tax Year**. Tax Year 2026-27 runs
1 April 2026 – 31 March 2027. Substance for a trading book is unchanged; numbering is not:

| Old | New | Content |
|---|---|---|
| s.111A | **s.196** | STCG on listed equity / equity-oriented funds, 20% |
| s.112A | **s.198** | LTCG on the same, 12.5% above ₹1.25 lakh |
| s.112 | s.197 | LTCG on other assets, 12.5% |
| s.43(5) | **s.66** | Definition of speculative transaction, with the recognised-exchange F&O exception |

Budget 2026 (1 February 2026) left capital-gains rates and the ₹1.25 lakh threshold unchanged and
raised only derivative STT.

### 3.2 Rates that apply to this desk

| Item | Rate | Notes |
|---|---|---|
| LTCG, listed equity / ETF, > 12 months | 12.5% above ₹1.25 lakh aggregate; **13.0%** with 4% cess | No indexation. Surcharge on capital gains capped at 15%, so the top-bracket effective rate is ~14.95%. |
| STCG, listed equity / ETF, ≤ 12 months | 20%; **20.8%** with cess | **No exemption threshold — taxable from the first rupee.** |
| Intraday equity | Slab; up to **31.2%** | Speculative business. Loss offsets only speculative income; 4-year carry. |
| F&O | Slab; up to **31.2%** | Non-speculative business. Loss offsets any head except salary; 8-year carry. |
| Dividend | Slab | Taxable in the shareholder's hands since FY21; 10% TDS above ₹10,000 per company per year **(working)**. |
| Buyback proceeds | Slab, as deemed dividend, with full cost allowed as a capital loss **(working)** | Finance (No.2) Act 2024, effective 1 Oct 2024 — the change that removed Indian buyback arbitrage. |

### 3.3 The three tax rules that shape the platform's code

1. **STT is deductible as a business expense against business income (intraday, F&O). It is not
   deductible against capital gains.** So the *effective* cost of an identical trade differs by
   classification, and `costs` cannot price a trade without knowing which book it belongs to.
2. **Speculative and non-speculative are separate businesses.** Intraday equity P&L must be computed
   and carried separately from F&O P&L, with separate carry-forward clocks (4 versus 8 years). A
   single blended "trading P&L" is a filing error waiting to happen.
3. **Turnover for audit purposes is the absolute sum of profits and losses**, not net profit
   (plus premium on options sold, per ICAI guidance **(working)**). A book that nets to zero can
   still generate a turnover that triggers audit.

### 3.4 Compliance surface

ITR-3 (or ITR-4 under presumptive s.44AD, up to ₹3 crore of digital turnover). Books of account
under s.44AA. Tax audit under s.44AB at ₹1 crore of turnover, extended to ₹10 crore where at least
95% of receipts and payments are digital — which they are, for a broker-settled book. Advance tax in
four instalments. Filing due 31 August (no audit) or 31 October (audit); **missing the deadline
permanently forfeits that year's loss carry-forward.** For a desk that expects negative years, the
carry-forward is a real asset and the filing date is a hard operational deadline, not an
accountant's problem.

### 3.5 What ELSS, NPS and the rest can and cannot do

They can defer or reduce tax on *savings*. They cannot host a *book*. None of them permits
self-directed security selection, order entry or an API. Under the new default regime there is no
80C or 80CCD(1B) deduction at all, so even the token benefit is gone for most taxpayers. **There is
no Indian analogue of trading inside a Roth IRA, and any design that assumes one is wrong.** The
practical implication is that the only tax planning available to this desk is holding period,
classification, realisation timing and the ₹1.25 lakh annual exemption — which is exactly what
Book L is.

---

## 4. Friction — the real Indian cost stack

Every component below lives in `src/costs.py`. No book computes its own cost.

### 4.1 Statutory schedule, effective 1 April 2026

| Levy | Delivery | Intraday | Futures | Options |
|---|---|---|---|---|
| STT | 0.10% buy + 0.10% sell | 0.025% sell | **0.05% sell** | **0.15% of premium, sell**; **0.15% of intrinsic on exercise, buyer** |
| STT, equity-oriented fund units | **0.001% sell only** | — | — | — |
| Stamp duty (buyer) | 0.015% | 0.003% | 0.002% | 0.003% |
| Exchange transaction, NSE | 0.00297–0.00307% | same | 0.00173–0.00183% | 0.03503–0.03553% of premium |
| Exchange transaction, BSE | 0.00375% | same | **0** | 0.0325% of premium |
| SEBI turnover fee | 0.0001% (₹10/crore) both sides | same | same | same |
| IPFT | 0.0001% | 0.0001% | 0.0005% | 0.0005% |
| GST | 18% on (brokerage + exchange + SEBI) | same | same | same |

### 4.2 Broker card (Zerodha class; Dhan / Groww / Upstox / Angel comparable)

| Item | Charge |
|---|---|
| Equity delivery brokerage | **₹0** |
| Equity intraday / futures | 0.03% or ₹20 per executed order, whichever is lower |
| Options | flat ₹20 per executed order |
| DP charge, delivery sell | **₹15.34 per ISIN per day** (₹3.50 CDSL + ₹9.50 broker + ₹2.34 GST); not on buys, intraday or F&O |
| Demat AMC | ~₹300 + GST per year |
| Kite Connect API | **₹500/month per key**, includes live WebSocket and historical candles |
| Dhan trading API / data API | **₹0 / ₹499/month** (5 years history, option chain, 20-level depth) |
| Fyers / Angel SmartAPI / Upstox | **₹0** for trading and market data |

Note the **₹20-per-order floor**: it makes small clips uneconomic and makes cost per basis point
depend on clip size. Intraday round trip is 8.3 bps at ₹1 lakh clips but 4.5 bps at ₹5 lakh clips.
`costs` must model the floor, not an average.

### 4.3 Spread and impact by segment

NSE publishes a monthly impact-cost file per security — the same input NSE uses for Nifty 50
eligibility (impact cost ≤ 0.50% for 90% of observations on a ₹10 crore portfolio). Working figures
for a ₹1 lakh order, to be replaced with the actual file at U0:

| Segment | Typical impact cost, one side **(working)** | Tradability |
|---|---|---|
| Nifty 50 | 2–6 bps | Clean |
| Nifty Next 50 / Nifty 100 | 5–10 bps | Clean |
| Nifty Midcap 150 | 8–20 bps | Usable; the binding cost, not liquidity |
| Nifty Smallcap 250 | 30–150 bps | **Closed** — plus ESM/GSM band and call-auction risk |
| Non-index / illiquid F&O stocks | 20–100+ bps in cash; 5–20% of premium in options | **Closed** |
| NIFTYBEES | ~11 bps quoted spread; ~5.5 bps half-spread | Clean |

### 4.4 Assignment and delivery risk

Index derivatives are cash-settled. All single-stock derivatives are physically settled, with the
margin ramp of §1.8 and forced square-off at 12:00 / 14:30 on expiry day if margin is short. **The
platform never holds a single-stock derivative, so this risk is designed out rather than managed** —
which is the correct answer at ₹50 lakh, where one stock-futures lot can be 30–50% of the book.

---

## 5. Inference — n, σ, MDE, and the gate

You cannot claim an edge you cannot measure. Every book publishes n, σ and MDE **before the first
peek**, in a pre-registration file, and gets a budget of **5 specifications**. After the fifth, the
book closes regardless of result.

> **MDE_ann = (z₁₋α/₂ + z₁₋β) × σ_ann / √T = 2.80 × σ_ann / √T**, at α = 0.05 two-sided, 80% power.
>
> **Gate (H4): MDE_ann ≤ ½ × E_net**, where E_net is the pre-registered after-cost, after-tax annual
> effect against the Nifty 50 TRI benchmark.

σ_ann is the annualised standard deviation of the **sleeve's return against the benchmark**, not of
the academic effect. This matters: the existence of an anomaly in the Indian literature is not the
question. The question is whether a retail-implementable, cost-and-tax-bearing sleeve can be shown
to clear H2. That test's unit is the sleeve-year, and sleeve-years are scarce.

### 5.1 The table that decides the desk

| Book / phenomenon | Indian book shape | σ_ann active | T usable | **MDE_ann** | E_net hypothesised | ½ E_net | Verdict |
|---|---|---|---|---|---|---|---|
| **L — holding-period and cost ledger** | Realisation schedule on the core | — | — | **n/a — arithmetic** | 95–130 bps | — | **OPEN** |
| **P — packaged versus self-run factor** | Published TRI + TER + tax comparison | — | 20 yr index TRI | **n/a — deterministic** | 30–150 bps of decision value | — | **OPEN** |
| B — SLBM lending yield on the core | Lending fee on held Nifty 50 names | 0.5% | 5 yr SLB bhavcopy | **0.63%** | 25–60 bps | 12–30 bps | **MARGINAL — ₹0 screen decides** |
| M — self-run momentum, Nifty 200 | 12-month formation, 12-month hold, annual | 8% | 20 yr | **5.01%** | 2.0% | 1.0% | **FAILS 5.0×** |
| R — results-season drift, Nifty 200 | Quarterly SUE, 3-month hold, long-only | 10% | 15 yr | **7.23%** | 1.9% | 0.95% | **FAILS 7.6×** |
| A — CAS closing-auction dislocation | Session-level, auction versus reference | 3.9% | **0.09 yr** | **36.4%** | 1.5% | 0.75% | **FAILS — dated re-open** |
| Index option premium sale | Nifty weekly, defined or naked | 8% | 0.43 yr | **>30%** | 0.5–1.2% | 0.25–0.6% | **FAILS ≥50×** |
| Index reconstitution / passive flow | ~2 rebalances/yr, event sleeve | 4%/event | 40 events | **1.77%/event ≈ 3.5%/yr** | 0.4% | 0.2% | **FAILS 8.9×** |
| Budget / RBI event day | 1 Budget + 6 MPC per year | 1.5%/event | 140 events | **0.35%/event ≈ 2.5%/yr** | unknown | — | **CLOSED — no admissible signal** |

Read the last row carefully. Budget and MPC days are the *only* phenomenon whose MDE arithmetic is
comfortable, because n is the number of events and events are plentiful. It is closed anyway, because
trading it requires a **directional forecast**, and this desk's AI rule forbids any model output
entering a size. Closed on absence of an admissible signal, not on measurability. That is the honest
distinction and it should be preserved in the STOP memo.

### 5.2 What it would take to re-open a predictive book

Solve the gate for the required gross effect. With T = 15 years and a delivery sleeve paying ~90 bps
of friction at four turns a year and 20.8% STCG on the gross:

> 0.723 σ ≤ 0.396 g − 0.45   ⟹   at σ = 6%, **g ≥ 12.1%/yr gross**

A 12%/yr gross alpha in the Nifty 200 from a publicly documented anomaly is not a credible claim.
The two ways to make the gate reachable are both structural, not statistical:

1. **Cut σ.** More names, longer holds, tighter benchmark. A sleeve with σ ≤ 2.6% against the Nifty
   is nearly the Nifty — which is the point: as you cut σ to make the effect measurable, you cut the
   effect.
2. **Raise T.** Only time does this. Book A's MDE falls from 36.4% today to 10.9% after one year of
   post-CAS data and **2.44% after twenty** — which is why it is deferred to a date rather than
   argued about.

**The conclusion is the design.** Every statistical alpha available to Indian retail at ₹25 lakh–₹1
crore on free data fails H4. The books that pass are the ones with no inference in them. This is not
pessimism; it is the reason Books L and P rank first and second, and the reason this platform is
allocation, execution and tax software rather than a signal factory.

---

## 6. Capacity at ₹25 lakh – ₹1 crore

**Envelope: ₹25 lakh – ₹1 crore. Design point: ₹50 lakh** (~US$5,300 at FBIL USD/INR 94.47 on 3 Sep 2026).
All lot and margin arithmetic in this document is at ₹50 lakh and must stay consistent.
Limits as numbers the code will assert: [p0-posture.md](p0-posture.md).

Why the floor is ₹25 lakh:

- One Nifty futures lot is ₹15.52 lakh notional — 62% of a ₹25 lakh book. Below ₹25 lakh, any
  derivative overlay is indivisible.
- The ₹15.34 DP charge is 3.8 bps on a ₹40,000 position but 0.8 bps on a ₹2 lakh position. A
  multi-name delivery book below ₹25 lakh is fee-dominated.
- The ₹20-per-order brokerage floor makes clips below ~₹67,000 pay more than 0.03%.

Why the ceiling is ₹1 crore:

- The ₹1.25 lakh LTCG exemption decays as 1/capital (§0.1). Book L's edge halves from 65 bps to 16
  bps across the envelope.
- Above ~₹1 crore, the Nifty Midcap 150 sleeve's impact cost starts to bite and the single-broker,
  single-machine operational posture stops being proportionate to the money at risk.
- The tax and compliance surface (books, advance tax, s.44AB audit, possible s.44AD ineligibility)
  grows faster than the edge.

### 6.1 Risk limits at 4/5 — moderately aggressive, stated as numbers

| Limit | Value | Rationale |
|---|---|---|
| Gross exposure | ≤ 100% of equity | No leverage. MTF closed (§2.5). |
| Active / factor sleeve | ≤ 40% of equity | The 4/5 expression: meaningful active risk, taken through a vehicle whose selection is defensible. |
| Single name | ≤ 6% of equity (₹3 lakh at ₹50 lakh) | Keeps impact inside 10% of a Nifty 200 name's 20-day median **delivery** value. |
| Single sector | ≤ 25% of equity | Indian index concentration in financials makes this bind, not decorate. |
| Naked short options | **Zero, always** | §2.4. |
| Single-stock derivatives | **Zero, always** | §1.8, §2. |
| Loss from one 4σ overnight gap on any single position | ≤ 2% of equity | Closes 1-lot short-straddle sizing at ₹50 lakh (1.66%) as marginal and 2 lots (3.3%) as prohibited. |
| Index-futures overlay | ≤ 1 lot per ₹50 lakh, monthly cadence at most | §2.3. |
| Order rate | ≤ 10 orders/second (TOPS) | Keeps the desk out of client-level algo registration. |
| Annual STOP | After-tax return trails Nifty 50 TRI by > 600 bps in a tax year | Whole-desk kill, not a book kill. |

Capacity headroom at these limits is roughly 100× on liquidity and ~10× on impact cost. **Capacity
is slack; do not spend it on turnover.**

---

## 7. Alpha last — Indian phenomena versus retail viability

| Phenomenon | Indian evidence | Retail-viable after cost and tax? | Verdict |
|---|---|---|---|
| **Equity premium (Nifty 50 TRI)** | Structural DII/SIP bid: DII inflow US$59.8bn CY26 YTD against FII outflow US$24.1bn. Packaged at 0.03–0.04% TER. | Yes — **it is the hurdle, not a book** | **VIABLE** |
| **Holding-period / STT arithmetic** | Statute: s.196 20.8%, s.198 13.0% above ₹1.25 lakh, s.66 31.2%; STT 0.10% versus 0.001% on ETF units | Yes, ~95–130 bps/yr, zero research risk | **VIABLE — Book L** |
| **Momentum in NSE** | Sehgal & Balakrishnan (2008); Sehgal & Jain (2011, 2015); combined relative + absolute strength outperforms price momentum and is unexplained by CAPM/FF3, attributed to investor overreaction (*IJoEM*, 2024). Counter-evidence: Bhattacharya et al., *Global Business Review* (2019), find value and momentum explained by risk models 2005–2016 and size/volume anomalies fading. | **Already packaged.** Nifty 200 Momentum 30 / Nifty 500 Momentum 50 index funds and ETFs at **0.30–0.34% TER** (direct/ETF; regular plans 0.93–1.87%) rebalance internally with **no investor-level realisation**. A self-run replication pays 23.8 bps per turn and 20.8% STCG. | **CANDIDATE-GATE — Book P decides; self-run (Book M) already fails H4 5.0×** |
| **Results-season drift (PEAD in India)** | *Theoretical Economics Letters* (2018): Nifty 500, 2002–2017, statistically significant 64-day drift, robust to beta, market cap, P/B, illiquidity and idiosyncratic volatility, and to sub-periods. | Existence is not the issue. The implementable sleeve's MDE is 7.23%/yr against ½ × 1.9%. And there is **no free Indian PIT consensus dataset**, so surprise must be seasonal-random-walk SUE from exchange filings. | **CLOSED at H0 — Book R** |
| **FII / DII daily flow** | NSE publishes provisional cash FII/DII at ~17:30–18:00 IST | The number describes a session that has already closed and is later revised. It is tradeable only overnight, and overnight delivery friction is 23.8 bps against any plausible one-day flow effect. | **CLOSED — cost and timing** |
| **Expiry-day effects** | Nifty (Tue, NSE) and Sensex (Thu, BSE) only | Two venues, maximum crowding, highest-STT product, sub-second edge decay against co-located algos, and CAS has just destabilised the closing print expiry settlement depends on. | **CLOSED** |
| **Ban-period / MWPL dislocation** | Delta-based FutEq from 8 Dec 2025, intraday random checks, ban list published pre-open, 1% / ₹5,000–₹1,00,000 daily penalties | The dislocation is real but lives entirely in single-stock F&O — physically settled, monthly-only, with a universe that changes quarterly. | **CLOSED** |
| **Budget / RBI policy days** | 1 Budget + 6 MPC per year; n = 140 over 20 years; MDE ≈ 2.5%/yr — the only comfortable MDE on this list | Requires a **directional forecast**. No model output may enter a size. | **CLOSED — no admissible signal** |
| **Midcap illiquidity premium** | Nifty Midcap 100 +2.1% MoM and Smallcap 100 +3.1% MoM to all-time highs while Nifty 50 is **−7.8% CY26 YTD** | Smallcap is closed by ESM/GSM (Stage II = ±2% periodic call auction, 100% margin, trade-for-trade). Midcap is permitted only inside the Nifty 200 core weight. The premium is currently being **paid out**, not earned. | **CLOSED at smallcap; core-weight only in midcap** |
| **Retail F&O as risk transfer** | SEBI, 20 Aug 2026: 87.7% of individuals lost in FY26; ₹91,685 crore aggregate; options 92% of losses; **₹25,000 crore of it was transaction costs**; active traders −18%, new entrants −40%, exits +76% | The most seductive Indian thesis and the most clearly false for this desk. A third of the loss is toll, not transfer; the residual accrues to co-located prop and FPI algos; and the pool is draining (index options premium ADTO −20% MoM to a 19-month low). Negative-sum with a rising toll. | **CLOSED** |
| **Index reconstitution / passive flow** | Passive AUM is *growing* in India: NIFTYBEES ₹66,777 crore, SBI Nifty 50 ETF ~₹2.16 lakh crore **(working)**; the flow now prints inside CAS | Effective n ≈ 40 rebalances. MDE 1.77%/event against ~0.4%/yr net. | **CANDIDATE-GATE, lowest rank; ₹0 screen only** |
| **CAS closing-auction dislocation** | Live 3 Aug 2026; pool ~1% of cash ADTO; documented end-of-day volatility; SEBI reforming SLBM specifically to deepen it | Genuinely new and genuinely un-crowded — and one month old. MDE 36.4% today, 10.9% at T=1, 2.44% at T=20. | **DEFERRED to a date — Book A, review 2027-08-31** |
| **Dividend / record-date capture** | Dividends slab-taxed in the shareholder's hands since FY21; 10% TDS above ₹10,000 per company **(working)** | Converts a 13.0%-LTCG asset into 31.2% slab income. Anti-edge. | **CLOSED** |
| **Buyback / open-offer arbitrage** | Buyback proceeds taxed as deemed dividend at slab from 1 Oct 2024, with cost allowed as a capital loss **(working)** | The arithmetic that made this work was deliberately removed by statute. | **CLOSED** |
| **SLBM lending yield** | ₹697 crore market-wide FY26 fee pool; R3 3-day series from 17 Aug 2026; SEBI reform consultation imminent | Free money on shares already held, *if* the fee clears friction. But the rules change within months. | **CANDIDATE-GATE — deferred, Book B** |

---

## 8. Candidate books, ranked by after-cost after-tax contribution per unit of research risk

### Book L (rank 1) — Holding-period, classification and cost ledger

| | |
|---|---|
| **Hypothesis** | For a retail Indian book, the largest reliably capturable after-tax gain is not an alpha but the difference between a naive and an optimal *realisation schedule*: crossing the 12-month line converts 20.8% to 13.0%; the ₹1.25 lakh s.198 exemption is use-it-or-lose-it each tax year; rebalancing through a 0.001%-STT ETF instead of 0.10%-STT constituents saves ~20 bps per turn; and speculative and non-speculative businesses must never be blended. |
| **Instrument** | NIFTYBEES / ICICI or Kotak Nifty 50 ETF / a direct Nifty 50 index fund, plus the delivery leg of every other book |
| **Horizon** | 12 months and longer, by construction |
| **Effect size** | **95–130 bps/yr at ₹50 lakh.** At 60%/yr turnover on a ₹50 lakh core at 11% gross: tax delta ₹41,990 (84 bps) + ETF-versus-constituent rebalancing saving ₹5,970 (12 bps) = 96 bps. At full annual realisation the tax delta alone is ₹59,150 = 118 bps. |
| **Why 2026** | The Income-tax Act 2025 came into force on 1 April 2026 with new section numbers; Budget 2026 raised derivative STT but left delivery, intraday and ETF-unit STT untouched, *widening* the ETF advantage; and the CAS regime moved the closing price of every F&O-eligible name, which changes where a rebalance order should be sent. |
| **Packaged?** | **Partly, and this must be said honestly.** A Nifty 50 index fund already defers all internal-rebalance tax to redemption, so it beats a self-managed 50-stock replication on tax without any work. Book L's *incremental* value is therefore over the realisation schedule of the **active sleeves** and the ETF-versus-index-fund choice for the core — not over a buy-and-hold index fund, which it partly recommends. |
| **Kill** | If `costs` + `tax` cannot reproduce a real broker contract note to **₹1** and a hand-worked Tax Year 2026-27 computation to **₹1** (H1), the book fails and so does the platform. If the measured schedule delta at ₹50 lakh is under **50 bps/yr**, close it and run a plain index fund. |
| **AI role** | **None.** |

### Book P (rank 2) — Packaged versus self-run, on Indian factor indices

| | |
|---|---|
| **Hypothesis** | For every documented Indian factor (momentum, low volatility, alpha, quality), a packaged index fund or ETF that bears turnover internally and defers the investor's tax event to redemption dominates a self-run replication that pays 23.8 bps per turn and 20.8% STCG — and the crossover is computable from published TRI, TER and exit-load data without any alpha claim. |
| **Instrument** | Nifty 200 Momentum 30 and Nifty 500 Momentum 50 index funds and ETFs (Motilal Oswal ETF **0.30%**, Motilal direct index fund **0.34%**, UTI / Axis / Bandhan direct ~0.3–0.5%; regular plans 0.93–1.87% and therefore excluded), Nifty 100 Low Volatility 30, Nifty Alpha 50; against a self-run Nifty 200 replication |
| **Horizon** | The comparison is over 20 years of published TRI; the resulting sleeve is held with annual or semi-annual rebalancing |
| **Effect size** | **30–150 bps/yr of decision value.** Sensitivity is entirely in the tax term: a self-run sleeve at 30%/yr turnover pays roughly 0.30 × 20.8% × gross in annual tax that the packaged vehicle defers. Against that, the packaged vehicle costs 30 bps of TER, plus a 1% exit load inside 15 days on some schemes. |
| **Why 2026** | Direct-plan factor TERs have compressed to 0.30–0.34%, and the Nifty 200 Momentum 30 TRI has just had a poor run (one representative direct plan showed −3.81% over one year to June 2026 against 13.42% over three years). The question is live, not rhetorical — and answering it costs ₹0. |
| **Packaged?** | That is the question. The expected verdict is **"buy the fund"**, and if so **that is a completed milestone**, not a failure: it closes Book M, retires a whole line of research, and frees the 40% active sleeve to be allocated defensibly. |
| **Kill** | If the packaged vehicle beats self-run by more than **100 bps/yr** after all cost and tax, Book M closes permanently and the sleeve is implemented in the fund. If self-run wins by more than 100 bps, Book M opens with its own pre-registration — but note it must still clear H4, which it currently fails 5.0×. If the two are within ±100 bps, buy the fund, because it carries no operational risk. |
| **AI role** | **None.** |

### Book B (rank 3) — SLBM lending yield on the existing core

| | |
|---|---|
| **Hypothesis** | Shares already held in the core can be lent through SLBM for a fee that exceeds its friction, without changing market exposure. |
| **Instrument** | SLBM R1/R3 series on F&O-eligible Nifty 50 and Nifty 200 constituents already held |
| **Horizon** | 3 days (R3) to one month (R1) |
| **Effect size** | Unknown; the ₹0 screen measures it. Market-wide fee pool was ₹697 crore in FY26 against ₹425 crore in FY25 and ₹346 crore in Q1 FY27 alone. |
| **Why 2026** | The R3 three-day series launched 17 August 2026; SEBI's chairman has said a reformed-SLBM consultation paper is imminent, covering universe expansion, net settlement and inter-exchange interoperability. |
| **Packaged?** | No retail-accessible packaged equivalent. |
| **Kill** | **Close if the median annualised lending fee on the desk's actual Nifty 50 / Nifty 200 holdings, measured from the free NSE SLB bhavcopy over 5 years, is under 25 bps.** Also close if the tax treatment of the lending fee cannot be settled in writing with a CA before any lending is done. Do not open before SEBI's reformed-SLBM circular is published — the R3 series has no repay, recall or rollover, so a lent share is genuinely locked. |
| **AI role** | **None.** |

### Book A (rank 4) — CAS closing-auction dislocation. Deferred to a date.

| | |
|---|---|
| **Hypothesis** | The auction-determined close for CAS-eligible stocks, formed in a pool ~1% of cash-market ADTO, is a noisier estimate of fair value than the 30-minute VWAP close it replaced, so the auction price relative to the 15:15 reference price has a mean-reverting component that did not exist before 3 August 2026. |
| **Instrument** | Cash delivery in Nifty 50 / Nifty 200 CAS-eligible names, entered in the 15:20–15:25 auction phase |
| **Horizon** | One session |
| **Effect size** | Hypothesised 1.5%/yr net **(working)** |
| **Why 2026** | Genuinely new microstructure in the single most important price of the day, in the world's largest equity derivatives market, with documented shallow pools and end-of-day volatility, and a regulator publicly committed to keeping it while reforming SLBM to deepen it. Nobody has 20 years of this. |
| **Packaged?** | No. |
| **Kill** | **Not open, and not to be opened before 2027-08-31.** MDE today is 36.4%/yr; at T = 1 year it is 10.9%; only at T ≈ 20 years does it reach 2.44% and clear the gate against a 1.5% effect. Any earlier opening is a peek. Review date is a hard calendar item in `ops`, not a judgement call. |
| **AI role** | **None.** |

### Book M (rank 5) — Self-run momentum, Nifty 200. Fails H4; gated behind Book P.

Hypothesis: a 12-month-formation, 12-month-minimum-hold, long-only Nifty 200 momentum sleeve,
rebalanced annually so that most exits land past the 12-month line, clears H2 net of 23.8 bps per
turn and 13.0% LTCG. Effect size hypothesised 2.0%/yr net; σ 8%; T 20 years; **MDE 5.01%/yr — fails
H4 by 5.0×.** It stays on the list only because Book P might return "self-run wins by >100 bps", in
which case the book gets one pre-registration and five specs, and the H4 failure is recorded in its
STOP memo as the expected outcome. `ai.extract` role: none.

### Book R (rank 6) — Results-season drift, Nifty 200. Closed at H0.

Hypothesis: quarterly seasonal-random-walk SUE from exchange-filed results predicts a 3-month drift
in Nifty 200 names, per the *Theoretical Economics Letters* (2018) Nifty 500 result. Effect
hypothesised 1.9%/yr net; σ 10%; T 15 years; **MDE 7.23%/yr — fails H4 by 7.6×.**

This is the book with a real AI job, and it is worth recording why even so it closes. India has **no
free point-in-time consensus estimate dataset**, so surprise must be computed from filed numbers,
and Indian quarterly results arrive as non-standard PDFs on the NSE and BSE filing portals.
Extracting consolidated versus standalone PAT, EPS, exceptional items and segment lines from those
PDFs is exactly a text-extraction job — `ai.extract`'s only legitimate purpose on this desk. But an
extraction module cannot rescue a book whose implementable MDE is four times its hypothesised gross
effect. **Closed at H0, before any peek**, with the STOP memo recording that the anomaly's existence
in the literature is not in dispute and its retail implementability is.

### Explicitly closed — do not revisit without the named Indian change

| Closed | Named Indian reason | What would re-open it |
|---|---|---|
| Index option premium selling, weekly or monthly | Friction ≈ VRP at India VIX 10.97; 0.15% premium STT since 1 Apr 2026; T < 6 months of the current regime; SEBI FY26 evidence of a draining negative-sum pool | India VIX 30-day median > 18 for a quarter **and** defined risk under 2% of equity per lot **and** T ≥ 1 year of a stable regime |
| Expiry-day anything | Two venues (Nifty Tue, Sensex Thu); sub-second decay against co-located algos; CAS destabilised the settlement print | Nothing within this desk's latency budget |
| Single-stock futures and options | Compulsory physical settlement; delivery-margin ramp to 100%; delta-based FutEq ban period with ₹5,000–₹1,00,000/day penalties; quarterly MWPL universe churn; one lot = 30–50% of the book | Cash settlement for single-stock derivatives, which SEBI has shown no sign of restoring |
| Cash equity intraday (MIS) | 8.3 bps round trip at ₹1 lakh clips; **speculative** income at 31.2% with 4-year ring-fenced carry; ~5× peak-margin ceiling | A material cut to intraday STT and reclassification out of s.66 speculative — neither proposed |
| Overnight close-to-open on delivery | 23.8 bps delivery round trip against a 5–15 bps overnight effect | Nothing |
| MTF leverage | 12.49–15.49% p.a. against a 5.4% forward earnings yield and ~11% expected return; interest not deductible against capital gains | MTF rates below ~8% |
| Nifty Smallcap 250 systematic | ESM Stage II = ±2% periodic call auction, 100% margin, trade-for-trade; 2%/5% bands; 30–150 bps impact | Repeal of ESM/GSM, which would be a policy reversal |
| Bank Nifty / FinNifty / Midcap Select weekly options | **They no longer exist.** Weeklies were cut to one benchmark per exchange from 20 Nov 2024 | A SEBI reversal of the one-weekly-per-exchange rule |
| Calendar-spread / expiry-day margin-benefit trades | Calendar-spread margin benefit is withdrawn on expiry day for contracts expiring that day | Restoration of the benefit |
| SGB | No new tranches since 2024; issuance discontinued; secondary-market maturity exemption withdrawn from 1 Apr 2026 **(working)**; thin discounted secondary | New issuance |
| Dividend capture, buyback arbitrage | Both converted to slab income by statute (FY21 and 1 Oct 2024 respectively) | Statutory reversal |
| Currency and commodity derivatives | Out of charter | Charter change |

---

## 9. Platform architecture — production-grade, staged

### 9.1 What v1 is

**One machine. One broker. One run per session, at ~16:15 IST**, after the post-close session settles
and the official CAS closes exist. The run emits an **instruction list** — a human-readable file of
intended orders with sizes, limits and reasons — which is placed the next morning against the
09:00–09:15 pre-open and the early continuous session. The following morning at 09:00, before the
pre-open, `ops` reconciles the previous day's fills against the **broker ledger and contract note**
to ₹1 and refuses to emit new instructions if the reconciliation fails.

Cadence is set by what the books need, not by what the market permits: Book L rebalances the core
quarterly and schedules realisations against the 12-month and 31-March boundaries; Book P re-decides
annually; Book B, if opened, acts on the SLB cycle. **Nothing in this desk needs an intraday loop**,
and that is a design result, not a limitation.

### 9.2 Modules

| Module | Owns | First needed at |
|---|---|---|
| `src/costs.py` | Every levy in §4: STT by instrument and side, stamp, exchange transaction by venue, SEBI turnover fee, IPFT, GST base, brokerage with the ₹20 floor, DP per ISIN per day, exercise-STT-versus-square-off comparison, impact cost from the NSE monthly file | **P0** |
| `src/tax.py` | s.196 / s.198 / s.66; ₹1.25 lakh aggregate exemption; slab + surcharge + 4% cess; speculative versus non-speculative separation; 4-year and 8-year carry clocks; absolute-sum turnover for audit; Tax Year boundaries | **P0** |
| `src/universe.py` | Nifty 50 / Next 50 / 100 / 200 / Midcap 150 membership *as of a date*; F&O eligibility and CAS eligibility flags; ESM/GSM stage; ban-list state; price-band state | **U0** |
| `src/panel.py` | Daily PIT panel from NSE and BSE UDiFF bhavcopy; corporate-action spine (bonus, split, rights, demerger, amalgamation, delisting, ISIN change); delivery volume; `close_method` column | **U0** |
| `src/harness.py` | Pre-registration files; MDE computation; the 5-spec counter; date-shift test for look-ahead; benchmark construction | **H0** |
| `src/portfolio.py` | Weights subject to §6.1 limits; the realisation scheduler (Book L); margin sizing from the broker endpoint + 25% buffer | **L1** |
| `src/execute.py` | Instruction-list generation; order placement under 10 OPS with the exchange algo ID; pre-open phase-1/phase-2 order-type rules; CAS-phase order rules | **L0** |
| `src/ops.py` | Broker-ledger and contract-note reconciliation to ₹1; the run log; calendar (Indian holidays, expiry Tuesdays, results season, Budget, MPC, Book A's 2027-08-31 review); kill-switch state | **L0** |
| `src/books/*.py` | One module per open book. A closed book's module is deleted and its STOP memo archived. | per book |
| `src/ai/extract.py` | **Only if Book R ever opens.** Parses Indian quarterly results PDFs and XBRL into typed fields with a per-field confidence and a source page. | not in v1 |

### 9.3 Data — buy nothing at P0

**Free, and sufficient through H0 and every ₹0 screen:**

| Source | What |
|---|---|
| NSE `all-reports` | **CM-UDiFF Common Bhavcopy Final (zip)** — the legacy CSV bhavcopy was discontinued 8 July 2024 per NSE circular 62424; F&O UDiFF bhavcopy; security-wise delivery position; VaR margin rate files; daily volatility; **monthly impact cost**; MTF category-wise turnover; short-selling; **SLBS bhavcopy**; F&O ban list; price-band change circulars |
| NSE / BSE corporate filings | Quarterly results, corporate actions (bonus, split, demerger, delisting), index reconstitution press releases — the PIT spine |
| BSE | Bhavcopy, notices, circulars |
| NSE Indices | Nifty 50 / 200 / factor-index TRI history, constituents, P/E, P/B, dividend yield |
| SEBI | Circulars; the FY25–FY26 derivatives profitability study |
| AMFI | Daily NAV, monthly AAUM, scheme TERs — the packaged competitor's real cost for Book P |
| RBI DBIE | 91-day T-bill (risk-free rate), CPI, USD/INR |

Access discipline, because it is load-bearing: `nseindia.com` applies anti-bot controls. The correct
pattern is a session-cookie warm-up, a browser user-agent, **no more than one request every two
seconds**, retry with exponential backoff, a **content-addressed local cache so any given day is
fetched exactly once, ever**, and **no fetching during market hours**. A polite, cached, once-a-day
fetcher is the difference between a working ₹0 data pipeline and an IP block.

**Paid, with working prices, and the milestone that may buy it:**

| Vendor / SKU | Price **(working)** | May be bought at |
|---|---|---|
| Kite Connect (Zerodha) | **₹500/month per key**; includes live WebSocket and historical candles; 1 quote/s, 3 historical/s, 10 orders/s, 200 orders/min | **L0**, for execution and reconciliation only |
| Dhan Data API | **₹499/month**; trading API free; 5 years history, option chain, 20-level depth | **L0**, as the alternative to Kite |
| Fyers / Angel SmartAPI / Upstox | **₹0** | Anytime; preferred if the free tier meets L0 |
| TrueData | **₹1,440–₹2,796/month** by segment bundle | Only if a specific book's exit criterion names minute bars, capped at 3 months |
| Global Datafeeds NimbleDataPro | from **~₹225 per exchange/month** | Same gate as TrueData |
| NSE Data & Analytics, CMOTS / Accord, LSEG India | Institutional, quote-only | **Outside the envelope. Do not contact.** |

**No paid SKU is purchased before its book has passed a ₹0 public screen and published its MDE.**

### 9.4 Execution posture

- **Order types.** Limit orders only, except inside the CAS 15:20–15:25 window where a market order
  is permitted for a small residual. Never a market order in the pre-open phase 2 (09:05–09:10) —
  it will be rejected.
- **Where a rebalance goes.** Core rebalances route to NIFTYBEES or the index fund, not to
  constituents, on the 20 bps STT arithmetic of §2.2 — unless the quoted ETF spread on the day
  exceeds 20 bps, which `execute` checks before emitting.
- **CAS-eligible names.** Any order referencing the official close for an F&O-eligible name must be
  placed into the auction, not into continuous trading after 15:15, because continuous trading in
  those names has ended.
- **Rate.** Hard cap at 8 orders/second in code, against the 10 OPS TOPS, with the exchange algo ID
  on every order.
- **Session.** Static-IP-whitelisted OAuth with 2FA, daily token renewal treated as an explicit
  workflow step in `ops`, not an exception handler.
- **Fallback.** Every instruction list is human-executable. If the API is down, the desk places the
  same orders by hand. A book that cannot be executed manually is not permitted.

### 9.5 AI layer — jobs, not thesis

| Permitted | Forbidden |
|---|---|
| `ai.extract`: parse Indian quarterly results PDFs / XBRL into typed fields with per-field confidence and source page, gated at ≥ 98% field-level agreement against 200 hand-labelled filings. Only if Book R opens. | **Any model output entering a return forecast, a signal, a weight or a position size.** |
| `ops`: an LLM reads the nightly run log and the reconciliation diff and writes a one-paragraph "what changed, what looks wrong" note for a human. | The same LLM changing a position, cancelling an order or overriding a limit. |
| Nothing else. | HMM, LightGBM, MLflow, Kaggle in `pyproject.toml` at seed. |

### 9.6 Not in v1 — explicit

Redis. Kafka. Kubernetes. Docker orchestration. Tick replay. Order-book reconstruction. A matching
engine. Multi-broker routing. A mobile app. A web dashboard. FIX. Co-location. Any intraday loop.
Any second machine. Polars, until a `panel` milestone actually imports it. Every one of these is a
cost with no counterparty on a desk whose binding constraints are STT and sample size.

---

## 10. Hurdles and STOP language

Benchmark for all hurdles: **Nifty 50 TRI, net of 0.04% TER, taxed at 13.0% on realisation**, on the
same capital and the same cash-flow schedule as the sleeve under test. That is NIFTYBEES, priced
honestly, and it is the thing every book must beat.

| # | Hurdle | Number | STOP |
|---|---|---|---|
| **H1** | Cost and tax fidelity | `costs` reproduces a real broker contract note to **₹1 per trade**, and `tax` reproduces a hand-worked Tax Year 2026-27 computation for a mixed delivery + intraday + F&O book to **₹1**, across cash delivery, ETF delivery, cash intraday, index futures, index options and exercise STT, plus DP charges | If either fails, **the platform stops.** No book proceeds on an unverified cost model. |
| **H2** | After-cost after-tax excess | Any active sleeve must beat the benchmark by **≥ 300 bps/yr** over the full PIT sample. (Justification: ~140 bps of self-inflicted drag on a 100%-turnover delivery sleeve — 23.8 bps friction, ~78 bps tax differential, ~40 bps impact — must be earned back twice over, and 300 bps must exceed the 30–34 bps TER of the packaged competitor by enough to pay for operational risk.) | Below 300 bps, the sleeve closes and its weight goes to the packaged vehicle or the core. |
| **H3** | Risk-adjusted | Active Sharpe versus the benchmark **≥ 0.40** after cost and tax, and **≥ 0.30 in each of two non-overlapping halves** | Fails either leg → close. |
| **H4** | Measurability | **MDE_ann = 2.80 σ/√T ≤ ½ × E_net**, with n, σ, MDE and E_net published in a pre-registration file **before the first peek**. Budget: **5 specifications per book.** | A book whose MDE exceeds half its pre-registered effect **closes at H0, before any data is looked at.** After the fifth spec, the book closes regardless of result. |
| **H5** | Capacity | Clears H2 at ₹50 lakh with impact cost from the NSE monthly file at **6× the actual order size**, and no single order exceeds **10% of the name's 20-day median delivery value** (delivery, not traded — MWPL is now 65× ADDV) | Fails → reduce breadth or close. |
| **H6** | Operability | One machine, one broker, one ~16:15 IST run, **≤ 10 orders/second**, exchange algo ID on every order, reconciled to the broker ledger to ₹1 the next morning before pre-open, with a documented manual fallback | If the loop needs a second machine, a second broker, or intraday supervision, **stop and redesign.** |
| **H7** | Whole-desk | After-tax return trails the Nifty 50 TRI by more than **600 bps in a tax year** | Halt all active sleeves, move to 100% core, and write an X0 review. |

**A negative honest result is a completed milestone.** A STOP memo in `docs/archive/` that says
"Book R closed at H0 because its implementable MDE was 7.23%/yr against a hypothesised 1.9%, here is
the arithmetic" is worth more than a book that trades on an unmeasurable claim. Books close; the
platform continues.

---

## 11. Risks unique to Indian retail algo trading

| Risk | Exposure | Mitigation in this design |
|---|---|---|
| **SEBI algo framework breach** | Framework applicable to all brokers since 1 Apr 2026; untagged automated orders are not permitted; >10 OPS requires per-exchange registration; sharing a strategy outside self/spouse/dependent children/dependent parents is prohibited | Hard 8 OPS cap in code; exchange algo ID asserted on every order or the order is not sent; the desk never becomes an algo provider, RA or PMS |
| **API 2FA / session expiry mid-run** | Static-IP OAuth with daily token renewal; a stale token silently fails an order | Token renewal is an explicit `ops` step with a pre-run assertion; every instruction list is manually executable |
| **Peak margin penalty** | 100% upfront since Sep 2021; four random snapshots; penalty applies even if the position closed intraday; the broker pays and recovers from the client | All sizing from the broker margin endpoint + 25% buffer; no position sized on notional |
| **Ban period / MWPL** | Delta-based FutEq since 8 Dec 2025, checked intraday; 1% / ₹5,000–₹1,00,000 per stock per day | **No single-stock derivatives, ever.** Risk designed out. |
| **Physical settlement surprise** | Delivery-margin ramp to 100%; forced square-off at 12:00 / 14:30 on expiry | Same: no single-stock derivatives. For index options, the exercise-STT-versus-square-off rule in `costs`. |
| **Tax audit on business income** | s.44AB at ₹1 crore / ₹10 crore digital; turnover is the absolute sum of profits and losses; books under s.44AA | Delivery-only design keeps the desk in capital gains, not business income, wherever possible; `tax` computes absolute-sum turnover and flags the audit threshold at every run |
| **Missed filing deadline destroys carry-forward** | 31 Aug / 31 Oct; loss carry-forward is permanently forfeited if late | Both dates are hard calendar items in `ops` with a 30-day warning |
| **CAS regime break invalidating history** | Closing-price mechanism changed 3 Aug 2026 for >200 names; pre-open changed 7 Sep 2026 | `close_method` column is a lock (L6); pooling across the break requires an explicit declaration |
| **Exchange halt** | Market-wide breaker at 10% / 15% / 20% on Nifty or Sensex; single-stock 2/5/10/20% bands; ESM Stage II call auction | Limit orders only; no position that requires exit on a specific day; no leverage means a halt is inconvenient, not fatal |
| **FII flow days and policy shocks** | FII outflow US$24.1bn CY26 YTD against DII inflow US$59.8bn; Fed and MPC dates move the index 1–3% | No directional overlay; the core *is* the market exposure and is meant to be |
| **Regulatory whipsaw on derivatives** | Six material derivative rule changes between Oct 2024 and Aug 2026, and NSE's IPO gives the exchange an incentive to defend volumes SEBI is compressing | Derivative sleeve is zero by default; the index-futures overlay is gated at 2× its own friction |
| **Single-broker concentration** | One broker, one demat, one API | Accepted at ₹25 lakh–₹1 crore; explicitly re-examined at the ₹1 crore ceiling |
| **SLBM lock-in** | R3 series has no repay, recall or rollover | Book B stays gated until SEBI's reformed circular is published |

---

## 12. What would change this design

Stated in advance so that a later agent can recognise the trigger rather than rationalise one:

1. **India VIX 30-day median sustained above 18 for a quarter** → re-examine defined-risk index
   option structures under §2.4's full re-open conditions.
2. **STT on derivatives reduced** → recompute §2.3 and §2.4 from scratch; the current closures are
   arithmetic, so the arithmetic changes with the rate.
3. **T+0 settlement actually mandated** → recompute the cash cycle; today it is indefinitely
   deferred and changes nothing.
4. **Cash settlement restored for single-stock derivatives** → the largest single unlock on this
   list; it would reopen an entire product class.
5. **SEBI's reformed SLBM circular** → Book B's gate.
6. **Twelve months of post-CAS data (2027-08-03)** → Book A's first legitimate look, with the review
   dated 2027-08-31.
7. **A free Indian PIT consensus-estimate dataset** → would not rescue Book R's MDE, but would change
   its σ and is worth recomputing.
8. **Capital crossing ₹1 crore** → re-derive §6 entirely; Book L's edge halves and the operational
   posture stops being proportionate.

---

## Appendix A — working numbers register

P0 (2026-09-05) closed the items it owns. Remaining items stay tagged **(working)** until the named
milestone. Verification notes: [p0-cost-verification.md](p0-cost-verification.md).

| # | Number used | Verify at | Status (2026-09-05) |
|---|---|---|---|
| W1 | NSE tick-size bands above ₹10,000 (₹1.00 and ₹5.00) | P0 | **Resolved.** NSE/CMTR/67133 (CM) and NSE/FAOP/67134 (stock futures), effective 15 Apr 2025: >₹10,000–₹20,000 tick ₹1.00; >₹20,000 tick ₹5.00. Index futures: ₹0.10 at 15,000–30,000; ₹0.20 above 30,000. |
| W2 | Sensex level ~78,000 and Sensex lot notional ~₹15.6 lakh | P0 | **Superseded.** BSE Sensex close **76,515.43 on 4 Sep 2026**; lot 20 → notional **₹15.30 lakh**. |
| W3 | FinNifty, Midcap Select, Next 50 lot notionals | P0 | **Lot sizes resolved** (NSE Jan 2026 lots: FinNifty 60, Midcap Select 120, Next 50 25). Notionals at Zerodha futures marks of 18 Aug 2026: FinNifty 26,367.2 × 60 = **₹15.82 lakh**; MIDCPNIFTY 15,008.3 × 120 = **₹18.01 lakh**; NIFTYNXT50 74,567.8 × 25 = **₹18.64 lakh**. Bank Nifty cash close 4 Sep 2026: 57,369.65 × 30 = **₹17.21 lakh**. |
| W4 | Nifty index futures / short option SPAN+Exposure ≈ ₹1.1–1.5 lakh per lot | P0 | **Superseded.** Zerodha futures margin calculator snapshot 18 Aug 2026: NIFTY 29-Sep-2026 NRML **₹1,80,367** (11.31%) at 24,533.5. No live margin API at P0 (L8). Re-read the endpoint at L0; never hard-code this as leverage. |
| W5 | Additional 2% ELM on short options on expiry day | P0 | **Resolved.** SEBI/HO/MRD/TPD-1/P/CIR/2024/132 (1 Oct 2024) §5.6; NSE Clearing NCL/CMPT/64639 (21 Oct 2024). Additional 2% ELM on short *index* options on expiry day, from 20 Nov 2024. |
| W6 | NSE monthly impact-cost values by segment (2–6 / 5–10 / 8–20 / 30–150 bps) | U0 | **Join ready, file not cached.** `panel.join_impact_cost` is in code. No NSE monthly impact-cost file was retrieved on 2026-09-05; segment bands stay **(working)** until U0 backfill stores the file. |
| W7 | Dividend TDS threshold ₹10,000 per company per year | P0 | **Resolved.** Finance Act 2025 raised the s.194 threshold from ₹5,000 to **₹10,000** per deductor per year from 1 Apr 2025; 10% TDS. |
| W8 | Buyback proceeds taxed as deemed dividend from 1 Oct 2024 with cost as capital loss | P0 | **Resolved as the 2024 rule.** Finance (No.2) Act, 2024: s.2(22)(f) from 1 Oct 2024; cost as capital loss (s.46A). Any ITA 2025 / Finance Act 2026 rewrite from TY 2026-27 was not verified from the Act text at P0 — re-read at X0 if a buyback ever appears. |
| W9 | SGB secondary-market maturity exemption withdrawn from 1 Apr 2026 | P0 | **Resolved.** Budget 2026: exemption on SGB redemption only for original subscribers who hold to maturity; secondary-market buyers taxable from 1 Apr 2026. |
| W10 | Turnover for s.44AB includes premium on options sold | P0 | **Resolved as ICAI, not statute.** Guidance Note on Tax Audit, 10th edition (Revised 2025), AY 2026-27: absolute P&L **plus** premium on options sold, without double-counting premium already inside broker P&L. Encoded in `tax.audit_turnover`. |
| W11 | SEBI 2026 MTF eligibility thresholds (income ≥ ₹5 lakh, net worth ≥ ₹25 lakh) | P0 | **Withdrawn.** No SEBI circular imposing those *client* thresholds was found. The June 2026 consultation paper is about *broker* net-worth. MTF is closed on carry arithmetic; these numbers must not be cited. |
| W12 | PaRRVA performance-verification regime live since May 2026 | P0 | **Resolved.** SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/51 (4 Apr 2025); full-scale operations **4 May 2026**. The desk is not an RA. |
| W13 | SBI Nifty 50 ETF AUM ~₹2.16 lakh crore and its EPFO-driven composition | P1 | Pending. AMFI monthly AAUM; scheme documents. |
| W14 | USD/INR ≈ ₹88 | P0 | **Superseded.** FBIL USD/INR reference **94.4688 on 3 Sep 2026**. ₹50 lakh ≈ US$5,300, not US$57,000. |
| W15 | Vendor prices: Kite ₹500/mo, Dhan data ₹499/mo, TrueData ₹1,440–2,796/mo, Global Datafeeds from ~₹225/exchange/mo | L0 | Pending. Zerodha charges page on 2026-09-05 still lists Kite Connect at ₹500/month. |
| W16 | Book A hypothesised net effect 1.5%/yr | A0 (2027-08-31) | Pending. Post-CAS data. |
| W17 | Nifty 50 TRI forward return assumption 11%/yr, used in Book L's effect size | H0 | **Recorded 2026-09-05** in `h0-prereg-book-l.md` as an assumption, not a forecast; Book L's *delta* is insensitive to it. |

---

*Companion: [india-equity-execution-plan.md](india-equity-execution-plan.md)*
