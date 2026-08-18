# Successor S4-P1 — Index marks checkpoint (2026-08-18)

**Verdict:** **Earned, not started.** V2 did not peek.  
**Logs:** `data/GOLDEN_PARQUET/s4_p1_coverage.log` (exit 1), `data/GOLDEN_PARQUET/s1_v2.log` (exit 3)  
**Charter:** [horizon-successor-s4-p1-index-marks-charter.md](../next/horizon-successor-s4-p1-index-marks-charter.md)  
**V2 prereg:** [horizon-successor-s1-v2-preregistration.md](horizon-successor-s1-v2-preregistration.md)

## Modules

`src/horizon/m9/index_option_store.py`, `v2_index_straddle.py`, `eval_horizon_successor_s4_p1_coverage.py`, `eval_horizon_successor_s1_v2.py`. Name V2 stub was not called. EOD bhavcopy was not used.

## Numbers

No 09:45/15:15 Nifty snapshots in `data/GOLDEN_IV/nifty_option_snapshots.parquet`. Coverage cannot run. V2 hard-exits INCONCLUSIVE (store missing), which is the locked abort, not a FAIL.

Forward V3 STT locked at **0.15% of premium** (Finance Act 2026, from 2026-04-01), seller, sell-to-open only.

## Decision

**Human/vendor step.** Acquire bid/ask for Nifty ATM straddle at 09:45 and 15:15 on folds A/B (2018–2019), DTE ∈ [1, 10], same strike held through flatten. Then rerun coverage (≥ 70% of frozen V2p-c sessions) and only then the V2 peek. Do not fill the store from FO bhavcopy.
