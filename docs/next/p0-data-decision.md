# P0 data decision

**Milestone:** P0 — Posture and cost lock  
**Date:** 2026-08-20  
**Authority:** [us-equity-execution-plan.md](us-equity-execution-plan.md) Build item 6

Authorized, and nothing else:

| Source | Role | When |
|---|---|---|
| Public (Yahoo / Vanguard) | After-tax VTI hold series 2005–2026 | Now |
| Broker (IBKR) fills | Calibrate `costs` within 3 bps / 0.3% of premium | Operational P0 remaining |
| Polygon Developer | Adjusted daily bars, corporate actions, **delisted tickers** | U0 |
| CBOE SPX EOD option history | Book A implied-minus-realized | A1 only |
| SEC EDGAR | Filing index and timestamps | U0 / B1 |
| FRED | Rates | As needed |

Fundamentals / consensus (Sharadar or equivalent) stay closed until B1 passes. No Databento, no tick data, no other vendor on the critical path of a first test.
