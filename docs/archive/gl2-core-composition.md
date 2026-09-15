# GL2 — Book Q, core composition disclosure

| | |
|---|---|
| **Date** | 2026-09-14 |
| **Spend** | $0 |
| **Status** | **Closed as disclosure on KIIDs.** **US mix measured** from the Vanguard taxable cost-basis export (marks **11 Sep 2026**). **Vehicle dated 2026-09-14: CSUS+VXUA 60/40.** |
| **Book Q** | This document. **No module and no runtime.** `household` does not exist yet (GL1); the ledger line is the payload in §4. |
| **Does not choose** | This programme recorded the investor's dated vehicle. It did not pick it. W0's CSPX+XUSE pair is a W0 record, not this GL2 vehicle. |

The Ireland pair was first **inferred** from the measured US taxable allocation (Vanguard cost-basis export, 11 Sep 2026). The investor then **dated that pair** on **2026-09-14** (§5). Inference is not a trade; dating it is the GL2 exit.

**Hard split (2026-09-14).** Only the Indian book uses the India line (12-month clock, INR, demat / rupee). The Ireland/global book — **CSUS+VXUA in full** — runs on the **USD line**: Irish accumulating USD share class, already-held USD (GL-L1 / FEMA s.6(4)), alien desk, 24-month foreign clock, **zero FX**. VXUA's India look-through (~1.70% working) is Schedule FA / household concentration **disclosure only**. It is **not** an India-desk lot, **not** INR-funded, **not** the 12-month Indian clock, **not** a Nifty sleeve. CSUS, VXUA, CSPX, XUSE, VWRA, VTI, VXUS are not India-line lots.

The wrapper migration (alien W1 / R1) may use this named vehicle. W1 still gates the trade.

This file is not a tax conclusion. Schedule FA, s.43 and FEMA remain W1 items.

US one-sentence description (US analyst, consumed as fact): **60/40 US total market + total international all-cap including EM, 100% equity, no bonds in this account.**

---

## 1. What each line tracks — from the KID / KIID

### XUSE — developed ex-US, no EM

| | |
|---|---|
| **Instrument (from the document)** | **iShares MSCI World ex-USA UCITS ETF (the “Fund”), USD Accu (the "Share Class")**, ISIN **IE000R4ZNTN3** |
| **Document** | PRIIPs Key Information Document, BlackRock Asset Management Ireland Limited |
| **Dated** | **09 April 2026** |
| **URL (public, $0)** | https://www.blackrock.com/it/investitori-privati/literature/kiid/eu-priips-ishares-msci-world-ex-usa-ucits-etf-usd-acc-ie000r4zntn3-en.pdf |
| **Index (quoted)** | “aims to achieve a total return … which **reflects the return of the MSCI World ex USA Index**, the Fund’s benchmark index (“Index”).” |
| **Universe (quoted)** | “The Index measures the performance of large and mid-capitalisation stocks across **developed market countries excluding the United States** which comply with MSCI's size, liquidity, and free-float criteria.” |
| **EM weight** | **None.** Developed-market countries excluding the United States. MSCI World is the developed composite; MSCI World ex USA is that composite with the US removed. No emerging-market country is in the index. |
| **Small-cap** | **None.** Large and mid only. |
| **Locked line facts (W0, unchanged)** | Ireland, accumulating, physical, TER **0.15%**, not US-situs. LSE ticker XUSE. |

The KID's own cost table states “Management fees and other administrative or operating costs **0.15%** of the value of your investment per year.” That matches W0.

Cross-check, not a substitute for the KID: iShares XUSE factsheet (August 2026, holdings as at 31 Aug 2026) names the same benchmark (**MSCI World Ex US Net Index**) and the same developed-ex-US description. justETF country slice as of **30 Jul 2026**: Japan, UK, Canada, Switzerland — developed names, no India.

**XUSE is not a substitute for VXUS.** VXUS is FTSE Global All Cap ex US: developed **and** EM (~26.4% of the sleeve as of 30 Jun 2026, working) **and** small-cap. XUSE has neither EM nor small-cap.

### VWRA — developed and emerging, large/mid, US inside

| | |
|---|---|
| **Instrument (from the document)** | **Vanguard FTSE All-World UCITS ETF (the "Fund")**, **(USD) Accumulating Shares**, ISIN **IE00BK5BQT80** |
| **Document** | UCITS Key Investor Information, Vanguard Group (Ireland) Limited |
| **Dated** | “This key investor information is accurate as at **28/07/2026**.” |
| **URL (public, $0)** | https://fund-docs.vanguard.com/ie00bk5bqt80-en.pdf |
| **Index (quoted)** | “seeks to track the performance of the **FTSE All-World Index** (the “Index”).” |
| **Universe (quoted)** | “The Index is comprised of large and mid-sized company stocks in **developed and emerging markets**.” |
| **EM weight** | **Present, ~10% of the line (working, G12).** The KIID confirms EM is in the index. It does not publish a numeric EM weight. |
| **Small-cap** | **None.** Large and mid only. Drops the all-cap feature of both VTI and VXUS. |
| **Locked line facts (W0, unchanged)** | Ireland, accumulating, physical, OCF **0.14%**, not US-situs. LSE ticker VWRA. |

The KIID charges table states ongoing charges **0.14%**, “based on expenses for the year ended **31 December 2025**.” That matches W0.

Issuer cross-check, not a substitute for the KIID: Vanguard Netherlands professional page, market allocation **as at 31 Jul 2026**, FTSE All-World benchmark. United States **61.6%**. Named emerging-market rows in the published top slice: Taiwan **3.17%**, China **2.82%**, India **1.63%**. Those three already sum to **7.62%** of the index; the rest of EM (Brazil, Saudi Arabia, and the smaller markets) sits below the cut. **~10% EM (working)** remains the round figure G12 uses. South Korea is classified **Pacific / developed** on that table (FTSE), not EM.

VWRA is **one** developed+EM large/mid line with the US **inside**. It is not a 60/40 pair of total-US + all-cap-ex-US.

### CSPX — W0 US sleeve (S&P 500, not total market)

Locked in `src/books/wrapper.py` and W0: **iShares Core S&P 500 UCITS ETF USD Acc**, IE00B5BMR087, Ireland, acc, physical, TER **0.07%**, not US-situs. LSE USD ticker CSPX. PRIIPs KID dated **09 April 2026**. Index (quoted): **S&P 500 Index** — “the 500 largest companies (i.e. companies with large market capitalisation) within the United States market.” It adds **no EM**, **no India**, and **no small/mid/micro**. Same-index peer, not closer to VTI: Vanguard S&P 500 UCITS ETF USD Acc **VUAA** IE00BFMXXD54, OCF **0.07%**, LSE USD.

VTI is **total US market** (large/mid/small/micro). CSPX leaves that gap. The pair's EM exposure, if the ex-US leg is XUSE, is exactly XUSE's, which is **zero**.

W0 measured the pair at **US 70% / ex-US 30%** (`US_WEIGHT` / `EXUS_WEIGHT`). That table is not re-derived here. The investor dated **stocks 60/40** US/international on **2026-09-14** (§5). That 70/30 is **W0 arithmetic, not this book**.

### CSUS — closest cheap US sleeve (MSCI USA large/mid)

| | |
|---|---|
| **Instrument (from the document)** | **iShares MSCI USA UCITS ETF (the “Fund”), USD Accu (the "Share Class")**, ISIN **IE00B52SFT06** |
| **Document** | PRIIPs Key Information Document, BlackRock Asset Management Ireland Limited |
| **Dated** | **10 September 2026** |
| **URL (public, $0)** | https://www.ishares.com/uk/individual/en/products/253740/ishares-msci-usa-b-ucits-etf |
| **Index (quoted)** | “reflects the return of the **MSCI USA Index**, the Fund’s benchmark index (Index).” |
| **Universe (quoted)** | “The Index measures the performance of **large and mid-market capitalisation companies listed in the United States** (US) equity market which comply with MSCI's size, liquidity, and free-float criteria.” |
| **EM / India** | **None.** US only. |
| **Small-cap** | **None.** Large and mid only. Closer to VTI than S&P 500 (mid is in); still not total market (small/micro out). |
| **Line facts** | Ireland, accumulating, physical (replicated), TER **0.03%**, not US-situs, not currency-hedged. LSE **USD** ticker **CSUS** (GBP line on LSE is CU1). **USD line** (alien desk, 24-month foreign clock, zero FX). **Not the India line.** **Not a W0-locked line.** |

The KID cost table states “Management fees and other administrative or operating costs **0.03%** of the value of your investment per year.” Issuer factsheet (CSUS): TER **0.03%**, ~**528** holdings, ~**US$5.0bn**. Same-index physical peer: Xtrackers MSCI USA UCITS ETF 1C IE00BJ0KDR00 (Ireland, acc, TER 0.07%). CSUS is named because the KID was fetched and the TER is **0.03%**.

MSCI USA covers about **85%** of US free-float (working, index-provider description). VTI covers the total market. The residual is small/micro.

### VXUA — closest ex-US sleeve (FTSE All-World ex US: developed **and** EM, large/mid)

**Do not confuse tickers.** US-listed **VXUS** (US9219097683) is the measured Vanguard Total International Stock ETF. The Irish fund below has LSE **GBP** ticker **VXUS** and LSE **USD** ticker **VXUA**. The USD line is **VXUA**. Identify it by ISIN.

| | |
|---|---|
| **Instrument (from the document)** | **Vanguard FTSE All-World ex-U.S. UCITS ETF (the "Fund")**, **(USD) Accumulating Shares**, ISIN **IE0009A5ADV9** |
| **Document** | UCITS Key Investor Information, Vanguard Group (Ireland) Limited |
| **Dated** | “This key investor information is accurate as at **20/08/2026**.” |
| **URL (public, $0)** | https://fund-docs.vanguard.com/ie0009a5adv9-en.pdf |
| **Index (quoted)** | “seeks to track the performance of the **FTSE All-World ex US Index** (the “Index”).” |
| **Universe (quoted)** | “The Index comprises **large and mid-cap stocks providing coverage of developed and emerging markets (excluding the US)**.” |
| **EM weight** | **Present.** The KIID names emerging markets. It does not publish a numeric EM weight. Same-index US-listed VEU print: EM **26.1%** of the ex-US index, India **4.2%** of stocks **(working, Vanguard VEU profile, as of Feb 2026)**. VWRA residual on the same FTSE All-World family: India **1.63% / (1 − 0.616) = 4.245%** of the ex-US sleeve **(working, 31 Jul 2026)**. |
| **Small-cap** | **None.** Large and mid only. VXUS is **All Cap**; this line drops small-cap. No Ireland LSE USD Acc tracking FTSE Global All Cap ex US or MSCI ACWI IMI ex-US was found at $0. |
| **Line facts** | Ireland, accumulating, physical (**index sampling** — KIID), OCF **0.12% (estimated — KIID: share class launched less than one calendar year ago)**, not US-situs, not currency-hedged. LSE **USD** ticker **VXUA**. Share-class inception **18 Aug 2026**; listing **20 Aug 2026**. Issuer print: share-class assets **US$26.39 M**, total assets **US$34.72 M** (Vanguard UK professional page, NAV as at **11 Sep 2026**). **Tiny.** A dealing fact, not a composition-rank change. **USD line** (alien desk, 24-month foreign clock, zero FX). India look-through is disclosure only — **not an India-desk lot.** **Not a W0-locked line.** |

The KIID charges table states ongoing charges **0.12%**. That figure is an estimate. Issuer product page: https://www.vanguard.co.uk/professional/product/etf/equity/E165/ftse-all-world-ex-us-ucits-etf-usd-acc

### IMID — closest single line on size-segment (ACWI IMI: large/mid/**small**, developed **and** EM)

| | |
|---|---|
| **Instrument (from the document)** | **State Street SPDR MSCI All Country World Investable Market UCITS ETF (Acc)**, ISIN **IE00B3YLTY66** |
| **Document** | Issuer product page + Jul 2026 factsheet; PRIIPs KID accurate as at **19 February 2026** |
| **Dated** | Factsheet holdings **31 Jul 2026**; fund assets **as of 08 Sep 2026** |
| **URL (public, $0)** | https://www.ssga.com/uk/en_gb/intermediary/etfs/state-street-spdr-msci-all-country-world-investable-market-ucits-etf-acc-spyi-gy |
| **Index (quoted)** | “The Fund seeks to track the performance of the **MSCI ACWI IMI (All Country World Investable Market Index) Index** (the "Index") as closely as possible.” |
| **Universe (quoted)** | “stocks and shares issued by companies in both **developed and emerging market countries** from around the world.” Optimised: “the Fund will typically hold only a subset of the securities included in the Index.” |
| **Small-cap** | **Present.** IMI = investable market (large, mid **and** small). Issuer page: “covers c.9000 securities across large, mid and small cap size segments.” |
| **EM weight** | **Present.** Numeric weight is not in the KID. |
| **Line facts** | Ireland, accumulating, physical (optimised sampling), TER **0.17%**, USD unhedged, not US-situs. LSE **USD** ticker **IMID**. Issuer: total fund assets **US$8,965.90 M** as of **08 Sep 2026**. **Not a W0-locked line.** |

Issuer factsheet **31 Jul 2026** (not a substitute for the KID): United States **62.72%**, India **1.59%**, Korea **2.31%** (MSCI classifies Korea as EM; FTSE classifies it developed). **(working)**

---

## 2. Measured US mix → dated Ireland mix

The Ireland pair below was **inferred** from the measured US taxable allocation, then **dated by the investor on 2026-09-14** as `CSUS+VXUA 60/40`. The mapping started from the CSV; the date in §5 is the choice.

Provenance of the mix: **measured from the cost-basis export.** Provenance of the vehicle: **investor-dated 2026-09-14.**

### Measured US taxable book (fact)

Source: `data/private/costbasisdownload_2391.csv`, Vanguard taxable brokerage, marks **11 Sep 2026 04:15 PM ET**, 38 lots. Total **$354,097.28**. Other brokers / cash / retirement **not** in this score. R0: `docs/archive/r0-embedded-gain.md`. USD/INR **95.69 (working)**.

| Ticker | Index | TER | $ | % of book |
|---|---|---|---:|---:|
| VTI | Morningstar US Total Market (formerly CRSP US Total Market) | 0.03% | 210,603.63 | 59.4762% |
| VXUS | FTSE Global All Cap ex US (developed **and** EM, All Cap) | 0.05% | 141,592.02 | 39.9868% |
| VOO | S&P 500 | 0.03% | 1,431.25 | 0.4042% |
| VTV | Morningstar US Large Cap Value | 0.03% | 470.38 | 0.1328% |

Economic mix: **US equity 60.0132% / international equity 39.9868% / bonds 0% / other 0%**. One decimal: **60.0 / 40.0**. **100% equity.**

**Confirmed 2026-09-14** from the same export (household now reads these lots; desks stay authoritative): **US 60.0132% / international 39.9868%** versus the dated **60/40** equity target. Bonds **0** in this taxable book (US/intl 70/30 sits in a US IRA, outside). **100% US-listed (VTI/VXUS + residual VOO/VTV)** — this is the pre-migration book, not a vehicle choice. This CSV does not name an Irish line.

VOO+VTV = **$1,901.63 = 0.54% of book** — residual overlap inside VTI, **not** a named tilt. **Do not add a third Ireland line.**

Ticker map for this book:

| US-listed (held) | Ireland USD Acc (dated core) | Note |
|---|---|---|
| **VTI** ($210,604, 59.5%) | **CSUS** | Closest cheap large/mid US. Not total-market (small/micro gap). |
| **VXUS** ($141,592, 40.0%) | **VXUA** | Same FTSE All-World ex-US family, minus small-cap. Has EM. |
| **VOO** ($1,431, 0.40%) | **CSPX** is the index match (S&P 500) | Already inside CSUS. **Not a third FA line.** |
| **VTV** ($470, 0.13%) | none | Large-value names already inside CSUS. **Not a tilt.** |

Inside VXUS (Vanguard F3369 / product page, **as of 30 Jun 2026**, working): **EM 26.40%** of VXUS; India **4.4% of VXUS common stock**. Europe 36.0%, Pacific 29.1%, North America 7.7%, Middle East 0.8%. All Cap (includes small). Korea in Pacific (FTSE developed).

Dated bonds US/intl 70/30 (GL-H11) is **not** in this CSV. Do not infer a bond UCITS from this export. W0's 70/30 is arithmetic, not this book.

### Ranking rule

Ireland candidates ranked by **composition fidelity** to the measured mix, then by **line count / TER / already-locked W0 lines**, in that order. This is a mapping, not a buy list.

### Dated pair — CSUS 60 / VXUA 40

| Sleeve | Line | ISIN | Domicile | Acc/dist | TER/OCF | Index | LSE USD | EM | Small-cap | Inferred weight |
|---|---|---|---|---|---|---|---|---|---|---|
| US | **CSUS** | IE00B52SFT06 | Ireland | Acc | **0.03%** | MSCI USA (large/mid) | CSUS | none | no | **60%** (dated) |
| Ex-US | **VXUA** | IE0009A5ADV9 | Ireland | Acc | **0.12%** (est.) | FTSE All-World ex US (large/mid, DM **and** EM) | **VXUA** | **yes** | no | **40%** (dated) |

Why this pair, in rank order:

1. **Composition.** The measured book is a **60/40 pair**, not one global line. VXUA is the Ireland LSE USD Acc line that actually has **EM** and sits in the **same FTSE All-World ex-US family** as VXUS (minus small-cap). CSUS is large+mid US, closer to VTI than S&P 500, still not total market.
2. **Line count.** Two lines — same FA count as W0's pair.
3. **TER.** Blended TER at 60/40 = **6.6 bps/yr (working: 0.60×3 + 0.40×12)**. Cheaper on fees than CSPX+XUSE at 60/40 (**10.2 bps**, working) and than VWRA (**14 bps**) / IMID (**17 bps**). This is a TER blend, **not** a re-run of W0 withholding arithmetic.
4. **W0 lock.** Neither CSUS nor VXUA is a W0-locked line. W0 remains CSPX+XUSE at **70/30**. Composition outranks that lock for *mapping*; it does not unlock a trade.

Remaining gaps versus VTI+VXUS: **US small/micro** (CSUS ≠ total market); **ex-US small-cap** (All-World ≠ Global All Cap); VXUA **AUM ~$26–35m** and three weeks old — spreads and capacity are a dealing fact.

### Closest single line — IMID **(inferred)**

On **size-segment fidelity** the measured book is all-cap on **both** sleeves. IMID (MSCI ACWI IMI) includes small-cap **and** EM. VWRA does not.

| | IMID (inferred closest single) | VWRA (W0-locked large/mid single) |
|---|---|---|
| Index | MSCI ACWI IMI | FTSE All-World |
| Size | Large **+ mid + small** | Large + mid only |
| EM | Yes | Yes (~10% of the line, working) |
| US weight | **62.72%** (31 Jul 2026 factsheet, working) | **61.6%** (31 Jul 2026 factsheet) |
| Can implement 60/40? | **No** — market-cap | **No** — market-cap |
| Korea | MSCI EM | FTSE developed |
| TER / OCF | 0.17% | 0.14% |
| FA lines | 1 | 1 |
| W0 | No | Yes — permitted single-line substitute |

**Closest single line = IMID.** Composition (all-cap) outranks VWRA's cheaper TER, FTSE family, and W0 lock. VWRA stays the locked large/mid FTSE alternative. Neither single line is a 60/40 pair of total-US + all-cap-ex-US.

### CSPX + XUSE does **not** match this book

Keep the KIID facts in §1 — they stay true. Stop treating the pair as compositionally equivalent to VTI+VXUS.

| | Measured VTI + VXUS | CSPX + XUSE | CSUS + VXUA **(dated)** |
|---|---|---|---|
| US sleeve | Total market (all cap) | S&P 500 (large) | MSCI USA (large/mid) |
| Ex-US sleeve | FTSE Global All Cap ex US | MSCI World ex USA | FTSE All-World ex US |
| EM in the ex-US sleeve | **~26.4% (working)** | **None** | **Yes** (~26% of the sleeve, working) |
| Small-cap | Yes, both sleeves | No | No |
| India look-through (USD line, not India desk) | **~1.76%** (measured) | **0** | **~1.70% (working)** |
| Dated weights | 60/40 | W0 arithmetic was **70/30** | Inferred **60/40** |

CSPX+XUSE at 60/40 is still developed-only: S&P 500 + MSCI World ex USA, **EM = 0**, USD-line India look-through = **0**. That is a different portfolio from the measured book. Both pairs still run on the USD line; neither is the India line.

### Lines that were looked for and not found

| Wanted | Result at $0 |
|---|---|
| Ireland LSE USD Acc tracking Morningstar / CRSP US Total Market or MSCI USA IMI | **Not found.** Closest cheap physical Acc is CSUS (large/mid). CSPX / VUAA are S&P 500. |
| Ireland LSE USD Acc tracking FTSE Global All Cap ex US or MSCI ACWI IMI ex-US | **Not found.** Closest is VXUA (FTSE All-World ex US, large/mid, EM present). |

Closing the US small-cap gap needs a **second** US line (Russell 2000 / S&P 600 / MSCI USA Small Cap UCITS). Extra Schedule FA line. GL-L4. Residual of VTI, not a named tilt. **Almost certainly no.**

Reconstructing VXUS as XUSE + standalone EM would still miss developed small-cap and would add a third FA line. Standalone EM **IE00B4L5YC18** (iShares MSCI EM UCITS ETF USD Acc, TER **0.18%**, physical, Ireland, accumulating) remains **analysis-only**. Adding it is **not** an allocation instruction. The dated pair already has EM inside VXUA, so this line is not required to reconstruct EM presence.

### W0 fee table — still true, still a **70/30** number

W0 locked arithmetic, not re-derived. Pair saving vs naive US-listed **22.04 bps/yr**; VWRA **18.73 bps/yr**. Pair fee advantage vs single line = **3.31 bps/yr** = **$117/yr ≈ ₹11,000/yr** at $354,097.

**That 3.31 bps is a 70/30 number.** It must not be reused as a 60/40 number. Withholding arithmetic is not re-run here. TER blends at **60/40 (working)** are in the pair table above.

| | CSPX + XUSE (**70/30**, W0) | VWRA (single line) |
|---|---|---|
| Recurring saving vs naive US-listed (W0) | **22.04 bps/yr** | **18.73 bps/yr** |
| Pair advantage on fees | **+3.31 bps/yr** = **$117/yr ≈ ₹11,000/yr** | — |
| Schedule FA lines | **2** | **1** |
| Extra FA line vs the other | **one extra line** | one fewer |
| Disclosure regime per line | s.43 Black Money Act **₹10 lakh/yr** penalty **(working, G7)**; de-minimis ₹20 lakh, this book is ~16× over | Same regime, one fewer line |
| Emerging markets | **None** — MSCI World ex USA is developed-only | **~10% of the line (working)** — FTSE All-World includes EM |
| World market capitalisation held | Developed only (US + DM ex-US) | Developed **and** the EM ~10% |

GL-H7 does not apply — the core configuration is composition. Optional sleeves stay at weight **0** until a **dated allocation instruction** (GL-H11). No gold, duration, cash-sleeve, or synthetic is picked here. This export has **no bonds**.

**No recommendation on IMID or VWRA.** The core vehicle is dated in §5.

---

## 3. India weight

Three routes for **this** book, plus the old G13 VWRA-path as a cross-check. The dated vehicle is CSUS+VXUA 60/40 on the **USD line**. While the INR desk's Nifty sleeve stays at default **0**, the VXUA India **look-through** may be the household's only India *equity concentration* — it is still **not an India-line lot** and **not worth a book** — worth **one disclosure line** (Schedule FA / household concentration). Only the Indian book uses the India line.

USD book mark **$354,097.28**. USD/INR **95.69 (working)**. Combined capital ≈ ₹3.89 crore (₹3.39 crore USD book at 95.69 + ₹50 lakh India design).

### (a) Measured VXUS — current-book payload

This is what the household **holds today**.

| Step | Number | Source |
|---|---|---|
| India share of VXUS common stock | **4.4%** | US analyst pack, Vanguard F3369 / product page, as of **30 Jun 2026** (working) |
| VXUS market value | **$141,592.02** | Cost-basis export, 11 Sep 2026 |
| India inside VXUS, USD | 0.044 × $141,592 ≈ **$6,230** | |
| India as % of USD book | **$6,230 / $354,097 ≈ 1.76%** | |
| India inside VXUS, INR | $6,230 × 95.69 ≈ **₹5.96 lakh ≈ ₹6.0 lakh (working)** | |
| Share of India-desk design | ₹6.0 lakh / ₹50 lakh = **12.0%** | |
| Share of combined capital | ₹6.0 lakh / ₹3.89 crore ≈ **1.5%** | |

EM in the USD book ≈ 0.2640 × 0.399868 ≈ **10.56% of book ≈ $37,400 (working)**.

This is **larger** than G13's VWRA-path ~1.1% / $3,900, because 40% of the book is fully international-with-EM, whereas VWRA's India is ~1.1–1.63% of a single global line.

### (b) Inferred pair — CSUS 60 / VXUA 40

CSUS contributes **0** India. VXUA holdings are not yet published (inception 18 Aug 2026). Working India of the ex-US sleeve from the **same FTSE All-World family**: VWRA India **1.63%** / ex-US residual **38.4%** = **4.245%** of VXUA **(working, 31 Jul 2026)**. VEU (same index, US-listed) prints India **4.2%** of stocks **(working)**.

| Step | Number |
|---|---|
| India as % of USD book | 0.40 × 4.245% ≈ **1.70% (working)** |
| USD | 0.0170 × $354,097 ≈ **$6,010** |
| INR | $6,010 × 95.69 ≈ **₹5.75 lakh ≈ ₹5.8 lakh (working)** |

Same order of magnitude as the measured payload. The residual gap is All-World (large/mid) versus Global All Cap (includes small).

### (c) Inferred single line — IMID

| Step | Number | Source |
|---|---|---|
| India share of IMID | **1.59%** | SSGA factsheet, **31 Jul 2026 (working)** |
| USD | 0.0159 × $354,097 ≈ **$5,630** | |
| INR | $5,630 × 95.69 ≈ **₹5.39 lakh ≈ ₹5.4 lakh (working)** | |

### Cross-check — G13 VWRA path (not the measured payload)

| Step | Number | Source |
|---|---|---|
| India share of MSCI EM | **~11.01% (working)** | G13: justETF, Aug 2026, on iShares MSCI EM UCITS ETF USD Acc **IE00B4L5YC18**. Live justETF country table fetched **2026-09-14** prints India **12.25%** as of **30 Jul 2026**. The G13 11.01% figure is retained as the working input. |
| EM share of a global index | **~10% (working)** | G12 / G13. Confirmed as *presence* from the VWRA KIID; numeric weight is working. |
| India share of a global line | 0.1101 × 0.10 = **0.01101 ≈ 1.1%** | |
| India inside VWRA, USD | 0.011 × $354,097 = **$3,895 ≈ $3,900** | |
| India inside VWRA, INR | $3,900 × 95.69 = **₹3,73,191 ≈ ₹3.7 lakh (working)** | |
| Issuer print (VWRA only) | India **1.63%** as at 31 Jul 2026 → **$5,772 ≈ ₹5.5 lakh** | Different index family arithmetic than G13; cross-check, not a replacement. |

Sensitivity to the live justETF print does not change the conclusion of G13: 12.25% × 10% = **1.23% ≈ $4,340 ≈ ₹4.2 lakh**. Still under a book. G13 is **not** what this CSV holds.

### Pair (CSPX + XUSE)

India weight of the USD book: **0**. $0. ₹0. There is no India inside MSCI World ex USA, and none inside the S&P 500.

---

## 4. Household payload — India-desk lots plus USD-line look-through

GL1 stores this line in `household`. The desks' own ledgers stay authoritative. This is a number, not a tax conclusion. **Only the Indian book uses the India line.** CSUS+VXUA lots join as `Desk.ALIEN` / `HoldingClock.FOREIGN_24M` / USD. The look-through is not a demat lot.

USD/INR **95.69 (working)** is the R0 mark-date stand-in. Per-lot Rule 115 / TT-rate source and date are a GL1 / W1 concern.

| Field | Value |
|---|---|
| `as_of` | **2026-09-14** |
| `usd_book_mark_usd` | **354097.28** |
| `usd_book_mark_date` | **2026-09-11** |
| `usd_inr_working` | **95.69** |
| `inr_desk_design_inr` | **5000000** |
| `inr_nifty_sleeve_weight` | **0** (default; not a GL2 allocation) |
| `core_choice` | **CSUS+VXUA 60/40** |
| `core_choice_dated` | **2026-09-14** |
| `equity_us_intl` | **60/40** (measured from the CSV; matches the dated weight) |
| `bond_us_intl` | **not in this export.** Prior **70/30** instruction remains a **GL-H11** note, not a Book Q vehicle. Optional duration stays weight **0**. |

**Current book (measured VXUS) — what is held today, until the wrapper trade:**

| Field | Value |
|---|---|
| `usd_line_india_lookthrough_weight` | **0.0176** (~1.76%) |
| `usd_line_india_lookthrough_usd` | **6230** |
| `usd_line_india_lookthrough_inr` | **596000** (₹6.0 lakh, working) |
| `total_india_exposure_inr` | **596000** USD-line look-through + INR desk (Nifty sleeve at 0). Look-through is **not** an India-desk lot. |
| `schedule_fa_core_lines` | **n/a** (US-listed today; FA count is a post-wrapper number) |
| `source` | Measured: 4.4% of VXUS × $141,592. Tagged working on the 4.4% country slice. |

**Dated vehicle — CSUS + VXUA 60/40 — post-wrapper USD-line India look-through (not the India desk):**

| Field | Value |
|---|---|
| `usd_line_india_lookthrough_weight` | **0.0170** (~1.70%, working) |
| `usd_line_india_lookthrough_usd` | **6010** |
| `usd_line_india_lookthrough_inr` | **575000** (₹5.8 lakh, working) |
| `schedule_fa_core_lines` | **2** |
| `source` | VWRA India 1.63% / 38.4% × 0.40. VXUA holdings not yet published. |

**If inferred single line IMID:**

| Field | Value |
|---|---|
| `usd_line_india_lookthrough_weight` | **0.0159** (1.59%) |
| `usd_line_india_lookthrough_usd` | **5630** |
| `usd_line_india_lookthrough_inr` | **539000** (₹5.4 lakh, working) |
| `schedule_fa_core_lines` | **1** |
| `source` | SSGA factsheet 31 Jul 2026. Tagged working. |

**If VWRA (G13 working — cross-check, not measured):**

| Field | Value |
|---|---|
| `usd_line_india_lookthrough_weight` | **0.011** (~1.1%) |
| `usd_line_india_lookthrough_usd` | **3900** |
| `usd_line_india_lookthrough_inr` | **370000** (₹3.7 lakh, working) |
| `schedule_fa_core_lines` | **1** |
| `source` | G13: 11.01% × 10% EM, tagged working |

Issuer cross-check, not stored as the payload: VWRA India **1.63%** as at 31 Jul 2026 → `$5772` / `₹552000` at 95.69.

**If CSPX + XUSE:**

| Field | Value |
|---|---|
| `usd_line_india_lookthrough_weight` | **0** |
| `usd_line_india_lookthrough_usd` | **0** |
| `usd_line_india_lookthrough_inr` | **0** |
| `total_india_exposure_inr` | INR desk only (Nifty sleeve at 0 until that desk allocates). CSPX+XUSE are still USD-line lots, not India-line. |
| `schedule_fa_core_lines` | **2** |

---

## 5. Configuration — vehicle dated CSUS+VXUA 60/40

| | |
|---|---|
| **Dated** | **2026-09-14** |
| **Signed by** | Investor |
| **Equity (stocks)** | **US / international 60/40** — dated, and **measured** from the 11 Sep 2026 export to one decimal. |
| **Bonds** | **US / international 70/30** was dated **2026-09-14** under **GL-H11**. **Not evidenced by this CSV** (bonds = 0 in the export). Not a Book Q line, not a product pick, not an implemented sleeve. Optional sleeves stay at weight 0 until a named instrument exists. US-situs bond funds remain inside **N5**. Do not infer a bond UCITS from this export. |
| **Vehicle** | **`CSUS+VXUA 60/40`.** CSUS IE00B52SFT06 (LSE USD Acc) at **60%**; VXUA IE0009A5ADV9 (LSE USD Acc) at **40%**. First inferred from VTI+VXUS, then dated. **Runs on the USD line** (alien desk, 24-month foreign clock, zero FX). **Not the India line.** **VOO is not a third line** — CSPX is the S&P 500 equivalent, already inside CSUS at $1,431 (0.40%). VTV ($470, 0.13%) is not a tilt. |
| **Process-gate date** | **2026-09-14** (disclosure closed; US mix measured; vehicle dated) |
| **Rule** | The wrapper migration (alien W1 / R1) uses this named vehicle. **W1 still gates the trade.** |
| **W0 record** | CSPX+XUSE at 70/30 was the W0 arithmetic line; VWRA was the permitted single-line substitute. W0's 3.31 bps pair-vs-single fee gap is a **70/30** number and is not re-run here. CSPX+XUSE is **not** this book's vehicle. |

A 60/40 instruction did not pick the vehicle; **this row does.** CSPX+XUSE would have dropped EM (USD-line India look-through = 0). CSUS+VXUA keeps EM near the measured ~10.56% / India look-through ~1.7% — still on the USD line, not the India desk.

**Not added:**

- `CSPX` for VOO — index match only; residual already in CSUS
- `IMID` or `VWRA` — single-line alternatives, not chosen
- `XUSE` — developed-only; not a substitute for VXUS
---

## G12 / G13

| Item | Result |
|---|---|
| **G12** | **Confirmed from the KIIDs.** XUSE → MSCI World ex USA, developed excluding the United States, **no EM**. VWRA → FTSE All-World, **developed and emerging**; EM **~10% (working)**. **Added:** CSUS → MSCI USA, large/mid US, no EM (KID **10 Sep 2026**). VXUA → FTSE All-World ex US, large/mid, **developed and emerging** (KIID **20/08/2026**). IMID → MSCI ACWI IMI, developed and emerging, IMI = large/mid/**small** (factsheet **31 Jul 2026**). |
| **G13** | **Measured payload now from VXUS:** India **~1.76% of the USD book ≈ $6,230 ≈ ₹6.0 lakh** at $354,097. Written as the §4 current-book payload. G13 VWRA-path **~1.1% ≈ $3,900 ≈ ₹3.7 lakh** retained as a **cross-check**, not as what this CSV holds. Not worth a book. |

---

*Authority: [global-equity-execution-plan.md](../next/global-equity-execution-plan.md) GL2 · [global-equity-architecture-blueprint.md](../next/global-equity-architecture-blueprint.md) Book Q · Product: [global-financial-market-analysis.md](global-financial-market-analysis.md) G12, G13 · US mix: `data/private/costbasisdownload_2391.csv` (11 Sep 2026) · W0: [w0-wrapper-arithmetic.md](w0-wrapper-arithmetic.md) · Close memo: [gl2-composition-note.md](gl2-composition-note.md)*
