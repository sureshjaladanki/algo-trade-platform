# Horizon M9-0 — Single-name IV Data Acquisition

**Status:** COMPLETE for store + coverage (2026-08-17); V1 dual-fold PASS (separate memo)  
**Charter:** [horizon-m9-range-monetization-charter.md](horizon-m9-range-monetization-charter.md)  
**Date:** 2026-08-17

---

## Why this is the critical path

Authority **V1** needs implied remaining range at the **name** level. The repo has India VIX
(`data/GOLDEN/^INDIAVIX.csv`) — enough for report-only **V0** and for **V1-index** (Nifty vs VIX) —
but not for single-name ATM IV.

Until this store existed, Track A could not be authority-tested. **V1-index** dual-fold
already **PASS**ed (2026-08-17); name-level V1 is the remaining Track A gate.

---

## Target schema (acceptance)

One row per `(symbol, date_only)` — **daily EOD**, causal for the next session’s Stage B decisions.

| Column | Type | Meaning |
|---|---|---|
| `symbol` | Utf8 | Same as GOLDEN (`RELIANCE.NS`, …) |
| `date_only` | Date | Session date of the IV mark |
| `atm_iv_pct` | Float64 | ATM IV in **percent** (India-VIX units), no look-ahead into T+1 |
| `atm_strike` | Float64 | Strike used (optional but preferred) |
| `underlying_close` | Float64 | Spot used for moneyness |
| `expiry` | Date | Expiry of the option used |
| `source` | Utf8 | `nse_bhavcopy_bs` \| `vendor` \| … |
| `dte` | Int32 | Calendar days to expiry at mark |

**Join rule for V1:** `attach_lagged_atm_iv` shifts the mark forward one calendar day, then
asof-joins backward. Session T never sees T's EOD IV; holidays inherit the last prior mark.
Never same-bar option prints until a 1m options store exists.

**Source (this build):** `nse_bhavcopy_bs` — NSE FO bhavcopy zip → Black–Scholes ATM IV,
spot = front-month FUTSTK settle, `r = 0`, `T = DTE/365`. Log: `data/GOLDEN_PARQUET/m9_0_iv_build.log`
(72,825 rows, 1,231 sessions, 2015-01-01–2019-12-31).

**Coverage gate:** ≥ 70% of Stage B `(symbol, session)` cells in folds A/B test windows must have
non-null `atm_iv_pct`, or V1 is thin and report-only.

Store path (proposed): `data/GOLDEN_IV/atm_iv_daily.parquet` (lazy Polars).

---

## Acquisition options (ranked)

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **A. Vendor EOD ATM IV panel** (Sensibull-class / paid FO history) | Fast; quality | Cost; licensing | **Preferred if budget exists** |
| **B. NSE F&O bhavcopy → Black–Scholes ATM IV** | Official; reproducible | Build cost; EOD only; stale for intraday | **Default DIY path** |
| **C. Unofficial live APIs scraped historically** | Appealing | ToS / stability / survivorship | **Forbidden for authority** |

### DIY path B — outline

1. Download NSE FO bhavcopy ZIPs for 2015–present (cash-market aligned).  
2. Filter option rows for trade-universe underlyings (map NSE symbols ↔ `*.NS`).  
3. Spot = **front-month FUTSTK settle** from the same file (not split-adjusted GOLDEN close).  
4. Pick near-month option expiry with DTE in \[7, 45\]; ATM = strike closest to that spot.  
5. Invert settle via Black–Scholes (`r = 0`); average CE/PE ATM IV when both exist.  
6. Emit the schema above; unit-test no future leakage (`attach_lagged_atm_iv` uses T+1 legality / asof).

Commands:

```powershell
poetry run python -m src.scripts.build_atm_iv_daily --start 2015-01-01 --end 2019-12-31
poetry run python -m src.experiments.eval_horizon_m9_0_coverage --folds A B
poetry run python -m src.experiments.eval_horizon_m9_v1 --folds A --max-symbols 8
```

Do **not** commit raw bhavcopy zips to git; materialize parquet only (`data/` is gitignored).

---

## Out of scope for M9-0

- Intraday option chains (Phase-2)  
- Full surface / skew models (V2+ may need them later)  
- Distributing proprietary FO dumps in the repo  

---

## Exit criteria

- [x] `data/GOLDEN_IV/atm_iv_daily.parquet` readable by `src.horizon.m9.iv_store`
  — 72,825 rows, 1,231 sessions (`m9_0_iv_build.log`)
- [x] Coverage report vs GOLDEN trade symbols for folds A/B
  — test A 79.8%, test B 78.4% (`m9_0_coverage.log`); gate 70%
- [x] Documented source + causality rules (this file + `attach_lagged_atm_iv`)
- [x] V1 harness smoke on ≥1 fold with non-thin n
  — fold A, 8 names, OLS n=28,169 (`m9_v1_smoke.log`); not authority V1

---

## Parallel (does not replace M9-0)

| Work | Role |
|---|---|
| **V1-index** | Nifty remaining range vs India VIX + index `range_q50` — dual-fold **PASS** 2026-08-17 (`m9_v1_index.log`); **drop `volume_z`** |
| **V0** | Already run — name range vs India VIX (report-only) |
| Track B SSF download | Separate; only escalate if V1-index FAIL or after V1 name PASS |
