# G1 charter — earnings drift, gross (cost-free)

Written **before** the residual peek. Windows are not revised after seeing results.
Skip overnight-repriced names is **G3**, not this gate.

| Lock | Choice |
|---|---|
| Instrument | Cash delivery, single-name vs Nifty close |
| Universe | G0 quarterly first-broadcast calendar, GOLDEN panel |
| Friction | **None.** 45 bps and 20.8% wait for G2 |
| T | First session close that provably contains the NSE timestamp |
| Close cutoff | 15:30 IST. Date-only / at-or-after-close → next session |
| Side | Sign of residual T−1 close → T close. Vendor SUE is not used |
| Authority window | T close → T+3 close |
| Companions | T→T+1 and T→T+5. Not authority |
| Statistic | Mean trade residual (side × residual), disaster-clipped −500 bps, session-block 95% CI, fold sign |
| Required effect | CI lower bound > 0 on T+3 |
| Hurdle | 0 bps (existence) |
| Economic hurdle | **45 bps** (printed beside MDE; charged in G2, not here) |
| σ prior | 600 bps |
| MDE | **28.2 bps** (n=3543, σ=600, 80% power two-sided) |
| Bootstrap | session-block, n_boot=500, seed=7 |
| Folds | calendar year of T; sign test among years with ≥2 events |
| Disaster clip | 500 bps floor, keep the row |
| Decay | 2015–19 vs 2020–25 is a column, not a gate |
| Annual / half-year | Not mixed in |

INCONCLUSIVE or FAIL stops Book G. Do not buy 2025 Integrated Filing.
Do not add guidance or sentiment. Do not promote a companion.
