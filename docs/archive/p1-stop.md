# STOP — P1 packaged versus self-run

Date: 2026-09-05
Closed at: P1
Author: agent

## What was claimed

A packaged Indian factor index fund or ETF (Nifty 200 Momentum 30 / Nifty 500 Momentum 50 / Nifty
100 Low Volatility 30 / Nifty Alpha 50) dominates a self-run replication after cost and tax, from
published TRI, TER and exit loads, with the self-run book reconciled to that TRI within **50 bps/yr
before costs**.

## What was measured

**The replication was not built.** U0 did not assemble point-in-time Nifty 200 (or factor-index)
constituent history (`docs/archive/u0-stop.md`). The membership spine is Nifty 50 + Next 50 as of
2026-09-05 plus STER-out. A self-run Momentum 30 book on that spine cannot be reconciled to the
Nifty 200 Momentum 30 TRI within 50 bps/yr — the difference would be universe error, not cost and
tax.

No NSE Indices TRI file and no AMFI TER panel was ingested in this milestone. `src/books/packaged.py`
implements `packaged_after_tax`, `self_run_after_tax` and the ±100 bps verdict bands on synthetic
paths only.

## Why it closed

P1 exit requires a faithful replication before the cost-and-tax gap is believed. That replication
does not exist on free data already in the repo, and L8 forbids buying a PIT membership vendor to
finish the screen. Default is the packaged vehicle: conservative, defensible, and the pre-registered
tie-break when the comparison is invalid.

## What would re-open it

A free dump of (1) daily TRI for the four factor indices over ~20 years and (2) point-in-time
constituents for those indices (or Nifty 200) covering the same span, such that pre-cost tracking
error versus the published TRI is ≤ 50 bps/yr. Then re-run the three-way verdict.

## What was deleted

Nothing. `src/books/packaged.py` stays as the after-tax functions. Book M does not open; see
[book-m-stop.md](book-m-stop.md).
