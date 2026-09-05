---
book: A
hypothesis: The CAS auction close, formed in a pool ~1% of cash ADTO, is a noisier fair-value estimate than the 30-minute VWAP it replaced, so auction versus the 15:15 reference has a mean-reverting component that did not exist before 3 August 2026.
instrument: Cash delivery in CAS-eligible names, entered in the 15:20–15:25 auction phase
horizon: One session
universe: F&O-eligible names in the U0 spine (Nifty 50 + Next 50)
n: 0.09
sigma_ann: 0.039
t_years: 0.09
mde_ann: 0.364
e_net_hypothesised: 0.015
half_e_net: 0.0075
passes_h4: false
inference: true
spec_budget: 5
specs_used: 0
---

# Pre-registration — Book A (CAS closing-auction dislocation)

Registered: 2026-09-05 at H0. **No auction prints, no 15:15 reference series, no return peek.**
T = 0.09 yr is calendar time from CAS go-live **3 August 2026** to this registration date, not a
sample of auction residuals.

## H4 today and later (still not a peek)

| T (years) | MDE_ann |
|---|---|
| **0.09 (today)** | **36.4%** |
| 1 | **10.9%** |
| 20 | **2.44%** |

E_net hypothesised **1.5%/yr** (W16, working). ½ E_net = 0.75%. Today **fails H4**. At T = 1, MDE
10.9% still fails. At T ≈ 20, MDE 2.44% would be the first time the gate is even in range against
1.5%.

## Kill / review

**Not open, and not to be opened before 2027-08-31.** Any earlier opening is a peek. Review date is a
hard calendar item for `ops`, not a judgement call. At review, recompute MDE at then-available T and
apply H4; do not reopen on a story.

## Specs used

0 of 5.
