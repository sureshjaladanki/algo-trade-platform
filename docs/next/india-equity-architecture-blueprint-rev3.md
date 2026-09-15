# Retail India desk — Architecture Blueprint, Rev 3.0

| | |
|---|---|
| **Date** | 2026-09-10 |
| **Status** | **BLUEPRINT Rev 3.0 / DRAFT — competing charter; does NOT replace Rev 2.0** |
| **Review** | Claude Opus |
| **Scope** | Listed Indian equity **ETFs and index funds** — broad, sectoral, thematic, factor (NSE / BSE). Own capital only. |
| **Brief** | Moderately aggressive (4/5). Horizon asked: **intraday versus ~7 calendar days (5 sessions)**. Stated motive: avoid a range-bound Nifty 50 (cited −6% vs S&P 500 +16% over one year). |
| **Does not replace** | [india-equity-architecture-blueprint-rev2.md](india-equity-architecture-blueprint-rev2.md) (Rev 2.0, **ACTIVE**) |
| **Superseded** | [india-equity-architecture-blueprint.md](india-equity-architecture-blueprint.md) (Rev 1.0 Nifty-beta) |
| **Companion** | [india-equity-execution-plan-rev3.md](india-equity-execution-plan-rev3.md) |
| **P0 posture** | **Unchanged until a human accepts Rev 3.0.** Live limits are [Rev 2.0 §12](india-equity-architecture-blueprint-rev2.md#12-risk-and-operations--the-numbers-the-code-asserts) |
| **Authorisation** | **Nothing here authorises a rupee, a module, a dependency, or a data purchase.** |

## This is a competing charter, not a re-scope

Rev 2.0 is ACTIVE. [Rev 2.0 §12](india-equity-architecture-blueprint-rev2.md#12-risk-and-operations--the-numbers-the-code-asserts), [Rev 2.0 §8](india-equity-architecture-blueprint-rev2.md#8-hurdles-stop-numbers-and-the-beta-report), every pre-registration
in `docs/next/` and every STOP memo in `docs/archive/` remain in force. P0, U0, H0, L1 and L2 are DONE;
P1 is STOPPED with a packaged default; L0 is in paper. **This document changes none of that.** A human
reads Rev 2.0 and this file and picks one.

Three briefs, three charters:

| Rev | Investor brief | Default holding | Primary hurdle |
|---|---|---|---|
| **1.0** | Accept Indian equity beta; harvest the tax and cost arithmetic on top of it | Packaged Nifty 50 + Book L realisation schedule | H2: beat Nifty 50 TRI by 300 bps |
| **2.0** | Decline that beta; want after-tax rupee carry at β ≈ 0 | Direct-plan arbitrage funds, tranched | R1: after-tax T-bill + 150 bps **and** β ≤ 0.15 |
| **3.0** | Risk 4/5; **1-day to 5-session ETF trading**; wants net rupees when Nifty is flat or down | **This file's product is a verdict and a screen, not a 5-session book** | H2 **and** H2-ABS, simultaneously — see §3.4 |

Rev 1.0 closed sector and thematic ETFs in a single line: *"higher TER, wider spreads, and concentration
that 4/5 risk does not license."* This brief asks that line to be re-opened and computed. It is computed
here, in full, and the closure holds — but **not for the reason Rev 1.0 gave**. Statutory friction on ETF
units is *not* the binding constraint; §5 shows it is 2.7–3.9 bps, a fifth of a stock's. What binds is the
quoted spread on everything that is not a Nifty 50 ETF, s.196 on every gain a 5-session book will ever
realise, the 25% sector cap, and a sample-size requirement measured in centuries. Rev 1.0's verdict was
right and its stated reason was incomplete. That correction is this document's first contribution.

Statutory rates, lot notionals, the option-premium kill, the MDE formula, the SEBI algo perimeter and the
capital envelope are **imported from Rev 1.0 and cited, not re-derived**. Numbers new to Rev 3.0 that are
not sourced to a statute, circular or published schedule are tagged **(working)** and registered in
[Appendix A](#appendix-a--working-numbers-register).

---

## 0. One-line thesis

At ₹50 lakh, on a 50–500 ms retail API, in a market that taxes every gain realised inside twelve months at
**20.8% from the first rupee** and charges the spread rather than the statute for anything less liquid than
NIFTYBEES, **cadence dominates the forecast**: the same 8%/yr gross return delivered through fifty
five-session round trips nets **0.32%/yr**, and delivered through one thirteen-month hold nets **6.89%/yr**
(§3.1) — so a 1-day or 7-day sectoral ETF book is not a strategy with a cost problem, it is a **cost
structure with a strategy attached**; and because the 4/5 sector cap converts sleeve alpha into desk alpha
at 0.25× while friction is paid at 1.0×, a 5-session rotator must produce **22.75%/yr of gross sector alpha**
to move the desk 300 bps (§3.2), against a minimum detectable effect that needs **848 years** of
point-in-time history to see 2%/yr (§3.3). **The desk that can exist is the one Rev 1.0 and Rev 2.0 already
describe**: a packaged, tax-deferred *different* Indian beta held past the twelve-month line for an investor
who still wants India (Book W), or Rev 2.0's β ≈ 0 carry container for one who does not — plus one genuinely
new, genuinely free deliverable this brief earns, which is the ETF tradability ledger (Book V).

---

## 1. The six questions, answered

Verdicts use Rev 1.0's vocabulary: **VIABLE** (a book may be built), **CANDIDATE-GATE** (a ₹0 screen with a
pre-committed kill number decides), **CLOSED** (do not revisit without the named Indian change).

| # | Question as asked | Verdict | The number that decides it |
|---|---|---|---|
| **Q1** | In a given trading day, can the direction of one or more sectoral indices be predicted? | **CLOSED** | Break-even accuracy **60.0%** at 14 bps all-in against an 81 bps median Bank session; **impossible at any accuracy** on a 132 bps quote. Magnitude is free; the sign is the scarce object. |
| **Q2** | Does the platform have an edge on sectoral indices/ETFs over the broader market? | **Exists at 6–12 months; CLOSED at 5 sessions** | The 6–12 month cross-section is already packaged at 0.30–0.34% TER with no investor-level realisation. A self-run 5-session version pays **760 bps/yr** of friction and 20.8% on every gain. |
| **Q3** | Can it predict a move ≥ round-trip cost? | **Yes — and it is the wrong question** | P(\|Bank session move\| ≥ 15 bps) = **89.9%**. The cost filter passes nine sessions in ten. It provides no information about sign. |
| **Q4** | Are sectoral indices/ETFs more resilient to volatility than individual stocks? Is sectoral momentum easier to call than single-stock? | **More resilient than a stock; less than Nifty 50. Marginally easier to call — and the gain is spent 2–4× over on the quote** | Effective breadth: Nifty Bank **6.1** names, Nifty IT **5.7**, Nifty 50 **22.1** (§6.2). A wider sectoral quote demands a **21.9 to 50.0 percentage-point** hit-rate improvement to pay for itself (§4.3). |
| **Q5** | Could day-trading or multi-day (~7 day) trading of these ETFs be a net-PnL-positive book? | **CLOSED — Books D and Z** | 5-session: required after-tax break-even accuracy **62.9%** at a 15 bps quote, **92.7%** at a stored sectoral quote; MDE **8.77–13.86%/yr** against ½ × E_net ≤ 1.0%. Intraday: same, plus s.66 at 31.2%, plus H6. |
| **Q6** | How does a 4/5 investor avoid a range-bound Nifty without shorting, futures, options or USD? | **Not with a short-horizon algo. VIABLE only as Book W or Rev 2.0** | Every packaged Indian equity alternative correlates **0.87–0.93** to Nifty 50 (§6.3). There is no low-correlation Indian equity beta. Escaping the tape means leaving equity (Rev 2.0), not rotating inside it. |

### 1.1 Q1 — Same-session direction of a sectoral index

**CLOSED as a retail-admissible, H4-clearing, cost-beating forecast.**

The honest framing is not "is there information?" but "how accurate must a rule be to survive the toll?"
For a symmetric long-or-flat bet that wins or loses the typical absolute move *m* and pays all-in
round-trip cost *c*, expectancy is *m*(2*p* − 1) − *c*, which is zero at

> **p\* = ½ + c / 2m**

| Vehicle | All-in RT *c* (§5) | Median 1-session \|move\| *m* **(working, W3-02)** | **p\*** pre-tax | **p\*** to net 10 bps after tax |
|---|---|---|---|---|
| NIFTYBEES-class, MIS | 13.8 bps | 61 bps (Nifty 50) | 61.3% | 66.5% (s.66, 31.2%) |
| NIFTYBEES-class, MIS | 13.8 bps | 81 bps (Bank, if it quoted like NIFTYBEES) | 58.5% | 67.5% |
| V-gate maximum quote | 15.2 bps | 81 bps | 59.4% | 68.3% |
| Stored BANKBEES quote | 79.7 bps | 81 bps | **99.2%** | — |
| Stored ITBEES quote | 131.7 bps | 94 bps | **>100% — impossible** | — |

Three things follow, and only the third is a matter of opinion.

1. **The required accuracy is 59–68% on same-day sectoral direction.** That is not a number this desk can
   pre-register. Rev 1.0 lock **L10** forbids a model output entering a forecast, a signal, a weight or a
   size — but L10 is *not* what closes this book, and pretending otherwise would be dishonest (§8.5).
2. **On stored sectoral quotes the arithmetic is not merely hard, it is unsatisfiable.** p\* ≥ 1 means no
   forecasting accuracy whatsoever produces positive expectancy. A perfect oracle loses money.
3. **Always-on daily rotation compounds the toll**: 252 × 13.8 bps = **34.8%/yr** of friction at a
   NIFTYBEES-class quote, **200.8%/yr** at a stored sectoral quote (§5.3).

**Reopen condition:** a *published, non-model* rule whose pre-registered one-session sleeve clears H4, **and**
a V-gate-measured live all-in round trip ≤ 10 bps on the traded name, **and** an H6-compatible design that is
still one ~16:15 IST run. None of the three exists.

### 1.2 Q2 — Edge on sectoral indices/ETFs over the broader market

**The phenomenon exists in the Indian literature at 6–12 month formation. It does not survive
implementation as a 5-session retail ETF book.**

What the Indian evidence actually says, and note the sign conflict at short horizons:

| Source | Finding | Horizon | Bearing on a 7-day book |
|---|---|---|---|
| Sehgal & Balakrishnan (2008); Sehgal & Jain (2011) | Stock **and industry/sectoral** momentum on NSE; 6-month formation / 6-month hold stronger than 12/12; a sectoral factor explains part of stock momentum | 6–12 months | Supports Book Q at monthly cadence. Says nothing about 5 sessions. |
| Sehgal & Jain (2015) | Industry robustness, 2000–2013 | 6–12 months | Same. |
| Joseph (2016) | **Short-term contrarian** behaviour in Metals, Auto, Banking, Energy on NSE | days to weeks | **Opposite sign** to a 5-session continuation rule. The literature this brief would lean on argues *against* Book D specifically. |
| Sharma, Subramaniam & Sehgal (2021) | Value and momentum largely **explained by risk models**, 2005–2016 | annual | The premium may be compensation, not alpha. |

And the competitor already exists: **Nifty 200 Momentum 30 / Nifty 500 Momentum 50 index funds and ETFs at
0.30–0.34% TER (direct)** rebalance internally with **no investor-level realisation event**. Rev 1.0's Book P
priced exactly this comparison and P1 STOPped with the packaged default
([p1-stop.md](../archive/p1-stop.md)). A self-run 5-session sectoral rotator pays 50 × 15.2 bps = **760 bps/yr**
plus 20.8% of every realised gain, to chase a cross-section that is sold, tax-deferred, for 34 bps.

**Reopen condition:** Book Q (monthly, not 5-session) clearing H4 after V-gate spreads. It currently fails
**7.5×** (§7).

### 1.3 Q3 — Can it predict whether the move exceeds round-trip cost?

**Yes, almost always — and this is the question the brief should stop asking.**

At Nifty Bank daily σ ≈ 1.2% **(working, W3-02)**, assuming a zero-mean normal session:

| All-in RT | P(\|session move\| ≥ RT) |
|---|---|
| 8.2 bps (ETF statutory only, ₹5 lakh clip) | **94.6%** |
| 15.2 bps (V-gate maximum quote) | **89.9%** |
| 79.7 bps (stored BANKBEES quote) | **50.7%** |
| 131.7 bps (stored ITBEES quote) | **27.2%** |

On a liquid vehicle the magnitude filter passes nine sessions in ten and therefore **carries almost no
information** — it is a filter that never filters. On an illiquid vehicle it becomes a coin flip, which is a
statement about the quote, not about the market.

The brief's question conflates two objects. **Magnitude is cheap and nearly certain; sign is expensive and
unknown.** A desk that can forecast "the move will exceed 15 bps" has learned nothing it can trade. Any
design document that answers Q3 affirmatively and moves on has answered the easy half.

### 1.4 Q4 — Resilience and relative predictability, sector versus single stock

**More resilient than a single stock. Less resilient than Nifty 50. Marginally more predictable than a
single name — and the entire gain is spent on the wider quote, two to four times over.**

Resilience, measured as effective breadth (inverse Herfindahl of index weights, **working, W3-03**):

| Basket | Names | Effective N | Idiosyncratic vol vs one stock (1/√N_eff) | Daily σ **(working, W3-02)** |
|---|---|---|---|---|
| A single large-cap (HDFCBANK) | 1 | 1.0 | 1.00 | 1.5–2.0% |
| **Nifty Bank / BANKBEES** | 12 | **6.1** | **0.40** | 1.1–1.4% |
| **Nifty IT / ITBEES** | ~10 | **5.7** | **0.42** | 1.3–1.5% |
| **Nifty 50 / NIFTYBEES** | 50 | **22.1** | **0.21** | 0.8–1.0% |

So the resilience claim in the brief is **true and quantified**: a sectoral ETF removes roughly 60% of
single-name idiosyncratic volatility. But it *adds* the systematic sector factor, which is why total σ still
rises from 0.9% to 1.2%/session relative to Nifty 50. **A sectoral ETF is a concentrated factor bet with the
stock-specific noise partly removed, not a diversified basket.** BANKBEES is effectively six names, and its
top holding is ~30% **(working, W3-03)**.

On predictability: it is plausible that a sector's direction is easier to call than a single name's residual,
because the predictable component of a sector return is systematic (rates, flows, currency, policy) while a
single name's is idiosyncratic. Grant the brief the point. Now price it:

> **A wider quote must be paid for in accuracy.** To justify an extra *Δc* of round-trip cost at typical
> move *m*, the rule's hit rate must improve by **Δp = Δc / 2m**.

| Extra cost over a NIFTYBEES-class quote | Horizon, median \|move\| | **Hit-rate improvement required** |
|---|---|---|
| +70 bps (stored BANKBEES vs NIFTYBEES) | 1 session, 81 bps | **+50.0 pp** |
| +70 bps | 5 sessions, 181 bps | **+19.3 pp** |
| +122 bps (stored ITBEES vs NIFTYBEES) | 5 sessions, 211 bps | **+28.9 pp** |

A 19-to-50 percentage-point improvement in directional accuracy, purchased by moving from the index to the
sector, is not a claim anyone should make. **The sector may be marginally more forecastable; it is
categorically more expensive to trade.** That trade is the whole of Q4, and it loses.

### 1.5 Q5 — Net-PnL-positive day-trading or ~7-day trading of these ETFs

**CLOSED. Books Z (intraday) and D (5-session) both fail independently on economics, tax and measurability.**

Intraday, two implementation routes, both closed:

| Route | Statutory RT (§5) | Tax | Independent additional kill |
|---|---|---|---|
| **MIS** | 8.3 bps @ ₹1 lakh; 4.5 bps @ ₹5 lakh | **s.66 speculative, slab to 31.2%**; losses offset only speculative income; 4-year carry | 4/5 posture is zero leverage, so MIS buys nothing; **H6 forbids an intraday loop**; 50–500 ms API against co-located prop |
| **Same-day delivery square** | 3.9 bps @ ₹1 lakh; 2.7 bps @ ₹5 lakh | **s.196, 20.8% from the first rupee** | Still a same-session forecast; T+1 funding; DP ₹15.34 per ISIN per sale day |

Five-session delivery, the brief's headline horizon, at a ₹5 lakh clip (2.7 bps statutory from `costs`,
including DP), requiring only **10 bps net** per completed trade:

| Spread scenario | Half-spread | All-in RT | **Required gross move per trade** | Required accuracy at that trade's median move |
|---|---|---|---|---|
| NIFTYBEES-class (~11 bps quoted, Rev 1.0) | 5.5 bps | **8.2 bps** | **20.8 bps / 5 sessions** | 55.8% |
| V-gate maximum (25 bps quoted) | 12.5 bps | **15.2 bps** | **27.8 bps** | **62.9%** |
| Stored BANKBEES quote 1.54% **(working, stale)** | 77 bps | **79.7 bps** | **92.3 bps** | **92.7%** |
| Stored ITBEES quote 2.58% **(working, stale)** | 129 bps | **131.7 bps** | **149.0 bps** | **impossible** |

Annualised: 50 five-session turns at 15.2 bps is **760 bps/yr** of friction, on top of which 20.8% is taken
from every gain and 0.21–0.29% of TER is taken from the vehicle. And the measurability, at the sleeve level:

| Book | σ_active vs Nifty 50 **(working)** | T | **MDE_ann** | E_net hypothesised | ½ E_net | Verdict |
|---|---|---|---|---|---|---|
| **D — 5-session sectoral TSMOM** | 14.0% | 20 yr (index) | **8.77%** | ≤ 2.0% | 1.0% | **fails 8.8×** |
| **D on the ETF's own history** | 14.0% | 8 yr **(working)** | **13.86%** | ≤ 2.0% | 1.0% | **fails 13.9×** |
| **Z — intraday** | 19.0% | 20 yr (index) | **11.90%** | ≤ 2.0% | 1.0% | **fails 11.9×** |
| **Z on the ETF's own history** | 19.0% | 8 yr **(working)** | **18.81%** | ≤ 2.0% | 1.0% | **fails 18.8×** |

Note which direction the ETF's own history moves the answer: **using the tradable instrument's real history
makes the book worse, not better,** because most Indian sectoral ETFs are far younger than their indices.
Backtesting the *index* and trading the *ETF* is a tradability look-ahead, and it is the specific error
lock **L13** (execution plan) exists to prevent.

**Reopen condition:** a named sectoral ETF with a V-gate-measured 20-day median quoted spread ≤ 11 bps
sustained for 12 months, **and** a specification at monthly or slower cadence, **and** H4 cleared on the
intersected T of §7. That is Book Q's gate, not Book D's. Book D has no reopen path at 5 sessions.

### 1.6 Q6 — Avoiding a range-bound Nifty without shorting, futures, options or USD

**Sector rotation is concentrated beta plus turnover. It is not an escape.**

| Candidate | Verdict | Binding Indian reason |
|---|---|---|
| Short cash equity | **Impossible** | No retail locate. SLBM R3 (17 Aug 2026) has no repay, recall or rollover; retail sits on the lending side (Rev 2.0 rung 3). |
| Index futures overlay | **Not a 7-day tool** | 1 Nifty lot = ₹15.52 lakh = **31% of a ₹50 lakh book**; RT 6.05 bps; hedge P&L lands in s.66 non-speculative at 31.2%, **not nettable** against s.196 capital gains (Rev 2.0 Book N). |
| Index options | **CLOSED** | Rev 1.0 §2.4: friction ≈ 1.02% of premium ≈ the entire VRP at India VIX 10.97. Unchanged. |
| LRS → S&P 500 | **Out of charter, and it is an FX view** | USD/INR at FBIL **94.4688 (3 Sep 2026)** against ~₹88 a year earlier: a large part of the rupee-denominated S&P print *is* the rupee. 20% TCS above ₹10 lakh, Schedule FA, non-equity 24-month tax treatment. Rev 2.0 already closed this. |
| 5-session BANKBEES / ITBEES rotation | **CLOSED** | Q1–Q5. And correlation to the thing being avoided is **0.87** (§6.3). |
| **Packaged different Indian beta, held > 12 months** | **VIABLE — Book W** | Next 50 / Midcap 150 / 200 Momentum 30 / 100 Low Vol 30 **direct-plan index funds**. Internal turnover, one tax event, s.198 at 13.0%. |
| **Rev 2.0 carry container** | **VIABLE if beta itself is declined** | β target ≤ 0.10, after-tax rupee yield. A different brief, and possibly the right one (§3.4). |

The uncomfortable finding, stated plainly because the brief's motive depends on it: **there is no
low-correlation Indian equity beta available in a packaged retail vehicle.** Every candidate in §6.3
correlates 0.87–0.93 with Nifty 50. Book W is a **tilt with tracking error**, not a hedge, and it will lose
money in a year when Indian equity loses money. If the requirement is positive rupees *regardless of* the
Indian tape, the requirement is β ≈ 0, and that is Rev 2.0 — not a faster version of Rev 1.0.

---

## 2. Constraint ladder for a 1-day / 5-session ETF desk

Rev 1.0's ladder was: no wrapper → STT on turnover → inference budget → capacity slack → alpha last. Rev 2.0
showed the ladder re-orders when the candidate set changes. For a **short-horizon ETF** candidate set it
re-orders again, and the top rung is one neither prior charter had to rank, because neither prior charter
proposed trading anything whose quote is not 11 bps.

| Rung | Constraint | The number at ₹50 lakh | What it kills | Rev 1.0 rank |
|---|---|---|---|---|
| **1** | **Quoted spread on the tradable vehicle** | Statutory ETF RT is **2.7–3.9 bps**. Stored sectoral quotes are **154–346 bps (working, stale)** — up to **50× the statute**. Gate: 20-day median quoted spread ≤ **25 bps** or the name is not an instrument. | Most sectoral and thematic ETFs, before a single signal is written | not ranked |
| **2** | **Cadence × spread** | 50 turns × 15.2 bps = **7.60%/yr**; 252 turns = **38.30%/yr**. At buy-and-hold, 0.15%/yr. Same instrument, 250× the toll. | The entire short-horizon identity | 2 (as STT on turnover) |
| **3** | **s.196 on every gain inside 12 months** | **20.8% from the first rupee, no ₹1.25 lakh exemption.** A 5-session book *never* reaches s.198's 13.0%. Delta on a 5% gain: **39 bps of the clip.** | Any tax-aware framing of a 7-day book | 1 (as no wrapper) |
| **4** | **s.66 if intraday** | 31.2% speculative, losses ring-fenced to speculative income, 4-year carry | Book Z as a business | 1 |
| **5** | **Sleeve→desk gearing under the 4/5 sector cap** | Single sector ≤ **25% of equity**. Desk excess = 0.25 × sleeve excess, but friction is 1.0 × sleeve. **300 bps of desk H2 needs 22.75%/yr of gross sector alpha** at 50 turns (§3.2). | Whole-book sector bets; "moderately aggressive 7-day sector trading" as a P&L driver | 4 (capacity, as slack) |
| **6** | **Sample / MDE, and it is scale-invariant** | MDE_ann = 2.80 σ/√T. σ_active 10.4–19%. T = 20 yr index, ~8 yr ETF. **T needed for a 2%/yr effect: 848 years.** Shrinking the sleeve does not help (§3.3). | Books D, Z and, on present numbers, Q | 3 |
| **7** | **H6 / latency / TOPS** | One ~16:15 IST run; 8 orders/second coded against TOPS 10; 50–500 ms round trip | Any intraday loop; any sub-second edge | — |
| **8** | **The packaged competitor** | Momentum / low-vol / Next 50 **direct index funds** at 0.15–0.34% TER, one deferred tax event | Self-run replication of a cross-section that is already sold in a fund | 5 (alpha last) |
| **9** | **Capacity** | A ₹5 lakh clip against BANKBEES AUM ₹8,379 crore **(working, W3-04)** is a rounding error | Nothing. **Slack — do not spend it on turnover.** | 4 |

Two consequences worth stating flatly.

**Rung 1 inverts Rev 1.0's stated reason for closing sectoral ETFs.** Rev 1.0 grouped "higher TER, wider
spreads" together. They are not comparable magnitudes: TER differs by 17–25 bps/yr, the quote differs by up
to 340 bps *per round trip*. At 12 turns a year the stored BANKBEES quote costs **9.77%/yr** and ITBEES
**16.09%/yr** in spread alone (§5.4). **The quote is the strategy's cost of goods, and it is not 3.9 bps.**

**Rung 5 is why "we called the sector correctly" does not recast the P&L.** A 4/5 mandate caps one sector at
25% of equity. A sleeve that beats Nifty by 400 bps moves the desk 100 bps. The friction, however, is
charged on the sleeve's own turnover at full rate. Skill is geared down; cost is not.

---

## 3. The four numbers that decide this brief

Everything in §1 reduces to four pieces of arithmetic. They are presented before the product board and the
book list because they are prior to both: if these four hold, no product selection and no signal rescues the
design.

### 3.1 Cadence dominates the forecast

Take a single gross return of **8%/yr** — generous for a sector sleeve, and deliberately held constant so
that only the *cadence* varies. Apply `costs` and the correct Indian tax class to each route:

| Route | Turns/yr | All-in RT | Friction | Tax class | **Net /yr** |
|---|---|---|---|---|---|
| 5-session rotation | 50 | 15.2 bps | 7.60% | s.196, 20.8% | **0.32%** |
| Monthly rotation | 12 | 15.2 bps | 1.82% | s.196, 20.8% | **4.89%** |
| Annual rebalance, held > 12 months | ~1 | 8.2 bps | 0.08% | s.198, 13.0% | **6.89%** |

**The same 8% gross return keeps 4% of itself at 5-session cadence and 86% of itself at buy-and-hold.** No
forecasting improvement available to a retail desk is worth 650 bps a year, which is what the cadence
decision alone is worth. This is the single most important number in the document and it requires no view
about whether sector momentum exists.

### 3.2 The 4/5 sector cap gears skill down and leaves cost at full rate

Rev 1.0 §6.1 caps a single sector at **25% of equity** and the whole active sleeve at 40%. One sectoral ETF
*is* one sector. So the desk-level excess return is 0.25 × the sleeve's, while the sleeve pays its own
friction and its own tax in full. Solving for the gross sector alpha required to deliver H2's 300 bps at the
desk:

| Cadence | Sleeve friction | Sleeve net needed | **Gross sector alpha needed** |
|---|---|---|---|
| Monthly, 12 turns | 1.82%/yr | 12.00%/yr | **16.98%/yr** |
| 5-session, 50 turns | 7.60%/yr | 12.00%/yr | **22.75%/yr** |
| Daily, 252 turns | 34.78%/yr | 12.00%/yr | **49.93%/yr** |

A 17–23%/yr gross alpha from a publicly documented sectoral momentum effect, in ETFs, on free data, is not a
credible claim. For calibration: Rev 1.0 computed that a Nifty 200 delivery sleeve needs **g ≥ 12.1%/yr
gross** to clear the same gate at 30-year-scale breadth, and called that non-credible. The sector cap makes
this brief's requirement roughly twice as demanding.

The honest alternative reading — *raise the cap* — is available and is a **charter change, not a milestone**.
The 4/5 sector cap exists because Indian index concentration in financials makes it bind rather than
decorate. Note also that the cap, not the 4σ overnight test, is the binding limit here: at Nifty Bank's
1.2%/session σ **(working)**, a 4σ overnight gap of 4.8% would permit **41.7%** of equity under the 2%-loss
rule. **The 25% sector cap is the stricter constraint and it should be cited as such** — the prior Rev 3.0
draft attributed the binding to the 4σ test, which is arithmetically wrong.

### 3.3 H4 is scale-invariant, and T is the binding scarcity

A tempting escape is "measure the sleeve, not the desk" or "run it small". Neither works. Scaling a sleeve by
weight *w* scales σ_active and E_net by the same *w*, so the ratio MDE / (½ E_net) is unchanged:

| Sleeve weight | Desk σ_active | Desk E_net | Desk MDE (T = 20) | **MDE ÷ ½E_net** |
|---|---|---|---|---|
| 100% | 10.40% | 4.00% | 6.51% | **3.26** |
| 40% | 4.16% | 1.60% | 2.60% | **3.26** |
| 25% | 2.60% | 1.00% | 1.63% | **3.26** |
| 10% | 1.04% | 0.40% | 0.65% | **3.26** |

**Position sizing cannot buy measurability.** The only two levers are σ and T, and Rev 1.0 already showed
they trade against each other: cutting σ to make an effect measurable cuts the effect.

What T would be required, at each candidate's σ, for MDE to fall to half of a given effect:

| σ_active | E_net 2%/yr | E_net 3%/yr | E_net 5%/yr | E_net 10.08%/yr (§3.4) |
|---|---|---|---|---|
| **10.4%** (monthly sector rotation) | **848 yr** | 377 yr | 136 yr | **33.4 yr** |
| **14.0%** (5-session TSMOM) | 1,537 yr | 683 yr | 246 yr | **60.5 yr** |
| **19.0%** (intraday) | 2,830 yr | 1,258 yr | 453 yr | **111.4 yr** |

India offers ~20 years of clean point-in-time sectoral *index* history and ~8 years of the *ETFs* that would
actually be traded **(working, W3-06)**. **Waiting does not fix this.** Rev 1.0's Book A was deferred to a
date because its T was 0.09 years and grows; these books' T is already 8–20 years and the requirement is 33
to 2,830. That is the structural difference between a **deferral** and a **closure**, and it is the same
distinction Rev 2.0 drew for Book T (331 years). Books D and Z close permanently. Book Q closes on present
numbers, with a reopen tied to a measured σ, not to the passage of time.

### 3.4 H2 and H2-ABS cannot both be satisfied by a long-India sleeve

The brief contains two requirements that this document must not quietly reconcile:

- *"net PnL positive algo strategy for Indian equity"* — an **absolute** rupee requirement.
- *"minimising exposure to range-bound/flat market"*, cited against a **−6% Nifty** — i.e. the absolute
  requirement is to be met **in a year when Indian equity fell**.

H2 (beat Nifty 50 TRI by 300 bps) is a *relative* hurdle and would score a −3% year against a −6% benchmark
as a success. This investor would not. So Rev 3.0 adds an absolute hurdle:

> **H2-ABS — after-tax desk return ≥ after-tax 91-day T-bill roll + 200 bps.**
> At a 5.60% T-bill **(working, W3-07)** taxed at 31.2% slab: 3.85% + 2.00% = **5.85%/yr**.
> Against Rev 2.0's sweep-FD base (6.60% → 4.54% after tax) the same rule reads **6.54%/yr**.

Now price H2-ABS for a long-only Indian equity sleeve in the year the brief describes:

| Nifty 50 TRI | Sleeve β | **Net alpha needed to clear H2-ABS** | E_net for H4 must be ≥ 2 × MDE | Verdict |
|---|---|---|---|---|
| −4.7% (−6% price + ~1.3% yield **(working)**) | 0.90 | **10.08%/yr** | needs T = **33.4 yr** at σ 10.4% | **unreachable** |
| −6.0% | 0.90 | **11.25%/yr** | needs T ≈ 26 yr | **unreachable** |
| 0.0% (flat) | 0.90 | **5.85%/yr** | needs T ≈ 99 yr | **unreachable** |
| +11.0% (long-run TRI) | 0.90 | **−4.05%/yr** — the beta alone clears it | — | trivially met, and irrelevant to the brief |

**Read the last two rows together.** H2-ABS is satisfied by Indian equity beta *only when Indian equity goes
up*, which is precisely the condition the brief excludes. In a flat or down year, no long-only Indian equity
sleeve — at any horizon, with any signal — clears H2-ABS, because the required alpha is 5.9% to 11.3% and
**even that required alpha fails H4** on the available sample.

This is the honest resolution of the brief and it is a structural, not empirical, finding:

> **A short-horizon algo cannot solve a beta problem. Only the absence of beta can.** If the requirement is
> positive after-tax rupees independent of the Indian tape, the answer is Rev 2.0's β ≈ 0 carry container
> (which clears an equivalent hurdle by construction, at 5.19–5.20% after tax with β 0.084). If the
> requirement is Indian equity exposure with a different shape, the answer is Book W — held past twelve
> months, with its possible multi-year underperformance printed in advance. There is no third product, and a
> 5-session sectoral rotator is not a candidate for either.

---

## 4. Product board — intraday versus ~7-day versus > 12-month hold

Verdicts use the **Book V gate** (§6.1): AUM ≥ ₹2,000 crore, 20-day median quoted spread ≤ 25 bps, ADV
notional ≥ ₹25 crore, 20-day median absolute premium/discount to NAV ≤ 15 bps. A name that fails the gate is
closed **even if its index is famous**. All AUM, TER and spread figures below are **(working)** and carried
forward unverified from the draft this file replaces; V0 measures them.

| Product | Intraday | ~7-day (5 sessions) | Hold > 12 months | Verdict | Binding reason |
|---|---|---|---|---|---|
| **Nifty 50 ETF** (NIFTYBEES, SETFNIF50, ICICI/Kotak) | ❌ | ❌ | ✅ | **VIABLE as core and as the H2 hurdle; never as a trade** | Statutory 3.9 / 2.7 bps; quoted ~11 bps; TER 0.03–0.04%. Trading it weekly pays 20.8% STCG to harvest beta already owned. |
| **Nifty 50 direct-plan index fund** | — | — | ✅ | **VIABLE — and it beats the ETF at low turnover** | No DP charge, no quoted spread, no exchange leg. Rev 1.0's L1 already recommended the direct fund at 4 turns/yr. Total drag **0.21%/yr** vs **0.37%/yr** for the ETF (§5.4). |
| **Nifty Next 50 ETF / index fund** | ❌ | ⚠️ | ✅ | **CANDIDATE-GATE at V0 as a *hold*; CLOSED as a rotator** | Different weights, same tape: ρ ≈ 0.90, β ≈ 1.15, active σ **8.15%** (§6.3). |
| **Nifty Midcap 150 index fund** | ❌ | ❌ | ✅ | **CANDIDATE-GATE as a *hold*, inside the 40% active cap** | ρ ≈ 0.88, active σ **8.13%**. Smallcap remains CLOSED (ESM/GSM Stage II, Rev 1.0). |
| **Nifty 200 Momentum 30 / 500 Momentum 50** | ❌ | ❌ | ✅ | **VIABLE — Book W, the 4/5 "not flat Nifty" sleeve** | Packaged cross-section at 0.30–0.34% direct TER, internal rebalance, one deferred tax event. P1 already defaulted packaged. |
| **Nifty 100 Low Volatility 30** | ❌ | ❌ | ✅ | **VIABLE — Book W, lowest-tracking-error variant** | ρ ≈ 0.93, β ≈ 0.85, active σ **5.25%** — the *least* measurement-hungry different beta, and still 136 years for a 5% effect. |
| **Nifty Bank ETF** (BANKBEES) | ❌ | ❌ | ⚠️ | **CLOSED as a 1-day or 7-day book; hold only inside the 25% sector cap after V0 passes it** | AUM ₹8,379 Cr, TER 0.21%; effective N 6.1, top-1 ~30%; stored quote 154 bps. 12 turns/yr costs **9.77%/yr** (§5.4). |
| **Nifty IT ETF** (ITBEES) | ❌ | ❌ | ⚠️ | **Same, and worse** | AUM ₹3,480–3,533 Cr, TER 0.29%; top-2 ~51%; stored quote 258 bps → **16.09%/yr** at 12 turns. |
| **Nifty Pharma ETF** (PHARMABEES) | ❌ | ❌ | ❌ | **CLOSED — expected V0 fail** | AUM ₹1,356 Cr is **below the ₹2,000 crore gate**; stored quote 346 bps. |
| **FMCG / BFSI / Consumption ETFs** | ❌ | ❌ | ❌ | **CLOSED** | FMCGIETF ₹809 Cr / quote 173 bps; BFSI ₹418–432 Cr / 196 bps; AXISCETF ₹14 Cr. Fail AUM **and** spread. |
| **PSU Bank / CPSE / most thematic ETFs** | ❌ | ❌ | ❌ | **CLOSED** | Liquidity, policy-event gap risk, single-name concentration. V0 may list exceptions; none are assumed. |
| **ETF units on MIS** | ❌ | — | — | **CLOSED — Book Z** | §1.5. s.66 at 31.2%, H6, latency, spread. |
| **Index futures / options / stock F&O / MTF** | ❌ | ❌ | — | **CLOSED** | Rev 1.0 §2; Rev 2.0 §5. Unchanged, and not re-litigated by a horizon change. |
| **Gold / silver / Bharat Bond / international FoF** | — | — | — | **OUT OF CHARTER** | Not Indian equity. The international leg is an FX view (§1.6). |

**The board's shape is the finding.** Every ✅ is in the "> 12 months" column. Nothing in this asset class is
viable at 1 day or 5 sessions, and the two columns the brief cares about are empty.

---

## 5. Worked all-in round trips

`src.costs.round_trip_bps` on 2026-09-10, NSE, Zerodha-class card, one buy order and one sell order, one ISIN
sold. **Spread is deliberately outside `costs`** — L1 makes `costs` the single source of *statutory, broker
and DP* friction only. Book V supplies the half-spread; all-in = statutory + half-spread. This separation is
load-bearing: it is why the ETF's 3.9 bps statutory figure must never be quoted as a trading cost.

### 5.1 Statutory only, from `costs`

| Product | ₹1 lakh | ₹2 lakh | ₹5 lakh | ₹12.5 lakh |
|---|---|---|---|---|
| **ETF units** (equity-oriented, STT 0.001% sell only) | ₹39.02 = **3.9 bps** | ₹62.70 = **3.1 bps** | ₹133.75 = **2.7 bps** | ₹311.37 = **2.5 bps** |
| Stock delivery (STT 0.10% both legs) | ₹238.02 = **23.8 bps** | ₹460.70 = 23.0 bps | ₹1,128.75 = **22.6 bps** | ₹2,798.87 = 22.4 bps |
| Cash intraday / MIS | ₹82.88 = **8.3 bps** | ₹118.56 = 5.9 bps | ₹225.61 = **4.5 bps** | ₹493.23 = 3.9 bps |

Rev 1.0's central ETF fact **survives this brief intact**: statutory ETF friction is one-sixth of a stock's,
because STT on the sale of an equity-oriented fund unit is 0.001% against 0.10% on a share, and nil on
purchase. At ₹5 lakh the ETF round trip is ₹133.75, of which STT is ₹5.00 and stamp duty is ₹75.00 —
**stamp duty is now the largest statutory line**, which is worth noticing because it is a buy-side levy and
therefore scales with turnover, not with holding period.

DP is ₹15.34 per ISIN per sale day: **1.5 bps at ₹1 lakh, 0.3 bps at ₹5 lakh.** That alone argues for ₹5 lakh
clips. At ₹50 lakh, ₹5 lakh is 10% of equity — permissible for an ETF (the 6% single-*name* cap applies to
stocks; the binding limit for a sectoral ETF is the **25% sector cap = ₹12.5 lakh**).

### 5.2 All-in, with spread scenarios

| Vehicle | Clip | Statutory | Half-spread **(working)** | **All-in RT** |
|---|---|---|---|---|
| ETF, NIFTYBEES-class quote (~11 bps) | ₹1 lakh | 3.9 bps | 5.5 bps | **9.4 bps** |
| ETF, NIFTYBEES-class quote | ₹5 lakh | 2.7 bps | 5.5 bps | **8.2 bps** |
| ETF, **V-gate maximum** (25 bps quoted) | ₹5 lakh | 2.7 bps | 12.5 bps | **15.2 bps** |
| ETF, stored BANKBEES quote (154 bps) | ₹5 lakh | 2.7 bps | 77.0 bps | **79.7 bps** |
| ETF, stored ITBEES quote (258 bps) | ₹5 lakh | 2.7 bps | 129.0 bps | **131.7 bps** |
| Stock delivery, Nifty 50 name | ₹5 lakh | 22.6 bps | 3–6 bps (NSE impact cost, W6) | **~26–29 bps** |
| MIS, NIFTYBEES-class | ₹1 lakh | 8.3 bps | 5.5 bps | **13.8 bps** |
| MIS, NIFTYBEES-class | ₹5 lakh | 4.5 bps | 5.5 bps | **10.0 bps** |
| MIS, stored BANKBEES quote | ₹5 lakh | 4.5 bps | 77.0 bps | **81.5 bps** |

### 5.3 Annualised friction by cadence — the table that closes Books D and Z

| Turns/yr | @ 8.2 bps (liquid ETF) | @ 15.2 bps (V-gate max) | @ 79.7 bps (stored BANKBEES) |
|---|---|---|---|
| 252 (daily) | **20.66%** | **38.30%** | **200.84%** |
| 50 (5-session) | **4.10%** | **7.60%** | **39.85%** |
| 12 (monthly) | 0.98% | 1.82% | 9.56% |
| 4 (quarterly) | 0.33% | 0.61% | 3.19% |
| 1 (annual) | 0.08% | 0.15% | 0.80% |

### 5.4 Total annual drag, including TER — vehicle choice at the desk's actual cadence

| Vehicle | TER | Half-spread | Turns/yr assumed | **Total drag /yr** |
|---|---|---|---|---|
| Nifty 50 **direct index fund** | 0.10% **(working)** | 0 | 4 | **0.21%** |
| NIFTYBEES ETF | 0.04% | 5.5 bps | 4 | **0.37%** |
| MOM30 direct index fund | 0.34% | 0 | 0 (internal rebalance) | **0.34%** |
| BANKBEES ETF | 0.21% | 77 bps | 12 | **9.77%** |
| ITBEES ETF | 0.29% | 129 bps | 12 | **16.09%** |

Rev 1.0's L1 conclusion is confirmed and extended: **at four turns a year the direct index fund beats the
ETF** (0.21% vs 0.37%), because the ETF's TER advantage of 6 bps does not pay for 22 bps of annual
half-spread and DP. The ETF wins only when intraday execution is needed — and on this desk it never is.
That is a real, arithmetic result and it is why Book W is specified in **index funds**, not ETFs.

---

## 6. Tradability, concentration and correlation — the three measurements that gate everything

### 6.1 The Book V gate

A named ETF is a **vehicle** only if all four hold, measured as of the date, from free sources:

| Test | Threshold | Why this number |
|---|---|---|
| AUM | ≥ **₹2,000 crore** | Below this, a ₹12.5 lakh sector position is a material share of a fund whose creation/redemption is an AP privilege this PAN does not hold. |
| 20-day median quoted spread | ≤ **25 bps** | At 25 bps the all-in 5-session RT is 15.2 bps and the required accuracy is already 62.9% (§1.5). Above it, the arithmetic is unsatisfiable, not merely hard. |
| ADV notional | ≥ **₹25 crore** | A ₹5 lakh clip must be ≤ 2% of a session's traded value so that H5's 6× impact stress is meaningful. |
| 20-day median \|premium/discount\| to NAV | ≤ **15 bps** | A persistent premium is a cost the investor pays twice: on entry and, if it mean-reverts adversely, on exit. |

**A name that fails is closed even if its index is famous**, and the pass list is **as-of-date** — trading on
the index while assuming the ETF was liquid is the look-ahead that lock **L13** exists to refuse.

### 6.2 Concentration — what a sectoral ETF actually is

Effective breadth = 1 / Σwᵢ², on **(working, W3-03)** weights to be replaced from the current factsheets:

| Basket | Names | Top-1 | Top-5 | **Effective N** |
|---|---|---|---|---|
| Nifty Bank | 12 | ~30% | ~80% | **6.1** |
| Nifty IT | ~10 | ~31% | ~81% | **5.7** |
| Nifty 50 | 50 | ~13% | ~39% | **22.1** |

**BANKBEES is a six-name position wearing an index's name.** That is the fact the 25% sector cap is
responding to, and it is the honest content of Rev 1.0's phrase "concentration that 4/5 risk does not
license."

### 6.3 Correlation — is there a different Indian equity beta?

Active σ against Nifty 50 = √(σ_s² + σ_n² − 2ρσ_sσ_n), at σ_n = 14%/yr **(all working, W3-05)**:

| Candidate | ρ to Nifty 50 | β | σ | **Active σ** | T needed for a 5%/yr effect |
|---|---|---|---|---|---|
| Nifty 100 Low Volatility 30 | 0.93 | 0.85 | 12% | **5.25%** | 35 yr |
| Nifty 200 Momentum 30 | 0.90 | 1.05 | 17% | **7.52%** | 71 yr |
| Nifty Midcap 150 | 0.88 | 1.10 | 17% | **8.13%** | 83 yr |
| Nifty Next 50 | 0.90 | 1.15 | 18% | **8.15%** | 84 yr |
| **Nifty Bank** | **0.87** | 1.15 | 20% | **10.43%** | **136 yr** |

Two readings, both necessary.

**For Book W:** every packaged alternative is 0.88–0.93 correlated to the index the investor wants to leave.
Book W is a **tilt**, it will fall in a falling Indian market, and none of these tilts can be *validated* —
even Low Vol 30, the tightest, needs 35 years to detect a 5%/yr effect. Book W is therefore correctly
classified as a **decision**, like Rev 1.0's Book P, and is explicitly **not required to clear H2's 300 bps**.
Its kill is a decision-rule kill (§8.2), not a t-statistic.

**For Book Q and Book D:** the sectoral sleeve has the *highest* active σ on the list and therefore the
*worst* measurability of any candidate — the opposite of the intuition that "sectors are easier than stocks."
Sectors are easier than stocks and **harder than the index**, and H4 is scored against the index.

---

## 7. Inference — n, σ, MDE, and the gate

Unchanged from Rev 1.0 and `src.harness.mde`:

> **MDE_ann = (z₁₋α/₂ + z₁₋β) × σ_ann / √T = 2.80 × σ_ann / √T**, α = 0.05 two-sided, 80% power.
> **Gate H4: MDE_ann ≤ ½ × E_net**, published before the first peek. **Five specifications per book.**

σ_ann is the sleeve's standard deviation **against the hurdle** (Nifty 50 TRI net of 0.04% TER), not the
academic effect's. Two Rev 3.0 amendments to how T is stated, both tightening:

1. **T is the intersection**, not the maximum, of: sectoral index history, the ETF's listing date, and the
   dates on which the name would have passed the Book V gate. Index T = 20 does not license trading a
   five-year-old ETF as though its quote and AUM existed in 2006.
2. **T is published before σ.** A book that chooses its σ after seeing its own returns has no pre-registration.
   σ must come from a return-free estimator — realised volatility of (sectoral index TRI − Nifty 50 TRI) from
   NSE Indices, which is public and is not the book's P&L.

| Book / phenomenon | Shape | σ_active **(working)** | T | **MDE_ann** | E_net hypothesised | ½ E_net | Verdict |
|---|---|---|---|---|---|---|---|
| **V — ETF tradability ledger** | Published AUM, ADV, quote, premium, TER, weights | — | — | **n/a — arithmetic** | Prevents mistaking a 154 bps quote for 3.9 bps | — | **OPEN** |
| **W — packaged different beta, held > 12 m** | Buy a direct-plan index fund; hold past the s.198 line | 5.25–8.15% | 20 yr TRI | **n/a — decision, not a measured edge** | Decision value; **may be negative for years** | — | **OPEN** |
| **Q — monthly rotation among V-pass ETFs** | 12-month formation, 1-month hold, long-only, 25% sleeve | 10.4% | 20 yr index | **6.51%** | 1.7% | 0.85% | **FAILS 7.7×** |
| **Q on the ETFs' own T** | same | 10.4% | 8 yr **(working)** | **10.30%** | 1.7% | 0.85% | **FAILS 12.1×** |
| **D — 5-session sectoral TSMOM** | ~50 turns/yr | 14.0% | 20 yr index | **8.77%** | ≤ 2.0% | 1.0% | **FAILS ≥ 8.8×** |
| **D on the ETFs' own T** | same | 14.0% | 8 yr **(working)** | **13.86%** | ≤ 2.0% | 1.0% | **FAILS ≥ 13.9×** |
| **Z — intraday MIS or same-day square** | 252 turns/yr | 19.0% | 20 yr index | **11.90%** | ≤ 2.0% | 1.0% | **FAILS ≥ 11.9×** |
| **Z on the ETFs' own T** | same | 19.0% | 8 yr **(working)** | **18.81%** | ≤ 2.0% | 1.0% | **FAILS ≥ 18.8×** |
| *Packaged MOM30 hold (comparator)* | one deferred tax event | ~7.5% | 20 yr | 4.70% | 34 bps of TER, not a forecast | — | **Buy the fund; do not self-run** (P1, Book M) |

Where Book Q's E_net comes from, so it can be checked: 12 turns × 15.2 bps = 1.82% of sleeve friction against
a 3.97% gross sector-momentum spread, leaving 2.15% pre-tax and **1.70% after 20.8% s.196**. At a 25% sleeve
that is **42 bps of the ₹50 lakh desk** — against **46 bps of desk-level friction**, and against Book L's
**already-measured 95.92 bps** ([l1-ledger-arithmetic.md](l1-ledger-arithmetic.md)). **A fully successful
monthly sector rotation would contribute less than half of what an arithmetic book already delivers with zero
research risk, while spending more in friction than it earns.** That ranking, not the MDE, is the reason
Book Q sits third.

---

## 8. Ranked books — kill numbers and AI role

Ranked by after-cost, after-tax rupee contribution **per unit of research risk**, the same criterion as
Rev 1.0 §8.

### 8.1 Book V (rank 1) — ETF tradability and routing ledger

| | |
|---|---|
| **Hypothesis** | Whether a named Indian ETF is a *vehicle* is fully determined by published AUM, ADV, quoted spread, premium/discount to NAV, TER and holding concentration — computable **before any return is examined**, and therefore carrying zero research risk. Further: given that the desk has decided to take a given exposure, the cheapest route among {ETF at market, direct index fund at NAV, constituent basket} is likewise fully determined. |
| **Instruments** | NSE/BSE quotes and traded value; AMFI AUM, TER and NAV; AMC factsheets for weights. |
| **Horizon** | Snapshot at V0; refreshed monthly, stored as-of-date (**L13**). |
| **Contribution** | Two parts, both arithmetic. (a) **Gate:** stops a 3.9 bps statutory story from concealing a 154–346 bps quote — worth 9.8–16.1%/yr on any 12-turn sector sleeve (§5.4). (b) **Routing:** extends Rev 1.0's `etf_vs_constituents` 20 bps rule to a three-way choice that adds the premium/discount term. On Rev 1.0's own core, choosing the direct fund over the ETF at 4 turns/yr is worth **16 bps/yr** (§5.4) — small, certain, and already inside Book L's remit. |
| **Kill** | If **zero** sectoral or thematic names clear the §6.1 gate, the sectoral-ETF product class is **closed** and Book Q is never built. If the 20-day median quoted spread cannot be reconstructed from free sources for a named ETF, **fail the name** — do not buy a vendor feed (L8). |
| **Arithmetic or inferential** | **Arithmetic. No MDE.** |
| **AI role** | **One narrow, permitted job** (§8.6): `ai.extract` may parse an AMC factsheet or SID into typed fields — TER, exit load, top-10 weights, index family — behind the standard 98% field-level agreement gate against 200 hand-labelled documents, with a deterministic cross-check against AMFI. **Extraction proposes; the gate arithmetic disposes.** No model output touches a return, a rank or a size. |

### 8.2 Book W (rank 2) — Packaged different Indian beta, held past twelve months

| | |
|---|---|
| **Hypothesis** | For a 4/5 investor who does not want to sit in a range-bound Nifty 50 but still wants Indian equity, the after-cost, after-tax way to take a *differently shaped* Indian bet is a **direct-plan index fund** on Nifty Next 50, Midcap 150, 200 Momentum 30 or 100 Low Volatility 30, held past the twelve-month line so the single realisation event lands at s.198's 13.0% — **not** a 5-session sectoral ETF rotator. |
| **Instruments** | Direct plans only; regular plans at 0.93–1.87% are excluded on TER alone (Rev 1.0). Sleeve ≤ **40% of equity** (Rev 1.0 §6.1 active cap); any one sector ≤ **25%**; remainder in the Nifty 50 core or, if beta is declined, Rev 2.0's carry container. |
| **Horizon** | **12 months minimum by construction**, scheduled through Book L's realisation scheduler (L2, DONE). |
| **Contribution** | **Decision value, not alpha, and it can be negative.** Nifty 200 Momentum 30 has already delivered −3.81% over one year to June 2026 against +13.42% over three years on one representative direct plan (Rev 1.0). The cadence arithmetic of §3.1 is the whole contribution: **6.89%/yr net of an 8% gross versus 0.32% at 5-session cadence.** |
| **Kill** | Three-part, pre-committed. (a) If every packaged alternative's 5-year TRI after TER trails Nifty 50 TRI by **> 300 bps annualised** and the investor still wants Indian equity, default to **100% Nifty 50 direct fund** (Rev 1.0's answer) — Book W closes. (b) If the sleeve requires more than **40%** of equity, or any single sector more than **25%**, to be worth holding, it is a leverage request, not a tilt — close it. (c) If the investor's requirement is positive rupees **independent of** the Indian tape, close Book W and go to **Rev 2.0**; §3.4 shows no long-India sleeve can meet that. |
| **Arithmetic or inferential** | **Decision.** No MDE is claimed and none is available: even the tightest candidate needs 35 years to detect a 5%/yr effect (§6.3). Book W is scored on TER, tax class and cadence — all published — and on nothing else. |
| **AI role** | **None.** |
| **Relation to P1** | P1 STOPped because point-in-time factor-index constituents could not be assembled for a self-run replication. **Book W does not need them: it buys the fund.** That is a completed use of P1's conservative default, not a re-litigation of it. |

### 8.3 Book Q (rank 3) — Monthly rotation among Book-V-pass ETFs. Gated; expected to close.

| | |
|---|---|
| **Hypothesis** | A 12-month-formation, 1-month-hold, long-only rank of V-pass sectoral and thematic ETFs, sleeve capped at 25% of equity with the remainder in the core, clears H2, H2-ABS and H4 after `costs` and s.196. |
| **Why monthly and not 5-session** | Three reasons, all in this document. 12 turns × 15.2 bps = **1.82%/yr** against 50 turns × 15.2 bps = **7.60%/yr** (§5.3). The Indian literature's momentum is 6–6 and 12–12, not 1-week (§1.2). And Joseph (2016) found short-term **contrarian** behaviour in exactly the sectors a 7-day continuation rule would trade — **the wrong sign**. |
| **Contribution if it worked** | Sleeve E_net 1.70%/yr → **42 bps of a ₹50 lakh desk**, against 46 bps of desk-level friction and Book L's already-measured 95.92 bps (§7). |
| **Kill** | Closes at K0 if MDE > ½ E_net — **which it does, 7.7× on index T and 12.1× on ETF T** — before any return is examined. If a human waives that on a revised σ, it closes at the ₹0 screen unless, simultaneously: after-cost after-tax excess over Nifty 50 TRI ≥ **300 bps** (H2) on V-pass dates only; **H2-ABS** cleared over the same sample; and **five specifications** not exhausted. |
| **Arithmetic or inferential** | **Inferential, and it fails.** |
| **AI role** | **None.** The ranker is a published past-return sort written into the pre-registration file — the same shape as closed Book M. An LLM narrative about monsoons, Fed cuts or the credit cycle is **not a feature** unless it is a dated, point-in-time column in the panel, and even then it does not enter a size. **L10 stays** (§8.6). |
| **Honest expectation** | **This book closes.** It is on the list so a later agent finds a door with a number on it rather than an unexamined idea. |

### 8.4 Book D (rank 4) — Five-session sectoral TSMOM. **Closed at pre-registration, no peek.**

The brief's headline book. Hypothesis: 5-session continuation on Nifty sectoral indices, expressed in ETFs,
is net positive after spread and s.196.

| Kill | Number |
|---|---|
| **Economics** | Required gross move **20.8 bps** per trade at a NIFTYBEES-class quote, **27.8 bps** at the V-gate maximum, **92.3 bps** on the stored BANKBEES quote — the last being roughly *half a typical Bank week*, consumed entirely by the quote. |
| **Cadence** | 50 turns × 15.2 bps = **7.60%/yr**; at the stored quote, **39.85%/yr**. |
| **Tax** | s.196 at **20.8% from the first rupee**. A 5-session book never reaches s.198; the forgone delta on a 5% gain is **39 bps of the clip**. |
| **Gearing** | **22.75%/yr gross sector alpha** required to move a 25%-capped sleeve 300 bps at the desk (§3.2). |
| **Measurability** | MDE **8.77%/yr** on index T, **13.86%** on ETF T, against ½ E_net ≤ 1.0%. T required for a 2%/yr effect: **1,537 years.** |
| **Sign** | Joseph (2016) reports short-term **contrarian** behaviour in several NSE sectors — the literature argues against this book's direction, not merely its size. |

**Permanently closed, not deferred.** Unlike Rev 1.0's Book A, waiting adds nothing: T is already 8–20 years
and the requirement is 1,537. STOP memo at K0, before any data access. `AI role: none.`

### 8.5 Book Z (rank 5) — Intraday sectoral ETF. **Closed at pre-registration, no peek.**

Break-even accuracy **59–68%** after tax on a liquid quote and **unsatisfiable at any accuracy** on a stored
sectoral quote (§1.1); 252 × 13.8 bps = **34.78%/yr** of friction; s.66 speculative at 31.2% with losses
ring-fenced and a 4-year carry; MDE **11.90–18.81%/yr**; and **H6 forbids an intraday loop** on a
one-machine, one-run desk against a 50–500 ms API and TOPS-capped 8 orders/second. Five independent kills,
any one sufficient. STOP memo at K0. `AI role: none.`

### 8.6 L10, confronted rather than negotiated

The brief says *"Algo platforms and AI as necessary"* and asks whether the platform can **predict** sectoral
direction. Rev 1.0's lock L10 forbids any model output entering a forecast, a signal, a weight or a size.
The temptation is to trade a narrow exception for the brief's ambition. **Do not, and the reason is
arithmetic rather than taste:**

> **MDE = 2.80 σ / √T is a property of the sample, not of the signal.** A perfect forecaster, an LLM, a
> gradient-boosted ensemble and a coin all face the same MDE. Books D, Z and Q fail H4 and H2 **before any
> signal is specified**. Relaxing L10 therefore buys exactly zero basis points of hurdle relief.

So there is nothing to sign an exception for, and **L10 stays by arithmetic**. The honest corollary is that
L10 is *not* the reason these books are closed, and any STOP memo that blames L10 is misattributing the kill
— the reasons are §3.1 through §3.4.

What this brief *does* legitimately create is one **document-parsing** job, which is a widening of Rev 1.0's
existing `ai.extract` remit and not a relaxation of the forecast prohibition:

| Permitted | Forbidden |
|---|---|
| `ai.extract.etf` — parse AMC factsheets and SIDs into typed fields (TER, exit load, top-10 weights, index family, disclosed AUM date) with per-field confidence and source page, gated at **≥ 98% field-level agreement** against 200 hand-labelled documents, with a deterministic cross-check against AMFI. Feeds **Book V's gate arithmetic only**. | **Any model output entering a return forecast, a rank, a signal, a weight or a position size.** |
| `ops` — an LLM writes one paragraph of "what changed, what looks wrong" over the run log and the reconciliation diff. Read-only. | The same LLM changing a position, cancelling an order, moving a threshold, or choosing which ETF to hold. |
| Nothing else. | HMM, LightGBM, MLflow, Kaggle client, Polars in `pyproject.toml` at seed. Unchanged. |

**The one-line test, inherited from Rev 2.0:** an AI may read a document the desk would otherwise read by
hand. It may not have an opinion about what the numbers in it are worth. Note that `ai.extract.etf` is
**not in v1** and is not required for V0 — six to twelve factsheets can be read by hand, and should be.

### 8.7 The fallback, stated so it cannot be treated as a defeat

If a human declines Rev 3.0's brief, the production-shaped desks are **Rev 1.0 (Book L + a packaged core)**
and **Rev 2.0 (carry container at β ≈ 0)**. Both already exist as charters with measured or worked numbers.
**Rev 3.0's contribution is the Q1–Q6 computation, the H2-ABS hurdle, and Book V's screen** — not a new live
book. A charter whose honest output is "the books you asked for do not exist, here are the numbers, and here
is the free screen that proves it" is a completed milestone.

---

## 9. Closed list and reopen conditions

Inherited from Rev 1.0 and Rev 2.0 and **not re-litigated by a change of horizon**:

| Closed | Still closed because | What would reopen it |
|---|---|---|
| Index option premium selling, weekly or monthly | Rev 1.0 §2.4: friction ≈ 1.02% of premium ≈ the entire VRP at India VIX 10.97; T < 6 months of the current regime; SEBI FY26 — 87.7% of individuals lost, ₹25,000 crore of it transaction cost | Rev 1.0's four-part condition, unchanged |
| Expiry-day anything | Two venues, maximum crowding, sub-second decay against co-located algos | Nothing inside this desk's latency budget |
| Single-stock futures and options | Physical settlement; delivery-margin ramp to 100%; delta-based FutEq ban with ₹5,000–₹1,00,000/day penalties; one lot is 30–50% of the book | Cash settlement restored for single-stock derivatives |
| Index futures as a 7-day tool | 1 lot = ₹15.52 lakh = 31% of equity; hedge P&L in a non-nettable 31.2% ledger | Lot notional ≤ ₹5 lakh (Rev 2.0 Book N's second condition) |
| Cash equity intraday (MIS), stocks or ETFs | s.66 speculative at 31.2%, 4-year ring-fenced carry; 8.3 bps at ₹1 lakh; H6 | Material intraday STT cut **and** reclassification out of s.66 |
| MTF leverage | 12.49–15.49% p.a. against ~11% expected equity or ~5.6% carry; interest not deductible against capital gains | MTF rates below ~8% |
| Nifty Smallcap 250 systematic | ESM Stage II = ±2% periodic call auction, 100% margin, trade-for-trade | Repeal of ESM/GSM |
| Book M — self-run momentum | H4 fails 5.0×; P1 defaulted packaged | An H4 waiver that does not exist |
| Book R — results-season drift | H4 fails 7.6×; no free Indian point-in-time consensus data | Neither is fixed by a free consensus dataset |
| Book A — CAS auction dislocation | MDE 36.4% today | **Deferred to 2027-08-31**, unchanged |
| **Book D — 5-session sectoral TSMOM** | §8.4: 7.60%/yr friction, 20.8% STCG, MDE 8.77–13.86%, 22.75% gross alpha required, contrarian literature | **Nothing at 5 sessions.** A liquid quote plus a monthly specification is Book Q's gate, not Book D's. |
| **Book Z — intraday sectoral ETF** | §8.5: five independent kills | Same four-part condition as intraday equity, plus H6 |
| Currency and commodity derivatives | Out of charter | Charter change |

---

## 10. Architecture delta against the existing `src/`

The existing tree is `costs.py`, `tax.py`, `universe.py`, `panel.py`, `harness.py`, `portfolio.py`,
`execute.py`, `ops.py`, `fetch.py`, `books/ledger.py`, `books/packaged.py`. Rev 3.0's delta is deliberately
tiny, because **a charter whose conclusion is "do not trade this" should not require a platform.**

| Module | Rev 3.0 change | First needed |
|---|---|---|
| `src/costs.py` | **None.** ETF, delivery, intraday, futures, options and exercise are already priced and verified to ₹1 at P0. §5's figures come from the shipped code. **Spread stays outside `costs`** — Book V passes a half-spread in. | — |
| `src/tax.py` | **None.** s.196 is the 7-day book's tax class and already exists; s.66 exists for the closed intraday case. | — |
| `src/fetch.py` | **None.** Reused as-is for AMFI and NSE quote pulls, with the inherited access discipline: session-cookie warm-up, ≤ 1 request per 2 seconds, exponential backoff, content-addressed cache, **no fetching between 09:00 and 16:15 IST**. | V0 |
| `src/universe.py` | **One as-of-date flag: `etf_liquid`**, set from the Book V pass list (**L13**). | V0 |
| `src/panel.py` | **No change on the expected path.** A sectoral-index-TRI + ETF LTP/NAV/premium join is required only if K0 leaves Book Q open, which it is not expected to. `close_method` (**L6**) already handles the 3 Aug 2026 CAS break for any CAS-eligible unit. | gated, F0 |
| `src/harness.py` | **No code change.** Three new pre-registration files loaded by the existing loader; three new `mde()` unit-test pins (6.51%, 8.77%, 11.90%). | K0 |
| `src/portfolio.py` | **No new limits.** Rev 1.0 §6.1's 25% single-sector and 40% active-sleeve caps already exist and already assert at a ₹1 breach (L2, DONE). Rev 3.0 only requires that **a sectoral ETF be classified as one sector** rather than as one name — a mapping, not a rule. | V0 |
| `src/execute.py` | **No change on the expected path.** No new order type; no intraday path; no F&O path. If a human accepts Book W, index-fund purchase and redemption instructions ride the existing instruction-list mechanism. | — |
| `src/books/ledger.py` | **One extended function.** `etf_vs_constituents` becomes a three-way `route_exposure(etf_quote, etf_premium, fund_ter, constituent_impact)` adding the premium/discount term. Roughly twenty lines; it belongs to Book L, which already owns routing. | V0 |
| `src/books/packaged.py` | **Extended, not rewritten.** Add Next 50, Midcap 150 and Low Vol 30 to the existing TRI-versus-TER comparison for Book W's decision note. No self-run replication — that is what P1 STOPped on. | F1 |
| **`src/books/etf_screen.py`** | **The only new module.** The §6.1 gate: AUM, ADV notional, 20-day median quoted spread, median premium/discount, TER, top-1 and top-5 weights, effective N, index family — per name, per as-of date. | V0 |
| `src/ai/*` | **Not created.** `ai.extract.etf` is specified in §8.6 and is **not in v1**; hand-read the factsheets. | — |

**Net: one new module, one extended function, one new universe flag, three pre-registration files, zero new
runtime dependencies.** Still not in v1, and still not: Redis, Kafka, Kubernetes, tick replay, order-book
reconstruction, a second machine, a second broker, FIX, co-location, any intraday loop, and Polars until a
panel milestone actually imports it.

---

## 11. Hurdles and STOP language

Benchmark for relative hurdles is unchanged: **Nifty 50 TRI net of 0.04% TER, taxed at 13.0% on realisation**,
on the same capital and cash-flow schedule as the sleeve under test. H1, H3, H5, H6 and H7 stand exactly as
in [h0-hurdles.md](h0-hurdles.md). Rev 3.0 adds one hurdle and tightens two.

| # | Hurdle | Number | STOP |
|---|---|---|---|
| **H1** | Cost and tax fidelity | Unchanged: `costs` reproduces a real contract note to **₹1**, `tax` a hand-worked Tax Year 2026-27 computation to **₹1**. **Rev 3.0 addition, stated as a boundary not a feature:** `costs` does **not** and must not contain a spread. A book that quotes 3.9 bps as its trading cost has failed H1's spirit even while passing its letter. | Fails → **the platform stops.** |
| **H2** | After-cost after-tax excess, relative | Unchanged: any active **long-India** sleeve beats the benchmark by **≥ 300 bps/yr** over the full point-in-time sample. **It still binds here**: a sectoral ETF sleeve is 0.87 correlated to Nifty 50 (§6.3), so beating a flat Nifty by 50 bps after 760 bps of churn is not an edge, it is a rounding error with a tax bill. | Below 300 bps → the sleeve closes and its weight goes to the packaged vehicle or the core. |
| **H2-ABS** | After-cost after-tax return, **absolute** — **new in Rev 3.0** | **After-tax desk return ≥ after-tax 91-day T-bill roll + 200 bps = 5.85%/yr** at a 5.60% T-bill **(working, W3-07)**; **6.54%/yr** on Rev 2.0's sweep-FD base. Added because H2 alone would score −3% against a −6% Nifty as success, and this investor would not. | Fails in a tax year → the *absolute* claim is withdrawn in writing, and the choice is stated explicitly: accept a relative mandate (Rev 1.0) or move to β ≈ 0 (Rev 2.0). **§3.4 shows no long-only Indian equity sleeve can clear H2-ABS in a flat or down year at any horizon.** Do not let a hurdle failure be recorded as bad luck. |
| **H3** | Risk-adjusted | Unchanged: active Sharpe ≥ **0.40** after cost and tax, and ≥ **0.30 in each of two non-overlapping halves**. | Fails either leg → close. |
| **H4** | Measurability | Formula unchanged. **Two Rev 3.0 tightenings:** (a) **T is the intersection** of index history, ETF listing date and Book-V-pass dates (§7); (b) **σ is published before the first return is read**, from a return-free estimator. **And it is scale-invariant** — shrinking a sleeve does not improve the ratio (§3.3). | MDE > ½ E_net → **closes at pre-registration, before any data is looked at.** Sixth specification → closes regardless of result. |
| **H5** | Capacity | Unchanged, plus an ETF-specific leg: a clip must be ≤ **2% of the name's 20-day median traded value**, and the modelled impact at **6× the actual clip** must not exceed **2× the quoted half-spread**. Capacity is otherwise slack (§2, rung 9). | Fails → reduce the clip, not the hurdle. |
| **H6** | Operability | Unchanged: one machine, one broker, one ~16:15 IST run, ≤ **8 orders/second** coded against TOPS 10, exchange algo ID on every order, reconciled to the broker ledger to ₹1 before the next pre-open, documented and exercised manual fallback. | **This closes Book Z by construction**, before any economics. If a design needs a second machine, a second broker or intraday supervision, **stop and redesign.** |
| **H7** | Whole-desk | Unchanged: after-tax return trails Nifty 50 TRI by **> 600 bps** in a tax year → halt active sleeves, move to 100% core, write an X0 review. **Rev 3.0 addition if a human accepts a sector sleeve:** realised single-sector weight above **25%** on any measurement date is a limit breach, not a drift, and halts the sleeve. | Halt and review. |

**A negative honest result is a completed milestone.** A STOP memo that says *"Book D closed at
pre-registration because its implementable MDE was 8.77%/yr against a hypothesised effect of at most 2.0%,
because 50 five-session turns cost 7.60%/yr, and because clearing H2 through a 25%-capped sleeve required
22.75%/yr of gross sector alpha — here is the arithmetic"* is worth more than a book trading on an
unmeasurable claim. Books close; the platform continues.

---

## 12. Risks specific to short-horizon ETF trading

| Risk | Exposure | Mitigation in this design |
|---|---|---|
| **Quoted spread mistaken for statutory cost** | The single most likely way this brief gets implemented badly: 3.9 bps is a real, citable, *shipped* number and it is 40× too small for a sectoral ETF | Spread is structurally outside `costs` (H1); Book V's gate is a precondition to any instrument list; §5.2's all-in table is the only quotable cost |
| **Premium/discount to NAV** | Thin ETFs trade away from NAV; creation and redemption belong to the AMC and its authorised participants, **not to this PAN** — the arbitrage that should close the gap is not available to the desk | V-gate: 20-day median \|premium\| ≤ 15 bps; routing rule prefers the index fund at NAV when the ETF's premium exceeds its spread advantage |
| **Backtesting the index and trading the ETF** | A tradability look-ahead that inflates every short-horizon result | **L13**: as-of-date `etf_liquid` flag; H4's intersected T; the date-shift test already in `harness` |
| **Sectoral ETF history shorter than sectoral index history** | Using the ETF's own T makes MDE 1.4–1.6× worse, in the direction nobody checks | H4 requires the intersection, and §7 tabulates both |
| **Concentration presented as diversification** | Nifty Bank is effectively 6.1 names with a ~30% top holding | Effective-N is a reported column in Book V; the 25% sector cap treats one sectoral ETF as one sector |
| **Correlation to the thing being avoided** | ρ 0.87–0.93 across every packaged alternative | Printed in §6.3 and in Book W's decision note. Sector rotation is never described as market-neutral |
| **Spread blow-out on event days** | RBI MPC, Budget, results clusters — precisely the days a sector rule wants to trade | Limit orders only; no MIS; **no book that must exit on a named day** |
| **CAS and the two closing mechanisms** | Some ETF units are CAS-eligible; the official close changed on 3 Aug 2026 for >200 names | **L6**: `close_method ∈ {vwap_30min, cas_auction}`; no pooling across the break without a declaration |
| **s.196 arriving as a surprise** | A profitable 7-day book is taxed at 20.8% from the first rupee with **no exemption**, and a loss year still generates s.44AB absolute-sum turnover | `tax` already computes this; the required-move tables in §1.5 are stated post-tax |
| **L10 leakage** | The brief explicitly invites AI directional prediction | §8.6: L10 stays, and the reason is that relaxing it buys zero hurdle relief. Book Q's ranker is a published sort or it does not exist |
| **A hurdle failure recorded as bad luck** | H2-ABS is structurally unreachable in a down year, not unluckily missed | §3.4 states this in advance so the failure is pre-diagnosed |
| **Single-broker, single-machine concentration** | Unchanged from Rev 1.0 | Accepted at ₹25 lakh–₹1 crore; re-examined at the ceiling |

---

## 13. What would change this design

Named Indian triggers, stated in advance so a later agent recognises one rather than rationalises one.

1. **Book V finds ≥ 3 sectoral ETFs with a 20-day median quoted spread ≤ 11 bps and AUM ≥ ₹2,000 crore** →
   re-run Book Q's MDE at the lower friction. Note Book D still faces 50 × 8.2 bps = **4.10%/yr** and
   MDE 8.77%, so it stays closed; this is a Book Q trigger only.
2. **STT on equity-oriented fund units raised toward the delivery rate** → the 2.7–3.9 bps statutory story
   dies, the case for index funds over ETFs strengthens further, and §5 must be re-run from `costs`.
3. **A holding-period concession below twelve months, or an s.196 exemption threshold** → not proposed, and
   the only change that would make a sub-12-month Indian book tax-rational. Without it, every 7-day gain is
   20.8% from the first rupee.
4. **Index lot notional ≤ ₹5 lakh** → reopens *hedged* expressions (Rev 2.0 Book N's second condition), not
   long-only 7-day ETF rotation.
5. **A free point-in-time Indian sectoral **ETF** quote and AUM history ≥ 15 years** → makes T honest in §7.
   It does not shrink σ, so it moves Book Q's MDE from 10.30% to 6.51% and leaves it failing 7.7×.
6. **A retail-accessible ETF creation/redemption channel** → would make the premium/discount tradable and
   turn Book V's routing term into a book rather than a rule. No sign of this.
7. **Capital crossing ₹1 crore** → re-derive Rev 1.0 §6 entirely; Book L's edge halves and the 25% sector cap
   becomes a ₹25 lakh position, at which point Book V's ADV test starts to bind.
8. **The investor's requirement resolves to "positive rupees regardless of the Indian tape"** → the answer is
   **Rev 2.0**, and it should be recorded as a charter selection with the §3.4 arithmetic attached, not as a
   Rev 3.0 amendment.
9. **The investor accepts a relative mandate** → the answer is **Rev 1.0**, already ACTIVE, with Book W as an
   optional ≤ 40% tilt. This file archives.

---

## Appendix A — Working numbers register

Nothing tagged **(working)** may be used in a live decision until it is resolved at the named milestone.
**W3-01 and W3-04 must be resolved before any other part of this design is read as actionable**, because the
entire product board depends on them.

| # | Number used | Where it matters | Verify at | Status (2026-09-10) |
|---|---|---|---|---|
| **W3-01** | **Sectoral ETF quoted spreads: BANKBEES 154 bps, ITBEES 258 bps, PHARMABEES 346 bps, FMCGIETF 173 bps, BFSI 196 bps** | Rung 1; §1.1, §1.5, §4, §5 — the binding constraint of the whole charter | **V0, first** | **Working and stale.** Third-party aggregator figures carried forward from the Rev 3.0 draft this file replaces; **not independently verified here.** Replace with a 20-day median from free NSE quotes. Every "stored quote" row in §5 is a scenario, not a measurement. |
| W3-02 | Daily σ: Nifty 50 0.8–1.0%; Nifty Bank 1.1–1.4%; Nifty IT 1.3–1.5%; HDFCBANK 1.5–2.0%. Median \|move\| = 0.6745σ | §1.1, §1.3, §1.4, §3.2 | F0 / U0 | **Working.** Order of magnitude. Recompute from the U0 panel; note the normality assumption used for P(\|move\| ≥ cost) is a convenience and understates tails. |
| W3-03 | Index weights → effective N: Nifty Bank 6.1 (12 names, top-1 ~30%), Nifty IT 5.7, Nifty 50 22.1 | §1.4, §6.2 | V0 | **Working.** Weight vectors are illustrative; replace from the current NSE Indices factsheets. |
| **W3-04** | **ETF AUM and TER: BANKBEES ₹8,379 Cr / 0.21%; ITBEES ₹3,480–3,533 Cr / 0.29%; PHARMABEES ₹1,356 Cr / 0.21%; FMCGIETF ₹809 Cr; BFSI ₹418–432 Cr; AXISCETF ₹14 Cr** | §4's pass/fail; §5.4's drag table | **V0** | **Working.** Carried forward unverified. AMFI monthly AAUM and scheme TER disclosures are the authority; AUM dates differ by name (29 May to 31 Jul 2026 as cited) and must be aligned. |
| W3-05 | Correlations and betas to Nifty 50: Low Vol 30 0.93/0.85; MOM30 0.90/1.05; Midcap 150 0.88/1.10; Next 50 0.90/1.15; Nifty Bank 0.87/1.15; σ_Nifty 14%/yr | §6.3 — the "no different beta" finding, and every active-σ input to §7 | F1 | **Working.** Compute from NSE Indices TRI over ≥ 10 years; publish before any σ is used in a pre-registration. |
| W3-06 | Usable T: sectoral **index** ~20 yr; sectoral **ETF** ~8 yr | §1.5, §3.3, §7 | K0 | **Working.** Resolve per name from actual NSE listing dates; the intersected T of §7 is what H4 uses. |
| **W3-07** | **91-day T-bill 5.60%**, and sweep FD 6.60%, as the H2-ABS bases | §3.4, §11 | K0, then quarterly | **Working.** Imported from Rev 2.0 (W4, W3 there). RBI auction results / DBIE; the actual bank card for the FD, not an aggregator. |
| W3-08 | Nifty 50 direct index fund TER ~0.10%; NIFTYBEES 0.04%; MOM30 direct 0.34% | §4, §5.4, §8.2 | F1 | **Working.** AMFI scheme TER disclosures. Rev 1.0 sourced the ETF and MOM30 figures; the plain index fund TER is a range across AMCs. |
| W3-09 | Nifty 50 dividend yield ~1.3%, used to convert a −6% price year to a −4.7% TRI year | §3.4 | F1 | **Working.** NSE Indices. Used only in a hurdle illustration, never in a size. |
| W3-10 | Book Q σ_active 10.4%, Book D 14.0%, Book Z 19.0% | §7's MDE column | **K0, before any peek** | **Working.** Derived in §6.3 from W3-05 for Q; D and Z add timing noise and are asserted. Must be pre-registered from a return-free estimator or the books close on H4's second tightening. |
| W3-11 | Book Q gross sector-momentum spread 3.97%/yr, giving E_net 1.70% | §7, §8.3 | K0 | **Working.** Reverse-engineered from a 1.70% E_net target, not measured. If the pre-registered gross is lower, Book Q's failure margin widens. |
| W3-12 | 8%/yr gross return used in the §3.1 cadence comparison | §3.1, §0 | — | **Working, and deliberately an assumption.** The comparison is a *ratio*; the conclusion (4% retained versus 86% retained) is insensitive to the level. |

Inherited and still open from Rev 1.0: **W6** (NSE monthly impact-cost file — needed for H5 on any stock leg
and for §5.2's Nifty 50 impact column), **W13** (SBI Nifty 50 ETF AUM composition), **W15** (vendor prices,
re-checked on the day of any purchase), **W16** (Book A's hypothesised effect, dated 2027-08-31).

---

*Competing charter. Does not replace [india-equity-architecture-blueprint-rev2.md](india-equity-architecture-blueprint-rev2.md)
(Rev 2.0, ACTIVE) until a human accepts it.*
*Companion: [india-equity-execution-plan-rev3.md](india-equity-execution-plan-rev3.md).*
