# Investor profile

**Status:** working household facts as of 2026-09-14. **Not a filed tax opinion.**
**This file is the taxpayer.** The [India desk](next/india-equity-architecture-blueprint-rev2.md) consumes it; it does not redefine it. Rev 2.0 is **ACTIVE** (declined-beta carry; milestone map [§13](next/india-equity-architecture-blueprint-rev2.md#13-twelve-month-staged-build)). Rev 1.0 Nifty-beta charter is [superseded](next/india-equity-architecture-blueprint.md). Rev 3.0 remains a competing draft.
**Not this taxpayer:** an offshore USD book, a US-person IRA / §1256 identity, or a 24-month foreign-share line. This desk is INR, India-source, listed Indian products.

---

## Identity

| | |
|---|---|
| Citizenship | Indian |
| Indian tax | Resident from FY 2025–26. **RNOR** now; **ROR** after the cliff in [residency-calendar.md](residency-calendar.md) |
| Capital | Own only. No third-party money, customers, pooled vehicle, or advertised performance |
| Family perimeter (SEBI algo) | Self, spouse, dependent children, dependent parents only. Never an algo provider, RA, or PMS |
| Risk | Moderately aggressive (4/5): cheap core **~75–80%** of the book; leftover **~20–25%** may be active sleeves. **4/5 does not cap sleeve count or how that leftover is split.** Core-heavy, no leverage. |
| Regime | New default regime. Working assumption of **no surcharge** (income below ₹50 lakh) |

Indian salary from **1 Sep 2025** is India-source and taxed in India even during RNOR. The RNOR zero cell is **foreign passive income received outside India**, not employment income and not this book.

---

## Indian tax

Rates are **working**. `tax` takes the [residency calendar](residency-calendar.md) for RNOR vs ROR. **India-source salary and Indian equity are taxed in India in both regimes.** Where a later foreign-income question appears, **ROR governs**.

| Income | Statute (ITA 2025, working) | Rate with 4% cess |
|---|---|---|
| Listed equity / equity-oriented funds, held **> 12 months** | s.198 | **12.5%** above ₹1.25 lakh aggregate per tax year, no indexation → **13.0%** |
| Listed equity / equity-oriented funds, held **≤ 12 months** | s.196 | **20%** flat from the first rupee → **20.8%** |
| Intraday equity (no delivery) | s.66 speculative business | Slab, up to **~31.2%**; losses only against speculative income, carry **4** years |
| F&O on a recognised exchange | s.66 exception, non-speculative business | Slab, up to **~31.2%**; losses against any head except salary, carry **8** years |

There is **no tax wrapper** for a self-directed book. Every rupee of realised gain is taxed in the tax year it is realised. The listed-equity long line is **12 months**, not 24. Indian set-off and carry-forward apply. `tax` in this repo is this identity; do not import an IRA rate, §1256 character, or a US wash-sale engine.

---

## Capital

| Book | Envelope | Known holdings (working) |
|---|---|---|
| INR India desk | **₹25 lakh – ₹1 crore**, design point **₹50 lakh** | Own-capital demat / direct-plan funds. New-regime slabs; no surcharge (working) |

This programme authorizes **₹0** live strategy capital until M6. Desk limits live in [Rev 2.0 §12](next/india-equity-architecture-blueprint-rev2.md#12-risk-and-operations--the-numbers-the-code-asserts); they follow from this identity, they are not a second taxpayer.

---

## Operating locks that follow from this identity

These are taxpayer facts enforced as platform gates, not preferences.

| Lock | Number |
|---|---|
| Own capital only | No client money, no pooled vehicle |
| Family perimeter | Self, spouse, dependent children, dependent parents — SEBI retail algo |
| Leverage / MTF / short stock / advertised performance | None in v1 |
| Live strategy capital | **₹0** until M6 |
| RNOR / ROR | [residency-calendar.md](residency-calendar.md). India-source taxed either way |
| Listed-equity long line | **12 months**, not 24 |
| AI tax conclusion | Forbidden. Written CA opinion where a blueprint working number requires it |
