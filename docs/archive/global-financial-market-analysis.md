# Global financial-market investment analysis

| | |
|---|---|
| **Date** | 2026-09-14 |
| **Status** | ANALYSIS / DRAFT for the architect |
| **Review** | Claude Opus |
| **Scope** | Every product and venue that is **not** the US tape and **not** the India tape, plus how the two existing desks join |
| **Taxpayer** | [investor-profile.md](../investor-profile.md) (2026-09-14) · calendar [residency-calendar.md](../residency-calendar.md) |
| **Does not replace** | [india-equity-architecture-blueprint-rev2.md](../next/india-equity-architecture-blueprint-rev2.md) Rev 2.0 (**ACTIVE**, 2026-09-14) · [alien-us-equity-architecture-blueprint.md](../next/alien-us-equity-architecture-blueprint.md) Rev 1.0 |
| **India identity** | Declined-beta **carry** desk. Rev 1.0 Nifty-delivery charter is [superseded](india-equity-architecture-blueprint.md). |
| **Imports as fact** | India Rev 2.0 product verdicts and closed list; alien-desk wrapper verdict, hurdles N1–N9, and the $60,000 situs cap; US-person desk pre-tax friction only |

Every number not sourced to a statute, circular, exchange rule, fund document or the desks above is tagged **(working)** and carries a verification owner in [Appendix A](#appendix-a--working-numbers-register). Milestones named **GL0–GL5** are new; **W1** is the alien desk's already-authorized written cross-border opinion.

---

## One-line thesis

Once the alien desk owns an Ireland-domiciled accumulating USD-line UCITS core and the India desk owns a **low-beta rupee carry core** (direct-plan arbitrage funds, Nifty beta off by default), **the entire non-US non-India product universe collapses to three things that are not alpha**: a wrapper configuration the alien desk has not yet priced correctly, a set of FEMA and settlement-calendar constraints that protect a step-up nobody else owns, and a cross-book realisation ledger — while every global premium (carry, cross-country value and momentum, term premium, commodity roll) fails its MDE gate by 5–16× *before* the Indian 24-month line converts it to slab tax. **There is no third equity book and none is proposed.**

---

## 0. Derivation — the constraint ladder for global products

This is not the India ladder and not the alien-US ladder. Both of those start at tax. A global product for this taxpayer starts one rung earlier, because unlike US-listed stock (already held) and Indian equity (rupees already onshore), **a non-US non-India product first has to be purchasable at all**.

### 0.1 Rung 1 — Funding and FEMA: can this be bought without LRS?

The USD book exists because of **FEMA s.6(4)**: a person resident in India may hold, own, transfer or invest in foreign currency, foreign security or immovable property outside India if it was acquired while resident outside India. **RBI A.P. (DIR Series) Circular No. 90 of January 2014** clarifies the operative sentence for this desk:

> "A person resident in India may freely utilise all their eligible assets abroad as well as **income on such assets or sale proceeds thereof** received after their return to India for making any payments or **to make any fresh investments abroad without approval of Reserve Bank**, provided the cost of such investments … are met exclusively out of funds forming part of eligible assets held by them."

Three consequences, all structural, and the first two are the most important findings in this document for the alien desk:

1. **The Book W wrapper migration and the Book R step-up are FEMA-clean without LRS.** Selling VTI/VXUS and buying Irish UCITS is a fresh investment abroad met exclusively out of s.6(4) eligible assets. No RBI approval. No LRS envelope consumed. This is the statutory basis the alien desk's plan assumes but does not cite, and it should be in W1's scope alongside the tax questions.
2. **There is a 180-day counterparty to that permission and it points at idle cash.** Regulation 7 of the Foreign Exchange Management (Realisation, Repatriation and Surrender of Foreign Exchange) Regulations, 2015 requires realised foreign exchange, **unless reinvested**, to be repatriated within 180 days, and practitioner commentary is explicit that *merely holding funds in a foreign bank or brokerage account is not "reinvestment."* Whether Reg 7 reaches s.6(4) assets at all is genuinely contested **(working)** — s.6(4) is a carve-out inside the Act — but the exposure is asymmetric: a strict reading would force sale proceeds home to India, which detonates **N6** (receipt in a US account, zero tolerance) and hands India a taxable receipt during RNOR. The cost-free response needs no legal opinion: **keep the sell-to-repurchase gap in Book R measured in days, and hold the cash sleeve in an instrument rather than as an idle deposit.** This is an independent reason for Book K below.
3. **Any global product that must be bought with rupees is out of reach.** It would need a new LRS remittance — 30–80 bps of bank FX spread **(working)**, 20% TCS above ₹10 lakh as a cash-flow drag, a scarce $250,000/FY envelope the brief forbids assuming, and it would compete for the ₹25 lakh–₹1 crore India book I am not permitted to reallocate. **This single rung closes MCX, GIFT City / IFSC, INR-denominated global feeder funds, and every Indian commodity contract before any of them reaches a tax or friction test.**

**Rung 1 verdict.** The viable global menu is exactly "things buyable with already-held USD through the existing offshore custody chain." Everything else is closed on funding, not on merit.

### 0.2 Rung 2 — Tax character, where India is the only tax authority

For a **non-US** product held by an NRA, the US does not appear at all: no US source, no 871(a) FDAP, no 871(a)(2) question, no 1042-S. The tax analysis is India-only, and it is harsher than the US one it replaces.

| Income from a non-US non-India product | Source country | India RNOR | India ROR |
|---|---|---|---|
| Dividends from foreign listed shares | Treaty WHT 10–15% typical; UK 0%; HK/SG 0%; CH 35% statutory with reclaim to 10% **(working)** | **0** if received outside India — **and the source WHT is therefore uncreditable, a dead cost** | Slab ~31.2%, FTC for source WHT via Form 67 |
| Distributions from a non-Irish / distributing fund | 0 from Ireland; varies elsewhere | **0** if received outside India | Slab ~31.2% |
| Accumulating Irish UCITS | **0** — nothing is distributed | **0** | Nothing realised; deferred into the capital gain |
| Gain on any foreign listed security, fund unit or ETC | Generally 0 (no source-country CGT for a non-resident on listed securities in the venues that matter) | **0** if received outside India | **>24 months → ≈13.0%** on the **INR-measured** gain, no indexation, no ₹1.25 lakh exemption; **≤24 months → slab ≈31.2%** |
| Interest on non-USD cash or foreign bonds | Gilts/Bunds/JGBs 0 to non-residents **(working)** | **0** if received outside India | Slab ~31.2% |

Two findings follow, and the second is the one that kills the global alpha menu.

**Finding A — source withholding on direct foreign shares is a pure, uncreditable loss during RNOR.** This is the same structural defect the alien desk used to close ADRs and US-listed international ETFs, and it applies identically to buying Toyota on the TSE or Nestlé on SIX. A Japanese 10% treaty rate requires a residence certificate and beneficial-ownership documentation lodged with a foreign custodian; a Swiss reclaim from 35% to 10% is a paper process with a multi-year lag. **An Irish accumulating fund suffers the fund-level withholding once, invisibly, and distributes nothing — the investor-level leak is zero in both regimes.**

**Finding B — the 24-month foreign-share line converts every published global factor premium into a slab-taxed sleeve.** No documented cross-country value, momentum, carry or roll strategy rebalances less often than every two years; most rebalance monthly or annually. At ROR, every one of them realises inside 24 months and pays **~31.2%**, not 13.0%. The spread between those two rates is **1,820 bps of realised gain**. A packaged accumulating UCITS that runs the same process internally produces no investor-level realisation — which is why, if a global tilt is ever wanted, it must arrive packaged and accumulating, never self-run.

### 0.3 Rung 3 — Situs and succession in a third country

The alien desk solved US situs by leaving the US. The global menu reintroduces the same problem in other jurisdictions, and this rung is where several otherwise-attractive products die.

| Jurisdiction | Trigger | Exposure | Effect on this board |
|---|---|---|---|
| **United Kingdom** | UK-situs assets of a non-UK-domiciled individual — shares on a UK register, i.e. **UK-incorporated companies** | Nil-rate band **£325,000**, 40% above **(working)** | Closes direct LSE-listed UK company shares. **Does not touch Irish-incorporated UCITS listed on LSE** — which is precisely why the core is bought there |
| **Ireland** | CAT on Irish-situs property; s.11(2A) CATCA 2003 deems shares in an Irish-incorporated company Irish-situs | 33% above a €20,000 class-C threshold **(working)** | **Substantially resolved, favourably.** **s.75 CATCA 2003** exempts gifts and inheritances of **units of an investment undertaking** (Part 27 TCA 1997) where **neither disponer nor successor** is domiciled or ordinarily resident in Ireland. An Irish UCITS ETF is an investment undertaking. The chain is: deemed situs → s.75 exemption. See §0.4 for why this matters more than it looks |
| **Luxembourg** | Succession tax follows the **deceased's residence**, not asset situs; only Luxembourg immovable property reaches a non-resident **(working)** | Nil for fund units | Luxembourg fund units carry **no** succession exposure — relevant only as the fallback if s.75 fails |
| Germany, France, Netherlands, Switzerland | German *Inlandsvermögen* needs ≥10% of a German company; French/Swiss rules reach local securities in some readings **(working)** | Small at this size | Adds a third-country question for no return. Confirms the close on direct European shares |
| Hong Kong, Singapore, Australia, Canada | No estate/inheritance duty (HK abolished 2006, SG 2008, AU 1979, CA never) | Nil | These are the *clean* venues on succession — and there is still nothing worth buying on them directly |

**Rung 3 verdict.** Irish accumulating UCITS units bought on LSE are neither US-situs nor UK-situs, and s.75 CATCA 2003 supplies a named statutory path out of Irish CAT. **That is a stronger position than the alien desk's blueprint currently records** (it lists Irish CAT as an unresolved working item with a fallback of "revert to the $60k cap plus a priced tail"). The statutory citation belongs in W1's brief so the opinion confirms rather than researches it.

### 0.4 Rung 4 — Wrapper, and the cost of an extra line

The alien desk has already decided accumulating over distributing and Ireland over Luxembourg. Both verdicts hold. Two refinements change the *reasons* and one changes the *arithmetic*.

**Ireland vs Luxembourg is a US-treaty question, not a subscription-tax question.** Luxembourg Circular L.G.-A. No. 61 (24 Dec 2024) lists the **USA** among jurisdictions for which a certificate of residence **cannot** be issued to a SICAV/SICAF, so Luxembourg funds suffer **30%** US withholding where Irish funds suffer 15%. Separately, **passive ETFs are exempt from Luxembourg's 0.05% *taxe d'abonnement*** **(working)**. The practical gap is therefore:

| Line | Ireland advantage over Luxembourg |
|---|---|
| US equity (1.02% SEC yield, W0) | **~15.3 bps/yr** (15 percentage points of WHT on the dividend) |
| World ex-USA / EM / bond / commodity | **~0 bps/yr** — no material US-source dividend for the treaty to reach |

So "Luxembourg only where no Irish equivalent exists" is correct for the US leg and **over-strict for every non-US leg**, where Luxembourg lines can be treated as substitutes on tracking and TER alone. This matters if s.75 ever fails: the fallback is not only "back to US-listed under a $60k cap" — it is **domicile-splitting**, keeping the US leg Irish and moving non-US legs to Luxembourg at roughly zero cost.

**W0's two core configurations are not the same portfolio, and the difference is emerging markets.** W0 records CSPX + XUSE (70/30) as the chosen pair and VWRA as "the permitted single-line substitute." **XUSE tracks MSCI World ex USA — developed markets only, no EM at all. VWRA tracks FTSE All-World, which includes EM at roughly 10% (working).** The pair and the single line differ by about 10% of global market capitalisation. That is a portfolio-composition fact, not a fee comparison, and it should be surfaced to the investor before the migration rather than discovered after.

**Every extra line is a Schedule FA row, and the penalty regime is not proportionate to the saving.** W0 measured the pair's recurring advantage over the single line at **22.04 − 18.73 = 3.31 bps/yr**, which on the $354,097 marked book is about **$117/yr ≈ ₹11,000/yr**. Against that, s.43 of the Black Money (Undisclosed Foreign Income and Assets) Act carries a **₹10 lakh per year** penalty for failure to disclose a foreign asset, with a de-minimis for non-immovable assets up to ₹20 lakh aggregate that this book is 16× over **(working)**. The pair wins on fees; the single line wins on disclosure surface and includes EM. **Line count is a compliance-risk variable, not only a cost variable, and W0 priced only the cost side.** The architect should hand the trade-off back with both numbers on it. I do not choose it — it touches composition.

### 0.5 Rung 5 — Friction, venue fixed cost, and the FX leg

Three product-structure facts, none of which needs a forecast.

**The currency of a share *line* is not currency exposure.** A USD line of a World ex-USA fund is unhedged; the currency risk lives in the assets. Buying the GBP or EUR line of the same fund buys identical economics and adds an FX conversion leg plus a second currency trail that the INR-measured gain computation at ROR has to carry. **There is never a reason to leave the USD line.** Conversely, a **currency-*hedged* share class is a hedge book wearing a wrapper** — it costs the interest differential, it takes an FX view the investor has forbidden, and the hedge P&L sits inside NAV where it is invisible. Closed.

**Venue fixed cost scales inversely with capital and binds at the envelope floor.** Adding Xetra, Tokyo and Hong Kong to an IBKR-class account costs roughly **$30/month of market data (working)** — trivial at $500,000 (7.2 bps/yr) and **144 bps/yr at the $25,000 floor**, which is more than the entire wrapper saving the desk is being rebuilt to capture. Almost every UCITS line worth owning has a **USD line on LSE**. One venue, one subscription, no FX leg. This is the arithmetic behind the LSE-only posture and it should be stated as a rule rather than rediscovered per product.

**Transaction taxes are the second venue filter.** UK **SDRT 0.5% on purchases of UK-incorporated shares** — 50 bps one-way, and explicitly *not* applicable to Irish-incorporated shares traded on LSE. Hong Kong stamp **0.1% each side**. Switzerland stamp **0.15%/0.30%**. France FTT **0.3%**, Italy **0.1%**, Spain **0.2%** **(all working)**. Against an 8–15 bps round trip on the LSE USD UCITS line at small size (4–8 bps at $100k+ clips, per the alien desk's rung 3), **every direct-share route on a taxed venue costs 3–10× the packaged route before withholding and situs are counted.**

**Session overlap is an execution fact, not a trade.** LSE trades 08:00–16:30 London; New York 09:30–16:00 ET is 14:30–21:00 London; Tokyo closes at 06:00–07:00 London; Australia and Hong Kong close before or just after the LSE open. Consequences:

- A US-exposure UCITS line dealt on LSE before 14:30 London is being made against a **stale index**, priced off futures. Deal it in the **final two hours of the London session**.
- A World ex-USA line has **zero overlap with Asia ever** and loses Europe at 15:30 London. Its structural sweet spot is a narrow **14:30–15:30 London** window when Europe is still open and the US session is live.
- Four weeks a year the offset moves: the US switches to EDT on the 2nd Sunday of March and the UK to BST on the last Sunday, and the reverse gap falls between late October and the first Sunday of November. In those weeks the overlap starts an hour earlier, at **13:30 London (working)**.

### 0.6 Rung 6 — Inference

`MDE_ann = 2.80 σ_ann / √T`, the same gate both existing desks use (India H4, alien N3). Publish n, σ and MDE before any peek; if MDE > ½ × the hypothesized after-cost after-tax effect, the book closes without a peek. Trial budget **5 pre-registered specs, α = 0.01** (N7). Note that annualising does not rescue a monthly sleeve: for an i.i.d. active return the ratio is frequency-invariant, so rebalancing faster buys observations and vol in equal measure.

Global premia are, without exception, annual-frequency phenomena documented on 30–50 years of index history with active volatilities of 5–16%. The full table is §5. **Every one fails by 4.8× to 15.8×**, and that is *before* Finding B converts them to slab tax. The RNOR window (2–3 years) cannot certify any of them, for exactly the reason the alien desk gave: discovery runs on history, and a book whose tape is the residency window has 24–36 observations.

### 0.7 Rung 7 — Alpha

Empty. Stated plainly in §2 and §5 rather than softened.

---

## 1. Product board

Verdicts: **VIABLE** (buy or use it) · **CANDIDATE-GATE** (a named, cheap test decides) · **CLOSED** (killed here, with a named reopen trigger in §3) · **OUT** (already owned by another desk, or not this analyst's job).

### 1.1 Developed equity outside the US

| Product | Verdict | Binding reason | Clip / cadence | Tax RNOR → ROR |
|---|---|---|---|---|
| **Irish accumulating ex-US or All-World UCITS, USD line, LSE** | **OUT — it is the alien desk's core, and it is correct** | Nothing on this board beats it: 0 investor-level WHT, 0 US-situs, 0 UK-situs, s.75 CAT path, no FX leg, 8–15 bps once | Min economic clip ~$5,000–$10,000 (commission floor); bought once | 0 → deferred, 13.0% at >24m on the INR gain |
| Direct developed local shares — Xetra, Euronext, SIX, TSE, ASX, TSX, SEHK, SGX | **CLOSED** | Rungs 2, 3, 5 together: 10–15% treaty WHT **uncreditable during RNOR**, TRC/Form-10F documentation per jurisdiction, third-country succession questions, 10–50 bps of local transaction tax, FX leg, per-venue market-data fee | n/a | WHT dead cost → slab 31.2% on dividends |
| **LSE-listed UK company shares** specifically | **CLOSED** | **SDRT 0.5% on purchase** plus UK IHT above a £325,000 nil-rate band. The one venue this desk uses is the one venue whose *own* shares are worst | n/a | 0% UK dividend WHT is the only good cell |
| Single-country / regional accumulating UCITS (Japan, Europe, UK, Pacific) | **CLOSED as a book**; permitted only as a **≤20% no-alpha-credit tilt** on the terms the alien desk already set for factor tilts | Country selection is a measurable claim and it fails at 10.6× (§5). Mechanically clean, economically unsupported | — | Same as core |
| US-listed developed-international ETFs (VEA, EFA, IEFA, EWJ) | **CLOSED — confirmed, not reopened** | Alien desk rung 1: the worst wrapper leak in the programme, ~72.5 bps/yr of double withholding, plus 100% US-situs | n/a | 25% FDAP → slab with FTC |
| Currency-hedged share classes of any of the above | **CLOSED** | A hedge book in wrapper clothing. Costs the interest differential (~200 bps/yr USD/INR, ~0–150 bps USD/DM) and takes an FX view the investor forbids | n/a | — |

**Does anything remain once the 30% ex-US UCITS line exists? No.** The developed-ex-US equity premium is fully captured, at the lowest available cost, in a line that already appears in the alien blueprint. The only open item is the composition question in §0.4, which is a wrapper configuration, not a book.

### 1.2 Emerging-market equity excluding India

| Product | Verdict | Binding reason | Clip | Tax RNOR → ROR |
|---|---|---|---|---|
| EM at index weight inside an All-World accumulating line | **OUT — part of the core if the single-line configuration is chosen** | Cheapest possible access; no decision to make beyond §0.4 | — | 0 → 13.0% deferred |
| Standalone Irish accumulating EM UCITS, USD, LSE | **CANDIDATE-GATE (GL2)** — *composition input only, not a sleeve* | Exists and is cheap: iShares MSCI EM UCITS ETF USD Acc, **IE00B4L5YC18, TER 0.18%**, physical, Ireland. Relevant **only if** the desk chooses CSPX + XUSE, which contains **no EM whatsoever** | ~$5,000 | 0 → 13.0% deferred |
| **EM ex-India UCITS** | **CLOSED — the product does not exist** | The market has built EM **ex-China** lines (iShares EXCS/EXCH IE00BMG6Z448 0.18%; Xtrackers XDEG IE00BM67HJ62 0.16%) and **no EM ex-India line**. The India double-count cannot be removed by substitution | n/a | — |
| Direct EM local markets — China A, Korea, Taiwan, Brazil | **CLOSED** | Rung 1 and rung 5: Stock Connect, investor-registration IDs, CVM 4373 registration. Structurally unavailable to a retail own-account book | n/a | — |
| HK-listed H-shares / China single-country | **CLOSED** | 20 bps round-trip stamp, PRC 10% dividend WHT, and it is a country bet that fails §5 at 10.6× | n/a | — |
| US-listed EM ETFs (VWO, IEMG) | **CLOSED — confirmed** | Same 72.5 bps double-withholding leak and US-situs | n/a | — |
| Frontier markets | **CLOSED** | Spread, capacity, custody | n/a | — |

**On the India weight inside the USD core.** Sized honestly: MSCI EM carries India at **11.01% (justETF, Aug 2026)**, and EM is roughly 10% of a global index **(working)**, so an All-World line holds India at about **1.1% of the whole USD book** — around **$3,900 ≈ ₹3.7 lakh** at the marked $354,097. The India desk's default beta is **≤ 0.10** (Rev 2.0), so that line may be **the household's only India equity**. It is still not worth a book — it is one ledger line so the household knows the number. Nifty is not reopened and no India product is judged here.

### 1.3 Rates, sovereign and credit

| Product | Verdict | Binding reason | Clip | Tax RNOR → ROR |
|---|---|---|---|---|
| **Irish accumulating global-aggregate or developed-sovereign UCITS, USD line** | **VIABLE AS A PRODUCT** — the only correct duration vehicle if duration is ever wanted. **Whether to hold duration is an allocation decision and is not mine** | Deferral is the entire game: a distributing bond fund pays slab ~31.2% on coupon every year at ROR; an accumulating line rolls it into a 13.0% gain at >24 months. On a 4% yield that gap is **~125 bps/yr vs ~52 bps/yr (working)** | ~$10,000 | 0 → deferred 13.0% |
| **Irish accumulating USD ultra-short / T-bill UCITS as the post-cliff cash sleeve** | **CANDIDATE-GATE (GL3) — Book K** | Two independent reasons: the ROR coupon-to-gain conversion above, and the FEMA Reg 7 "reinvested, not idle" exposure in §0.1 | ~$10,000; institutional MMF classes at $100k–$5m minimums are **out of reach** | 0 → deferred 13.0% |
| Distributing bond funds, any domicile | **CLOSED** | Slab ~31.2% on every distribution at ROR, plus Form 67 forever. Strictly worse than accumulating, same reasoning the alien desk applied to equity | n/a | — |
| Direct foreign sovereigns — gilts, Bunds, JGBs | **CLOSED** | 0% source WHT is the only good cell. Against it: 20–50 bps dealing on non-benchmark lines, ladder management, slab-taxed coupon at ROR, and a UCITS line is cheaper and diversified | $100k+ for institutional lines | Coupon slab at ROR |
| Global IG and HY credit as a book | **CLOSED** | ~90–110 bps IG spread and ~300 bps HY **(working)** does not survive 13.0–31.2% tax, 15–40 bps dealing, and default/downgrade risk at retail size. Permitted only at index weight inside an aggregate line | — | — |
| EM local-currency sovereign debt | **CLOSED** | It is an FX carry trade wearing a bond label — forbidden — plus 10–20% source WHT and ~10% currency vol | — | — |
| Term-premium / duration timing as a book | **CLOSED at MDE** | §5: fails 9.1× | — | — |
| Non-USD cash and money-market instruments | **CLOSED** | Holding EUR, GBP or JPY cash *is* an FX position | — | — |
| US money-market funds | **OUT — already closed on the alien desk** | RIC shares are US-situs | — | — |

### 1.4 FX

The investor forbids FX alpha and forbids a currency hedge as a strategy. I confirm both are also the right answer on the arithmetic, and then state what is left.

| Product | Verdict | Binding reason |
|---|---|---|
| G10 FX carry, trend, value | **CLOSED three times over** | Forbidden by the investor; fails MDE at 8.1× (§5); and at ROR the P&L is slab ~31.2% with a live risk of business-income characterisation |
| INR NDF, offshore INR | **CLOSED** | A resident individual taking an offshore INR NDF position is not a permitted FEMA transaction **(working)**; also forbidden; also unmeasurable |
| USD→INR hedge of the USD book | **CLOSED on arithmetic as well as instruction** | Covered parity prices the hedge at the interest differential — roughly **200 bps/yr (working)** against a **3.5%/yr working** INR depreciation assumption. Before friction it is close to a wash; after dealing cost it is a loss; and **every forward roll is a realisation**, slab-taxed at ROR. The investor's instruction and the arithmetic agree |
| Non-USD share lines of the same fund | **CLOSED** | Adds an FX leg and a second currency trail in the INR-gain computation for identical economics |
| **Translation accounting at ROR** | **VIABLE — a measurement obligation, not a trade** | At ROR the gain is computed in **rupees**. A flat USD book still produces an Indian taxable gain from INR depreciation. The ledger must carry USD cost and the conversion basis. **Which rate applies (Rule 115 / TT buying rate on which date) is unresolved and belongs in W1** |
| **Session-overlap and listing-basis execution rules** | **VIABLE — an execution rule, not a book** | §0.5. Deal US-exposure lines in the last two hours of the London session; deal ex-US lines in the 14:30–15:30 London window. As *alpha* the basis is measurable and **negative** — see §5 |

### 1.5 Commodities, gold and the commodity roll

| Product | Verdict | Binding reason | Clip | Tax RNOR → ROR |
|---|---|---|---|---|
| **LBMA-backed physical gold ETC, USD line, LSE** | **VIABLE AS A PRODUCT** if gold is wanted at all. **Whether to hold gold is an allocation decision and is not mine** | TER 0.12–0.25% **(working)**; secured-note structure; allocated LBMA bars; **not US-situs, not UK-situs**; no US filing; buyable with already-held USD on the one venue already subscribed | ~$5,000 | 0 → 13.0% at >24m on the INR gain |
| **GLD and US-listed metal trusts** | **CLOSED** | Grantor-trust structure sells gold monthly to pay expenses, creating a stream of deemed dispositions for the holder; situs is unsettled against a **hard $60,000 cap**; and the TER gap alone is **~28 bps/yr** against the ETC | n/a | — |
| COMEX / CME metals futures (GC, MGC) | **CLOSED** | **Identical arithmetic to the alien desk's futures-core kill**: a quarterly roll is a realisation, slab ~31.2% at ROR, with business-income characterisation risk. §1256 is worth 0 to an NRA. Also indivisible: GC 100oz ≈ $400,000 and MGC 10oz ≈ $40,000 at ~$4,000/oz **(working)** | GC = 80% of the $500k ceiling | Slab 31.2% every year |
| **MCX gold and silver; all Indian commodity derivatives** | **CLOSED** | Rung 1 first — it needs rupees I cannot reallocate. Then: Gold Mini (100g) ≈ **₹11 lakh = 22% of a ₹50 lakh book (working)**; CTT on the sell side; two-month rolls; **non-speculative business income at slab 31.2%** with 8-year carry | Indivisible below Guinea/Petal, which are illiquid | Slab 31.2% |
| Broad-commodity swap-based UCITS as a book | **CLOSED at MDE** | §5: fails 15.8×, the worst ratio on the board. Index-weight allocation is not my call | — | — |
| Silver and PGM ETCs | **CLOSED as a book** | 2× the volatility, 0.19–0.40% TER, and a VAT question that gold (investment gold, VAT-exempt) does not have **(working)** | — | — |
| Gold-miner equity | **OUT** | It is equity and it already sits at index weight inside the core |
| LBMA / COMEX / MCX basis, EFP, loco-London arbitrage | **CLOSED** | Requires unallocated London accounts and futures margin. The MCX–London gap is an FX-plus-import-duty-plus-local-premium composite — i.e. a forbidden currency and policy trade wearing a metals label |

### 1.6 Wrappers that are not the already-chosen equity UCITS

| Wrapper | Verdict | Binding reason |
|---|---|---|
| Ireland, accumulating | **OUT — decided** | Alien desk rung 2 |
| Luxembourg | **OUT — decided, with a refinement** | Correct for the US leg (**15.3 bps/yr**, the US treaty, not the subscription tax, which passive ETFs escape). **Roughly neutral for non-US legs**, so Lux ex-US/EM/bond lines may be treated as substitutes on tracking and TER |
| Cayman / BVI offshore funds and feeders | **CLOSED** | No US treaty → 30% US WHT; $100k–$1m minimums; opaque; and each is another Schedule FA line with a ₹10 lakh penalty exposure |
| Synthetic (swap-based) **ex-US and EM** UCITS | **CANDIDATE-GATE (GL4) — Book S**, extending W2's existing gate | W2 passed synthetic at **20.6 bps/yr** advantage on the **US** leg, where the value comes from recovering residual 15% US withholding under the 871(m) qualified-index exception. **That mechanism does not exist for non-US underlyings** — the advantage there is smaller (5–15 bps **(working)**, from the counterparty's local WHT position). Same 10% NAV counterparty cap, same ≥10 bps threshold |
| **Offshore portfolio bonds / unit-linked life wrappers (Dublin, Luxembourg, Isle of Man)** | **CLOSED — and named, because it is the single most mis-sold product to this exact profile** | Marketed as tax deferral for the internationally mobile. Reality: **100–150 bps/yr** of wrapper plus adviser charges **(working)**, 5–8 year surrender penalties, $50k–$100k minimums, and at ROR a foreign life policy's proceeds are most likely "income from other sources" at slab — s.10(10D) requires an Indian insurer. It buys, at 100+ bps, the deferral an accumulating UCITS gives for 0 |
| UK ISA and SIPP, Singapore SRS and CPF, HK MPF, foreign pensions | **OUT — ineligible** | Each requires UK/SG/HK residency or local employment income. The taxpayer fails the entry test for all of them. Not a judgement, a fact |
| **GIFT City / IFSC — NSE IX, India INX, IFSC feeder funds, IFSC-routed US stock receipts** | **CLOSED** | Rung 1. A resident individual funds an IFSC account under **LRS**, which the brief forbids assuming. Also: the tax character of an IFSC holding for a resident individual is unsettled. The obvious question, killed explicitly |
| ELSS, NPS, PPF and Indian wrappers | **OUT** | Already closed on the India desk |

### 1.7 Cross-listings

| Product | Verdict | Binding reason |
|---|---|---|
| **ADRs** | **CLOSED — confirmed, with two added reasons** | Alien desk: 5–20 bps/yr depositary fees, home-country WHT uncreditable during RNOR, unsettled situs. Added: an ADR is commonly treated as **US-situs**, so it consumes the $60,000 budget for exposure a UCITS line gives at zero situs; and ADR/ordinary conversion arbitrage is a sub-second, locate-dependent business with a per-share conversion fee |
| **GDRs** (London/Lux, on Indian and EM issuers) | **CLOSED** | Reg S / 144A distribution restricts most lines to institutions at $100k+ clips with 100–300 bps OTC quotes; an Indian resident acquiring GDRs of Indian companies in the secondary market is a live FEMA question **(working)**; conversion headroom is issuer-controlled; and the two-way gap *is* the FX plus conversion cost |
| **India/US dual listings** — INFY, WIT, HDB | **CLOSED, and on principle** | The premium/discount is fungibility-limited and depositary-headroom-driven. There is no short leg (no short stock in v1; no retail cash short in India). Long-only, it is **an India single-name book living inside the USD account** — precisely the third national desk the brief forbids. Dual-listed names live in the book whose currency funds them, and in one book only |
| **US/UK dual listings** — SHEL, BP, RIO, AZN | **CLOSED** | SDRT 0.5% on the UK leg exceeds any observed basis; no short leg; UK IHT on the UK line |
| Listing-basis / session-overlap arbitrage | **CLOSED as alpha; retained as an execution rule** | §5: the basis is measurable and its net effect is **negative** — 2–6 bps of gap against an 8–15 bps round trip |

### 1.8 Joins between the two tapes

| Item | Verdict | Reason |
|---|---|---|
| **Cross-book realisation sequencing and loss set-off at ROR** | **VIABLE — arithmetic — Book J** | §4 |
| **Cliff and settlement calendar for the R1 step-up** | **VIABLE — arithmetic, date-bound — Book T** | §4. An input to the alien desk's R1; R1 owns execution |
| Total-India exposure measurement across both books | **VIABLE — $0 ledger line** | §1.2 |
| Cross-margining, netting, or capital transfer between books | **CLOSED** | No mechanism exists. LRS runs one way and is not the funding path; repatriation is a wire, not a strategy |
| Repatriation timing and household cash flow | **OUT** | Household capital decision, not mine |

---

## 2. Candidate books, ranked

Ranked by after-cost, after-**both**-tax contribution per unit of research risk. Arithmetic above predictive, because the evidence in §5 leaves no predictive candidate standing. **AI role is `none` on all five** — these are ledger, calendar and document-arithmetic books with no feature to extract and no forecast to make. The AI prohibition that matters here is the standing one: **no AI-generated tax conclusion; W1 written opinion only.**

### Book T (rank 1, and first in time) — Cliff, settlement and receipt calendar for the step-up

- **Hypothesis.** The alien desk's Book R is worth a measured **240 bps of current INR capital** and expires on **31 Mar 2028**. It is executed across venues and settlement cycles that nobody currently owns, and the failure mode is a **trade-date/receipt-date straddle across the cliff**: the realisation is trade-dated inside FY 2027-28 (RNOR) while the cash settles in early April 2028 (ROR). The whole 240 bps sits on the correct answer to that timing question.
- **Instrument.** No instrument. A dated calendar: FY-end **31 Mar 2028 (Friday)**; LSE and NSE holiday calendars for the final week; UK clocks move to BST on **26 Mar 2028**, so the 29–31 March session overlap is the normal 14:30–16:30 London; the UK/EU/Swiss move to **T+1 settlement is targeted for 11 Oct 2027 (working)**, i.e. before the window, which removes a day of straddle risk **if it lands on time**.
- **Effect size.** Zero new return. It protects 240 bps and the **N6** zero-tolerance receipt rule. That is the highest-value-at-risk item on this page.
- **Recommendation, stated as a constraint rather than a design.** Execute the step-up with **at least two clear weeks** of margin before 31 Mar 2028, not in the final session, so no leg straddles the cliff. Keep the sell-to-repurchase gap in **days**, both to avoid market risk and to stay clearly inside the FEMA Reg 7 "reinvested" reading (§0.1).
- **Kill.** None — it is a calendar, and it either exists before R1 or R1 runs blind.

### Book J (rank 2) — The join ledger: cross-book realisation and loss set-off at ROR

- **Hypothesis.** From FY 2028-29 one Indian return carries both books. Indian capital-loss set-off rules do not care which currency produced the loss: **a realised long-term capital loss can be set off against long-term capital gains including foreign-share LTCG, and a short-term loss against either.** A loss realised on the India desk can therefore shelter a gain realised on the USD desk in the same tax year, and vice versa. This is arithmetic, forecast-free, and **no single-desk document can see it** because each desk sees one currency.
- **Instrument.** A shared lot ledger spanning both books, denominated in INR, carrying the 12-month Indian line and the **24-month** foreign line separately.
- **Effect size.** Sheltering ₹5 lakh of gain is worth **₹65,000 to ₹1.56 lakh** depending on which bucket it lands in — roughly **17–41 bps of combined capital, one-off (working)**, plus a recurring timing benefit whose size depends on realisation volume.
- **Why it exists in 2026.** Because the household has exactly one PAN, two books, and no shared ledger. It becomes live on **1 Apr 2028** and not a day before — at RNOR both sides are zero and there is nothing to set off.
- **Already packaged?** No.
- **Kill.** If the measured cross-book set-off value at GL1 is **< 25 bps of combined capital**, Book J is not a book: fold the rule into India **Book S** (Rev 2.0 tranche ledger) and alien Book R and close it. **Open question for W1:** whether losses from other capital assets can reduce s.198 gains that carry the ₹1.25 lakh exemption. That is a tax conclusion, and it is forbidden to this analysis.

### Book K (rank 3) — Post-cliff cash-sleeve wrapper

- **Hypothesis.** At ROR, USD cash held as deposits or directly held T-bills pays **slab ~31.2% on interest every year**. The same economics inside an **Irish accumulating USD ultra-short bond UCITS** distributes nothing and is taxed once, at 13.0% on the INR-measured gain, after 24 months. It is also unambiguously *invested* rather than idle, which is the cheap answer to the FEMA Reg 7 question in §0.1.
- **Instrument.** Irish-domiciled accumulating USD ultra-short / T-bill UCITS ETF, USD line on LSE, TER ~0.07–0.10% **(working)**. **Not** an institutional MMF share class — $100k–$5m minimums put those out of reach.
- **Effect size.** **~30–70 bps/yr on the cash balance at ROR (working)**: roughly 125–170 bps of annual slab drag replaced by a ~98 bps accrual-equivalent that is further reduced by deferral. **Exactly zero during RNOR** — T-bills are already 0/0 and the wrapper adds nothing before the cliff.
- **Does not contradict the alien desk.** Its rule is "never a US money-market fund, because RIC shares are US-situs." An Irish accumulating line is neither a US MMF nor US-situs. This extends the cash verdict into a wrapper the US menu could not offer.
- **Kill.** Close and hold T-bills if the actual cash sleeve is **under ~$50,000** or the measured saving is **under 30 bps/yr on the sleeve**. Be honest about scale: at a $17,700 sleeve this is worth about $100/yr, and the FEMA argument may be the larger half of the case.

### Book Q (rank 4) — Core composition disclosure: EM presence and the India double-count

- **Hypothesis.** W0 records CSPX + XUSE and VWRA as substitutes. They are not: **XUSE is developed-only and carries no EM; VWRA carries EM at ~10% (working).** The choice therefore decides whether the USD book holds emerging markets at all — and, downstream, whether it holds India at ~1.1% of book on top of the ₹50 lakh India desk.
- **Instrument.** None. Two KIIDs and a spreadsheet.
- **Effect size.** As *return*: the pair's **3.31 bps/yr** fee advantage (W0, measured) against one extra Schedule FA line. As *information*: the difference between holding and not holding 10% of world market capitalisation, surfaced before an irreversible migration rather than after.
- **Kill.** Closes immediately once the index of the chosen ex-US line is confirmed from its KIID and the India weight is written into the ledger. **This book's deliverable is a number and a disclosure, not a trade.** The composition choice belongs to the investor and the alien desk; ≈₹3.7 lakh of India inside VWRA does not reopen a Nifty-beta sleeve on the INR desk.

### Book S (rank 5) — Synthetic replication on the non-US legs

- **Hypothesis.** W2 passed synthetic at **20.6 bps/yr** over physical on the S&P 500 leg, where the mechanism is recovering residual 15% US withholding through a swap on a qualified index outside 871(m). For **World ex-USA, EM and bond** legs there is no US withholding to recover, so any advantage must come from the counterparty's own local withholding position and is smaller.
- **Effect size.** **5–15 bps/yr (working)** if it exists at all.
- **Kill.** W2's existing gate, unchanged: **< 10 bps/yr measured advantage over ≥5 years, or any counterparty above 10% of NAV → physical only.**

### No predictive book is proposed

Stated as a result, not an omission. Every global premium in §5 fails its MDE gate by **4.8× to 15.8×** on history alone, before Finding B applies slab tax to the net effect. **A negative result honestly measured is a completed analysis.** The correct global posture for this household is: the existing accumulating UCITS core, correctly configured; the existing India desk; a shared ledger; and nothing else.

---

## 3. Explicitly closed, with the named change that would reopen

| Closed | Named reopen trigger |
|---|---|
| Direct developed-market local shares | A treaty-relief-at-source regime that removes the reclaim burden **and** removal of the local transaction tax. Neither is in prospect |
| LSE-listed UK company shares | Abolition of SDRT on listed UK shares |
| Single-country and regional UCITS as a book | Nothing statistical will reopen this; only a change in the investor's allocation mandate, which is not mine |
| US-listed international and EM ETFs | Repeal or extension of §871(k) to foreign-equity dividends of a US RIC |
| EM ex-India UCITS | **Launch of the product.** It does not exist today — only EM ex-China |
| Direct EM local markets | A retail-accessible registration route (currently institutional) |
| Distributing bond funds; direct foreign sovereigns | India taxing foreign accumulating fund NAV growth on accrual — which would remove the deferral advantage and flatten the comparison |
| Global IG/HY credit as a book | IG spreads sustained above ~250 bps with unchanged dealing cost |
| Term premium, commodity roll, cross-country value and momentum, FX carry, dollar premium | Only **T** moves these, and slowly. Re-run §5 when usable history extends materially, or if the Indian foreign-share long-term line moves from 24 months to 12 |
| G10 FX carry, INR NDF, USD/INR hedge | A change in the investor's mandate. The arithmetic also has to change, and covered parity does not move |
| GLD and US-listed metal trusts | A settled situs ruling placing a physically-backed grantor trust outside US-situs **and** a W3-lifted cap |
| COMEX and MCX metals futures | India ceasing to treat rolled derivative P&L as a realisation — i.e. a wrapper that does not exist |
| Broad-commodity UCITS as a book | Nothing statistical. Allocation only |
| MCX, Indian commodity derivatives, GIFT City / IFSC | **A funding path that is not LRS** — e.g. RBI permitting s.6(4) eligible offshore assets to fund an IFSC account directly. Named so a later agent recognises the trigger rather than rationalises one |
| Cayman/BVI funds; offshore portfolio bonds and unit-linked life wrappers | None credible. These lose to an accumulating UCITS by 100+ bps/yr on structure |
| UK ISA/SIPP, SG SRS/CPF, HK MPF | A change of residence, which is a different programme |
| ADRs, GDRs, dual listings, listing-basis arbitrage | Retail two-sided access with a short leg, which v1 forbids |

---

## 4. How the two tapes connect

**Nothing physically connects them, and nothing should.** Two currencies, two custody chains, two settlement cycles, one PAN. There is no cross-margining path, no netting, and no capital bridge: LRS runs India→offshore only and is not the funding path, while a repatriation is a wire whose tax character is set by what was realised, not by the wire. **The join is a tax return and a ledger, not a trade.**

Five connections, each with its kill.

**1. One Indian return from FY 2028-29.** It carries India-source salary and Indian equity; foreign capital gains computed **in rupees**; foreign dividends and interest at slab with Form 67 FTC; and **Schedule FA** listing every foreign holding. This is where the two books meet, and it is the only place they do.

**2. Loss set-off across the boundary — the one join that pays.** Book J. Real, arithmetic, live only at ROR. Kill: < 25 bps of combined capital → fold into Books L and R.

**3. INR depreciation makes the USD book systematically more expensive to realise.** At ROR the 13.0% applies to the INR-measured gain, so at a working 3.5%/yr depreciation a *flat* USD position accrues Indian tax while a flat INR position does not. The consequence is a **sequencing** fact, not a weighting one: per unit of gain, realising in the USD book costs more than realising in the INR book. That belongs in the shared ledger. **It is not an argument to hedge** (§1.4) and **it is not an argument to reallocate** — it is the reason the alien desk's step-up is worth 240 bps.

**4. Settlement calendars and the cliff.** Book T. India T+1, US T+1, LSE T+2 moving to T+1 on a **targeted 11 Oct 2027 (working)**. The realisation is trade-dated; the **receipt** is settlement-dated, and N6 governs the receipt. **A step-up trade in the last days of March 2028 settles in FY 2028-29, when the taxpayer is ROR.** Do not run the step-up into the wire.

**5. Which book a dual-listed name lives in.** The one whose currency funds it, and one book only. Kill on the join trade: the India/US pair has no short leg, no retail locate in India, and long-only it builds an India single-name book inside the USD account. **Closed on principle as well as on cost.**

**Measurement obligation, not a reallocation:** total India exposure is the INR desk plus whatever India sits inside the USD core — zero if the ex-US line is developed-only, about **₹3.7 lakh** if it is All-World. Write the number down. Do not act on it here.

---

## 5. Inference — n, σ, MDE and the gate

`MDE_ann = 2.80 σ_ann / √T`. Gate: **MDE > ½ × E_net → close without a peek.** E_net is after cost and after **ROR** tax; where a sleeve rebalances inside 24 months, the applicable rate is slab **31.2%**, not 13.0% (Finding B). All σ and T inputs are **(working)**, owner GL0.

| Candidate | Sleeve shape | σ_ann active | T usable | **MDE_ann** | E_net hypothesised | ½ E_net | Ratio | Verdict |
|---|---|---|---|---|---|---|---|---|
| **Book T — cliff and settlement calendar** | Dated arithmetic | — | — | **n/a** | protects 240 bps | — | — | **OPEN** |
| **Book J — cross-book set-off** | Ledger arithmetic | — | — | **n/a** | 17–41 bps one-off | — | — | **OPEN** |
| **Book K — cash-sleeve wrapper** | Rate arithmetic | — | — | **n/a** | 30–70 bps on the sleeve | — | — | **OPEN** |
| **Book Q — core composition** | Two KIIDs | — | — | **n/a** | 3.31 bps + disclosure | — | — | **OPEN** |
| **Book S — synthetic non-US legs** | 5y NAV comparison | — | — | **n/a** (deterministic) | 5–15 bps | — | — | **GATE at 10 bps** |
| Country selection / regional tilt | Over/underweight countries, annual | 6.0% | 40 yr | **2.66%** | 0.50% | 0.25% | **10.6×** | **CLOSED** |
| Cross-country momentum | 12-1 country momentum, monthly, slab-taxed | 9.0% | 40 yr | **3.98%** | 1.65% | 0.83% | **4.8×** | **CLOSED** |
| Cross-country value | CAPE-sorted countries, annual, slab-taxed | 8.0% | 40 yr | **3.54%** | 1.17% | 0.58% | **6.1×** | **CLOSED** |
| G10 FX carry | Forward-rate-bias basket | 10.0% | 40 yr | **4.43%** | 1.10% | 0.55% | **8.1×** | **CLOSED** — also forbidden |
| Global term-premium timing | Duration on/off | 6.0% | 40 yr | **2.66%** | 0.58% | 0.29% | **9.1×** | **CLOSED** |
| Global credit-spread carry | IG/HY overweight | 5.0% | 30 yr | **2.56%** | 0.45% | 0.22% | **11.4×** | **CLOSED** |
| Commodity roll / carry | Broad-commodity roll-optimised | 16.0% | 30 yr | **8.18%** | 1.03% | 0.52% | **15.8×** | **CLOSED** — worst ratio here |
| Dollar / currency trend | Trend on G10 | 8.0% | 40 yr | **3.54%** | 0 (forbidden) | — | ∞ | **CLOSED** |
| **Listing-basis / session overlap** | Cross-venue gap, per session | 40 bps/event | 1,250 events | **3.17 bps/event** | **negative** — 2–6 bps gap vs 8–15 bps round trip | — | — | **CLOSED — measurable and negative** |

**Read the last row the way the India desk reads its Budget/MPC row.** It is the one global phenomenon whose MDE arithmetic is comfortable, because events are plentiful. It is closed anyway, and for the cleanest possible reason: **the effect is smaller than the cost of capturing it.** That is a measured negative, not an unmeasurable maybe, and it should be preserved as such in the STOP memo.

**The gate sorts the global menu with no ambiguity.** Every predictive global book fails, and the failures are not marginal — the best ratio on the board is 4.8× against a gate of 1.0×. Solving the gate for the required gross effect at σ = 8%, T = 40 and a slab-taxed annual sleeve gives roughly **g ≥ 5.5%/yr gross of a country-selection alpha**, which is not a credible claim from any published global premium. As with India, **the two ways to make the gate reachable are structural, not statistical**: cut σ (which means converging on the index, i.e. giving up the effect), or raise T (which only time does).

---

## 6. What the architect must consume

**Viable products.** Irish accumulating USD-line UCITS on LSE — equity core (already decided), and, *if* the allocation ever calls for them, the same wrapper for global-aggregate duration and for the post-cliff cash sleeve. LBMA-backed physical gold ETC, USD line on LSE, *if* gold is ever wanted. Session-overlap execution rules. Nothing else.

**Closed products, as a list to enforce, not re-litigate.** §1 and §3. The highest-frequency mistakes this list prevents: buying developed equity on a local exchange; buying a currency-hedged share class; buying GLD; buying an offshore portfolio bond; buying a non-USD line of the same fund; adding a venue subscription.

**Books in rank order, with kill numbers.** T (calendar — no kill, it exists or R1 runs blind) · J (< 25 bps of combined capital → fold into L and R) · K (< 30 bps/yr on the sleeve or sleeve < $50,000 → hold T-bills) · Q (closes on reading two KIIDs) · S (< 10 bps/yr or counterparty > 10% NAV → physical). **No predictive book.**

**Gates the product evidence supports** — decision rules, not platform design:

- **G1 — No new INR funding.** Every global product must be buyable with already-held USD under FEMA s.6(4). This closes MCX, GIFT City and INR feeders before any other test.
- **G2 — No new venue** unless it clears **≥ 25 bps/yr net of its own market-data and FX cost at the $25,000 floor**, where fixed costs bind hardest.
- **G3 — No new tax jurisdiction.** No product that creates a filing obligation in a third country. This is the global sibling of the alien desk's FIRPTA close.
- **G4 — Fewest lines.** Each additional foreign holding is a Schedule FA row against a ₹10 lakh-per-year penalty regime. Line count is a compliance-risk variable, not only a cost variable.

Existing hurdles govern unchanged and are **not** re-derived here: **N3** (MDE before every peek), **N5** (US-situs ≤ $60,000), **N6** (receipt in a US account), **N7** (5 specs, α = 0.01), **N8** (report at RNOR and at ROR; ROR governs), **N9** (≥ 15 bps/yr per-book minimum), and India **H4**.

**Data: free vs paid.** Everything in this analysis is **free** — fund KIIDs, factsheets and audited annual reports; LSE published spreads; exchange holiday calendars; RBI circulars, FEMA rules and the Irish/Luxembourg statutory texts; broker fee schedules. **Total new spend authorized by this document: $0.** The only purchase anywhere near it is the alien desk's already-authorized **W1 written cross-border opinion ($1,500–$3,000)**, whose scope this analysis argues should be widened — see below.

**Broker and eligibility gates — the binding rung.** All of them sit downstream of **W1**, and three items should be added to its brief:

1. Will the custodian holding the already-held USD (a) maintain the account for an India-resident non-US person and (b) offer **LSE dealing**? A US retail brokerage with no international-venue access cannot execute the core at all. **If the answer is no, an account transfer precedes R1 — which adds weeks to the only date-bound milestone in the programme.**
2. **FEMA s.6(4) and RBI A.P. (DIR Series) Circular 90 of January 2014** as the authority for the wrapper migration and the step-up — and the interaction with the **180-day rule in Regulation 7** of the 2015 Realisation/Repatriation Regulations, especially for idle cash.
3. **s.75 CATCA 2003** as the named statutory path out of Irish CAT on UCITS units where neither disponer nor successor is Irish-domiciled or ordinarily resident. This should be confirmed, not researched, and it materially improves the alien desk's rung-2 position.

**Working-numbers register.** Appendix A.

---

## 7. What would change these verdicts

Stated in advance so a later agent recognises a trigger rather than rationalises one.

1. **India introduces accrual or mark-to-market taxation of foreign fund units** — a PFIC analogue. This inverts the entire thesis: the accumulating wrapper's deferral disappears, distributing and direct become comparable, and §1 is recomputed from scratch. **The single largest tail risk on this page.**
2. **The Indian foreign-share long-term line moves from 24 months to 12.** Every annual-rebalance global sleeve moves from 31.2% to 13.0%, raising every E_net in §5 by roughly 60–80%. Most still fail the gate — **recompute anyway**, because the closures are arithmetic.
3. **W1 returns "no broker will hold Irish UCITS."** The global menu collapses with the core: Books K, Q and S close, the gold ETC closes, and the household reverts to US-listed under the $60,000 cap plus a priced tail.
4. **FEMA s.6(4) is read narrowly on reinvestment, or Reg 7's 180-day rule is applied to s.6(4) assets.** Books W and R both stall, and idle offshore cash acquires a forced-repatriation risk that collides head-on with N6. **Highest-impact single unresolved item in the register.**
5. **A funding path to IFSC/GIFT City that is not LRS.** Reopens the entire INR-funded global menu currently closed at rung 1.
6. **Launch of an EM ex-India UCITS line.** Would make the India double-count removable by substitution rather than only measurable.
7. **A UCITS launches an accumulating global factor line with an effective holding period beyond 24 months.** The only structure that could bring a global premium inside the tax line — worth recomputing §5's E_net column if one appears.
8. **UK abolishes SDRT, or the UK IHT nil-rate band changes materially.** Reopens direct LSE UK shares for analysis, though they still lose to the wrapper.
9. **UK/EU T+1 slips past 11 Oct 2027.** Book T's margin around the 31 Mar 2028 cliff needs an extra day.
10. **Capital crosses ~$500,000, or an entity or trust enters the picture.** Different programme; re-derive rungs 1 and 3 entirely.

---

## Appendix A — working numbers register

Every number in this document that is not sourced to a statute, circular, exchange rule, fund document or one of the desk blueprints. **GL0–GL5** are new milestones for this analysis; **W1** is the alien desk's already-authorized written cross-border opinion.

| # | Number or claim used | Verify at | Note |
|---|---|---|---|
| G1 | **FEMA s.6(4) + RBI A.P. (DIR Series) Circular 90 (Jan 2014) authorise the wrapper migration and step-up without LRS or RBI approval** | **W1** | Circular text quoted in §0.1. Highest priority in this register — the alien desk's Books W and R both rest on it |
| G2 | **Reg 7, FEM (Realisation, Repatriation and Surrender) Regulations 2015 — 180-day rule — and whether it reaches s.6(4) assets** | **W1** | Contested. Asymmetric downside: a strict reading collides with N6 |
| G3 | **s.75 CATCA 2003 exempts units of an investment undertaking where neither disponer nor successor is Irish-domiciled or ordinarily resident** | **W1** | Statute located; confirm the specific fund is an "investment undertaking" per s.739B(1) TCA 1997 and that s.11(2A) deemed situs is displaced |
| G4 | Rule 115 / TT-rate basis for converting a foreign-share capital gain to INR at ROR | **W1** | Drives every ROR number on both desks |
| G5 | Whether losses from other capital assets can be set off against s.198 gains carrying the ₹1.25 lakh exemption | **W1** | Book J's kill number depends on it |
| G6 | Whether a resident individual may take an offshore INR NDF position under FEMA | **W1** | Product is closed on two other grounds; recorded for completeness |
| G7 | Black Money Act s.43 penalty ₹10 lakh/yr; Finance (No.2) Act 2024 de-minimis ₹20 lakh for non-immovable foreign assets | **W1** | Drives gate G4 (fewest lines) |
| G8 | UK IHT nil-rate band £325,000, 40% above; UK-situs = UK register; Irish-incorporated LSE-listed shares outside it | **GL0** | Also the basis for the SDRT exemption |
| G9 | Local transaction taxes: UK SDRT 0.5%; HK stamp 0.1%/side; CH 0.15/0.30%; FR 0.3%; IT 0.1%; ES 0.2%; SG scripless nil | **GL0** | Rung 5 |
| G10 | Treaty dividend WHT for an Indian resident: JP 10%, DE 10%, FR 10%, NL 10%, CH 10% after reclaim from 35%, AU 15%, CA 15%, UK 0%, HK/SG 0% | **GL0** | Rung 2, Finding A |
| G11 | Luxembourg *taxe d'abonnement* 0.05%, **passive ETFs exempt**; Circular L.G.-A. 61 (24 Dec 2024) lists the USA as no-CoTR for SICAV/SICAF | **GL0** | Sourced; refines the alien desk's Ireland-vs-Lux reason |
| G12 | **XUSE tracks MSCI World ex USA (developed, no EM); VWRA tracks FTSE All-World (EM ~10%)** | **GL0** | Confirm both from the KIIDs. Book Q's whole content |
| G13 | India weight ~11.01% of MSCI EM (justETF, Aug 2026); EM ~10% of a global index → India ~1.1% of book | **GL0** | EM figure sourced; the ~10% global EM share is working |
| G14 | Venue market-data fees ≈ $30/month for three added venues; IBKR spot FX ~0.2 bps with a $2 minimum | **W1** | Drives gate G2 and the 144 bps-at-the-floor arithmetic |
| G15 | Irish accumulating USD ultra-short UCITS: availability, TER 0.07–0.10%, minimum economic clip | **GL1** | Book K's instrument |
| G16 | Book K arithmetic: USD cash yield 4.0%; slab drag 125–170 bps/yr vs ~98 bps accrual-equivalent; saving 30–70 bps/yr | **GL1** | Recompute against the actual cash balance and yield |
| G17 | Gold ETC TER 0.12–0.25%; issuer domicile and situs; GLD TER 0.40% and grantor-trust expense-sale mechanics; silver VAT treatment | **GL1** | §1.5 |
| G18 | Gold ~$4,000/oz and ~₹1,10,000/10g in 2026; MGC 10oz ≈ $40,000; MCX Gold Mini 100g ≈ ₹11 lakh | **GL0** | Indivisibility arithmetic |
| G19 | USD/INR 1-year forward points ≈ 200 bps/yr by covered parity | **GL0** | The hedge kill in §1.4 |
| G20 | LSE / NSE exchange holiday calendars for the final week of March 2028; UK BST start 26 Mar 2028; UK/EU/CH T+1 target 11 Oct 2027 | **GL0** | Book T |
| G21 | DST-gap weeks shifting the London/New York overlap to 13:30 London (≈3 weeks in March, ≈1 week around late Oct–early Nov) | **GL0** | Execution rule |
| G22 | LSE UCITS USD-line spread inside vs outside the US overlap window | **GL1** | Measure against own fills; complements alien-desk N4 |
| G23 | All σ_ann and T inputs in the §5 inference table | **GL0** | Published before any peek, per N3 |
| G24 | Synthetic advantage on non-US legs 5–15 bps/yr; counterparty exposure within the 10% NAV UCITS cap | **GL4** | Book S; extends W2 |
| G25 | Offshore portfolio bond / unit-linked wrapper all-in cost 100–150 bps/yr; s.10(10D) unavailable for a foreign insurer | **GL0** | The §1.6 kill |
| G26 | Whether an Indian resident may acquire GDRs of Indian companies in the secondary market under FEMA | **GL0** | Product closed on three grounds regardless |
| G27 | Book J value 17–41 bps of combined capital, one-off | **GL1** | Depends on G5 and on actual realisation volume |

---

*Companion documents, not replaced by this one: [india-equity-architecture-blueprint-rev2.md](../next/india-equity-architecture-blueprint-rev2.md) · [alien-us-equity-architecture-blueprint.md](../next/alien-us-equity-architecture-blueprint.md) · [investor-profile.md](../investor-profile.md)*
