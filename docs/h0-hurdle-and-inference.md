# H0 — Hurdle and inference design

**Status:** published 2026-08-20, before any strategy peek  
**Formula:** MDE = 2.8 σ / √n_eff at two-sided 95% / 80% power. Gate: MDE ≤ 0.5 × hypothesized effect.  
**Trial budget:** 5 pre-registered specs per book, α = 0.01, logged including abandonments.

| Book | Bet | n | Haircut | n_eff | σ | Hypothesized | MDE | Ratio | Gate |
|---|---|---|---|---|---|---|---|---|---|
| C | Location, bands, harvest vs static VTI (accounting) | 1 household | 1 | 1 | 0 | 25 bps/yr | 0 | 0 | **pass** |
| A | One 30–45 DTE SPX 20–25Δ put-spread cycle (sleeve P&L) | 240 (12 × 20y) | 1 | 240 | 150 bps of sleeve | 116 bps/cycle | 27.1 | 0.23 | **pass** |
| B | Name-event 20-day PEAD, numeric surprise, $ADV > $20M | 30,000 | 5× cluster | 6,000 | 800 bps | 100 bps/event | 28.9 | 0.29 | **pass** |

Book A units: the observation is the *sleeve* cycle. Diluting into the 80% passive core is a portfolio weight, not the series the MDE is computed on. Book B hypothesized effect is the 100 bps economic hypothesis; 40 bps is the later kill threshold, not the effect size used here.

Walk-forward: purged and embargoed contiguous folds (`src.harness.purged_embargoed_splits`). Deflated Sharpe: Bailey & López de Prado (2014) in `src.harness.deflated_sharpe`. The harness raises unless `print_mde` has run for the current spec.

At least one book clears the MDE ratio, so H0 does not stop the programme.
