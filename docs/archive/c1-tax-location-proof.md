# C1 — Tax and location accounting proof

**Date:** 2026-08-20  
**Exit:** simulated after-tax excess vs static VTI ≥ 25 bps/yr, zero wash-sale violations, audit trail of every harvest.

## Result

| | |
|---|---|
| Window | 2018-01-02 – 2023-12-29 (5.99 years) |
| Representative book | $100k VTI + $500/month DCA, taxable |
| Harvest terminal | $224,338 |
| Static VTI terminal | $219,624 |
| After-tax excess | **35.5 bps/yr** |
| Wash-sale violations | **0** |
| Harvest events | 46 (full audit on `SimResult.audit`) |
| Gate | **pass** — keep harvest, location, and bands |

Priced through `src.costs` (liquid-ETF round trip) and `src.tax` (ST 40%, 31-day quarantine). Substitutes are the VTI / ITOT / SCHB whitelist; ITOT and SCHB are marked at the VTI close (same total-market exposure). Harvested losses are assumed to offset household short-term gains at the working ST rate; tax savings are reinvested.

Location and MES band overlay are retained regardless: high-turnover long-only → IRA when contribution room exists; 1256 stays taxable; drift outside a 5% band is corrected with an MES overlay rather than a cash-equity sale.

## Not this milestone

C2 (live shadow year / 1099-B) is not started. A0 / B0 public screens ran 2026-08-21; A1 still needs CBOE history and B1 still needs the Polygon PIT panel.
