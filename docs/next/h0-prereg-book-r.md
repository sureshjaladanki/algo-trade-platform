---
book: R
hypothesis: Quarterly seasonal-random-walk SUE from exchange-filed results predicts a 3-month drift in Nifty names, per Theoretical Economics Letters (2018) on Nifty 500.
instrument: Cash delivery, 3-month hold, long-only
horizon: Quarterly events, 3-month hold
universe: U0 Nifty 50 + Next 50 (blueprint named Nifty 200; no Nifty 200 PIT membership in U0)
n: 15
sigma_ann: 0.10
t_years: 15
mde_ann: 0.0723
e_net_hypothesised: 0.019
half_e_net: 0.0095
passes_h4: false
inference: true
spec_budget: 5
specs_used: 0
---

# Pre-registration — Book R (results-season drift)

Registered: 2026-09-05 at H0. **No filings, no SUE, no return series accessed.** Closed on this
arithmetic: see [book-r-stop.md](../archive/book-r-stop.md).

## H4

MDE_ann = 2.80 × 10% / √15 = **7.23%/yr**. E_net hypothesised **1.9%/yr**, ½ E_net = **0.95%**.
**Fails H4 by 7.6×.**

India has no free point-in-time consensus dataset. Surprise would have been seasonal-random-walk SUE
from filings. `ai.extract` dies with this book.

## Specs used

0 of 5. No specifications will be run.
