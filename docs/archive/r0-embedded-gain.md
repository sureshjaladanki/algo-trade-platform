# R0 — Embedded-gain and cliff-date ledger

**Date:** 2026-09-14
**Spend:** $0
**Status:** **Exit passed.** Working-mark step-up **180 bps** of capital ≥ 100 (N9). Prior 240 bps used per-lot acquire-date FX; that converted file is not in the repo.

Source: one Vanguard taxable cost-basis export (`data/private/costbasisdownload_2391.csv`), 38 covered MinTax lots, marks **11 Sep 2026 04:15 PM ET**. Household reads these lots (`src/household.py`); it does not write them and is not a filing source. INR per USD is the household working mark **95.69**, source `yahoo_usdinr_working`, date **2026-09-11**, applied to **both** cost and value — tagged **working**. G4 / Rule 115 / TT-rate remains W1. Cliff date **31 Mar 2028** is the working last RNOR year from the investor's day-count facts, not a filed opinion.

This file is this Vanguard taxable account only. Other brokers, cash, and retirement accounts are not in the score.

## Book (this file)

38 lots. US-listed ETFs: VTI + VXUS plus residual VOO and VTV. No Irish lines. No bonds.

| | USD | INR (working mark 95.69) |
|---|---|---|
| Cost | **307,061.36** | ₹2.94 crore |
| Value (11 Sep 2026) | **354,097.28** | ₹3.39 crore |
| Unrealised | **47,035.92** | **₹45.01 lakh** |
| of which FX accretion | — | **₹0** at this working mark |

USD matches the broker's Total cost / Market value columns to **$0.01**. Broker short-term / long-term gain columns on the mark date sum to the same **$47,035.92** (ST **$23,632.24** / LT **$23,403.68**). Those are US holding-period labels, not the Indian 24-month clock.

INR is **not** Rule 115. Using one mark-date rate on both legs scores no FX accretion. The 2026-09-13 write-up used per-lot Yahoo acquire-date rates **86.78–95.76** (converted `data/private/r0-lots.csv`, gitignored, not present to replay) and printed INR unrealised **₹60.52 lakh**, of which FX accretion **₹15.51 lakh**, and **240 bps**. That methodology is not mixed into the table above.

## Tax if sold after the cliff

Working cliff 31 Mar 2028. **16** lots would still be under 24 months (the Apr–Jul 2026 buys); **22** would be long. Almost all USD gain sits in the long lots (**$45,670.43** long / **$1,365.49** short).

| | INR (working mark) |
|---|---|
| 13.0% on long lots | ₹5.68 lakh |
| ~31.2% on short lots | ₹0.41 lakh |
| **Tax after the cliff** | **₹6.09 lakh** |
| **Step-up worth** | **180 bps of current INR capital** |

The illustration (200k → 400k, INR 62 → 92, ~862 bps) remains retired. This book was bought from Jul 2025. On the household working mark, USD gain is ~15.3% and N9 still clears. A later G4 / W1 named acquire-date basis would re-run (`revalue`); it would add FX accretion and would not be a new peek.

## Exit / Stop

Exit: step-up ≥ **100 bps of capital** on the **real** ledger. **Passed (180, working mark).**
Stop: below 100 bps — not fired.

N9 still holds. R1 is not authorized. Vehicle still pending. W1 (broker eligibility + written opinion) still gates the trade. Wrapper migration must not run until the vehicle is named. The working last year for R1 is FY 2027–28; latest safe trade date is **17 Mar 2028** ([gl0-cliff-calendar.md](gl0-cliff-calendar.md)).
