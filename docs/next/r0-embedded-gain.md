# R0 — Embedded-gain and cliff-date ledger

**Date:** 2026-09-13
**Spend:** $0
**Status:** **Exit passed.** 240 bps of capital ≥ 100.

Source: one Vanguard taxable cost-basis export (`data/private/costbasisdownload_2391.csv`), marks **11 Sep 2026**. Converted lot file: `data/private/r0-lots.csv` (gitignored). INR per USD is Yahoo `USDINR=X` on the acquire date (prior close if the date is closed) and on the mark date — a working stand-in for the RBI/prescribed rate until N0. Cliff date **31 Mar 2028** is the working last RNOR year from the investor's day-count facts, not a filed opinion.

This file is this Vanguard taxable account only. Other brokers, cash, and retirement accounts are not in the score.

## Book (this file)

38 lots. US-listed ETFs: VTI + VXUS (the W0 naive core) plus residual VOO and VTV.

| | USD | INR |
|---|---|---|
| Cost | 307,061 | ₹2.78 crore |
| Value (11 Sep 2026) | 354,097 | ₹3.39 crore |
| Unrealised | **47,036** | **₹60.52 lakh** |
| of which FX accretion | — | ₹15.51 lakh |

USD/INR at acquire: 86.78–95.76. On the mark date: **95.69**.

## Tax if sold after the cliff

Working cliff 31 Mar 2028. 16 lots would still be under 24 months (the Apr–Jul 2026 buys); the rest would be long.

| | INR |
|---|---|
| 13.0% on long lots | ₹7.67 lakh |
| ~31.2% on short lots | ₹0.46 lakh |
| **Tax after the cliff** | **₹8.14 lakh** |
| **Step-up worth** | **240 bps of current INR capital** |

The illustration (200k → 400k, INR 62 → 92, ~862 bps) is retired. This book was bought from Jul 2025, so the USD gain is ~15% and most of the rupee move had already happened. It still clears N9.

## Exit / Stop

Exit: step-up ≥ **100 bps of capital** on the **real** ledger. **Passed (240).**
Stop: below 100 bps — not fired.

R1 is not authorized. W1 (broker eligibility + written opinion) still gates the trade. The working last year for R1 is FY 2027–28; it can also run in the current RNOR year.
