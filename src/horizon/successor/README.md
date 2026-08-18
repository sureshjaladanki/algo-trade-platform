# Horizon successor

Active map: [horizon-successor-implementation-plan.md](../../../docs/next/horizon-successor-implementation-plan.md) (Rev 3).  
Fresh M0–M9 is **historical**. This package is P2 (fade bound). P1 (index vol) lives in `src/horizon/m9/`.

## Freeze

- Production Regime → Horizon → Precision is **frozen**. No `predict_horizon_gbm` / Top-K / H=6 / 60–30 swap.
- Fresh M6 harness stays hard-exit. Do not remount Stage C.
- Precision Execution Bridge is not on this path.
- `eval_horizon_m9_v2_stub.py` is Fresh Track A ledger, **not** P1 V2. Do not acquire `option_marks_daily.parquet`.
- S4-P1 is **index** snapshots at 09:45/15:15, not EOD bhavcopy.
- Name V1 PASS is **report-only** (lagged EOD ATM). V1-index is P1 V1.

## Products

| Product | Code | Status |
|---|---|---|
| P1 index vol | `src/horizon/m9/` + V1n / V2p-b / V2p-c / V2 harnesses | V2p-c **PASS**. S4-P1 store **not started**. V2 hard-exits without 09:45/15:15 snapshots |
| P2 fade vs cheaper \(c\) | `fade_bound.py` + `eval_horizon_successor_s2_c0.py` | C0 **PASS** at 3 bps. SSF **not earned** (`c_max` ≈ 4.5). Intraday P2 STOP |
| S6 multi-day fade | `fade_bound.py` + `eval_horizon_successor_s6_multiday.py` | T+3 c=6 **INCONCLUSIVE**. Do not buy SSF |

## Authority logs (reprint, do not re-peek)

| Ledger | Where |
|---|---|
| M3 K1 | Fresh M3 harness / checkpoint |
| M4R drift | `data/GOLDEN_PARQUET/m4r_drift_ledger.log` |
| M4R-b F1/F2 | `data/GOLDEN_PARQUET/m4rb_full_run.log` |
| V0 | `data/GOLDEN_PARQUET/m9_v0_vix_bridge.log` |
| V1-index PASS | `data/GOLDEN_PARQUET/m9_v1_index.log` |
| V1n PASS / V2p-0 | `data/GOLDEN_PARQUET/s1_v1n.log` |
| V2p-b INCONCLUSIVE | `data/GOLDEN_PARQUET/s1_v2pb.log` |
| V2p-c PASS | `data/GOLDEN_PARQUET/s1_v2pc.log` + [v2pc memo](../../../docs/archive/horizon-successor-s1-v2pc-memo.md) |
| S4-P1 charter | [index-marks charter](../../../docs/next/horizon-successor-s4-p1-index-marks-charter.md) — store not started |
| C0 PASS | `data/GOLDEN_PARQUET/s2_c0.log` |
| C0-ladder | `data/GOLDEN_PARQUET/s2_c0_ladder.log` + [cost-ladder memo](../../../docs/archive/horizon-successor-s2-cost-ladder-memo.md) |
| S6 INCONCLUSIVE | `data/GOLDEN_PARQUET/s6_multiday.log` + [S6 memo](../../../docs/archive/horizon-successor-s6-multiday-fade-memo.md) |
| Name V1 (report-only) | [horizon-m9-v1-memo.md](../../../docs/archive/horizon-m9-v1-memo.md) |
