# G3 charter — gap already in

Written **before** the G1 residual peek. This gate does not run unless G1 and G2 PASS.

| Lock | Choice |
|---|---|
| Input | G1 T+3 events with a non-null overnight residual |
| Overnight gap | Residual of T open vs T−1 close, name minus Nifty |
| Percentile | **50th** of \|overnight residual\| on that sample |
| Keep | Events with \|overnight residual\| **at or below** that percentile |
| Drop | Missing overnight (publish the count). Do not impute |
| Authority | Cost-free T+3 trade residual on the kept (small-gap) sleeve |
| Companions | Large-gap T+3 (already repriced); small-gap T+3 net of 45 bps and 20.8% |
| Statistic | Same as G1: disaster clip −500, session-block 95% CI, fold sign |
| Required effect | CI lower bound > 0 on the small-gap sleeve |
| Hurdle | 0 bps |
| σ prior | 600 bps |
| MDE (expected) | **~40 bps** at n ≈ 1772 (half of G1 n=3543). Actual n and MDE print before the restricted mean |
| Percentile freeze | Do not move 50 after seeing the print |

If the small-gap sleeve does not PASS and the large-gap companion does, the edge exists only where the gap already repriced the news: **there is no trade.**

Do not add guidance or sentiment. Do not scan other event types.
