# F1b charter — pre-announcement ranking skill

Written **before** the ranking peek. This is execution-plan F3 /
blueprint F1b **skill**, not a residual trade and not F2.
HuggingFace Nifty-50 weight files are the wrong universe.

| Lock | Choice |
|---|---|
| Source | NSE Indices monthly MCWB zips (Nifty 50 and Next 50) |
| Universe | Next 50 members in the cut-off month |
| Score | 6-month average free-float mcap ending 31 Jan / 31 Jul |
| Months required | **5** of the six (skip the name otherwise) |
| Liquidity screen | mean monthly avg. impact cost ≤ **0.50%** |
| F&O screen | not applied this pass (no PIT F&O field in MCWB) |
| 1.5× rule | Next 50 name ≥ **1.5** × smallest Nifty 50 6-month FF mcap |
| Labels | F0 semi-annual **additions** only. Ad-hoc swaps are out |
| Cut-off map | PR in Jan–Apr → 31 Jan; PR in Jul–Sep → 31 Jul |
| Authority statistic | Top-k hit rate. k = number of semi-annual additions that cycle |
| Hit | Actual addition's Next 50 rank ≤ k |
| Naive | Random Next 50 rank; pooled **0.0407** (k/50 per addition) |
| Required | CI lower bound of hit rate > naive |
| n | **29** semi-annual additions |
| MDE | **0.1028** hit-rate points (80% power, two-sided, vs naive) |
| 1.5× companion | recall and precision of the published buffer; not the gate |
| Universe miss | addition absent from Next 50 at cut-off; dropped from hit-rate n |
| Hold-out print | 2015–2019 vs 2020–2025; rule is not fit on either slice |
| Residual trade | not this peek |
| Bootstrap | unused (binomial CI). Residual n_boot=500 does not apply |

Do not fit a model. Do not re-window F1a. Do not open F2.
