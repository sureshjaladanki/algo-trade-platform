# A0.5 — $0 spread-cost kill screen

**Date:** 2026-08-21
**Spec:** `A.spread-cost-kill`
**Spend:** $0 (ThetaData FREE EOD SPX chains from 2023-06-01 + Yahoo `^GSPC`)
**Not A1.** n=38 MDE=68.1 bps ratio=0.59 (H3 closes A1 certification on the FREE window). This peek is a kill screen on *spread cost*, not implied-minus-realized.

| | |
|---|---|
| Monthly expiries attempted | 54 |
| Spreads reconstructed (30–45 DTE, 20–25Δ, 50–100 wide) | 37 |
| Mean credit (points) | 6.86 |
| Mean bid–ask both legs / credit | 37.3% |
| Mean all-in round-trip / credit | 37.8% |
| Mean credit retained after all-in | 62.2% |
| Retention hurdle | 25% |
| ATM `costs` bucket all-in high | 2.0% of premium |
| Sparse / unbuildable | False |
| Gate | **authorize A1 CBOE dump** |

Fees from `src.costs.vertical_spread_round_trip` (two legs, open+close). Delta from bid/ask mid + SPX close, European Black–Scholes, working r=5% q=1.3%.
