# Successor S1 — V2 Zenodo last-trade (report-only, 2026-08-18)

**Verdict:** V2 **FAIL (report)**. Pooled session-block CI includes 0. This is **not** quote V2 and **does not** invoke P1 STOP.  
**Logs:** `data/GOLDEN_PARQUET/s4_p1_zenodo_coverage.log`, `data/GOLDEN_PARQUET/s1_v2_zenodo.log`  
**Pre-registration:** [horizon-successor-s1-v2-zenodo-preregistration.md](horizon-successor-s1-v2-zenodo-preregistration.md) (locked before ingest)  
**Source:** Bhat, Aparna (2024). *Nifty spot, futures and options one-minute data from 2017 to 2020*. Zenodo. https://doi.org/10.5281/zenodo.10899828 (CC0)

## Modules

`src/horizon/m9/zenodo_ltp.py`, `src/scripts/build_nifty_option_snapshots_zenodo.py`. Store: `data/GOLDEN_IV/nifty_option_snapshots_zenodo.parquet` (`source=zenodo_bhat_1m_ltp`). Bid = ask = last-trade close. The quote path `nifty_option_snapshots.parquet` was not written. V2p-c was not retuned. `eval_horizon_m9_v2_stub.py` was not called.

## Coverage (before peek)

Frozen V2p-c selection rebuilt on A+B. Gate ≥ 70%.

| Fold | Selected | Marked | Coverage |
|---|---|---|---|
| A | 61 | 61 | **100%** |
| B | 89 | 84 | **94.4%** |

January 2018 expiry zip is absent in the deposit; fold A selected sessions still marked. Five fold-B sessions lack a 09:45+15:15 last-trade on the held contract.

## Numbers

Last-trade short ATM straddle, 09:45 → 15:15, GOLDEN spot in the denominator. Cost-free (spread ≡ 0).

| Fold | Marked | Mean | CI (bps) | MDE | Gate |
|---|---|---|---|---|---|
| A | 61 | +1.2 bps | **[−3.3, +5.3]** | 4.3 | FAIL (report) |
| B | 84 | +0.1 bps | **[−3.0, +3.4]** | 3.2 | FAIL (report) |

**Pooled:** mean **+0.6 bps**, CI **[−1.9, +3.1] bps**, sign **2/2** (both point estimates > 0), MDE **2.5 bps**, n=145.

Companion paired vs all-session last-trade short straddle: mean **+0.9 bps**, CI **[−1.9, +3.5] bps**. Not the gate.

2018 is monthly-only, so most sessions used nearest DTE ≥ 1 rather than DTE ∈ [1, 10]. Holiday clip: March 2018 last Thursday (29th) was not a session; expiry set to last traded date (28th). 0-DTE never selected.

## Cleanup

No quote-store fill from last-trade. No P1 STOP. No V3. No V2p-c retune. No EOD bhavcopy. No TradingTuitions 2021–22 substitute.

## Decision

**Superseded.** Range-space V2p-c did not show up as a significant 09:45–15:15 last-trade short straddle, even with spread set to zero. Product hunt **STOP**: do not buy vendor bid/ask. See [horizon-successor-stop-memo.md](horizon-successor-stop-memo.md).
