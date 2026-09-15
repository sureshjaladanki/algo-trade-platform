# Retail India desk — Architecture Blueprint, Rev 2.0

| | |
|---|---|
| **Date** | 2026-09-08 |
| **Accepted** | 2026-09-14 |
| **Status** | **BLUEPRINT Rev 2.0 / ACTIVE** |
| **Review** | Claude Opus |
| **Scope** | Listed Indian equity and equity derivatives (NSE / BSE). Own capital only. Declined-beta carry desk. |
| **Replaces** | [india-equity-architecture-blueprint.md](../archive/india-equity-architecture-blueprint.md) (Rev 1.0) — **SUPERSEDED 2026-09-14** |
| **Milestone map** | [§13](#13-twelve-month-staged-build) (no separate execution-plan file; the Rev 1.0 plan is superseded with that charter) |
| **Limits** | [§12](#12-risk-and-operations--the-numbers-the-code-asserts) · hurdles [§8](#8-hurdles-stop-numbers-and-the-beta-report) |

## This is the charter

A human accepted Rev 2.0 on **2026-09-14**. This document authorises the India programme: modules,
milestones, and — after M6 — the first rupee. [india-equity-architecture-blueprint.md](../archive/india-equity-architecture-blueprint.md)
(Rev 1.0) and [india-equity-execution-plan.md](../archive/india-equity-execution-plan.md) are retained as the
record of the **Nifty-beta charter that was not chosen**. Pre-registrations and STOP memos
written under Rev 1.0 stay in `docs/archive/` as history; they do not reopen a Nifty-beta core.

The two blueprints answered different investor briefs. Rev 1.0 was written for an investor who accepts
Indian equity beta as the default holding and wants the after-tax realisation schedule on top of it
optimised. Rev 2.0 is written for an investor who has **declined that beta** — Nifty 50 ~−4% over
one year against S&P 500 ~+19% — and wants net-positive rupee PnL without it. That single change
re-orders the constraint ladder, demotes Rev 1.0's rank-1 book by two-thirds of its rupee value, and
opens a container Rev 1.0 never priced because Rev 1.0 never needed a place to put money that is not
in the market.

**No number in Rev 1.0 is contradicted here without a sourced Indian replacement.** Where Rev 1.0's
arithmetic still holds — futures round-trip friction, lot notionals, the option-premium kill, the
MDE table, the SEBI algo perimeter — it is imported and cited, not re-derived. Numbers that are new
to Rev 2.0 and not yet sourced to a statute, circular or published schedule are tagged **(working)**
and listed in [Appendix A](#appendix-a--working-numbers-register).

---

## 1. One-line thesis

At ₹50 lakh with no tax wrapper, no retail borrow and a ₹15.52 lakh minimum hedge increment, India
offers this desk **no constructible market-neutral book and no measurable cross-sectional alpha** —
but it does offer a legal, continuously divisible, near-zero-beta container that pays a
money-market return and is **taxed as equity** (s.198, 13.0% above a ₹1.25 lakh annual exemption)
rather than as interest (31.2% slab). So the product of this desk is **after-tax rupee carry with
the beta switched off by default**, worth **65–134 bps/yr at ₹50 lakh purely on tax class**; its
risk-taking is confined to two gated event books that must beat that carry rather than beat zero;
and the rupee price of declining Indian beta is printed every quarter instead of assumed away.

---

## 2. Desk identity

This ₹50 lakh book is a **single-PAN, own-capital, zero-leverage carry desk with a capped event
sleeve and an explicit, human-signed beta switch that is off by default.** Its default state is
₹27.5 lakh of direct-plan arbitrage-fund units across at least two AMCs — the packaged, colocated,
borrow-financed cash-futures book this desk cannot build itself — held past the 12-month line so it
is taxed at 13.0% under s.198, plus a sweep/overnight operating and event float. It is **not** a
market-neutral long/short book, **not** a Nifty tracker with a tax overlay, **not** an F&O desk, and
**not** a short-the-index expression of the investor's bearish view. It holds zero futures, zero
options, zero single-stock derivatives and zero short cash positions, at all times, by construction
rather than by discipline.

### 2.1 Verdict on the "small market-neutral book across from prop desks" candidate

**DROPPED — not gated, not deferred.** It fails on five independent binding Indian reasons, each of
which is arithmetic and any one of which is sufficient. The full computation is
[§7, Book N](#book-n-rank-5--market-neutral-cash-versus-index-futures-dropped-at-h0). In one
paragraph:

There is no retail locate — SLBM R3 (17 Aug 2026) has no repay, recall or rollover and retail sits
on the *lending* side, so the cash short leg does not exist. The futures hedge is only available in
₹15.52 lakh increments, so on a ₹40 lakh long basket the best achievable residual is **−13.1% net
beta of equity**, which is not neutral. The two legs land in **non-fungible tax ledgers** — long-leg
gains at 13.0%/20.8% capital gains, hedge-leg P&L at 31.2% non-speculative business — so a flat year
of +₹10,000 gross produces **−₹12,750 after tax** and an 8-year business-loss carry-forward against
income the desk does not generate. STT is charged on notional, so neutrality **doubles the toll
without changing the net exposure being paid for**: the monthly roll alone is 68 bps/yr of equity, of
which 56 bps is STT. And the residual return of a neutral book *is* cross-sectional alpha, which
Rev 1.0 already measured at **MDE 5.01%/yr against ½ × 2.0%** — a 5.0× H4 failure that hedging makes
worse, not better. Reopen requires **all three** of: a retail-accessible locate, an index lot
notional at or below **₹5 lakh** (10% of equity), and a cross-sectional effect that clears H4.

The market-neutral *exposure* survives. The market-neutral *book* does not. You buy the neutral book
from someone who has colocation, cheap borrow and an equity-oriented tax wrapper, for 25–40 bps of
TER. That is Book C.

---

## 3. Capital map at ₹50 lakh

Design point ₹50,00,000. Envelope ₹25 lakh – ₹1 crore; the scaling behaviour of every line is in
[§3.2](#32-how-the-map-scales-across-the-envelope).

| Sleeve | Instrument | ₹ | % of equity | Tax class | Sleeve β | β contribution |
|---|---|---|---|---|---|---|
| **Carry core** | Direct-plan arbitrage funds, ≥ 2 AMCs, ≤ 30% each | 27,50,000 | 55.0% | s.198 / s.196 — equity-oriented | 0.08 **(working)** | 0.044 |
| **Operating + event float** | Bank sweep FD / overnight fund | 10,00,000 | 20.0% | Slab (interest / s.50AA) | 0.00 | 0.000 |
| **Event sleeve, deployed** | Tendered or allotted cash equity, episodic | 5,00,000 | 10.0% | s.196 | ~0.40 | 0.040 |
| **Reserve** | Overnight fund, unallocated | 7,50,000 | 15.0% | Slab | 0.00 | 0.000 |
| **Conditional beta sleeve** | Nifty 50 direct index fund — **default zero** | 0 | 0.0% (cap 15%) | s.198 | 1.00 | 0.000 |
| **F&O** | — | **0** | **0.0%** | — | — | — |
| **Total** | | **50,00,000** | **100.0%** | | | **0.084** |

- **Gross exposure 100% of equity. Borrowed rupees: zero.** No MTF, no margin funding, no pledge for
  leverage. Pledging is permitted only to post SPAN, and SPAN is zero because F&O is zero.
- **Net Nifty 50 beta: default target ≤ 0.10, hard cap 0.25** with the conditional sleeve fully on,
  **whole-desk STOP at a realised rolling-quarter beta above 0.30** (§12).
- **Liquidity assertion:** at least **20% of equity** must be redeemable to bank within T+1 at all
  times. Overnight funds settle T+1; arbitrage funds settle **T+2 (working)**; the sweep is same-day.
  The carry core therefore cannot fund an event on the day it is found, which is why the float exists
  and is sized at 20%.

### 3.1 Why the carry core is ₹27.5 lakh and not ₹40 lakh

Because the ₹1.25 lakh s.198 exemption saturates. At a 5.60% net-of-TER carry **(working)**:

> ₹1,25,000 ÷ 0.0560 = **₹22,32,143**

**The first ₹22.3 lakh of arbitrage-fund carry is tax-free**, provided the units are held past 12
months and no other s.198 gain competes for the exemption in the same tax year. The next rupee is
taxed at 13.0%. Sizing the core at ₹27.5 lakh puts ~81% of its annual gain inside the exemption and
leaves headroom for tranche-timing slippage; sizing it at ₹40 lakh would push ₹1.0 lakh of gain a
year into the taxed band for no additional risk-adjusted return, while consuming the liquidity the
event sleeve needs. It also means **the conditional beta sleeve competes with the carry core for the
same exemption** — turning the beta switch on has a tax cost the register must print (§8.3).

### 3.2 How the map scales across the envelope

| Capital | Carry core 55% | Exemption saturation point | Exemption as bps of capital | Event sleeve 10% | Events fundable at ≤ 6%/event |
|---|---|---|---|---|---|
| ₹25,00,000 | ₹13,75,000 | ₹22,32,143 — **core is wholly inside it** | 65 bps | ₹2,50,000 | 1–2 concurrent |
| ₹50,00,000 | ₹27,50,000 | 81% of core inside it | 33 bps | ₹5,00,000 | 2–3 concurrent |
| ₹1,00,00,000 | ₹55,00,000 | 41% of core inside it | 16 bps | ₹10,00,000 | 3–4 concurrent |

The desk is **better, per rupee, at the floor of the envelope than at the ceiling** — the opposite of
Rev 1.0's conclusion for a beta core, and for the same reason: a fixed-rupee exemption applied to a
low-yield sleeve saturates sooner. At ₹1 crore the marginal rupee of carry is taxed at 13.0% and the
whole design's edge over sweep FD narrows from 65 bps to roughly **45 bps (working)**. Re-derive §3
before crossing ₹75 lakh.

---

## 4. Constraint ladder — ordered by what actually binds at ₹50 lakh

Rev 1.0's ladder was: no wrapper → STT on turnover → inference budget → capacity slack → alpha last.
That ordering is correct **for a long-only candidate set**, where lot size and borrow never bind.
Rev 2.0's candidate set includes hedged and neutral books, and for those the ladder inverts: two
constraints Rev 1.0 never had to rank kill an entire identity before any cost or inference argument
is reached.

| Rung | Constraint | The number at ₹50 lakh | What it kills | Rev 1.0 rank |
|---|---|---|---|---|
| **1** | **Tax class of the container** | Same 5.60% gross is worth **5.19% after tax** as an equity-oriented fund and **3.85%** as a specified mutual fund. **134 bps** on 100% of capital, every year, whether or not the desk trades. | Every design that parks idle capital in debt | 1 (as "no wrapper") |
| **2** | **Lot indivisibility** | 1 Nifty lot = ₹15,52,000 = **31.0% of equity**. Best achievable hedge residual on a ₹40 lakh basket: **−13.1% net beta**. | Every hedged, neutral or overlay identity | not ranked |
| **3** | **Borrow** | SLBM R3 (17 Aug 2026): no repay, recall or rollover; retail is the lender; borrow is prop. **Locate probability for a retail PAN ≈ 0.** | Every cash short leg | not ranked |
| **4** | **Tax-bucket non-fungibility** | Capital-gain leg 13.0%/20.8% vs business leg 31.2%, **not offsettable**. A +₹10,000 gross hedged year is **−₹12,750 after tax**. | Every two-leg book whose legs sit in different heads | not ranked |
| **5** | **STT on notional** | Futures RT **6.05 bps = ₹939.58/lot**; delivery RT **23.8 bps**; ETF/MF units **3.9 bps**. Neutrality doubles gross for constant net. | Every high-cadence book; makes hedging a turnover tax | 2 |
| **6** | **Sample / MDE** | MDE_ann = 2.80 σ/√T. Momentum 5.01% vs ½×2.0%. PEAD 7.23% vs ½×1.9%. Nifty TSMOM **7.90% vs ½×4.0%** (§7, Book T). | Every predictive book, including the bearish one | 3 |
| **7** | **Latency** | Retail API 50–500 ms; TOPS 10 OPS, coded at 8. Any hedge that must move inside one second is stale. | Books already dead at rungs 2–5 | — |
| **8** | **Capacity** | Carry core redeems at NAV with **zero impact**; event clips of ₹3 lakh are a fraction of a percent of a Nifty 200 name's delivery value. | Nothing. **Slack — do not spend it on turnover.** | 4 |

Two consequences worth stating flatly.

**Rung 1 is worth more than rungs 5–8 combined, and it requires no trading.** The tax-class decision
applies to every rupee for every day of the year and costs one form. The best trading idea in this
document is worth less.

**Rung 2 is the reason this is not a Rev 1.0 with a hedge bolted on.** At ₹50 lakh the Indian
derivatives market has a minimum position size of 31% of the book. There is no such thing as a
"small" hedge here. Any design that says "hedge the beta out" has not divided ₹15,52,000 by
₹50,00,000.

---

## 5. Product board

**Cadence** is the maximum rate at which the desk would touch the product, not the rate the market
permits. **Smallest clip** is the minimum economically sensible transaction against ₹50 lakh.

| Product | Verdict | Binding Indian reason | Cadence | Smallest clip | vs ₹50 lakh |
|---|---|---|---|---|---|
| **Arbitrage fund, direct plan** | **VIABLE — core** | Equity-oriented (≥65% equity, hedged) → s.198 13.0% with the ₹1.25 lakh exemption, vs s.50AA slab on debt. STT 0.001% sell-only on units. Continuously divisible. | Monthly tranche in; redeem only past the 12-month line | ₹500–₹5,000 | **0.01%** |
| **Overnight / liquid fund** | **VIABLE — float only** | T+1 settlement funds the event sleeve. Taxed at slab regardless of holding period (s.50AA). Never a carry instrument. | Daily | ₹500 | **0.01%** |
| **Bank sweep FD** | **VIABLE — operating cash and ASBA float** | ASBA/UPI blocks funds *in the bank account*; the carry core cannot serve as IPO float. DICGC cover ₹5 lakh per bank — spread it. | Continuous | ₹1 | — |
| **Cash equity delivery, episodic (event legs)** | **VIABLE — capped at 10%** | Only route to tender into an open offer or hold an IPO allotment. 23.8 bps RT; DP ₹15.34/ISIN/sale-day. | Event-driven, ~4–6 turns/yr | ~₹30,000 (DP charge ≤ 5 bps) | **0.6%** |
| **Nifty 50 direct index fund** | **GATED — beta register, default zero** | No DP charge, no quoted spread, no exchange leg; TER 0.05–0.20% vs NIFTYBEES 0.04% + ~11 bps spread + ₹15.34 DP. Rev 1.0's L1 reached the same conclusion at 4 turns/yr. | Annual, human-signed | ₹500 | **0.01%** |
| **Equity ETF (NIFTYBEES class)** | **GATED — beta register, second choice** | 3.9 bps RT beats a 23.8 bps constituent basket, but the index fund beats both when intraday execution is not needed — and it never is here. | Annual | ~₹30,000 | **0.6%** |
| **IPO retail category (ASBA/UPI)** | **CANDIDATE-GATE — ₹0 screen** | Statutory retail reservation at ≤ ₹2,00,000 per PAN per issue is a genuine retail-only allocation. Adverse selection is the whole question. | ~50–80 issues/yr, apply/skip rule | 1 lot ≈ ₹14,000–15,000; cap ₹2,00,000 | **4.0% max** |
| **On-market open offer / delisting tender** | **CANDIDATE-GATE — ₹0 screen** | SEBI SAST open offers and Delisting Regulations reverse book-building create a priced, dated, on-exchange tender window. Acceptance-ratio risk is the whole question. | ~20–35 offers/yr, ~8–12 arbitrageable | 1 share | **~0.001%** |
| **Equity savings fund** | **OUT** | 35–65% equity → LTCG 12.5% only after **24 months** under the amended s.50AA regime **(working)**, and 10–35% unhedged net equity smuggles beta into a sleeve labelled neutral. | — | — | — |
| **Index futures** | **OUT** | 1 lot = 31.0% of equity (rung 2). Hedge-leg P&L lands in a non-nettable 31.2% business ledger (rung 4). Monthly roll on a ₹46.56 lakh hedge = **68 bps/yr of equity**, 56 bps of it STT. | — | 1 lot ₹15,52,000 | **31.0%** |
| **Index options — weekly or monthly** | **OUT** | Rev 1.0 §2.4 stands unchanged: friction ≈ **1.02% of premium** ≈ the entire VRP at India VIX 10.97; MDE **>30%/yr** on a regime under 6 months old; SEBI FY26 — 87.7% of individuals lost, ₹25,000 cr of it transaction cost. 4σ week on one short straddle = **₹82,940 = 1.66% of equity**. | — | 1 lot | **31.0% of notional** |
| **Stock futures / stock options** | **OUT** | Physical settlement, delivery-margin ramp to 100%, delta-based FutEq ban with ₹5,000–₹1,00,000/day penalties, quarterly MWPL churn. One lot is 30–50% of the book. | — | 1 lot | **30–50%** |
| **Cash equity intraday (MIS)** | **OUT** | s.66 **speculative**: slab to 31.2%, losses ring-fenced to speculative income, 4-year carry. 8.3 bps RT at ₹1 lakh clips. | — | — | — |
| **Cash short via SLBM** | **OUT** | Rung 3 — no retail locate. R3 series has no repay, recall or rollover. | — | — | — |
| **SLBM lending on held stock** | **OUT in Rev 2.0** | Rev 1.0 gated this on σ 0.5% / MDE 0.63% vs 25–60 bps. Rev 2.0 **removes its input**: the desk holds almost no individual stock, and ETF/MF units are outside the SLB universe. Closed by absence of inventory, not by disagreement. | — | — | — |
| **MTF** | **OUT** | 12.49–15.49% p.a. against a ~5.6% carry and a declined ~11% beta. Interest not deductible against capital gains. | — | — | — |
| **Cash-and-carry run in-house** | **OUT** | ₹15.52 lakh cash leg + ₹1.80 lakh SPAN = **34.6% of equity for one unit**, capturing an implied-financing spread over T-bill of **20–80 bps (working)** against ~10 bps of RT friction per roll. Prop with colocation prices it first; retail is the taker. **This is Book C's underlying, and buying it packaged costs 25–40 bps of TER.** | — | ₹17,32,000 | **34.6%** |
| **Non-Indian parking sleeve (LRS → US T-bill)** | **OUT — and it is a currency view, not a parking sleeve** | USD/INR moved to **94.4688 on 3 Sep 2026** (FBIL) from ~₹88, so the S&P's ~+19% was ~+27% in rupees; **the gap the investor cites is majority FX**. Capturing it means LRS, 20% TCS above ₹10 lakh (creditable, cash-flow drag), 50–100 bps FX round trip, Schedule FA disclosure, and slab-taxed foreign interest with FTC. A rupee-denominated desk taking that trade is long USD, not parked. | — | — | — |
| **Currency / commodity derivatives** | **OUT OF CHARTER** | Charter is Indian equity. | — | — | — |

---

## 6. Cost and tax engine

`src/costs.py` and `src/tax.py` remain the single sources of Indian friction and Indian tax, exact to
**₹1**, with the Rev 1.0 P0 surface intact. Rev 2.0 adds five items Rev 1.0 did not need. All five
are load-bearing: the entire thesis rests on the s.50AA-versus-s.198 boundary.

### 6.1 Additions to `costs`

| Item | Rate | Note |
|---|---|---|
| **Mutual-fund stamp duty on purchase** | **0.005% of the invested amount**, deducted before units are allotted; applies to lumpsum, SIP, switch-in and dividend reinvestment, since 1 Jul 2020 **(working — verify against the Indian Stamp Act amendment)** | ₹250 on a ₹50 lakh deployment. Rev 1.0 has no MF purchase leg and therefore no line for this. |
| **STT on equity-oriented fund unit repurchase** | **0.001%, sell side only** | Already in Rev 1.0's schedule for ETF units; extended to AMC redemptions. |
| **Exit load** | Arbitrage funds typically **0.25% if redeemed within 15–30 days (working — read each SID)** | A hard `costs` input, not a footnote. No unit is redeemed inside its load window except as a STOP action. |
| **STT on exchange tender-offer sales** | Charged at the **delivery rate on the seller, 0.10% (working)** | Verify against a real tender-window contract note **before Book E is opened**, not after. A 10 bps error flips a 0.5%-per-event book. |
| **Kotak-class ₹0-brokerage API trap** | ₹0 brokerage on API-routed orders for resident individuals; **app-routed delivery after 30 days can be 0.20%** | ₹600 on a ₹3 lakh event position squared off by hand — **24× the ₹25 the desk budgeted**. `execute` must refuse to hand off a position past day 25 without re-pricing it. |

### 6.2 Additions to `tax`

| Provision | Treatment | Why it is load-bearing |
|---|---|---|
| **Specified mutual funds (old s.50AA; ITA 2025 section number (working))** | Units of a fund investing **> 65% in debt** → gains deemed **short-term at slab (31.2%)** regardless of holding period. Funds with **35–65% equity** → 12.5% LTCG only after **24 months (working)**. Funds with **≥ 65% equity** → equity-oriented → **s.196 / s.198**, 12-month line. | This is the statutory boundary the entire desk is built on. `tax` must classify every fund the desk holds by its **actual equity percentage as disclosed in the scheme portfolio**, not by its category label, and refuse to price a scheme whose percentage has not been read. |
| **Equity-oriented status of arbitrage funds** | SEBI's Arbitrage Fund category mandates **≥ 65% in equity and equity-related instruments**; hedged exposure still counts toward the 65% for the equity-oriented test **(working — confirm with a CA in writing before the first rupee)** | If this is wrong, Book C's 134 bps becomes **−0 bps and a penalty**. It is the single largest legal-interpretation risk in Rev 2.0. |
| **s.198 exemption is aggregate** | ₹1,25,000 per tax year across **all** s.198 gains — arbitrage units, index-fund units, IPO allotments held > 12 months, tendered shares held > 12 months | The exemption is a shared, use-it-or-lose-it budget. `tax` owns the running balance; `portfolio` reads it before scheduling any redemption. |
| **Tender / open-offer proceeds** | On-market tender through the exchange window → **capital gains** (s.196 if ≤ 12 months), not business income, provided the desk's stated position on listed shares is consistent under CBDT Circular 6/2016 **(working — CA opinion in writing)** | Book E's after-tax number is 20.8% or 31.2% depending on this. |
| **IPO listing gains** | s.196 at **20.8%**, from the first rupee, no exemption | Book I's gross must be discounted by 20.8%, not by 13.0%. |

### 6.3 Worked example — the whole thesis, exact to ₹1, at ₹50,00,000

One tax year, full deployment into a single container, no trading. This isolates rung 1.

**(a) Arbitrage fund, direct plan, held 12 months + 1 day, 5.60% net-of-TER (working)**

| Line | ₹ |
|---|---|
| Amount invested | 50,00,000 |
| MF stamp duty 0.005% | −250 |
| Units allotted for | 49,99,750 |
| Value after 5.60% | 52,79,736 |
| STT on repurchase, 0.001% | −53 |
| Exit load (past window) | 0 |
| Redemption proceeds | **52,79,683** |
| Capital gain vs ₹50,00,000 cost | 2,79,683 |
| Less s.198 exemption | −1,25,000 |
| Taxable | 1,54,683 |
| LTCG 12.5% | 19,335 |
| Cess 4% | 773 |
| **Tax** | **20,108** |
| **After tax** | **2,59,575 = 5.19%** |

**(b) Liquid fund, same 5.60%, same 13 months — specified mutual fund, s.50AA**

| Line | ₹ |
|---|---|
| Amount invested | 50,00,000 |
| MF stamp duty 0.005% | −250 |
| Value after 5.60% | 52,79,736 |
| Gain (deemed short-term, no exemption, no STT) | 2,79,736 |
| Slab 30% + 4% cess = 31.2% | −87,278 |
| **After tax** | **1,92,458 = 3.85%** |

**(c) Bank sweep FD at 6.60% (working)**

| Line | ₹ |
|---|---|
| Interest | 3,30,000 |
| TDS 10% (creditable) | (33,000) |
| Slab 31.2% | −1,02,960 |
| **After tax** | **2,27,040 = 4.54%** |

| Comparison | Delta ₹ | Delta bps of ₹50 lakh |
|---|---|---|
| Arbitrage fund vs liquid fund | **+67,117** | **+134** |
| Arbitrage fund vs sweep FD | **+32,535** | **+65** |
| Sweep FD vs liquid fund | +34,582 | +69 |

**The conservative claim is +65 bps**, because a sweep FD is what most retail investors actually
hold. The headline 134 bps only applies against a liquid fund. Book C's kill number is set against
the conservative one.

Note the counterparty direction, which runs opposite to intuition: ₹50 lakh in FD carries bank credit
exposure above the ₹5 lakh DICGC cover unless it is split across ten banks. ₹50 lakh of MF units sits
in a trust, marked daily, with no issuer credit. **The tax-advantaged container is also the lower
credit-risk one.**

### 6.4 Worked example — why the F&O cost model still ships with zero live F&O

`costs` must price futures, options and exercise exactly, to ₹1, even though the desk will never send
one of those orders. Three reasons, all of them decisions rather than executions:

1. **Book C's yield is a function of derivative STT.** Arbitrage funds earn the cash-futures basis by
   selling futures. The 1 Apr 2026 hike from 0.02% to 0.05% on the sell side is a **~36 bps/yr drag
   on a monthly-rolled arbitrage book (working: 0.03% × 12)**. That is 27% of Book C's 134 bps edge,
   already spent. If derivative STT is cut, Book C's yield rises and the calculation must re-run.
2. **Every OUT verdict in §5 is arithmetic, so it is re-evaluable.** Book N's reopen test and Rev
   1.0's option-premium reopen test both need a working futures cost model to answer.
3. **The beta register must price the hedge it declines.** A human turning the beta switch on is
   entitled to see, in rupees, what hedging it would have cost: 3 lots × ₹939.58 × 12 rolls =
   **₹33,825/yr**, plus ₹6,76,376 of margin locked, plus a ₹2,32,800 single-day MTM call on a 5%
   adverse move. The register prints that number every time.

**The F&O cost model is a decision instrument, not an execution path.** `execute` has no F&O order
type at all.

---

## 7. Strategy books, ranked

Two arithmetic books open. Two gated behind ₹0 screens with hurdles they may well fail. Two named and
closed so they cannot be re-proposed by assertion.

### Book C (rank 1) — Carry container: tax-class arbitrage on the non-risk sleeve

| | |
|---|---|
| **Hypothesis** | The largest reliably capturable after-tax gain available to a ₹50 lakh Indian desk that declines equity beta is not an alpha but the **tax class of the container the idle capital sits in**: the same ~5.60% money-market gross return is worth 5.19% after tax inside an equity-oriented arbitrage fund (s.198, 13.0% above a ₹1.25 lakh exemption) and 3.85% inside a debt fund (s.50AA, 31.2% slab). |
| **Instruments** | Direct-plan arbitrage funds, **minimum two AMCs, maximum 30% of equity per AMC**, screened on: disclosed equity ≥ 65%, 3-year weekly-NAV beta to Nifty 50 ≤ 0.10, TER ≤ 0.40%, AUM ≥ ₹2,000 crore, exit load window read from the SID |
| **Cadence** | **Twelve monthly tranches in; redemptions only from lots past the 12-month line.** No tactical switching. |
| **Contribution after cost, after tax** | **+65 bps/yr vs sweep FD; +134 bps/yr vs liquid fund**, at ₹50 lakh. Central working claim **95 bps**. In rupees: **₹32,535 to ₹67,117 per year.** |
| **Risk** | Basis compression (index futures ADT ~−44% Mar→May 2026; NSE Aug 2026 volumes −22.6% MoM) shrinks the very spread these funds harvest. Arbitrage-fund AUM inflows compress it further. A negative month is possible and has happened; the sleeve is low-beta, not no-risk. **Reclassification risk is the tail: if arbitrage funds lose equity-oriented status, the thesis inverts overnight.** |
| **Kill number** | Close and move to sweep FD if the **rolling 3-year net-of-TER category yield falls below 0.79 × the prevailing sweep-FD rate** for two consecutive quarters. Derivation: the after-tax break-even is y_arb × (1 − 0.13 effective) ≥ y_fd × 0.688 ⟹ y_arb ≥ 0.79 × y_fd. At FD 6.60% the break-even is **5.21%**. Also close if measured beta exceeds 0.10, or if CBDT/SEBI changes the equity-oriented test. |
| **Arithmetic or inferential** | **Arithmetic.** No MDE. The only measured input is a published NAV series. |
| **AI role** | `ai.extract` reads the SID for exit load, TER, cut-off and disclosed equity percentage. Extraction proposes; a deterministic screen disposes. |

### Book S (rank 2) — Tranche ledger and realisation scheduler

This is Rev 1.0's Book L, re-pointed from a beta core to a carry core. **The machinery survives the
re-scope; two-thirds of its rupee value does not** — Rev 1.0's 95–130 bps was 84 bps of tax delta on
an *11% gross* core. Strip the beta and the same code yields ~57 bps on a 5.60% core, because the
delta is proportional to the gain being scheduled. This must be said plainly rather than carried
forward at Rev 1.0's headline.

| | |
|---|---|
| **Hypothesis** | Twelve monthly tranches make a rolling 1/12 of the carry core cross the 12-month line every month, converting s.196 (20.8%) redemptions into s.198 (13.0%) redemptions while preserving monthly liquidity, and consuming the ₹1.25 lakh aggregate exemption before every 31 March. |
| **Instruments** | The carry core's lots; every event-sleeve exit; the conditional beta sleeve if it is ever on |
| **Cadence** | Monthly tranche in; the crossing calendar and exemption tracker run nightly; the March harvest runs by 20 March |
| **Contribution** | On a ₹27.5 lakh core at 5.60%: annual gain ₹1,54,000. Fully realised inside 12 months → 20.8% = **₹32,032**. Realised past 12 months with the exemption → (1,54,000 − 1,25,000) × 13.0% = **₹3,770**. **Delta ₹28,262 = 57 bps of ₹50 lakh.** Range **50–80 bps** depending on how much of the event sleeve's exits it can also defer. |
| **Risk** | Scheduling risk only: a forced redemption inside the 12-month line (a STOP, a margin call that cannot occur here, or a mis-sized event) destroys the benefit for that tranche. Tracking risk is zero — the core has no target weights to track. |
| **Kill number** | If the measured delta at ₹50 lakh is **under 30 bps/yr**, reduce Book S to the exemption harvest alone (33 bps, unconditional) and delete the tranche scheduler. If it is under 15 bps, close the book and buy one lumpsum. |
| **Arithmetic or inferential** | **Arithmetic.** No MDE. |
| **AI role** | **None.** |

### Book E (rank 3) — On-market event arbitrage: SAST open offers and delisting tenders

| | |
|---|---|
| **Hypothesis** | A SEBI SAST open offer or a Delisting Regulations reverse book-building creates a **priced, dated, on-exchange tender window**. When the market discount to the offer price exceeds the expected post-offer price drop weighted by (1 − acceptance ratio), the trade has positive expectancy that is a function of published documents rather than of a price forecast. |
| **Instruments** | Cash equity delivery in the target name; tendered through the exchange tender window via the broker |
| **Cadence** | ~20–35 offers/yr **(working)**; ~8–12 arbitrageable; average hold 30–60 days; 4–6 sleeve turns/yr |
| **Contribution, hypothesised** | ₹5 lakh average deployed × 5 turns × **1.0% net per event (working)** = ₹25,000 gross → ₹19,800 after 20.8% STCG = **40 bps of ₹50 lakh**. **But that capital is displaced from the carry core, which earns 5.20% after tax on ₹5 lakh = ₹26,000 = 52 bps.** **Incremental contribution: −12 bps central; range −30 to +65 bps.** |
| **Risk** | Acceptance-ratio risk is the whole trade and it is adversely selected: you receive **full acceptance in the offers that fail and partial acceptance in the ones that work**. Worked adverse case — buy at ₹98 against a ₹100 offer, 40% accepted, residual sold at ₹94 post-offer: 0.4 × (+2.04%) + 0.6 × (−4.08%) = **−1.63% per event**. Add offer withdrawal, CCI/regulatory delay, and an escrow-to-settlement lag. |
| **Kill number** | Close at the ₹0 screen if **any** of: median after-cost after-tax net per event **< 0.80%**; fewer than **8** arbitrageable events per year in the 12-year corpus; or **incremental** contribution over the carry core **< 25 bps/yr**. Close later if two consecutive live quarters produce a negative incremental. |
| **Arithmetic or inferential** | **Inferential, marginal.** σ per event ≈ 4% **(working)**, n ≈ 250 over 12 years → **MDE per event = 2.80 × 4% / √250 = 0.71%** against ½ × 1.5% = 0.75%. **Passes H4 by 5 bps.** That is a pass, not a comfortable one, and it is the reason the screen has a hard event-count floor: if the corpus yields fewer than 250 usable events, MDE rises and the book closes on measurability before it is ever traded. |
| **AI role** | **Load-bearing.** `ai.extract` parses SEBI letters of offer and NSE/BSE tender-offer circulars into typed fields (offer price, offer size, record date, tender window open/close, escrow, conditionality), each with a per-field confidence and a source page, cross-checked deterministically against the exchange circular. **Extraction feeds a deterministic spread computation. It never produces an expected return.** |
| **Honest expectation** | **This book closes.** The central incremental is negative. It gets a ₹0 screen because the screen is free and the corpus is reusable; it does not get live capital on hope. |

### Book I (rank 4) — IPO retail-category application book

| | |
|---|---|
| **Hypothesis** | The **statutory retail reservation at ≤ ₹2,00,000 per PAN per issue** is one of the few Indian allocations that institutions cannot take. A rule that conditions apply/skip on observable subscription dynamics and issuer characteristics has positive after-tax expectancy net of the ASBA float's opportunity cost. |
| **Instruments** | Mainboard IPO applications via ASBA/UPI; allotted shares sold on listing day (T+3 since Dec 2023) |
| **Cadence** | ~50–80 mainboard issues/yr; ≤ **3 concurrent applications** (₹6 lakh blocked ≤ 12% of equity) |
| **Contribution, hypothesised** | **10–50 bps/yr (working)**, central **25 bps**. Float opportunity cost: ₹6 lakh held in sweep rather than carry = ₹6,00,000 × 0.66% = **₹3,960 = 8 bps**. **Incremental central: +17 bps.** |
| **Risk** | **Winner's curse, and it is the entire book.** In an oversubscribed issue the retail allotment is one lot (~₹15,000) with a 5–15% probability; in an undersubscribed issue you are allotted the full ₹2 lakh and the listing is usually negative. Any historical "average listing gain" statistic that is not weighted by realised allotment probability is a fiction, and the screen must decompose it. Secondary risks: listing-day gains are s.196 at **20.8% from the first rupee**; UPI mandate acceptance is a manual, timed step (17:00 IST on the closing day). |
| **Kill number** | Close at the ₹0 screen if the **allotment-probability-weighted, adverse-selection-decomposed, after-tax expected value per issue is below ₹1,500**, or if the incremental over the carry core is **< 15 bps/yr**. Also close if the screen cannot reconstruct basis-of-allotment probabilities for at least **500** issues. |
| **Arithmetic or inferential** | **Inferential.** σ of listing-day return ≈ 30% **(working)**; n ≈ 600–800 issues over 10–12 years → **MDE per issue = 2.80 × 30% / √700 = 3.18%** against ½ × 10% = 5.0%. **Passes H4.** The measurability is fine; the economics are the question. |
| **AI role** | `ai.extract` parses the RHP and the basis-of-allotment document into typed fields (issue size, retail quota, price band, lot size, subscription ratios by category, allotment ratio). Deterministic cross-check against the exchange's subscription file. **No model output enters the apply/skip decision** — the rule is a published, hand-written threshold on extracted fields. |

### Book N (rank 5) — Market-neutral, cash versus index futures. DROPPED at H0.

Named and computed so it cannot be re-proposed by assertion. This is the candidate the brief asked to
be tested; it fails five independent binding tests at ₹50 lakh.

Construction under test: long a ₹40 lakh Nifty 200 basket, short Nifty index futures to neutral.

| # | Kill | Number |
|---|---|---|
| **1** | **No borrow** | The cash-short variant does not exist. SLBM R3 (17 Aug 2026) has no repay, recall or rollover; retail is structurally the lender; borrow is proprietary. There is no locate to write into a runbook. |
| **2** | **Lot indivisibility** | Hedge available only in ₹15,52,000 steps. k = 3 → ₹46,56,000 short vs ₹40,00,000 long → **net −₹6,56,000 = −13.1% of equity**. k = 2 → **+17.9%**. Best achievable \|net beta\| = **0.131**, contributing **1.83%/yr of equity volatility** at Nifty σ = 14% — from the hedging error alone. |
| **3** | **Tax-bucket non-fungibility** | Long-leg gain s.198/s.196; hedge-leg P&L s.66 non-speculative. A year in which the basket gains ₹3,00,000 and the hedge loses ₹2,90,000 (gross **+₹10,000**) produces tax of 13.0% × (3,00,000 − 1,25,000) = **₹22,750** and a ₹2,90,000 business loss carried 8 years against income this desk does not generate. **After tax: −₹12,750 on a profitable year.** |
| **4** | **STT on notional** | Monthly roll: 3 lots × ₹939.58 × 12 = **₹33,825/yr = 68 bps of equity**, of which STT is 3 × ₹776 × 12 = **₹27,936 = 56 bps**. Plus ₹6,76,376 of SPAN + 25% buffer locked (13.5% of equity), plus a **₹2,32,800 same-cycle MTM call** on a 5% adverse index day against an unrealised offsetting gain. Neutrality doubles the gross and therefore the toll; it does not change the net exposure being paid for. |
| **5** | **Measurability** | The residual return of a neutral book **is** cross-sectional alpha. Rev 1.0: σ 8%, T 20 yr, **MDE 5.01%/yr against ½ × 2.0% = 1.0% — fails 5.0×**. Hedging adds 68 bps of cost to the numerator and nothing to the sample. |

**Reopen requires all three of:** (a) a retail-accessible locate published in a SEBI reformed-SLBM
circular; (b) index lot notional at or below **₹5,00,000** (≤ 10% of equity at the design point); and
(c) a cross-sectional Indian effect that clears H4 on its own, before any hedge is added. Two of
three is not enough. `AI role: none.`

### Book T (rank 6) — Nifty time-series momentum overlay. CLOSED at H0.

The systematic expression of the investor's stated bearish view, named so the view cannot enter the
desk through a side door.

Hypothesis: a 12-month time-series momentum rule on the Nifty 50, monthly cadence, expressed as long
1 lot / flat / short 1 lot of the index future, delivers 3–5%/yr gross by being out of the market
during declines.

| Test | Number | Verdict |
|---|---|---|
| **H4 measurability** | σ_ann of the overlay ≈ 13%; T = 21 yr of usable Nifty history → **MDE_ann = 2.80 × 13% / √21 = 7.90%/yr** against ½ × 4.0% = 2.0% | **Fails 4.0×.** And unlike Book A in Rev 1.0, **waiting does not fix it** — T is already 21 years. Reaching MDE ≤ 2.0% needs T = 331 years. This is a permanent closure, not a deferral. |
| **Granularity** | The sleeve's beta steps 0 → 0.31 → 0.62 in one lot. There is no such thing as a 5% position. | Fails the §3 beta cap on the first signal. |
| **Tax** | F&O P&L is s.66 non-speculative at **31.2%**, against a carry core taxed at 13.0%. A winning overlay is taxed at 2.4× the rate of the book it sits beside. | Structural. |
| **Cost** | 4 signal flips/yr × ₹939.58 = ₹3,758 = **7.5 bps of equity.** | Cheap — and the *only* test this book passes. |

**The honest finding, and it is the answer to the investor's sentiment:** you do not need an algo to
be short Indian beta. Not holding it is free, instantaneous, and available today. What you need an
algo for is **being paid while you do not hold it** — which is Book C. A directional index overlay
converts a free decision into a 31.2%-taxed, 4.0×-unmeasurable, 31%-granular position. Closed.
`AI role: none.`

### 7.1 Books carried forward from Rev 1.0

| Rev 1.0 book | Rev 2.0 status | Reason |
|---|---|---|
| **L — holding-period ledger** | **Becomes Book S, revalued 95–130 bps → 50–80 bps** | The machinery is correct; its rupee value was levered to an 11% beta core the investor declines. |
| **P — packaged vs self-run factor** | **Superseded.** `docs/archive/p1-stop.md` already defaulted to packaged. | Rev 2.0's factor sleeve is zero. The packaged-vs-self logic survives, re-pointed at Book C: the packaged vehicle *is* the market-neutral book. |
| **B — SLBM lending** | **Closed by absence of inventory** | The desk holds almost no individual stock; MF and ETF units are outside the SLB universe. Not a disagreement with Rev 1.0's gate. |
| **A — CAS auction dislocation** | **Deferral inherited, 2027-08-31** | Unchanged. MDE 36.4% today. Rev 2.0 adds no data and no reason to look early. |
| **M — self-run momentum** | **Stays closed**, MDE 5.01× | Unchanged. |
| **R — results-season drift** | **Stays closed**, MDE 7.6× | Unchanged — but `ai.extract` **does not die with it** in Rev 2.0 (§10). |
| **Index option premium selling** | **Stays closed** | Rev 1.0's three kills stand, and the reopen conditions are inherited verbatim. |

---

## 8. Hurdles, STOP numbers, and the beta report

The investor de-emphasised "beat NIFTYBEES after 13% LTCG" as the life goal. Rev 2.0 therefore makes
the **primary hurdle a rupee, low-beta hurdle** — and still prints the NIFTYBEES comparison every
quarter, in both directions, so that neither beta nor anti-beta is smuggled in as free.

### 8.1 The hurdle ladder

| # | Hurdle | Number | STOP |
|---|---|---|---|
| **R0 — Existence** | Book C after-tax yield ≥ **after-tax sweep-FD rate + 25 bps** | At FD 6.60%: FD after tax **4.54%**; Book C must clear **4.79%**. Design case **5.19%**. The 25 bps is the operational cost of running an MF sleeve — statements, tranche ledger, CA time. | Fails → **the desk has no reason to exist.** Move to sweep FD, write the X review, stop. |
| **R1 — Primary (rupee, low-beta)** | Desk after-tax rupee return ≥ **after-tax 91-day T-bill roll + 150 bps**, **and** realised rolling-4-quarter Nifty 50 beta ≤ **0.15**. Both legs. | T-bill 5.60% **(working)** → after tax 3.85% → hurdle **5.35% = ₹2,67,500** at ₹50 lakh. Design central case **5.50% = ₹2,75,000**. **Clears by 15 bps.** | Fails the rupee leg → close the gated books, collapse to C + S. Fails the beta leg → the beta register is being violated; halt and review §12. |
| **R2 — Activity** | Books E and I together add ≥ **50 bps/yr** after cost, after tax, **net of the carry-core return they displace** | Derivation: the sleeve's self-inflicted drag is 52 bps displaced carry + ~14 bps friction (23.8 bps × 4 turns on a ₹5 lakh sleeve) + ~10 bps STCG-vs-LTCG differential. Netting the displacement into the measure leaves the bar at the operational-risk premium for two books, PDF extraction, tender mechanics and allotment tracking: **50 bps = ₹25,000/yr.** | Below 50 bps for two consecutive quarters → both books close, capital returns to Book C, and the extraction pipeline is archived. |
| **R3 — NIFTYBEES report (reported, never a kill)** | After-tax return and realised beta against **Nifty 50 TRI net of 0.04% TER, taxed at 13.0% on realisation**, printed quarterly with the rupee cost of the beta decision | See §8.3. | **No STOP.** A beta-free desk trailing a rising market is a priced decision, not a failure. |
| **H1 — Cost and tax fidelity** | Inherited from Rev 1.0 and extended: `costs` reproduces a real contract note to **₹1**, **and** an AMC account statement and MF capital-gains statement to **₹1**; `tax` reproduces a hand-worked Tax Year 2026-27 computation to **₹1** across s.198, s.196, s.50AA, s.66 speculative and s.66 F&O | | Fails → **the platform stops.** No book proceeds on an unverified cost model. |
| **H4 — Measurability** | Inherited verbatim: **MDE_ann = 2.80 σ/√T ≤ ½ × E_net**, pre-registered before the first peek, **5 specifications per book** | Book E 0.71% vs 0.75% (marginal pass). Book I 3.18% vs 5.0% (pass). Book N fails 5.0×. Book T fails 4.0×. | A book whose MDE exceeds half its pre-registered effect closes at H0. Sixth spec → closes regardless of result. |
| **H5 — Capacity** | Carry core redeems at NAV with **zero market impact**. Each event position ≤ **10% of the name's 20-day median delivery value** and ≤ 6% of equity. | Capacity is slack at every sleeve. | Fails → reduce the clip, not the hurdle. |
| **H6 — Operability** | One machine, **two run windows** (09:00 reconcile, 23:15 treasury), ≤ **8 orders/second**, exchange algo ID on every order, MF cut-off assertions enforced in code, manual fallback exercised | §11. | Needs a second machine, a second broker, or intraday supervision → **stop and redesign.** |
| **R7 — Whole-desk STOP** | **Any** of: after-tax return below the after-tax T-bill roll in a tax year; peak-to-trough NAV drawdown > **6%** of equity; realised rolling-quarter Nifty beta > **0.30**; Book C below R0 | A near-zero-beta desk that draws down 6% has a broken model, not bad luck. | Halt all active books, hold the carry core or FD, write `docs/archive/x0-review-YYYY-MM.md`. |

### 8.2 The uncomfortable number, stated up front

**The arithmetic books alone do not clear R1.** Book C + Book S deliver **5.19–5.20% after tax**
against an R1 hurdle of **5.35%**. The desk clears its own primary hurdle only if Books E and I
together add **at least 15 bps** — and Book E's central incremental estimate is **negative**.

Three honest consequences:

1. **R1 is deliberately set where it bites.** A hurdle the design clears by construction is
   decoration. This one is 15 bps away from failing.
2. **If Book C's realised yield falls 30 bps, the whole desk fails R1** even with both gated books
   open at their central estimates. The single largest fragility in Rev 2.0 is one **(working)**
   number, and it is the first thing a human must verify (Appendix A, W1).
3. **The fallback is not zero.** R1 failure collapses the desk to C + S, which still beats sweep FD by
   65 bps and a liquid fund by 134 bps at zero beta. **"Buy the arbitrage fund, tranche it, and stop"
   is a completed decision, not a defeat** — and it is the most likely outcome of this design.

### 8.3 The beta report — printed quarterly, in both directions

| Line | Number, printed every quarter |
|---|---|
| Desk after-tax rupee return, tax-year to date | ₹ and % |
| Realised Nifty 50 beta, rolling 4 quarters | decimal, against caps 0.15 / 0.25 / 0.30 |
| **NIFTYBEES benchmark**: Nifty 50 TRI net of 0.04% TER, taxed at 13.0% on realisation | ₹ and % |
| **Cost of the beta decision** | (benchmark − desk) × capital, in rupees |
| Trailing-12-month realised value of the same line | ₹ |

**Both directions matter, and both are printed.** Over the twelve months to 8 Sep 2026, Nifty 50 was
~−4% price (TRI ~−2.7% at a ~1.3% dividend yield **(working)**), so a zero-beta desk earning +5.5%
after tax would have beaten NIFTYBEES by roughly **820 bps** with beta 0.084. **That is one year of a
benchmark that happened to fall, and it is not evidence.** Nifty 50 TRI has compounded ~11–12% over
twenty years; at that rate the beta decision costs **475 bps/yr = ₹2,37,500 at ₹50 lakh**. The
register prints the realised cost, not the assumed one, and it prints it whether it is positive or
negative. **Neither the investor's view nor the market's history is allowed to be free.**

---

## 9. Research harness

Inherited from Rev 1.0's H0 in full — `src/harness.py`, MDE_ann = 2.80 σ/√T, the typed
`PreRegistration` record with a file SHA taken before the first data access, `spec_budget_guard`
refusing a sixth specification, and `date_shift_test` for look-ahead. Four Rev 2.0 amendments:

1. **Event books pre-register two MDEs, not one.** A per-event MDE and an annualised MDE derived from
   the **realised** events-per-year in the corpus, never from a hoped-for count. A book that clears
   per-event and fails annualised is closed. Book E's event-count floor (250 usable events over 12
   years) is part of its pre-registration, not a screen output.
2. **Point-in-time for documents, not just prices.** Rev 1.0's PIT discipline was built for a price
   panel. Rev 2.0's inputs are majority PDF: SEBI letters of offer, exchange tender circulars, RHPs,
   basis-of-allotment documents, scheme information documents, AMC statements. The PIT rule is the
   same and the trap is different: **a document's usable timestamp is its publication time, not its
   dated time, and an amended letter of offer supersedes the original.** `panel` stores both, keyed by
   retrieval time, and refuses to serve an amendment to a study dated before the amendment landed.
3. **Adverse selection is a pre-registered decomposition, not a robustness check.** Books E and I both
   have outcomes that are conditional on being selected into them. Each pre-registration must state,
   before the screen runs, how the outcome will be decomposed into the selected and unselected
   populations, and what decomposition would close the book.
4. **Spec budget is 5, unchanged, and the apply/skip rule counts as a spec.** A threshold moved is a
   specification used.

Data, and it is nearly all free:

| Source | What | Cost |
|---|---|---|
| **AMFI** | Daily NAV for every scheme, scheme TERs, monthly AAUM — Book C's entire input | ₹0 |
| **AMC / RTA** | Scheme information documents, monthly portfolio disclosures (equity %), factsheets | ₹0 |
| **SEBI** | Letters of offer (SAST), delisting documents, circulars, the FY26 derivatives study | ₹0 |
| **NSE / BSE** | Tender-offer circulars, corporate actions, IPO subscription files, basis-of-allotment, CM-UDiFF bhavcopy | ₹0 |
| **RBI DBIE / auction results** | 91-day T-bill cut-offs, repo, CPI, FBIL USD/INR | ₹0 |
| **NSDL / CDSL** | Consolidated Account Statement — the reconciliation authority for MF units | ₹0 |
| Broker API | Execution and reconciliation for the **event sleeve only** | ₹0–₹500/mo, **not before M7** |

Access discipline is inherited verbatim: session-cookie warm-up, browser user-agent, **≤ 1 request per
2 seconds**, exponential backoff, a content-addressed local cache so any given document is fetched
exactly once ever, and **no fetching between 09:00 and 16:15 IST**.

**Book C, Book S and the ₹0 screens for Books E and I require no paid data and no broker API.**

---

## 10. AI layer — permitted and forbidden

Rev 1.0 concluded that `ai.extract` died with Book R and shipped nothing AI in v1. **Rev 2.0 reverses
that, and the reason is structural rather than a change of taste: this desk's primary inputs are
documents, not prices.** Three of the five load-bearing data sources are semi-structured PDFs
published on regulator and exchange portals with no machine-readable equivalent. That is exactly the
job extraction is good at, and it sits behind a deterministic wall.

### Permitted

| Job | Where | Gate |
|---|---|---|
| `ai.extract.offers` — SEBI letters of offer and NSE/BSE tender circulars → typed fields (offer price, size, record date, window open/close, escrow, conditionality) with per-field confidence and source page | Book E | ≥ **98% field-level agreement** against **200 hand-labelled offers**, **plus** a deterministic cross-check: extracted offer price must equal the exchange circular's to ₹0.01 or the field is refused, not corrected |
| `ai.extract.issues` — RHP and basis-of-allotment → issue size, retail quota, price band, lot, category subscription ratios, allotment ratio | Book I | Same 98% gate against 200 hand-labelled issues, plus a deterministic cross-check against the exchange subscription file |
| `ai.extract.schemes` — SID and monthly portfolio → TER, exit-load window, cut-off, **disclosed equity percentage** | Book C | Same 98% gate; the equity percentage is additionally floored at the SEBI category minimum and refused if the document is older than one quarter |
| `ai.extract.statements` — AMC account statement, MF capital-gains statement, NSDL/CDSL CAS → typed lots for reconciliation | `ops` | Extraction **proposes**; `tax` and `costs` recompute independently; a difference above **₹1** is a reconciliation break that blocks the next run |
| `ai.classify` — route an inbound corporate-action or offer document to a book, or to "ignore" | `ops` | A false positive is caught by the deterministic check; a false negative loses an event and is logged. Bounded downside both ways. |
| `ops` narrative — one paragraph of "what changed, what looks wrong" over the run log, reconciliation diff, tranche ledger and exemption tracker | `ops` | Read-only. It cannot place, cancel, size or redeem. |

### Forbidden

- **Any model output entering a return forecast, a signal, a weight, a position size, a redemption
  timing decision, or the beta switch.** Unchanged from Rev 1.0's L10 and non-negotiable.
- An LLM choosing which arbitrage fund to hold. That is a deterministic screen on yield, TER, beta and
  disclosed equity percentage.
- An LLM deciding whether to apply for an issue or tender into an offer. Those are hand-written
  thresholds on extracted fields, and each threshold move costs a specification.
- An LLM as the **authority** in the ₹1 reconciliation path. Extraction proposes; arithmetic disposes.
- Model-assisted "sanity checking" of a number that `costs` or `tax` produced. If the two disagree,
  the arithmetic wins and the extraction is a bug.
- HMM, LightGBM, MLflow, Kaggle client, Polars in `pyproject.toml` at seed. Unchanged.

**The one-line test:** an AI may read a document the desk would otherwise read by hand. It may not
have an opinion about what the numbers in it are worth.

---

## 11. Platform architecture

### 11.1 What v1 is

**One machine. One AMC channel plus (later) one broker. Two run windows per day.** The desk emits a
human-readable **instruction list** for the next session; every instruction is placeable by hand.
Nothing here needs an intraday loop, and — unlike Rev 1.0 — the core book does not even need a
broker API.

### 11.2 The Indian clock this desk actually lives on

The binding deadline is not the market close. It is the mutual-fund cut-off.

| Time (IST) | Step | Owner |
|---|---|---|
| **08:45** | Read overnight exchange and SEBI circulars: new letters of offer, tender windows opening/closing, IPO opens/closes/basis-of-allotment, corporate actions | `events` |
| **09:00** | **Reconcile** prior day to ₹1 against the broker ledger, the AMC statement and the NSDL/CDSL CAS. **A break blocks every instruction today.** | `ops` |
| 09:00–09:05 | Pre-open phase 1 — market and limit orders permitted | `execute` |
| 09:05–09:10 | Pre-open phase 2 — **limit orders only**; a market order here is rejected | `execute` |
| 09:15 → | Continuous: place event-sleeve legs as limit orders | `execute` |
| **13:30** | **Liquid / overnight fund purchase cut-off** — funds must be *realised* in the AMC account, not merely instructed **(working)** | `treasury` |
| **15:00** | **Arbitrage fund purchase cut-off — the single hardest deadline of the day.** Same realised-funds rule. Missing it costs one day of NAV and shifts the tranche's 12-month crossing date by a day. | `treasury` |
| 15:20–15:35 | CAS: only if an event leg must reference the official close of an F&O-eligible name | `execute` |
| 17:00 | UPI mandate acceptance on an IPO closing day — a timed manual step, asserted, never automated silently | `ops` |
| **23:15** | **Treasury run**, after the AMFI NAV upload **(working: ~23:00 deadline)**: mark the carry core, update the tranche ledger and the 12-month crossing calendar, update the s.198 exemption balance, run the Book C break-even monitor, emit tomorrow's instruction list | all |
| 23:30 | `ops` narrative note over the run log and reconciliation diff | `ops` |

Three consequences the code must encode, not document:

1. **A purchase instruction emitted at 23:15 must clear the bank by 15:00 the next day.** `treasury`
   computes the funds-transfer deadline from the redemption/settlement calendar and refuses to emit an
   instruction whose funding path cannot land in time.
2. **Arbitrage-fund redemption is T+2 (working).** An event found on Monday cannot be funded from the
   carry core before Wednesday. That is why the float exists at 20% and why the event sleeve is capped
   at 10%.
3. **Two closing-price mechanisms still exist** (Rev 1.0 §1.2). `panel` keeps
   `close_method ∈ {vwap_30min, cas_auction}` for every row. Event legs in F&O-eligible names that
   reference the official close go into the **auction**, not into continuous trading after 15:15.

### 11.3 Modules

| Module | Owns | First needed at |
|---|---|---|
| `src/costs.py` | Rev 1.0's full statutory stack **plus** MF stamp duty 0.005%, MF-unit STT 0.001% sell, exit load, tender-window STT, the ₹20 brokerage floor, DP ₹15.34/ISIN/sale-day, and the app-vs-API brokerage trap | **M0** |
| `src/tax.py` | s.196 / s.198 / s.66 speculative / s.66 F&O **plus** specified-mutual-fund treatment (old s.50AA), the equity-oriented test by disclosed equity percentage, the aggregate ₹1.25 lakh exemption ledger, 4-year and 8-year carry clocks, absolute-sum audit turnover, Tax Year boundaries | **M0** |
| `src/treasury.py` | **New.** AMFI NAV ingest; scheme eligibility screen (equity %, beta, TER, AUM, exit load); the **tranche ledger** (lot, date, cost, 12-month crossing date, exit-load expiry); the Book C break-even monitor against 0.79 × y_fd; MF cut-off and settlement calendar | **M1** |
| `src/portfolio.py` | The §3 capital map and every §12 limit, asserted not assumed; the realisation scheduler (Book S); the exemption-consumption plan to 31 March; sleeve beta aggregation | **M2** |
| `src/events.py` | **New.** Offer and issue corpus; deterministic spread and acceptance-ratio computation; the apply/skip and tender/skip rules as hand-written thresholds | **M3** |
| `src/panel.py` | Reduced from Rev 1.0. Daily CM-UDiFF bhavcopy for **event names only**, corporate-action spine, 20-day median delivery value for H5, `close_method`. **This desk does not need a 5,100-session Nifty 500 panel** because it runs no cross-sectional book. | **M3** |
| `src/harness.py` | Rev 1.0's harness plus the four §9 amendments | **M3** |
| `src/execute.py` | Instruction-list generation; MF purchase/redemption instructions; broker orders for event legs under **8 OPS** with the exchange algo ID; pre-open phase-2 and CAS order-type rules; **no F&O order type exists** | **M6** |
| `src/ops.py` | Reconciliation to ₹1 across three authorities (broker ledger, AMC statement, NSDL/CDSL CAS); run log; kill-switch state; the Indian calendar of §11.4; the beta register | **M6** |
| `src/ai/extract.py` | The four extraction jobs of §10, each behind its 98% gate and its deterministic cross-check | **M3** |

### 11.4 Calendar items the code asserts

31 March (tax-year boundary and the last date to consume the ₹1.25 lakh exemption — the desk's harvest
runs by **20 March**, not 30 March); 31 August / 31 October ITR deadlines, **missing which permanently
forfeits loss carry-forward**; advance tax 15 Jun / 15 Sep / 15 Dec / 15 Mar; every tranche's
12-month crossing date and exit-load expiry; every open tender window's close; every open IPO's UPI
mandate deadline; the quarterly Book C break-even review; the quarterly beta report; **Rev 1.0's Book
A review on 2027-08-31**, inherited unchanged.

### 11.5 Not in v1 — explicit

Redis. Kafka. Kubernetes. Docker orchestration. Tick replay. Order-book reconstruction. Multi-broker
routing. A web dashboard. FIX. Colocation. Any intraday loop. Any second machine. Polars until a
module actually imports it. **Any F&O order type.** Any cross-sectional factor panel. Every one of
these is a cost with no counterparty on a desk whose binding constraint is a tax classification.

---

## 12. Risk and operations — the numbers the code asserts

| Limit | Number | Why this number |
|---|---|---|
| Gross exposure | ≤ **100%** of equity; borrowed rupees **0** | No MTF, no margin funding, no pledge for leverage. |
| **Net Nifty 50 beta, default state** | ≤ **0.10** | §3 map computes 0.084. |
| **Net Nifty 50 beta, hard cap** | ≤ **0.25** | Beta register fully on (15% index fund) plus the default 0.084. |
| **Realised rolling-quarter beta STOP** | > **0.30** → halt | Beta-smuggling detector. A carry desk cannot drift into being an equity desk. |
| Single AMC | ≤ **30%** of equity (₹15,00,000) | AMC operational risk is real (Franklin Templeton, Apr 2020). Minimum **two** AMCs, always. |
| Single scheme | ≤ **30%** of equity | Same. |
| Arbitrage-fund scheme beta | ≤ **0.10**, measured on 3-year weekly NAV | Assumed beta is how a neutral sleeve becomes a long one. |
| Disclosed equity percentage of any "equity-oriented" holding | ≥ **65%**, read from the latest monthly portfolio, refused if older than one quarter | The tax classification depends on it. |
| Single event position | ≤ **6%** of equity (₹3,00,000) and ≤ **10%** of the name's 20-day median **delivery** value | Rev 1.0's H5 discipline, inherited. |
| Concurrent event positions | ≤ **4** | Sleeve cap 15% of equity. |
| IPO applications | ≤ **₹2,00,000** per issue (statutory), ≤ **3** concurrent (₹6,00,000 = 12% of equity blocked) | ASBA blocks funds in the bank; the carry core cannot serve as float. |
| Liquidity floor | ≥ **20%** of equity redeemable to bank within **T+1**, at all times | Arbitrage funds are T+2. |
| Exit-load breach | **Refused**, unless the redemption is a STOP action | 0.25% is 5× a month of carry. |
| F&O positions | **0, always** | Rungs 2 and 4. Designed out, not managed. |
| Naked short options | **0, always** | Rev 1.0 §2.4, inherited. |
| Single-stock derivatives | **0, always** | Physical settlement, MWPL, ban list. Inherited. |
| Short cash positions | **0, always** | Rung 3 — no locate. |
| Order rate | ≤ **8 orders/second** in code, against TOPS 10 | Keeps the desk out of client-level algo registration. |
| Untagged order | **Refused** | Exchange algo ID on every order or it is not sent. |
| Family perimeter | Self, spouse, dependent children, dependent parents **only** | SEBI retail-algo framework. Never an algo provider, RA or PMS. |
| **Peak-to-trough NAV drawdown STOP** | > **6%** of equity → halt all books | A desk designed for β ≤ 0.10 and σ ≈ 2% that draws down 6% has a broken model, not bad luck. |
| **Whole-desk STOP (R7)** | After-tax return below the after-tax T-bill roll in a tax year | Halt, hold the carry core or FD, write the X review. |

### 12.1 Risks specific to Rev 2.0

| Risk | Exposure | Mitigation |
|---|---|---|
| **Reclassification of arbitrage funds out of equity-oriented** | The entire 134 bps thesis, on 55% of capital, overnight | Written CA opinion **before the first rupee** (M6 gate); `tax` classifies by disclosed equity percentage rather than category label; quarterly re-read of the monthly portfolio |
| **Basis compression** | Index futures ADT ~−44% Mar→May 2026; NSE Aug 2026 volumes −22.6% MoM; the 1 Apr 2026 STT hike is a **~36 bps/yr (working)** drag on a monthly-rolled arbitrage book | The R0/Book C break-even monitor runs monthly on AMFI NAV and closes the book at 0.79 × y_fd, before opinion is involved |
| **Arbitrage-fund AUM inflow** | Retail crowding compresses the spread the funds harvest | Same monitor. The kill is a ratio, not a level, so it survives a change in the rate environment |
| **A single-AMC operational failure** | ₹27.5 lakh in one trust | ≥ 2 AMCs, ≤ 30% each, and the NSDL/CDSL CAS is an independent reconciliation authority |
| **Missing the 15:00 MF cut-off** | One day of NAV; the tranche's 12-month crossing date shifts | `treasury` computes the funding deadline and refuses an instruction it cannot fund in time |
| **Redeeming inside the exit-load window** | 0.25% = 5× a month of carry | `portfolio` refuses; only a STOP can override, and the override is logged in rupees |
| **Event-sleeve adverse selection** | The whole of Books E and I | Pre-registered decomposition (§9.3); a hard incremental hurdle over the carry core (R2); expected outcome recorded as closure |
| **The app-vs-API brokerage trap** | ₹600 vs ₹25 on a ₹3 lakh position held past 30 days | `execute` re-prices any event position at day 25 and refuses a silent manual hand-off |
| **Missed ITR deadline** | Permanent forfeiture of loss carry-forward | Hard calendar item with a 30-day warning, inherited from Rev 1.0 |
| **Anti-beta drift becoming an unexamined view** | The investor's bearish view calcifying into a permanent, unpriced position | §8.3 prints the rupee cost of the decision every quarter, in both directions |
| **SEBI algo framework breach** | Applicable to all brokers since 1 Apr 2026 | 8 OPS cap in code, algo ID asserted, static-IP OAuth with 2FA, daily token renewal as an explicit step. Note the carry core sends **no exchange orders at all** |

---

## 13. Twelve-month staged build

Every milestone before **M6** costs **₹0** in software and data. Live capital is blocked until M6.
Broker-API spend is blocked until **M7** and may never be incurred at all.

| ID | Weeks | Spend | Build | Exit — a number |
|---|---|---|---|---|
| **M0** | 1–3 | ₹0 | `costs` and `tax` extended: MF stamp duty, MF-unit STT, exit load, tender STT, the app-vs-API trap; specified-mutual-fund treatment, the equity-oriented test by disclosed percentage, the aggregate exemption ledger | **H1 to ₹1** against a real contract note, a real AMC account statement and a real MF capital-gains statement; a hand-worked Tax Year 2026-27 computation to ₹1 across s.198, s.196, s.50AA and both s.66 heads |
| **M1** | 3–6 | ₹0 | `treasury`: AMFI NAV ingest, direct-plan arbitrage-fund universe, 5-year realised net-of-TER yield with the **post-1-Apr-2026 period measured separately**, worst rolling 1-month and 3-month return, 3-year weekly-NAV beta, break-even monitor | **Book C verdict with a number.** Open only if the trailing 3-year net yield ≥ 0.79 × the prevailing sweep-FD rate **and** the post-Apr-2026 sub-period does not breach it. Otherwise `docs/archive/book-c-stop.md` and the desk is an FD |
| **M2** | 6–9 | ₹0 | `portfolio`: the §3 map and every §12 limit asserted; the tranche ledger; the Book S realisation scheduler and exemption-consumption plan | A simulated 24-month schedule shows a rolling 1/12 crossing the 12-month line monthly and the ₹1.25 lakh exemption consumed by **20 March**; every §12 limit has a test that fails on a **₹1** breach |
| **M3** | 9–14 | ₹0 | `events` corpus (12 years of SEBI letters of offer and exchange tender circulars, cached); reduced `panel`; `harness` amendments; `ai/extract.py` for offers and issues | **≥ 98% field-level agreement** on 200 hand-labelled documents per extractor, with the deterministic cross-check live; **n, σ, MDE per event and annualised published before any spread is computed** |
| **M4** | 14–18 | ₹0 | Book E ₹0 screen | Open only if: median after-cost after-tax net per event ≥ **0.80%**, ≥ **8** arbitrageable events/yr, ≥ **250** usable events in the corpus, and incremental over the carry core ≥ **25 bps/yr**. Else `docs/archive/book-e-stop.md` |
| **M5** | 16–22 | ₹0 | Book I ₹0 screen, with the adverse-selection decomposition | Open only if: allotment-probability-weighted after-tax EV per issue ≥ **₹1,500**, ≥ **500** reconstructible issues, incremental ≥ **15 bps/yr**. Else `docs/archive/book-i-stop.md` |
| **M6** | **week 20** | ₹0 | **FIRST RUPEE GATE** | All of: H1 to ₹1; Book C open with a number; the tranche ledger simulated; **20 consecutive paper sessions with zero reconciliation break above ₹1**; a **written CA opinion** on the equity-oriented status of the chosen schemes and on the capital-gains treatment of tender proceeds; the beta register signed at zero. **First deployment: Book C only, two tranches of ₹5,00,000, thirty days apart.** Everything else in sweep FD |
| **M7** | months 6–9 | **₹0–₹6,000/yr** | **API spend starts here, or never.** Only if Book E or Book I opened. Prefer a ₹0 tier (Fyers / Angel SmartAPI / Upstox / Kotak Neo Trade); Kite Connect ₹500/month only if the free tier fails L0-equivalent testing | `execute` demonstrably refuses: an untagged order, a market order in pre-open phase 2, a ninth order in one clock second, an order breaching any §12 limit, a redemption inside an exit-load window, and an MF instruction whose funding cannot land by 15:00 |
| **M8** | months 9–12 | ₹0 | Event books live at **one-third size** for one full quarter | Two consecutive quarters of positive **incremental** contribution over the carry core before full size. R2 measured, not asserted |
| **X** | quarterly, from month 6 | ₹0 | Kill review | R0, R1, R2, the beta report, the working-numbers register, spend against the ladder, and every reopen condition in §14 checked as a list |

**Spend ladder:** Tier 0 = ₹0 through M6 and every screen. Tier 1 = ₹6,000/yr, unlocked at M7 only.
Tier 2 = ₹8,400 one-off for three months of minute bars, only against a named exit criterion in a
specific pre-registration — **no book in Rev 2.0 currently has one.** Tier 3 = ₹35,000/yr hard
ceiling, never exceeded before a book is live and after-tax profitable for two consecutive quarters,
and it exists mainly to pay for the CA engagement. NSE Data & Analytics, CMOTS/Accord and LSEG India
are outside the envelope. **Do not contact them.**

**The most likely spend profile for this desk over twelve months is ₹0 in software and one CA
invoice.** Book C needs no broker API — MF purchases route through the AMC, RTA, MF Utility or an
exchange MF platform. The first live rupee therefore costs nothing to deploy, which is the correct
answer for a design whose central case is "buy the packaged neutral book and tranche it".

---

## 14. What would change this design

Named Indian triggers, stated in advance so a later agent recognises one rather than rationalises one.

1. **Arbitrage-fund net-of-TER yield below 0.79 × the sweep-FD rate for two consecutive quarters** →
   Book C closes, the desk collapses to FD, and Rev 2.0 has no thesis left. **This is the trigger to
   watch.**
2. **Arbitrage funds reclassified out of equity-oriented** — by a SEBI change to the category's equity
   minimum, or a CBDT position that hedged equity does not count toward the 65% test → the entire
   design is repriced from rung 1 down. Largest single regulatory risk in this document.
3. **A change to s.198's 12.5% rate or the ₹1.25 lakh threshold** → re-derive §3.1 and §6.3. The
   saturation point moves linearly with the threshold.
4. **Derivative STT reduced** → arbitrage-fund gross yields rise by roughly the reduction × the fund's
   roll count (**~12× (working)**); Book C improves; Rev 1.0's futures and option closures are also
   arithmetic and must be re-run.
5. **India VIX 30-day median above 18 for a full quarter** → the cash-futures basis widens (good for
   Book C) **and** Rev 1.0's option-premium reopen condition's first leg is met. Both are checked; the
   option reopen still needs its other three legs.
6. **A SEBI reformed-SLBM circular that gives a retail PAN a real locate** → rung 3 falls; Book N gets
   one of its three reopen conditions.
7. **Index lot notional at or below ₹5,00,000** (≤ 10% of equity at ₹50 lakh) → rung 2 falls; Book N
   gets its second. Hedging becomes constructible at this capital for the first time.
8. **A measurable Indian cross-sectional effect clearing H4 on free data** → Book N's third. All three
   together, and only then, reopen the market-neutral identity with fresh arithmetic.
9. **Buyback small-shareholder reservation restored with capital-gains rather than deemed-dividend
   treatment** → reopens a genuinely retail-only event edge that statute removed on 1 Oct 2024.
10. **T+0 settlement actually mandated, or same-day MF switch** → the event sleeve's funding path
    shortens, the 20% float can shrink, and more capital moves to the carry core.
11. **Capital crossing ₹75 lakh** → the exemption saturates at 41% of the core by ₹1 crore, the edge
    over FD narrows toward ~45 bps **(working)**, and §3 must be re-derived before, not after.
12. **The investor's beta view changes** → it is recorded in the beta register, signed and dated, with
    the §8.3 rupee cost attached. It does not enter the code as a parameter default.

---

## Appendix A — working-numbers register

Nothing tagged **(working)** may be used in a live decision until it is resolved by the named
milestone. Items W1 and W6 are the two that a human must verify **before reading any further into
this design**, because the whole thesis rests on them.

| # | Number used | Verify at | How |
|---|---|---|---|
| **W1** | **Arbitrage-fund category net-of-TER yield 5.60%/yr** | **M1 — before anything** | AMFI daily NAV, direct plans only; 1/3/5-year rolling annualised; the **post-1-Apr-2026 sub-period measured separately** because the STT hike lands inside it; worst rolling 1-month and 3-month return reported alongside |
| W2 | Post-Apr-2026 derivative-STT drag on a monthly-rolled arbitrage book ≈ **36 bps/yr** (0.03% × 12) | M1 | Scheme monthly portfolio turnover disclosures and factsheets; compare realised yield either side of 1 Apr 2026 across ≥ 10 schemes |
| W3 | Sweep FD **6.60%** | M1, and on the day of every review | The actual bank card, not an aggregator |
| W4 | 91-day T-bill **5.60%** (the R1 hurdle base) | M1, quarterly | RBI auction results / DBIE |
| W5 | Arbitrage-fund beta to Nifty 50 ≤ **0.10** | M1 | 3-year weekly-NAV regression per scheme; a scheme above 0.10 is not eligible |
| **W6** | **Equity-oriented status of arbitrage funds for s.198**, i.e. hedged equity counting toward the ≥ 65% test | **M6 — written CA opinion, before the first rupee** | Read the ITA 2025 definition of equity-oriented fund and the SEBI category circular; obtain the opinion in writing. **If this is wrong, Book C is −0 bps and a penalty.** |
| W7 | Section number under ITA 2025 for specified mutual funds (old s.50AA), and the 35–65% / 24-month rule | M0 | Read the Act. Rev 1.0 mapped s.111A→196, s.112A→198, s.112→197, s.43(5)→66; the specified-MF provision was not mapped |
| W8 | MF stamp duty **0.005%** on purchase, switch-in and SIP | M0 | Indian Stamp Act amendment effective 1 Jul 2020; confirm against an actual MF transaction statement |
| W9 | Arbitrage-fund exit load **0.25% within 15–30 days** | M1 | Read every candidate SID; store the window per scheme in `treasury` |
| W10 | Equity-oriented MF purchase cut-off **15:00 IST with realised funds**; liquid/overnight **13:30 IST** | M1 | SEBI circular on uniform cut-off and realisation of funds; confirm with the chosen AMC in writing |
| W11 | Arbitrage-fund redemption settlement **T+2** | M1 | AMC scheme documents; the 20% float sizing depends on it |
| W12 | AMFI NAV upload deadline ≈ **23:00 IST** (drives the 23:15 treasury run) | M1 | AMFI/SEBI NAV disclosure norms |
| W13 | **STT on shares tendered through the exchange tender-offer window = 0.10% delivery rate on the seller** | M3, **before Book E opens** | A real tender-window contract note. A 10 bps error flips a 0.5%-per-event book |
| W14 | Tender proceeds and IPO listing gains treated as **capital gains**, not business income, under a consistent CBDT Circular 6/2016 position | M6 — written CA opinion | Same opinion as W6 |
| W15 | Open offers **20–35/yr**, arbitrageable **8–12/yr**, σ **4%/event**, net **1.0%/event** | M3–M4 | The 12-year corpus itself. These are the pre-registration inputs and must be published before any spread is computed |
| W16 | IPO listing-day σ **30%**, n **600–800** over 10–12 years, EV/issue | M5 | Exchange issue files and basis-of-allotment documents; decomposed by realised allotment probability |
| W17 | Event-position beta ≈ **0.40** while held | M4 | Measured on the corpus, not assumed; feeds the §3 beta aggregation |
| W18 | Nifty 50 −4% and S&P 500 +19% over one year to 8 Sep 2026; Nifty 50 dividend yield ~1.3% | M1 | NSE Indices TRI and the S&P index series. Used only in the §8.3 report, never in a size |
| W19 | Edge over FD narrows to ~**45 bps** at ₹1 crore | X review before ₹75 lakh | Re-run §6.3 at the higher capital with the exemption held constant |
| W20 | Equity savings funds: 35–65% equity → 12.5% LTCG after **24 months** | M0 | Read the amended provision. Only needed to keep the category closed for the right reason |

Inherited unresolved from Rev 1.0 and still open: **W6** (NSE monthly impact-cost file, needed for
H5 on event positions), **W13** (SBI Nifty 50 ETF AUM composition — now irrelevant unless the beta
register is switched on), **W15** (vendor prices, re-checked on the day of purchase), **W16** (Book A's
hypothesised effect, still dated 2027-08-31).

---

*Active charter. Milestone map: [§13](#13-twelve-month-staged-build). Supersedes [india-equity-architecture-blueprint.md](../archive/india-equity-architecture-blueprint.md) (Rev 1.0).*
