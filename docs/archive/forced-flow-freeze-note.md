# Forced-flow freeze note

**Date:** 2026-08-19  
**Status:** **LOCKED** for this branch  
**Authority:** [forced-flow-architecture-blueprint.md](../next/forced-flow-architecture-blueprint.md) Rev 2, [forced-flow-execution-plan.md](../next/forced-flow-execution-plan.md)

This branch is an **orphan**. It keeps repository scaffolding and the closed-programme numbers. It does not contain the cascade / Fresh / Successor source tree.

---

## What is frozen

| Item | Posture |
|---|---|
| Production cascade (Regime → Horizon → Precision) | Frozen. Not a live book. Not a research input. |
| Cash MIS directional | **CLOSED** |
| Remaining-session index vol | **CLOSED** |
| Same-session fade, including T+k of the reject rule | **CLOSED** |
| Rev 1 momentum book and FII-flow overlay | **Withdrawn** — buy the packaged fund; do not DIY the sort |

## Why the momentum book is withdrawn

Indian momentum is real, but a personal-demat 12-1 sort pays STCG (~20.8%) on every rebalance while a momentum index fund rebalances internally at no tax cost to the holder. The DIY version starts two to four percentage points a year behind the fund before operational risk. A future factor sort must clear roughly **+2.5% a year over the matching index fund after tax**. That bar is not attempted here.

## What this branch spends on

Book F (index reconstitution and F&O list changes), then Book G (earnings drift) only if a free calendar exists. The passive core is capital and the after-tax benchmark, not a research programme.

## Constants (locked before any peek)

| Constant | Value |
|---|---|
| Delivery round trip | **45 bps** |
| Short-term gains | **20.8%** |
| Long-term gains | **12.5%** (passive hold, applied on exit) |
| Index futures round trip | 10–12 bps, **reference only** |

April 2026 derivatives STT is the forward hurdle. Sample-era futures STT is a historical reprint, not a live cost.

## Closed-programme summaries

Numbers below are inherited from the prior tree and are **not reproduced** on this branch. Reprint from the original logs before using any figure as a hurdle.

| Programme | Summary |
|---|---|
| Cascade (Regime / Horizon / Precision) | [cascade-closed.md](cascade-closed.md) |
| Fresh (event-causal MIS) | [fresh-closed.md](fresh-closed.md) |
| Horizon Successor (range / fade / remaining-session vol) | [horizon-successor-closed.md](horizon-successor-closed.md) |
| Methods that survive | [inherited-learnings.md](inherited-learnings.md) |
