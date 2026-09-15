# STOP — Book Q (GL2 composition note)

Date: 2026-09-14
Closed at: GL2
Author: quant-ai-developer

## What was claimed

W0 records CSPX + XUSE (70/30) as the chosen pair and VWRA as the permitted single-line substitute. They are not the same portfolio. XUSE tracks MSCI World ex USA — developed only, no EM. VWRA tracks FTSE All-World, EM ~10% (working). The choice decides whether the USD book holds emerging markets, and whether it holds India at ~1.1% of book. Book Q's deliverable is a number and a disclosure, not a trade. Instrument: none. Horizon: one-shot, before the wrapper migration. Universe: the two candidate UCITS lines already locked in W0. Pre-registered E_net: n/a — nothing statistical.

## What was measured

Nothing was measured statistically; the book closed on two public documents and arithmetic, at $0, before any data SKU.

- **XUSE.** PRIIPs KID dated **09 April 2026**. Instrument name from the document: **iShares MSCI World ex-USA UCITS ETF (the “Fund”), USD Accu (the "Share Class")**, ISIN **IE000R4ZNTN3**. Index: **MSCI World ex USA Index**. Universe: “large and mid-capitalisation stocks across **developed market countries excluding the United States**.” EM: **none**.
- **VWRA.** UCITS KIID accurate as at **28/07/2026**. Instrument name from the document: **Vanguard FTSE All-World UCITS ETF (the "Fund")**, **(USD) Accumulating Shares**, ISIN **IE00BK5BQT80**. Index: **FTSE All-World Index**. Universe: “large and mid-sized company stocks in **developed and emerging markets**.” EM: **present, ~10% (working)**.
- **India weight (G13).** ~11.01% of MSCI EM (justETF, Aug 2026, working) × EM ~10% of a global index → **~1.1% of the USD book ≈ $3,900 ≈ ₹3.7 lakh** at the marked $354,097. Written as the household payload in `docs/archive/gl2-core-composition.md` §4. `household` does not exist yet (GL1).
- **Trade-off, both numbers, no recommendation.** Pair fee advantage **3.31 bps/yr** ($117/yr ≈ ₹11,000/yr) versus **one extra Schedule FA line** under a **₹10 lakh/yr** s.43 regime (working) versus holding versus not holding **~10% of world market capitalisation**. Fee axis favours the pair; disclosure axis favours the single line; composition axis is not a cost question.

This programme does not choose the composition.

## Why it closed

Book Q's kill: closes the moment the two KIIDs are read and the India weight is in the ledger. That happened on 2026-09-14. It is a disclosure, not a trade.

The investor dated **stocks US/intl 60/40** on **2026-09-14**, then dated the vehicle **CSUS+VXUA 60/40** the same day (§5 of the GL2 document). That names the composition. GL-H7 does not apply to the core vehicle — it is composition. Bonds US/intl **70/30** currently sit in a **US IRA** (tax-free, **working**), outside this book's taxable brokerage; the GL-H11 bond mix is **not** a sleeve instruction for the taxable book. Optional sleeves stay at weight **0**.

Not a tax conclusion. W1 still gates the wrapper trade.

## What would re-open it

A specific, checkable change — not “more research”:

- Blueprint §13 trigger 7: **an EM ex-India UCITS launches**, so the India double-count becomes removable by substitution rather than only measurable.
- Blueprint §13 trigger 3: **W1 returns that no custodian will hold Irish UCITS** — Books K, Q and S close with the core; this disclosure survives as a historical record.
- The investor and the alien desk **date a named configuration**. **Filled 2026-09-14: `CSUS+VXUA 60/40`.** That filled §5 of the GL2 document. It did not reopen Book Q.

A later agent must not treat W0's CSPX+XUSE as the GL2 vehicle, and must not let the migration run on a different composition than §5.

## What was deleted

**No code was removed.** No module was created. No runtime book existed. No registry entry was deleted. Optional sleeves stay at weight 0. The standalone EM line (IE00B4L5YC18) was not added as a sleeve.

Artefacts written, not deleted: `docs/archive/gl2-core-composition.md` (the disclosure) and this memo.

---

*Shape: India STOP memo template in [india-equity-execution-plan.md](india-equity-execution-plan.md), plus the global rule that a closed book states whether code was removed. Authority: [global-equity-execution-plan.md](../next/global-equity-execution-plan.md) GL2.*
