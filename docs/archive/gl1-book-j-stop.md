# STOP — Book J (GL1, household join set-off)

Date: 2026-09-14
Closed at: GL1
Author: quant-ai-developer

## What was claimed

From FY 2028-29 one Indian return carries both books. A loss on one desk can shelter a gain on the other. Effect size: sheltering ₹5 lakh of gain is worth **₹65,000 to ₹1.56 lakh** (17–41 bps of combined capital, one-off, working). Instrument: a shared INR ledger plus a set-off book. Live from **1 Apr 2028**. Kill: measured value **< 25 bps of combined capital** (≈ **₹97,000** at the marked books, GS3) → fold the rule into India Book L and alien Book R and close the book. **The ledger survives.** Pre-registered: the estimate straddled the kill.

## What was measured

Working volume ₹5 lakh of foreign LTCG sheltered by an India STCL, G5 **not** applied (W1). Combined capital ₹3.89 crore. $0. No peek.

| Regime | Value | vs ₹97,000 |
|---|---|---|
| RNOR | **₹0** | below |
| ROR, 13.0% foreign long line **(governs)** | **₹65,000** (16.7 bps) | **below** |
| ROR, 31.2% foreign short sensitivity | ₹1,56,000 (40.1 bps) | above |

`household` reproduced India lots to ₹1 and alien USD lots to $0.01. A planted cross-clock error is caught. That is GL-H1; it is not Book J's kill.

## Why it closed

**GL-H2.** Measured cross-book set-off at ROR on the 24-month foreign line is **₹65,000 < ₹97,000**. Indian reason: at the marked books the 13.0% of ₹5 lakh is 16.7 bps of combined capital. The sequencing fact remains (realising in the USD book costs more per unit of gain because INR depreciation is itself taxable); it is not a hedge and not a reallocation, and it does not need a book.

## What would re-open it

A dated re-measurement of **actual** realisation volume where the ROR set-off value is **≥ ₹97,000** (25 bps of then-current combined capital), still without a G5 tax conclusion unless W1 has answered it in writing. A G5 "yes" that pulls s.198 gains into the sheltered set is not enough on its own without the volume. Not "more research".

## What was deleted

**No module deleted.** `src/household.py` is kept (Schedule FA and Form 67 need it either way). `src/books/set_off.py` is retained as the **folded rule plus the measurement record**, imported by India Book L (`src/books/ledger.py` `realisation_order`) and alien Book R (`src/books/step_up.py` `realisation_order`). It is not a live book: no orders, no capital, no registry entry. A closed global book that left a *new third desk* would be a failure; this closure did not add a venue, a broker, or a session.

The join tax surface in `src/tax.py` (INR-measured foreign gain, named FX basis, 8-year carry, no third jurisdiction) stays. It is `tax`, not Book J.

listing-basis and session-overlap arbitrage is closed as measured and negative — a 2–6 bps gap against an 8–15 bps round trip, with a comfortable MDE. That is a measured negative, not an unmeasurable maybe, and a later agent must not reopen it as one.
