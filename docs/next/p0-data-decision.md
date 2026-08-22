# P0 data decision

**Milestone:** P0 — Posture and cost lock  
**Date:** 2026-08-21  
**Revision:** Rev 1.1 spend-deferral (Claude Opus). P0 authorizes **$0** paid data.  
**Authority:** [us-equity-execution-plan.md](us-equity-execution-plan.md) Build item 6; Blueprint §3.1

P0 is an interpretability gate (cost, tax, after-tax VTI), not a procurement gate. Polygon Developer and CBOE history are **revoked** from P0. They were the wrong SKUs at the wrong time: Developer is 10 years against B1’s 16-year window, and CBOE was authorized before A0.5 could kill Book A at $0.

## Authorized at P0 — $0 paid

| Source | Role | When |
|---|---|---|
| Public (Yahoo / Vanguard) | After-tax VTI hold series 2005–2026; VIX, SPX, listed bars, `^PUT` | Now |
| Broker (IBKR) fills | Calibrate `costs` within 3 bps / 0.3% of premium (tiny live size) | Operational P0 remaining |
| SEC EDGAR | Filing index, timestamps, Form 25/15 identifiers | U0 / B0 / B0.5 |
| FRED | Rates | As needed |
| ThetaData **FREE** | SPX EOD chains from 2023-06-01 | **A0.5 only** — kill screen, cannot certify A1 |

## Explicitly not authorized at P0

| Source | Why closed here | First possible authorization |
|---|---|---|
| CBOE DataShop, SPX only, no calcs, 2012–present dump | A0.5 may kill Book A at $0; full-market OPRA and CGI are never in scope | **A1**, working $25–35, same files serve A2 |
| CBOE Optsum 2005–2011 | 2012–present already clears H3 (n≈175, MDE 31.7 bps) | Closed |
| Polygon Developer / Advanced | Wrong default for B1 (history depth or delisted quality) | Only if Norgate trial fails, at **B1** |
| Norgate US Platinum | B0.5 may kill Book B at $0 | **B1**, trial then $346.50 / 6 months |
| Sharadar SF1/SEP | Fundamentals are a B2 question | **B2**, and only if B1 passes |
| Databento / tick / CRSP | Capital-scale closed | Never in v1 |

Discovery vendor ceiling before L0: **$700**. Do not buy A-tape and B-panel in the same month.
