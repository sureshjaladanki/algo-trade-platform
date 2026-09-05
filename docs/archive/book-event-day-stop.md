# STOP — Budget and MPC event days

Date: 2026-09-05
Closed at: H0
Author: agent

## What was claimed

Trade the Union Budget day and RBI MPC days (1 Budget + 6 MPC per year) as an event sleeve.

## What was measured

**Nothing was measured; the book closed before any data access.**

n = **140** events over 20 years (7 events/yr × 20). σ = 1.5%/event. MDE ≈ **0.35%/event ≈ 2.5%/yr**.
This is the **only** phenomenon on the §5.1 list whose MDE arithmetic is comfortable. Specs used 0
of 5. E_net unknown — it was never hypothesised, because there is no admissible signal.

## Why it closed

**Not H4.** Closed on **absence of an admissible signal.** Trading the day requires a **directional
forecast**. **L10** forbids any model output entering a return forecast, a signal, a weight, or a
position size. Comfortable measurability does not create a legal signal for this desk.

## What would re-open it

A non-forecast, non-model rule that is fully specified in a pre-registration *and* does not use LLM
or statistical-model output in the size — for example a regulator-mandated closed market, which is
not an event-day *trade*. A better forecast is not a reopen.

## What was deleted

No event-day book module. Budget and MPC dates remain calendar items in `ops` for *avoiding*
operational surprises, not for positioning.
