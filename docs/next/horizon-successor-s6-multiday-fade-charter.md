# Successor S6 — Multi-day fade charter (T-03)

**Status:** RUN 2026-08-18 — T+3 c=6 **INCONCLUSIVE** (MDE 10.2 ≥ 6). See [horizon-successor-s6-multiday-fade-memo.md](../archive/horizon-successor-s6-multiday-fade-memo.md).  
**Date:** 2026-08-18  
**Authority:** [horizon-successor-architecture-blueprint.md](horizon-successor-architecture-blueprint.md) Rev 3 §8  
**Why this is a new family:** C0 showed ~+5 bps of Short-fade at a 3 bps haircut. Intraday SSF cannot clear that bound (`c_max` ≈ 4.5 vs forward RT ≈ 5–10). The remaining lever is **`c/σ`**: a 2–10 session futures hold (~6 / 400 ≈ 1.5%) rather than another instrument at the same 90-minute horizon.

## Hypothesis

The frozen event `prior_day_high_reject` Short has fold-consistent drift to MIS flatten. That drift may continue (or mean-revert further) over the next 1–5 **sessions** on large-cap names. Test it on in-repo **daily** bars before buying futures history.

## Locked choices

| Item | Value |
|---|---|
| Rule | `prior_day_high_reject` Short only. No new rules. No N-bar exhaustion |
| Horizon | Close-to-close **T+1, T+2, T+3, T+5** (pre-register all four; authority = the one declared **before** the peek — pick **T+3** unless a written reason names another) |
| Cost | **c = 6 bps** scalar (optimistic multi-day futures RT: STT + spread + one overnight gap buffer). Companions 8 and 12 |
| Folds | R2017–R2022, pooled `k5_pooled`, sign ≥ 5/6 |
| Geometry | None — vertical at the horizon close. Disaster clip at −500 bps (same as C0, not drop) |
| Data | In-repo daily bars from GOLDEN / parquet. **No SSF download** until PASS |

## Gate

Pooled `EV_net` CI LB > 0 at c = 6 **and** sign ≥ 5/6.

| Verdict | Next |
|---|---|
| **PASS** | Earn survivorship-safe F&O eligibility + lot panel; reprint on futures paths (or cash paths with measured RT) |
| **FAIL** | This signal has no friction-ratio escape. If V2p-c also FAIL → **programme FAIL**; next charter must change **market** |
| **INCONCLUSIVE** | MDE ≥ 6 bps — repair power; do not buy data |

## Forbidden

New event rules, cash Stage C, remounting Top-K / H=6 / 60–30, treating a PASS as an intraday MIS reopen, downloading SSF to manufacture power.
