# STOP — Book S (GL4, non-US synthetic)

Date: 2026-09-14
Closed at: GL4
Author: quant-ai-developer

## What was claimed

W2 passed synthetic over physical at **20.6 bps/yr** on the S&P 500 leg, recovering residual 15% US WHT through a swap on a qualified index outside IRC 871(m). For World ex-USA, EM and bond legs that mechanism does not exist. Working expectation (G24): **5–15 bps/yr**, often below W2's unchanged gate of **10 bps/yr over ≥ 5 years** and every counterparty **≤ 10% of NAV**. Pre-registered: a STOP is a completed milestone; physical only.

## What was measured

Window: five years to **31 Jul 2026**, published NAV (factsheets), not LSE prints. Same asof as W2. $0.

**World ex-USA (honest pair to XUSE).** No listed synthetic UCITS. justETF's MSCI World ex USA list (as of 13 Sep 2026) has eight lines, all physical (full replication or sampling). Physical lock: iShares MSCI World ex-USA UCITS ETF USD Acc (**XUSE**, IE000R4ZNTN3), TER 0.15%, launched **24 Jan 2025**. History to 31 Jul 2026 is **~1.5 years < 5**. Cannot pass.

**EM (the ≥5y published NAV pair at $0).**
| Series | 5y figure | Source |
|---|---|---|
| MXFS NAV cumulative | **45.08%** → **7.73%/yr** | Invesco factsheet 31 Jul 2026, IE00B3DWVS88, OCF 0.09% + swap 0.00%, unfunded |
| IEMA NAV annualised | **8.04%/yr** | iShares factsheet 31 Jul 2026, IE00B4L5YC18, TER 0.18%, physical |
| MSCI EM net TR | 47.11% / **8.03%/yr** | Invesco cumulative / iShares printed (NDUEEGF) |
| MSCI EM **gross** TR | **8.52%/yr** | MSCI USD gross factsheet, 31 Jul 2026. Yahoo `^652800-USD-GRTR` is a stub (no 5y series) |

Advantage of synthetic over physical: **−31.2 bps/yr** (below 10; synthetic lags). Vs net: MXFS **−30 bps**, IEMA **+1 bp**. Vs gross: both lag; MXFS lags more. History ≥ 5 years (MXFS launched 26 Apr 2010; IEMA 25 Sep 2009).

**Bond.** No ≥5y Irish/Luxembourg accumulating **USD** synthetic vs physical pair found at $0. Listed USD Treasury accumulating UCITS are physical. Not measured; cannot pass.

**Counterparty (MXFS).** Unfunded swap. justETF / Invesco names: BofA Merrill Lynch, Goldman Sachs, J.P. Morgan, Morgan Stanley, Nomura. Latest holdings: Invesco Markets plc annual report **30 Nov 2025**. Swap MTM (UCITS Art. 52 metric): J.P. Morgan **3.60% of NAV**, Goldman Sachs 0.71%, Morgan Stanley 0.01%. All ≤ 10%. The 31 Jul 2026 factsheet does not print a live % of NAV per name; the live print is the annual report, not an invented 9% figure. Cap holds. Stop is the tracking gate, not concentration.

W2 US leg is untouched: advantage **20.6 bps/yr**, `w2_passes() is True`, synthetic US leg cap 50%.

## Why it closed

W2's gate, unchanged: **< 10 bps/yr** measured advantage over ≥ 5 years → physical only. EM printed **−31.2 bps/yr**. World ex-USA has no synthetic line and <5y physical history. Bond has no ≥5y pair. Counterparty cap did not bind.

G24's 5–15 bps working band was the right side of the gate; the measured EM line is worse than that band. IRC 871(m) is not the reason and is not claimed for non-US underlyings.

listing-basis and session-overlap arbitrage is closed as measured and negative — a 2–6 bps gap against an 8–15 bps round trip, with a comfortable MDE. That is a measured negative, not an unmeasurable maybe, and a later agent must not reopen it as one.

## What would re-open it

A listed synthetic **MSCI World ex-USA** (or matching EM) accumulating USD UCITS with **≥ 5 years** published NAV, advantage **≥ 10 bps/yr** vs the physical equivalent, **and** every counterparty **≤ 10% of NAV** on a live holdings print. Launch of a World ex-USA swap line is not enough; it still has to clear the gate. An 871(m) change does not reopen this. Not "more research".

## What was deleted

**Nothing.** The GL4 extension stays in `src/books/synthetic.py` and `tests/test_synthetic.py` as a measured-fail record so G24 cannot be reopened as an unmeasured maybe. No module was added; none is removed. No registry entry was created. A closed global book that leaves a *new* module behind is how a join layer becomes a third desk — this closure did not add a module, so there is none to delete. W2's US-leg functions, `SYNTHETIC_ADVANTAGE_HURDLE_BPS = 10.0`, and `COUNTERPARTY_CAP_NAV = 0.10` are unchanged.
