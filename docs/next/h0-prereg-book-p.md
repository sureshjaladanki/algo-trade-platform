---
book: P
hypothesis: For every documented Indian factor (momentum, low volatility, alpha, quality), a packaged index fund or ETF that bears turnover internally and defers tax to redemption dominates a self-run replication that pays delivery friction and 20.8% STCG.
instrument: Nifty 200 Momentum 30 and Nifty 500 Momentum 50 index funds and ETFs (Motilal Oswal ETF 0.30%, Motilal direct 0.34%, UTI / Axis / Bandhan direct ~0.3–0.5%; regular plans excluded), Nifty 100 Low Volatility 30, Nifty Alpha 50; versus a self-run Nifty 50 + Next 50 replication (U0 spine)
horizon: Comparison over published TRI; resulting sleeve held with annual or semi-annual rebalancing
universe: Factor indices named above; self-run leg is U0 Nifty 50 + Next 50, not a peeked Nifty 200 PIT membership
n: n/a
sigma_ann: n/a
t_years: 20
mde_ann: n/a
e_net_hypothesised: 0.0030
half_e_net: n/a
passes_h4: true
inference: false
spec_budget: 5
specs_used: 0
---

# Pre-registration — Book P (packaged versus self-run)

Registered: 2026-09-05 at H0. **No book data accessed.** Decision value hypothesised **30–150 bps/yr**
(front matter stores 30 bps, the floor of that range). T = 20 years of *published* TRI is a data
availability claim, not a return peek.

## Why there is no MDE

The comparison is **deterministic** given published TRI, TER and tax. H4 does not apply.

## Kill thresholds (not H4)

- Packaged beats self-run by **> 100 bps/yr** after cost and tax → Book M closes permanently; implement the fund.
- Self-run beats packaged by **> 100 bps/yr** → Book M may open only against `h0-prereg-book-m.md` (H4 already fails 5.0×).
- Within **±100 bps** → buy the fund (no operational risk).

## Specs used

0 of 5.
