# F1 charter — effect exists (cost-free)

Written **before** the residual peek. Windows are not revised after seeing results.

| Lock | Choice |
|---|---|
| Instrument | Cash delivery, single-name vs Nifty-50 close |
| Friction | **None.** F1 is cost-free. 45 bps and 20.8% wait for F2 |
| Dates | Effective session from PIT difference. Announcement dates unrecoverable |
| Authority window | T−20 close → T close (F1-effective, **not** F1a) |
| Statistic | Mean trade residual (bps), disaster-clipped at −500 bps, session-block 95% CI, fold sign test |
| Additions | Long residual = r_name − r_Nifty |
| Deletions | Short residual = −(r_name − r_Nifty). Evaluated separately |
| Companions | T−40→T−20 (labelled pre-window, not pre-announcement); T→T+20 fade (F1c) |
| Required effect | CI lower bound > 0 on the authority window |
| Hurdle | 0 bps |
| σ prior | 600 bps (blueprint sketch) |
| MDE additions | **323.5 bps** (n=27, σ=600, 80% power two-sided) |
| MDE deletions | **420.2 bps** (n=16, σ=600, 80% power two-sided) |
| Bootstrap | session-block, n_boot=500, seed=7 |
| Folds | calendar year of T; sign test among years with ≥2 events |
| Disaster clip | 500 bps floor, keep the row |
| Purge | 5 calendar days on rolling year folds (no model is fit here) |

F1a (announcement→effective) is **not** this peek. If MDE ≥ |point|, the verdict is INCONCLUSIVE;
the repair is more event history from this panel, not a different window.
