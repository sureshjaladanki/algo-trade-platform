# Successor S1 V2p-b — post-open residual (2026-08-18)

**Verdict:** **INCONCLUSIVE** (thin). Clock repair did not produce a passable sample. Residual > 0 is not a session product on this charter.  
**Log:** `data/GOLDEN_PARQUET/s1_v2pb.log`  
**Pre-registration:** [horizon-successor-s1-v2pb-preregistration.md](horizon-successor-s1-v2pb-preregistration.md) (locked before the run)

## Why

V2p-0 took the session’s first bar (`bars_to_mis > 0` → 09:30 bleed). Stage B `open_30m_range` is only complete at **09:45**. One locked change: first bar at/after 09:45. Residual **> 0** unchanged. V1n was not re-peeked.

## Numbers

AdmitPowerPlan printed **before** selection: n=110 sess=220 expected_mde=9.3 bps.

| Fold | Test sessions | Selected | Share | Gate |
|---|---|---|---|---|
| A | 245 | **3** | 1.2% | thin n=3 sess=3 |
| B | 244 | **2** | 0.8% | thin n=1 sess=1 |

V2p-0 was 3 / 3 sessions. The clock was not the bottleneck. `range_q50` is almost never above VIX-implied at the remaining-session decision bar, so the three-way never fires.

## Decision

**Do not** scan 10:00 / q75 / other clocks. **Do not** retune the residual threshold. **Do not** acquire index-option marks. **Do not** salvage with name V1.

P1 V1 / V1n remain **PASS** (forecast incremental). P1 V2p residual>0 **cannot** be tested on this charter. A rewritten V2p needs a **new selection definition**, not a third clock. The earned data spend, if the programme continues, is **S4-P2 SSF** (C0 already PASS), under an explicit charter.
