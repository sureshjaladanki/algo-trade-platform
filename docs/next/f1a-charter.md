# F1a charter — announcement to effective (cost-free)

Written **before** the F1a residual peek. This is not a move of the
F1-effective T−20 window.

| Lock | Choice |
|---|---|
| Instrument | Cash delivery, name vs Nifty close |
| Friction | None |
| Entry | Close of the first NSE session on or after the recovered announcement date |
| Exit | Close of the PIT effective session |
| Statistic | Mean trade residual, disaster-clipped −500 bps, session-block 95% CI, fold sign |
| Additions | +(r_name − r_Nifty) |
| Deletions | −(r_name − r_Nifty), separate sleeve |
| Required effect | CI lower bound > 0 |
| Hurdle | 0 bps |
| σ prior | 600 bps |
| MDE additions | **323.5 bps** (n=27) |
| MDE deletions | **420.2 bps** (n=16) |
| Bootstrap | session-block, n_boot=500, seed=7 |

Evening press releases may make the entry close pre-announcement;
that is accepted as the recoverable free calendar, not interpolated.
Ad-hoc events keep their actual notice, including short notice.
