# $0 feasibility screens — Books C, A, B

**Date:** 2026-08-21  
**Spend:** $0 (Yahoo, EDGAR, Wikipedia, working `costs` / `tax`). No CBOE, Polygon, IBKR, or fills.

These are go/no-go screens for *whether to spend later*. They are not the plan’s certified exits. Run with `poetry run python -m src.screens`.

| Book | $0 result | Next spend if you continue |
|---|---|---|
| **C** | **Feasible.** C1 **35.5 bps/yr** vs static VTI, 0 modelled washes (hurdle 25). | C2 needs a funded year and a 1099-B — an audit, not a data purchase. |
| **A** | **Do not skip CBOE.** Mean VIX–RV net of expensive-end SPX cost **2.91 vol points**, sign stable in 5/5 sub-periods (n=259). | A1/A2 need CBOE SPX EOD. PUTW Yahoo history is dead; packaged path used CBOE PUT. After-tax PUT 5.1% vs VTI 15.2% in 2016–2026 — the 1256 wedge is ~98 bps, not a VTI-beater by itself. |
| **B** | **Do not skip Polygon.** Listed S&P 400, $20–100M ADV, long-only 20-day net drift **80.9 bps** (kill 40) on 17,143 events. MDE printed first (ratio 0.38). | B1 needs a delisted PIT panel. This screen can only kill; a hit is survivorship-biased. |

## What this does *not* certify

| Still blocked | Why |
|---|---|
| C2 | Funded IBKR year + 1099-B |
| A1 / A2 | CBOE SPX EOD (20–25Δ, 30–45 DTE put-spread) |
| A3 | IBKR paper (free) after A1 |
| B1 | Polygon delisted PIT panel |
| B3 | IBKR paper (free) after B1 |

Detail: [c1-tax-location-proof.md](c1-tax-location-proof.md), [a0-public-vrp-screen.md](a0-public-vrp-screen.md), [b0-public-pead-screen.md](b0-public-pead-screen.md).
