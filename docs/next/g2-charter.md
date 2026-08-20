# G2 charter — net of delivery and STCG

Written **before** the G1 residual peek. This gate does not run unless G1 PASSes.

| Lock | Choice |
|---|---|
| Input | Disaster-clipped G1 T+3 trade residual |
| Formula | **net = 0.792 × (gross − 45)** |
| Delivery | 45 bps round trip, charged once per event |
| Tax | 20.8% STCG on the net-of-cost residual |
| Comparator | After-tax passive hold. Residual is already vs Nifty; this gate haircuts the active excess |
| Statistic | Mean net bps, session-block 95% CI, fold sign (same folds as G1) |
| Required effect | CI lower bound > 0 |
| Hurdle | 0 bps net |
| σ prior | 600 bps (conservative on the net scale) |
| MDE | **28.2 bps** (n=3543, σ=600) |
| Annual print | Events/year × 25% stated active weight × per-event net, labelled unadjusted for overlap |
| Companions | None. T+1 / T+5 stay G1 companions |

FAIL or INCONCLUSIVE stops Book G. Do not open G3. Do not move the window.
G1 FAIL / INCONCLUSIVE never reaches this peek.
