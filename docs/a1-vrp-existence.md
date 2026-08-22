# A1 — VRP existence

**Date:** 2026-08-22
**Spec:** `A.spx-put-spread-20-25d-30-45dte`
**Spend:** $0 OptionsDX SPX EOD 2012–2023 + ThetaData FREE 2024–present (Cboe DataShop historical cart $580, above the $100 stop)
**Tape:** bid/ask + Yahoo `^GSPC`. Vendor IV/greeks unused. Splice at expiry 2024-01-01 (OptionsDX before, ThetaData FREE after). Completes the pre-registered 2012–present window, including the named 2024 stress year. Not an extension to 2005–2011.

MDE printed first: n=173 MDE=31.9 bps ratio=0.28.

OptionsDX-only (already published): n=138 IV−RV 5.27 vs cost 3.79 (1.39×). Theta tail gate n=31.

| | |
|---|---|
| Monthly expiries | 174 |
| Gate observations (20–25Δ, 30–45 DTE) | 169 |
| Window | 2012-01-10 – 2026-06-10 |
| Mean IV−RV (vol pts) | 4.91 |
| Mean spread round-trip (vol pts) | 4.14 |
| Multiple (IV−RV / cost) | **1.19×** (hurdle 2×) |
| Mean net of cost | 0.77 |
| Spread-cost (not ATM fallback) | 169/169 |
| Sign stable net in ≥ 4 of 5 sub-periods | True |
| Gate | **Book A STOP (IV-RV <= 2x spread round-trip)** |

### Sub-periods (net of spread cost)

| Window | Mean | n |
|---|---|---|
| 2012-01-01 – 2014-05-31 | 1.37 | 24 |
| 2014-06-01 – 2016-10-31 | 0.87 | 29 |
| 2016-11-01 – 2019-03-31 | 1.79 | 29 |
| 2019-04-01 – 2021-08-31 | 1.81 | 29 |
| 2021-09-01 – 2026-12-31 | -0.55 | 58 |

### Stress years (raw IV−RV)

| Year | Mean |
|---|---|
| 2018 | 1.54 |
| 2020 | 2.06 |
| 2024 | 1.44 |

### Pre-registered grid (raw IV−RV, ATM cost not applied)

| Delta | Tenor | Mean IV−RV | n |
|---|---|---|---|
| 10Δ | 0 DTE | 19.34 | 2 |
| 15Δ | 0 DTE | 16.92 | 2 |
| 20Δ | 0 DTE | 15.30 | 2 |
| 25Δ | 0 DTE | 14.22 | 2 |
| 30Δ | 0 DTE | 14.05 | 2 |
| 10Δ | 7 DTE | 6.71 | 143 |
| 15Δ | 7 DTE | 5.46 | 143 |
| 20Δ | 7 DTE | 4.65 | 143 |
| 25Δ | 7 DTE | 4.06 | 141 |
| 30Δ | 7 DTE | 3.53 | 142 |
| 10Δ | 14 DTE | 7.17 | 143 |
| 15Δ | 14 DTE | 5.74 | 143 |
| 20Δ | 14 DTE | 4.79 | 143 |
| 25Δ | 14 DTE | 4.05 | 143 |
| 30Δ | 14 DTE | 3.46 | 143 |
| 10Δ | 30 DTE | 8.21 | 141 |
| 15Δ | 30 DTE | 6.48 | 141 |
| 20Δ | 30 DTE | 5.30 | 141 |
| 25Δ | 30 DTE | 4.38 | 141 |
| 30Δ | 30 DTE | 3.67 | 141 |
| 10Δ | 45 DTE | 9.55 | 138 |
| 15Δ | 45 DTE | 7.69 | 138 |
| 20Δ | 45 DTE | 6.40 | 138 |
| 25Δ | 45 DTE | 5.41 | 138 |
| 30Δ | 45 DTE | 4.61 | 138 |

0DTE and 7DTE rows document the Blueprint closure of 0DTE as an alpha book. They are not an A1 search. Do not extend to 2005–2011.
