# Architect review — Book F unblock

**Reviewer:** Claude Opus, AI Architect (Indian equity / NSE reconstitution).  
**Date:** 2026-08-19. **Standing:** Decisive. Supersedes the F1b memo sentence that blocked a pre-announcement residual until F1a/F2 passed.

Input pack: [forced-flow-status.md](../next/forced-flow-status.md).  
Applied as [blueprint Rev 3](../next/forced-flow-architecture-blueprint.md) and [execution plan](../next/forced-flow-execution-plan.md).  
Next peek charter: [f3-residual-charter.md](../next/f3-residual-charter.md).

---

## Programme verdict

Book F's public leg is closed. Announcement-to-effective Nifty 50 flow is INCONCLUSIVE on existence and FAIL on economics: the addition sleeve centres at +26 to +52 basis points against a 45 basis point delivery round trip and 20.8% short-term tax, and the harness that measured it had an MDE of 323 basis points against a required effect of roughly 300 — meaning an effect large enough to be a product would have been seen. Trackers print at the effective close and professionals express the same view in single-stock futures at a quarter of our friction; a retail cash book is the worst-positioned participant in that window and should not be in it. What survives is the private leg: prints put roughly three quarters of the addition move between the January cut-off and the press release, and the mechanical Next 50 rank predicts additions out of sample at a 66.7% top-k hit rate against a 4.1% naive baseline (PASS). That leg has never been measured with an ex-ante label, so it is measured once — a fixed top-3, equal-weight, cash-only basket held from the first session of February/August to the session after the announcement, benchmarked against Next-50 ranks 21–50, with a 300 basis point economic hurdle and a 448 basis point MDE published before the peek, and with INCONCLUSIVE pre-registered as terminal because no further Nifty 50 events exist. In parallel Book G opens, which is the only book on this desk where statistical power exceeds the effect by an order of magnitude. Book F taught the mirror of the cascade's lesson: the cascade failed because friction exceeded the effect across thousands of decisions, and Book F failed because measurement error exceeded the effect across tens.

---

## Diagnosis (summary)

- F1/F1a INCONCLUSIVE is not a licence to keep spending on the public window. MDE ≈ required product-sized effect (~300 bps gross). The centre (+26 / +52 bps) cannot clear 45 bps delivery. Close C1 on economics.
- T−20 sits inside the announcement window (NSE gives ≥ four weeks' notice). F1-effective is a subset of F1a — two peeks, one window.
- T−40→T−20 on *actual* additions (+538 bps) vs announce→T (+52 bps) implies most of the move is pre-PR. That companion is locked (look-ahead labels). F3-RESIDUAL tests whether a *predicted* basket earns it.
- Sequencing error: ranking PASS was blocked behind an unpassable public residual. Rev 3 unblocks C2.

Indian-market notes retained in Rev 3: F&O is a Nifty 50 inclusion field (omit for now — conservative dilution); announcement window is professionally crowded; Next 50 offset muddles deletions; capacity is not binding at ₹25L–₹1Cr; rank hit rate already cooler in 2020–25 (76.9% → 54.5%).

---

## Terminal rule for the outstanding peek

Written into the F3-RESIDUAL charter before any run:

- **GO** — point ≥ 450 bps **and** CI lower bound > 0 **and** both era halves positive. Opens F5, not live capital.
- **STOP** — point < 300 bps.
- **INCONCLUSIVE** — anything between, **resolves to STOP for capital.** No further Nifty 50 events exist to repair power.
