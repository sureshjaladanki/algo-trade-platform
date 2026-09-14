# A0 — $0 VIX–RV / PUTW screen

**Date:** 2026-08-21
**Spec:** `A.public-vix-rv-putw`
**Spend:** $0 (Yahoo VIX, SPX, PUTW, VTI; working SPX ATM 30–45 cost)
**Not A1.** A green screen is permission to buy CBOE SPX EOD. It does not certify the 20–25Δ put-spread.

## VIX minus subsequent 21-day SPX RV

Non-overlapping 259 windows. Cost haircut from `src.costs` SPX ATM 30–45 (mid and all-in high).

| | vol points |
|---|---|
| Mean raw VIX–RV | 3.29 |
| Net of mid cost | 3.00 |
| Net of expensive-end cost | 2.91 |
| Sign stable in ≥ 4 of 5 sub-periods (expensive) | True |
| Gate | **buy CBOE tape** |

### Sub-periods (net of expensive-end cost)

| Window | Mean | n |
|---|---|---|
| 2005-01-01 – 2008-12-31 | 0.42 | 48 |
| 2009-01-01 – 2012-12-31 | 5.58 | 48 |
| 2013-01-01 – 2016-12-31 | 3.12 | 48 |
| 2017-01-01 – 2020-12-31 | 1.87 | 48 |
| 2021-01-01 – 2026-12-31 | 3.36 | 67 |

### Stress years (raw VIX–RV)

| Year | Mean |
|---|---|
| 2018 | 0.25 |
| 2020 | -0.23 |
| 2024 | 2.78 |

## PUTW vs after-tax VTI

Source: `^PUT` (PUTW Yahoo history is unusable; CBOE PUT index is the packaged put-write path). Ordinary-income column taxes index year-returns at the working 40% rate when the series has no distributions.

| Window | 2016-02-24 – 2026-08-20 |
| PUTW/PUT before-tax CAGR | 8.75% |
| After-tax packaged (ordinary) | 5.08% |
| After-tax VTI (same window) | 15.19% |
| DIY 1256 marked CAGR | 6.07% |
| 1256 vs ordinary wedge | 98 bps/yr |
| Packaged max drawdown (window) | -30.0% |
| CBOE PUT index max drawdown (full) | -37.1% |
| Stress years | 2018: -6.1%, 2020: 1.7%, 2024: 17.9% |

PUTW max drawdown is cash-secured puts, not the defined-risk spread, so it is an upper bound on short-vol pain, not an A2 kill.

