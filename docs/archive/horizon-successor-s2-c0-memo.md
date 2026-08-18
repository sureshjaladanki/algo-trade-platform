# Successor S2 — C0 fade cost-bound (2026-08-17)

**Verdict:** C0 **PASS** at 3 bps (pooled K5 + sign 6/6).  
**Log:** `data/GOLDEN_PARQUET/s2_c0.log`  
**Pre-registration:** [horizon-successor-s2-c0-preregistration.md](horizon-successor-s2-c0-preregistration.md)

## Modules

`src/horizon/successor/fade_bound.py`, `eval_horizon_successor_s2_c0.py`. First live caller of `k5_pooled`.

## Numbers (authority sleeve `prior_day_high_reject` Short)

Unconditional transition pool, vertical-only, disaster **clip** (379 rows at −500 bps; not dropped). Six disjoint years R2017–R2022.

| Fold | n | sess | c=3 CI (bps) | MDE |
|---|---|---|---|---|
| R2017 | 9994 | 247 | [−4.0, +9.3] | 6.6 |
| R2018 | 9752 | 244 | [−4.5, +12.6] | 8.5 |
| R2019 | 10013 | 244 | [−3.6, +14.1] | 8.9 |
| R2020 | 10601 | 248 | [−0.3, +28.7] | 14.5 |
| R2021 | 11372 | 247 | [−5.1, +11.1] | 8.1 |
| R2022 | 11737 | 246 | [−7.3, +10.7] | 9.0 |

**Pooled c=3:** mean CI **[+1.5, +8.9] bps**, sign **6/6**, MDE **3.7 bps**, n=63,469, sess=1,476. `k5_pooled` PASS.

Per-fold CIs all include 0 — the sparse-book lesson. Cash `c_eff` companion is **negative** dual-fold (LB ≈ −40 to −18 bps): lowering \(c\) is the product, not a cash reprint.

Companions `vwap_loss` / `gap_fill_short` stay report-only; no new winner.

## Cleanup

No Stage C. No N-bar exhaustion. First execution aborted before pooled K5 (harness demanded 8 folds of a 6-year design); sleeve/cost/clip unchanged; pooled read is the authority.

## Decision

**Go for P2 instrument change.** SSF history is *earned*, not started. S3: do not download until V2p is resolved *or* an explicit S4-P2 start. Do not treat cash `c_eff` as the hurdle.
