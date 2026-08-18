# Successor S2 — C0 cost ladder (T-01)

**Date:** 2026-08-18  
**Authority:** [horizon-successor-architecture-blueprint.md](../next/horizon-successor-architecture-blueprint.md) Rev 3 §5.2  
**Harness:** `src/experiments/eval_horizon_successor_s2_c0.py` (pooled `k5_pooled` at every `C0_HAIRCUTS_BPS`)  
**Log:** `data/GOLDEN_PARQUET/s2_c0_ladder.log` (reprint; not a new peek)

Sleeve, folds, disaster **clip**, and costs are byte-identical to [horizon-successor-s2-c0-preregistration.md](horizon-successor-s2-c0-preregistration.md). The original run pooled only c = 3. This memo publishes the pre-registered 3/5/8 table.

**Reprint (2026-08-18):** `s2_c0_ladder.log`. Authority sleeve `prior_day_high_reject` Short. n=63,469, sess=1,476, MDE 3.7 bps at every haircut. Disaster clip 379 rows at floor.

| Haircut | Pooled CI | Sign | Verdict |
|---|---|---|---|
| c = 3 | **[+1.5, +8.9]** | 6/6 | PASS (historical C0) |
| c = 5 | **[−0.5, +6.9]** | 5/6 | **pooled LB FAIL** — instrument gate |
| c = 8 | **[−3.5, +3.9]** | 1/6 | FAIL both legs |

Location-shift check: c=5 and c=8 CIs are the c=3 interval minus 2 and 5 bps exactly. **`c_max` = 4.5 bps** (pooled CI LB crosses 0 at `3 + 1.5`).

## Forward SSF round-trip (2026 schedule, not sample-era)

Pre-registered as a **friction schedule** to verify against a current NSE/broker circular. Not an in-repo measurement.

| Component | bps of notional |
|---|---|
| STT, futures sale (0.02%, post-Oct-2024; was 0.01% across R2017–R2022) | ~2.0 |
| Exchange transaction charges (both sides) | ~0.35 |
| Stamp duty (buy) + SEBI fees | ~0.22 |
| GST 18% on brokerage + charges | ~0.1 |
| Brokerage (₹20/order flat, ~₹10 L notional) | ~0.4 |
| 2 × half-spread, liquid SSF | 1–4 |
| MIS forced square-off market exit (not in the C0 label) | 1–3 |
| **Total forward RT** | **≈ 5.1–10.1** |

Sample-era futures STT was half of today's. The 2017–2022 paths were cheap in a way 2026 is not.

## Gate

Pooled CI LB > 0 **and** sign ≥ 5/6 at **c = 5**.

## Decision

**P2 STOP (bounded at `c_max`).** Do not open S4-P2. Do not download SSF. Next: T-02 (V2p-c) and T-03 (S6 multi-day fade), in parallel, both killable in ≤2 machine-days.

If the ladder reprint unexpectedly clears at c = 5, still do **not** buy the panel until the forward schedule's floor sits below the reprinted `c_max`.
