# B0 — $0 listed PEAD screen

**Date:** 2026-08-21
**Spec:** `B.public-listed-pead`
**Spend:** $0 (EDGAR 8-K dates + Yahoo bars on names that still trade)
**Not B1.** Survivorship can only help a long-only drift. A miss kills Polygon spend. A hit is permission to buy a delisted PIT panel.

MDE printed first: n=17143, n_eff=3428.6, MDE=38.3 bps.

| | |
|---|---|
| Mid-cap events ($20–100M ADV at event) | 17143 |
| Mean net-of-cost 20-day drift | **80.9 bps** |
| Kill threshold | 40 bps |
| Working cost | mid-cap all-in high from `src.costs` (25 bps) |
| Universe | Current S&P 400 listed names, 2010–2026 |
| Gate | **buy Polygon PIT panel** |

Long-only: positive announcement-window return only. Forward window starts at t+1. Events are all 8-Ks, not Item 2.02 only, so non-earnings filings dilute the mean toward zero. This is not a PIT panel (delisted names are missing).

