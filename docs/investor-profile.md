# Investor profile

**Status:** working household facts as of 2026-09-14. **Not a filed tax opinion.** W1 still gates any capital move.
**This file is the taxpayer.** Desk blueprints consume it; they do not redefine it.
**Not this taxpayer:** the US-person desk's IRA / 40%–20% / §1256 identity. Import that desk's pre-tax measurements only.

Programmes on this household: [alien US desk](next/alien-us-equity-architecture-blueprint.md) (USD, NRA/RNOR) and the India equity desk (INR, India-source). Same PAN, two books.

---

## Identity

| | |
|---|---|
| Citizenship | Indian |
| US person | **No.** Nonresident alien (NRA). Substantial-presence tripwire is 183 US days in a calendar year |
| Indian tax | Resident from FY 2025–26. **RNOR** now; **ROR** after the cliff in [residency-calendar.md](residency-calendar.md) |
| Treaty | India–US DTAA claimed. W-8BEN on file; Indian PAN as foreign TIN. No ITIN unless a form forces a 1040-NR |
| Capital | Own only. No third-party money, customers, dealer inventory, or advertised performance — the IRC 864(b)(2) own-account safe harbor depends on it |
| Family perimeter (SEBI algo) | Self, spouse, dependent children, dependent parents only. Never an algo provider, RA, or PMS |
| Risk | Moderately aggressive (4/5): cheap core **~75–80%** of the book; leftover **~20–25%** may be active sleeves. **4/5 does not cap sleeve count or how that leftover is split.** Core-heavy, no leverage. |

Indian salary from **1 Sep 2025** is India-source and taxed in India even during RNOR. The RNOR zero cell is **foreign passive income received outside India**, not employment income.

---

## Two tax systems, three regimes

Rates are **working**. `tax` takes the [residency calendar](residency-calendar.md), not a single rate. Every result is reported at RNOR **and** at ROR; where they differ, **ROR governs**.

| Income | US (NRA, W-8BEN, DTAA) | India, RNOR | India, ROR |
|---|---|---|---|
| Dividends from US corporations and US-listed ETFs | **25%** withheld (30% without W-8BEN). An individual does not get the 15% company rate | **0** if received in a US account | Slab, up to **~31.2%** with cess, FTC for the 25% via Form 67 |
| Capital gains on listed US stock and ETFs (non-USRPI) | **0** (not 183 days, not a US trade or business) | **0** if received in a US account | Other capital assets: **> 24 months → ≈13.0%** on the **INR-measured** gain, no indexation, no ₹1.25 lakh exemption; **≤ 24 months → slab ≈31.2%** |
| Interest on USD cash | Bank deposits and registered-form portfolio interest generally not 871-taxed | **0** if received in a US account | Slab |
| India-source salary / Indian equity | — | Taxed in India | Taxed in India |

There is **no IRA, no Roth, no §1256 character, no IRC 1091 wash-sale engine, and no §475(f)**. One taxable offshore book plus fund domicile. Indian set-off and 8-year carry-forward apply at ROR.

Hard receipt rule during RNOR: **every cash leg lands in a US account.** A dividend or sale proceed paid directly into India can be “received in India” and taxed there even while RNOR.

US estate: NRA exemption **$60,000** (working). Stock of a US corporation — including US-listed ETF shares — is US-situs. Irish UCITS units, US bank deposits, and directly held T-bills are not (working). Aggregate US-situs market value **≤ $60,000** unless a priced estate tail lifts it.

---

## Capital

Funding of the USD book: already-held USD in US bank and brokerage accounts from the NRI period. **Not LRS-funded.** No incremental Indian FX required.

| Book | Envelope | Known holdings (working) |
|---|---|---|
| USD offshore (alien desk) | **$25,000 – $500,000**, single taxable book. Internal break at **$60,000** (estate exemption) | Vanguard taxable, marks **11 Sep 2026**: **$354,097** in US-listed ETFs (VTI + VXUS, residual VOO/VTV). Other brokers, cash, and retirement accounts are **not** in that score. See [R0](archive/r0-embedded-gain.md) |
| INR India desk | **₹25 lakh – ₹1 crore**, design point **₹50 lakh** | Own-capital demat / direct-plan funds. New-regime slabs; working assumption of no surcharge (income below ₹50 lakh) |

Above ~$500k US-situs the estate arithmetic and the single-machine posture both argue for an entity or trust, which is a different programme.

USD consumption is assumed in INR later. No currency hedge; no FX alpha is claimed. At ROR, INR depreciation on a USD book is itself an Indian taxable gain — which is a reason to step up before the cliff, not to hedge.

---

## Operating locks that follow from this identity

These are taxpayer facts enforced as platform gates, not preferences.

| Lock | Number |
|---|---|
| Own capital only | IRC 864(b)(2) |
| US-situs aggregate | ≤ **$60,000** unless W3 prices the tail |
| Receipt location during RNOR | US account, **zero tolerance** |
| US days | Alert **150**, tripwire **183** — [residency-calendar.md](residency-calendar.md) |
| RNOR window for a 0/0 realisation | Through **FY 2027–28** — same file |
| Foreign-share long line (India, ROR) | **24 months**, not 12 |
| Leverage / short stock / advertised performance | None in v1 |
| AI tax conclusion | Forbidden. W1 written opinion only |
