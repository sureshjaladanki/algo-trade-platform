# STOP — Book R (results-season drift)

Date: 2026-09-05
Closed at: H0
Author: agent

## What was claimed

Quarterly seasonal-random-walk SUE from exchange-filed results predicts a 3-month drift in Nifty
names, following *Theoretical Economics Letters* (2018). Instrument: cash delivery, long-only.
Universe in this desk: U0 Nifty 50 + Next 50 (blueprint named Nifty 200). Pre-registered E_net
**1.9%/yr** net of cost and tax. See `docs/next/h0-prereg-book-r.md`.

## What was measured

**Nothing was measured; the book closed on arithmetic before any data access.**

n = 15 sleeve-years, σ_ann = 10%, T = 15 yr, MDE_ann = **7.23%/yr**, ½ E_net = **0.95%**, specs used
0 of 5.

The anomaly's existence in the Indian literature is **not** in dispute: *Theoretical Economics
Letters* (2018), Nifty 500, 2002–2017, statistically significant 64-day drift, robust to beta, market
cap, P/B, illiquidity and idiosyncratic volatility, and to sub-periods.

## Why it closed

**H4.** Implementable MDE 7.23%/yr against ½ × 1.9% = 0.95% — **fails 7.6×.** Retail
implementability is the question, not existence.

India has **no free point-in-time consensus-estimate dataset**, so surprise would have been
seasonal-random-walk SUE from NSE/BSE filings. `ai.extract` — the desk's only legitimate AI use for
filings — **dies with this book.** An extraction module cannot rescue a sleeve whose MDE is four
times its hypothesised gross effect. L10 still forbids any model output entering a size.

## What would re-open it

A structural change that cuts sleeve σ against the Nifty 50 TRI enough that 2.80 σ/√T ≤ 0.95% at the
then-available T, **and** a free Indian PIT consensus dataset (which would still not, on today's σ
and T, clear H4). Not "a better SUE".

## What was deleted

No `src/books/r.py`. No `src/ai/extract.py`. Neither will be added while this memo stands.
