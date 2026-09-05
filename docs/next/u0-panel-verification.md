# U0 — Panel verification

Date: 2026-09-05
Milestone: U0
Fetcher: `src/fetch.py` + `src/panel.py`. Cache under `data/cache/` (content-addressed). Live fetches: ≤ 1 request / 2 s, exponential backoff, weekday 09:00–16:15 IST refused. Weekends are not market hours (blueprint §9.3). Rebuild of a cached day uses `allow_network=False`.

## Evidence tests

Implemented in `tests/test_panel.py`. Named names and dates:

### Survivorship — Sterlite Industries

- **Name:** STER, ISIN INE268A01049 (Sterlite Industries (India) Ltd).
- **Last session:** 26 Aug 2013. No-dealing from 27 Aug 2013 (merger into Sesa Goa; BSE notice 20130820-27).
- **2012-12-31 panel:** STER present.
- **2013-08-27 panel:** STER absent.
- **Rank:** on 2012-12-31, RELIANCE’s cross-sectional rank by unadjusted close **changes** if STER is dropped using a 2013 survivor filter. The PIT panel does not apply that filter.

### Demerger — Reliance / Jio Financial Services

- **Parent:** RELIANCE, ISIN INE002A01018.
- **Child:** JIOFIN, ISIN INE758E01017.
- **Record / ex date:** 20 Jul 2023. Ratio **1:1** (RIL scheme; NCLT). Special pre-open child reference **₹261.85**.
- **Fixture unadj closes:** 19 Jul 2023 RELIANCE ₹2,796.00; 20 Jul 2023 RELIANCE ₹2,534.15 + JIOFIN ₹261.85.
- Combined holding value gap **0** (< 1%). Adjustment factor on pre-ex RELIANCE rows = 2534.15 / 2796 ≈ 0.90635, stored not only applied.

### Look-ahead

`date_shift_test` (in `src/harness.py`, H0) lags `unadj_close` by one session and recomputes a feature. An honest lag feature moves. A feature that reads a frozen (date, symbol) → next-close map does **not** move and the test fails. Planted leak is in the unit test, not in the panel.

### Surveillance — ESM Stage II

- **Name:** SETCO. NSE circular 5 May 2026: SETCO moved Stage I → Stage II **effective 6 May 2026**; ±2% periodic call auction.
- **5 May 2026:** SETCO remains in the cash tradable set.
- **6 May 2026:** `universe.tradable_symbols` **refuses** SETCO (`esm_stage == 2`).

### `close_method` (L6)

- RELIANCE is F&O-eligible in the fixture.
- 31 Jul 2026: `vwap_30min`.
- 3 Aug 2026: `cas_auction`.
- SETCO on 3 Aug 2026 (not F&O in the fixture): `vwap_30min`.
- Column non-null on every row. Month counts include 2026-07 vs 2026-08.

## Index membership (narrowing)

Current NSE constituent CSVs for Nifty 50 and Nifty Next 50 are in `tests/fixtures/u0/` (archives.nseindia.com, fetched 2026-09-05). Point-in-time **Nifty 200 / 500 / Midcap 150 / Smallcap 250 reconstitution history was not assembled from free press-release bulk files** in this milestone. Per the plan, the membership spine used for books is **Nifty 50 + Nifty Next 50**, walked from the 2026-09-05 snapshot plus events (Sterlite out 2013-08-27). See `docs/archive/u0-stop.md`. Full CM bhavcopy rows remain the listed-universe PIT set (survivorship).

## W6 impact cost

`join_impact_cost` joins `month` + `symbol` → `impact_cost_bps`. A real NSE monthly impact-cost file was not cached (no single stable public CSV URL verified on 2026-09-05). Fixture values are placeholders for the join path. **W6 stays pending** until a monthly file is in `data/` and the segment bands are replaced.

## 5,000 sessions

Offline rebuild is proven on the fixture cache (`test_rebuild_offline`).

CM backfill 2006-01-02 → 2026-09-04 finished 2026-09-05: **`poetry run python -m src.panel count --root data` = 5,103** (above the 5,000-session floor). Objects live in gitignored `data/cache/`. Re-run is a no-op for days already stored.

```powershell
poetry run python -m src.panel backfill --start 2006-01-02 --end 2026-09-04 --root data
poetry run python -m src.panel count --root data
```

Pace is 2 seconds per request. Do not run on weekdays 09:00–16:15 IST.
