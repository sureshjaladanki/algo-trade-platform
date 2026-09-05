# P1 — Packaged versus self-run

Date: 2026-09-05
Milestone: P1
Pre-registration: [h0-prereg-book-p.md](h0-prereg-book-p.md)

**Verdict: invalid comparison — default to the packaged vehicle.** STOP memo:
[p1-stop.md](../archive/p1-stop.md). Book M: [book-m-stop.md](../archive/book-m-stop.md).

The ±100 bps bands and the after-tax functions exist in `src/books/packaged.py`. They were not
applied to live NSE TRI because a self-run replication on Nifty 50 + Next 50 cannot be reconciled
to Nifty 200 Momentum 30 (or the other factor indices) within 50 bps/yr before costs.

Recommended sleeve until P1 reopens: a **direct-plan** Nifty 200 Momentum 30 / Nifty 500 Momentum 50
index fund or ETF at the published ~0.30–0.34% TER, weight ≤ 40% of equity (active sleeve cap),
annual or semi-annual cadence set by the fund. No self-run book.
