# F0 — Event pool

**Gate:** F0 (execution plan). **Date:** 2026-08-19.

## Reconstruction

Events are the first-session difference in point-in-time Nifty-50
membership. The membership walk is the in-repo replacement ledger.
Announcement dates are not on that ledger and were not purchased.

**Families with PIT membership:** nifty_50
**Index price series without membership:** NIFTYCEMENT.csv, NIFTY_IND_DEFENCE.csv, NIFTY_OIL_AND_GAS.NS.csv, NIFTY_PVT_BANK.NS.csv, ^CNXAUTO.csv, ^CNXENERGY.csv, ^CNXFINANCE.csv, ^CNXFMCG.csv, ^CNXIT.csv, ^CNXMETAL.csv, ^CNXPHARMA.csv, ^CNXPSUBANK.csv, ^CNXREALTY.csv, ^INDIAVIX.csv, ^NSEI.csv

## Counts

Total events **68** (additions 34, deletions 34).
In the GOLDEN tradable universe on the effective session: **43**.

| year | family | event_type | n |
|---|---|---|---|
| 2015 | nifty_50 | addition | 4 |
| 2015 | nifty_50 | deletion | 4 |
| 2016 | nifty_50 | addition | 3 |
| 2016 | nifty_50 | deletion | 3 |
| 2017 | nifty_50 | addition | 6 |
| 2017 | nifty_50 | deletion | 6 |
| 2018 | nifty_50 | addition | 4 |
| 2018 | nifty_50 | deletion | 4 |
| 2019 | nifty_50 | addition | 2 |
| 2019 | nifty_50 | deletion | 2 |
| 2020 | nifty_50 | addition | 4 |
| 2020 | nifty_50 | deletion | 4 |
| 2021 | nifty_50 | addition | 1 |
| 2021 | nifty_50 | deletion | 1 |
| 2022 | nifty_50 | addition | 2 |
| 2022 | nifty_50 | deletion | 2 |
| 2023 | nifty_50 | addition | 1 |
| 2023 | nifty_50 | deletion | 1 |
| 2024 | nifty_50 | addition | 3 |
| 2024 | nifty_50 | deletion | 3 |
| 2025 | nifty_50 | addition | 4 |
| 2025 | nifty_50 | deletion | 4 |

## Implied F1 sample

F1 can use at most the 43 tradable events, split by
addition vs deletion, and only those whose pre-registered window
has both endpoint closes (no interpolation).

## Which sub-gates the dates support

- **F1a** — unsupported: announcement dates are unrecoverable_from_pit; announcement-to-effective residual cannot run
- **F1b** — unsupported: pre-announcement ranking needs the announcement date; this is F3's job if a free calendar appears later
- **F1c** — supported: post-effective reversal on effective dates (n=68, tradable=43)
- **F1-effective** — supported as the existence test this peek can actually run: T-20 close to T close residual vs Nifty, dated on the PIT difference (n=68, tradable=43). This is not F1a.

## Stop check

The pool was built from in-repo membership. Book F does not stop
at F0. Power vs the 600 bps prior is printed in the F1 charter
before the peek. Announcement dates remain unrecoverable here;
F1a is not run.
