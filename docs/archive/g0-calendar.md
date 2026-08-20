# G0 — Results calendar

**Gate:** G0, free NSE filings. **Date:** 2026-08-19.
Charter: `docs/next/g0-charter.md`. Not a residual peek.

## Source

NSE public `corporates-financial-results` JSON (quarterly).
Timestamps are IST as published (`exchdisstime`, else `broadCastDate`).
Raw chunks under `data/raw/nse_results/`. No vendor.

## Coverage

- panel names: **100**
- names with ≥1 quarterly filing: **95**
- events after first-broadcast dedup: **3586**
- span: 2015-01-15 17:12:03 .. 2025-02-17 22:32:13
- missing names: ENRIN.NS, HDFCLIFE.NS, SBILIFE.NS, TATACAP.NS, TMCV.NS
- G1 MDE at this n, σ=600: **28.1 bps**

The 2025–26 custom windows on this endpoint thin out (NSE moved
results onto Integrated Filing). The working sample is 2015 through
early 2025. That is enough for a first G1 test. Do not buy a vendor
to fill 2025.

| year | events | names |
|---|---|---|
| 2015 | 321 | 81 |
| 2016 | 328 | 82 |
| 2017 | 338 | 84 |
| 2018 | 348 | 87 |
| 2019 | 345 | 87 |
| 2020 | 352 | 89 |
| 2021 | 364 | 92 |
| 2022 | 346 | 92 |
| 2023 | 372 | 94 |
| 2024 | 377 | 95 |
| 2025 | 95 | 95 |

## Book G

PASS. Free calendar exists on the GOLDEN panel. G1 is unblocked.

**Verdict: PASS**
