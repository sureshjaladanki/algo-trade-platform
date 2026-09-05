# STOP — Index reconstitution / passive flow

Date: 2026-09-05
Closed at: H0
Author: agent

## What was claimed

Capture index reconstitution / passive-flow pressure around Nifty adds and deletes. Passive AUM is
growing (NIFTYBEES ₹66,777 crore; SBI Nifty 50 ETF ~₹2.16 lakh crore, working). Hypothesised E_net
**~0.4%/yr**.

## What was measured

**Nothing was measured; the book closed on arithmetic before any data access.**

Effective n ≈ **40** rebalances, σ = **4%/event**, MDE = **1.77%/event ≈ 3.5%/yr**. ½ E_net = **0.2%/yr**.
**Fails H4 by 8.9×.** Specs used 0 of 5.

## Why it closed

**H4.** 1.77%/event against ~0.4%/yr net. Rank was already lowest among ₹0 screens; the gate fails
before a screen is run. U0 membership is a 2026-09-05 Nifty 50 + Next 50 snapshot plus STER-out
2013-08-27 — not a reconstitution event book.

## What would re-open it

A free, complete PIT reconstitution history whose implementable event sleeve has 2.80 σ/√n ≤ 0.2%/yr
at the then-available n, after cost and tax. Buying a membership vendor to *look* is not a reopen
(L8).

## What was deleted

No reconstitution book module.
