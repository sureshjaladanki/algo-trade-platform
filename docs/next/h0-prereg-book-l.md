---
book: L
hypothesis: Optimal realisation schedule (12-month line 20.8%→13.0%, s.198 ₹1.25 lakh exemption, ETF vs constituent STT) beats a naive schedule on a ₹50 lakh Indian equity core.
instrument: NIFTYBEES / ICICI or Kotak Nifty 50 ETF / a direct Nifty 50 index fund, plus the delivery leg of every other book
horizon: 12 months and longer, by construction
universe: Nifty 50 core (U0 membership spine: Nifty 50 + Next 50)
n: n/a
sigma_ann: n/a
t_years: n/a
mde_ann: n/a
e_net_hypothesised: 0.0095
half_e_net: n/a
passes_h4: true
inference: false
spec_budget: 5
specs_used: 0
---

# Pre-registration — Book L (holding-period and cost ledger)

Registered: 2026-09-05 at H0. **No book data accessed.** SHA is the file hash `harness` records at load.

## Why there is no MDE

This book is **arithmetic**: `costs` + `tax` on a realisation schedule. H4 does not apply. `passes_h4`
is true so the book may proceed to L1; it is not a claim that a statistical gate was cleared.

## Effect

**95–130 bps/yr at ₹50 lakh** (front matter stores the lower bound 95 bps). Blueprint worked example:
at 60%/yr turnover on a ₹50 lakh core at an **11%/yr TRI assumption (W17 — assumption, not a
forecast)**: tax delta ₹41,990 (84 bps) + ETF-versus-constituent rebalancing saving ₹5,970 (12 bps) =
96 bps. At full annual realisation the tax delta alone is ₹59,150 = 118 bps.

## Kill

- H1: if `costs` + `tax` cannot reproduce a contract note and a Tax Year 2026-27 hand-worked book to **₹1**, the platform stops.
- If the measured schedule delta at ₹50 lakh is under **50 bps/yr**, close Book L and run a plain index fund.

## CAS (L6)

Core rebalances after 3 August 2026 use `close_method`. No pooling of pre- and post-CAS closes for
F&O-eligible names without an explicit declaration at L1.

## Specs used

0 of 5. A sixth specification is refused by `spec_budget_guard`.
