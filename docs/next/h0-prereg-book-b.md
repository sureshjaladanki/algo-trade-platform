---
book: B
hypothesis: Shares already held in the core can be lent through SLBM for a fee that exceeds its friction, without changing market exposure.
instrument: SLBM R1/R3 series on F&O-eligible Nifty 50 / Next 50 names already held
horizon: 3 days (R3) to one month (R1)
universe: U0 membership spine (Nifty 50 + Next 50); not a Nifty 200 PIT book
n: 5
sigma_ann: 0.005
t_years: 5
mde_ann: 0.0063
e_net_hypothesised: 0.0060
half_e_net: 0.0030
passes_h4: false
inference: true
spec_budget: 5
specs_used: 0
---

# Pre-registration — Book B (SLBM lending yield)

Registered: 2026-09-05 at H0. **No SLB bhavcopy or fee series was read for this file.** σ = 0.5% and
T = 5 yr are the blueprint §5.1 planning numbers (SLB bhavcopy depth), not estimates from a peek.
U0 did not ingest SLB bhavcopy; n = 5 sleeve-years.

## H4

MDE_ann = 2.80 × 0.5% / √5 = **0.63%**. Hypothesised E_net **25–60 bps** (front matter uses the
generous top of the range, 60 bps, so ½ E_net = **30 bps**). **0.63% ≰ 0.30% → H4 fails.** Blueprint
verdict is **MARGINAL — ₹0 screen decides**, which is why this is not a H0 STOP memo: S0 still
requires SEBI's reformed-SLBM circular before any screen.

## Kill (when S0 opens)

Close if the median annualised lending fee on held names, from free NSE SLB bhavcopy over 5 years, is
under **25 bps**. Also close if lending-fee tax treatment is not in writing with a CA. R3 has no
repay, recall or rollover.

## Specs used

0 of 5.
