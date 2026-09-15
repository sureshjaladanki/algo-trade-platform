# GL1 — Household join ledger and Book J

| | |
|---|---|
| **Date** | 2026-09-14 |
| **Spend** | $0 |
| **Status** | **GL1 exit passed. Book J STOP** — measured value below 25 bps. `household` is kept |
| **Authority** | [global-equity-execution-plan.md](../next/global-equity-execution-plan.md) GL1 · [global-equity-architecture-blueprint.md](../next/global-equity-architecture-blueprint.md) Book J |
| **Taxpayer** | [investor-profile.md](../investor-profile.md) · calendar [residency-calendar.md](../residency-calendar.md) |

This file is arithmetic, not a tax conclusion. Rule 115 / TT-rate (G4) and s.198 set-off against other-asset losses (G5) remain **W1**.

---

## 1. Can `household` reproduce both ledgers?

**Yes.** The join ledger reads India `Lot` rows and alien USD lots. It does not write a lot, adjust a basis, or file.

| Desk | Tolerance | Result |
|---|---|---|
| India (INR) | **₹1** (GS8 / GL-H1) | Reproduced |
| Alien (USD) | **$0.01** (GS8 / GL-H1) | Reproduced |

**Only the Indian book uses the India line.** The 12-month Indian clock is INR / demat / rupee. The Ireland/global book — including **CSUS+VXUA in full** — joins as `Desk.ALIEN` / `HoldingClock.FOREIGN_24M` / USD (zero FX). CSUS, VXUA, CSPX, XUSE, VWRA, VTI, VXUS are not India-line lots. A planted cross-clock tag (including tagging VXUA as `INDIA_12M`) raises `ClockContamination`.

Per-lot conversion stores **source and date**. Named bases: `rule_115_tt_buying` (G4, W1, swappable) and `yahoo_usdinr_working` (R0 stand-in). A W1 answer change is a re-run (`revalue`), not a rebuild.

---

## 2. Book J measured value vs ₹97,000 / 25 bps

Working volume from the analysis: sheltering **₹5 lakh** of gain (G27). Combined capital **₹3.89 crore** (₹3.39 crore marked USD book + ₹50 lakh India design). Kill **₹97,000** (GS3).

G5 is **not** applied (other-asset losses are not used against s.198 exempt gains).

| Regime | Bucket | Value | vs ₹97,000 | bps of ₹3.89 crore |
|---|---|---|---|---|
| **RNOR** | — | **₹0** | below | 0 |
| **ROR (governs)** | Foreign LTCG 13.0% | **₹65,000** | **below** | **16.7** |
| ROR sensitivity | Foreign STCG 31.2% | ₹1,56,000 | above | 40.1 |

**ROR governs: ₹65,000 < ₹97,000.** Book J is not a book. The 17–41 bps working band (G27) is now a measured 16.7 bps on the 24-month foreign line that this desk intends to use. The 31.2% sleeve is a sensitivity, not the governing number.

Closure was pre-registered: the ₹65,000–₹1.56 lakh estimate straddled the kill.

STOP memo: [gl1-book-j-stop.md](gl1-book-j-stop.md). The set-off **rule** (realise the INR book first) is folded into India Book L (`src/books/ledger.py`) and alien Book R (`src/books/step_up.py`). `src/books/set_off.py` is retained as that folded rule plus the measurement record — not a live book, no orders, no capital.

---

## 3. Dual reporting

Every join number is reported at RNOR and at ROR. **ROR governs.**

| Number | RNOR | ROR (governs) |
|---|---|---|
| Book J set-off value | ₹0 | ₹65,000 |
| Foreign LTCG tax on the hand-worked ₹2,80,000 INR gain | ₹0 | ₹36,400 |

Hand-worked transition (to ₹1): $10,000 @ ₹80 → $12,000 @ ₹90 = **₹2,80,000** INR-measured gain. Closed **15 Mar 2028** (FY 2027-28, RNOR, not received in India) → **₹0**. Closed **2 Apr 2028** (FY 2028-29, ROR, >24 months) → **₹36,400**. Same economics, ≤24 months → **₹87,360**. Cross-book: India STCL ₹1,00,000 against that foreign LTCG → tax **₹23,400**, value **₹13,000**. Unused foreign LTCL ₹50,000 carries **8 years** through **FY 2036-37**. No third jurisdiction.

Join tax does not use IRA, §1256, or 40/20. No IRA_RATE on join numbers. `tax` for this book stays NRA/RNOR/ROR.

---

## 4. Schedule FA and USD-line India look-through

| Line | Status |
|---|---|
| FA line register | Count of distinct alien symbols on the join ledger (GS10 shape: 1–2 core once the wrapper is chosen). Today's tests plant CSPX+XUSE = **2** as a **counterfactual** (USD-line India look-through **0**), not the live default. Live vehicle is **CSUS+VXUA 60/40** on the **USD line** (`Desk.ALIEN` / `FOREIGN_24M` / USD) |
| USD-line India look-through | **Not** an India-desk lot. Working look-through inside **CSUS+VXUA 60/40** **~1.70% / ~$6,010 / ₹5.8 lakh** (GL2, tagged **working**; VXUA holdings not yet published; Schedule FA / household concentration). Current US-listed book (VXUS) prints **~1.76% / ~$6,230 / ₹6.0 lakh**. VWRA G13 **~1.1% / ~$3,900** remains the **unchosen substitute**, not the default. GL2 vehicle **dated 2026-09-14**: **CSUS+VXUA 60/40**. **Only the Indian book uses the India line.** Bonds US/intl **70/30** sit in a **US IRA** (tax-free, **working**) outside this book's taxable brokerage — **not** a taxable-book sleeve |

---

## 5. G27 / G5

| Item | Result |
|---|---|
| **G27** | **Resolved as measurement.** Working one-off value **16.7 bps** (₹65,000) at ROR on the 13.0% foreign long line. Below 25 bps. Book J closed |
| **G5** | **Open, W1.** Whether other-asset losses set off against s.198 gains carrying the ₹1.25 lakh exemption is not answered here. Measurement does not apply that set-off |
| **G4** | **Open, W1.** Rate source and date are stored per lot |

---

*Companion: [gl0-cliff-calendar.md](gl0-cliff-calendar.md) · STOP: [gl1-book-j-stop.md](gl1-book-j-stop.md) · Product: [global-financial-market-analysis.md](global-financial-market-analysis.md) Book J, G5, G27, GS3, GS8, GS10*
