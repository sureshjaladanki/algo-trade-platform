# Tiingo $0 coverage — Yahoo-missing S&P 400

**Date:** 2026-08-22
**Spend:** $0 (Tiingo Starter, 500 unique symbols/mo)
**Not B1.** Lock 5: ticker-keyed, no licensed index PIT. A hit tightens the B0.5 bound; it does not certify the panel.

| | |
|---|---|
| Current S&P 400 | 399 |
| Left the index (ever − current) | 654 |
| Yahoo-cache-missing leavers | 316 |
| In Tiingo ticker file | 225 (71.2%) |
| Recovered (major exchange, series ended) | 200 |
| OTC with history back to 2010 | 2 |
| Usable (recovered + OTC history) | **202 (63.9%)** |
| Tiingo usable EOD on disk | **202** (+ successors CADE/VRE/ENDPQ/JOY/SIVBQ/LNW) |
| OTC stub (short history) | 0 |
| Reject (known splice / ticker reuse) | 1 |
| Absent from Tiingo | 91 |
| After successor join (Yahoo + Tiingo + remaps) | **N_missing = 59**, w=**12.9%**, zero-drift bound **71.7 bps** (Item 2.02 mean still 82.3) |

EOD sample (adj close, cached under `data/raw/tiingo`):

| Symbol | Status | Exchange | File start | File end | Bars / error | First bar | Last bar |
|---|---|---|---|---|---|---|---|
| AAI | recovered | NYSE | 2001-09-17 | 2011-11-30 | 483 | 2010-01-04 | 2011-11-30 |
| AAN | recovered | NYSE | 2020-11-25 | 2024-10-03 | 969 | 2020-11-25 | 2024-10-03 |
| ABMD | recovered | NASDAQ | 1987-07-30 | 2023-01-03 | 3268 | 2010-01-04 | 2023-01-03 |
| ACC | recovered | NYSE | 2004-08-12 | 2022-08-09 | 3172 | 2010-01-04 | 2022-08-09 |
| ACXM | recovered | NASDAQ | 1984-09-07 | 2018-10-01 | 2202 | 2010-01-04 | 2018-10-01 |
| ADVS | recovered | NASDAQ | 1995-11-16 | 2015-07-16 | 1393 | 2010-01-04 | 2015-07-16 |
| AF | recovered | NYSE | 1993-11-18 | 2017-10-02 | 1951 | 2010-01-04 | 2017-10-02 |
| AHL | recovered | NYSE | 2003-12-05 | 2019-02-15 | 7 | 2026-02-25 | 2026-03-05 |

Successor pulls this run (not in the original 202 usable set):

| Symbol | Source | Bars | Window |
|---|---|---|---|
| EFOR / CVSA / MFIC / KODK / SVC / NVRI / DHC | Yahoo | ~3.2k–4.2k | successor remaps (ASGN, ATGE, AINV, EK, HPT, HSC, SNH) |
| CADE / VRE / ENDPQ / JOY / SIVBQ / LNW | Tiingo | 1.8k–4.1k | BXS, CLI, ENDP, JOYG, SIVB, SGMS |

Absent from Tiingo ticker file (old symbols): AAXN, ADS, AINV, AKRX, AMB, APY, ASGN, ASNA, ATGE, BIG, BRE, BXS, CBB, CFX, CHFC, CLI, CPO, CREE, CSAL, DF, DRQ, EK, ELY, ENDP, ERI, ESV, EXBD, FBHS, FII, GDI, GMT, GPS, HANS, HFC, HPT, HSC, HTSI, HUB-B, JCG, JCOM, JCP, JOYG, JW-A, KAR, LANC, LKQX, LNCR, LPS, LRY, MLHR, MNK, MPW, NAL, NCR, NST, NVE, NYB, NYCB, OFC, OMI, PDE, PMTC, PNM, POL, PPDI, PSS, PSTG, QSFT, RCII, RDK, RE, ROVI, SGMS, SIVB, SNH, SPN, TCB, TMST, TNB, TPX, TUP, TWTC, UTR, VCLK, VSCO, WFSL, WGOV, WPG, WTR, WYND, ZI.

EOD/file disagreements: **AHL** stays in N_missing (DIRTY_IDENTITY; 7 bars in 2026). **SIVB→SIVBQ** is on disk but also dirty — kept out of the bound recovery. **AAN** file/API history starts 2020. Remaining hard hole (~59) includes JCP, bankruptcies, and a few still-listed Yahoo 404s (MPW, PSTG, VSCO, OMI, ELY→MODG not yet cached).

Tiingo Starter allows 50 requests/hour. This is not Norgate: no PERMNO, no licensed S&P 400 PIT. Bound detail: [b05-item-202-bound.md](b05-item-202-bound.md).
