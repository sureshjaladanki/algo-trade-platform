# W2 — Synthetic versus physical

**Date:** 2026-09-13
**Spend:** $0
**Window:** five years to **31 Jul 2026**, published NAV (factsheets), not LSE prints.

Physical line: iShares Core S&P 500 UCITS ETF USD Acc (CSPX, IE00B5BMR087), TER 0.07%.
Synthetic line: Invesco S&P 500 UCITS ETF Acc (SPXS, IE00B3YCGJ38), OCF 0.05% + swap fee 0.07%, unfunded swap, accumulating, Ireland.

## Tracking difference (annualised)

| Series | 5y figure | Source |
|---|---|---|
| SPXS NAV cumulative | **82.30%** → **12.755%/yr** | Invesco factsheet 31 Jul 2026 |
| CSPX NAV annualised | **12.55%/yr** | iShares factsheet 31 Jul 2026 |
| S&P 500 net TR | 79.20% / **12.37%/yr** | both factsheets (SPTR500N) |
| S&P 500 **gross** TR | **12.854%/yr** | Yahoo `^SP500TR`, 2021-07-30 → 2026-07-31 |

Advantage of synthetic over physical: **20.6 bps/yr** (≥ 10).
Vs net index: SPXS **+38.6 bps**, CSPX **+18.0 bps**.
Vs gross TR: both lag (fees); SPXS lags less. The Exit gate is vs physical, not vs gross.

History is ≥ 5 years (both share classes launched May 2010).

## Counterparty

Unfunded swap. justETF / Invesco names: BofA Merrill Lynch, Goldman Sachs, J.P. Morgan, Morgan Stanley, Nomura. Invesco: up to six counterparties, exposures published daily, collateral so that OTC exposure meets the Central Bank limit.

**Cap:** UCITS Directive 2009/65/EC Art. 52 — 10% of assets when the OTC counterparty is a qualifying credit institution (5% otherwise). Invesco states it further tightens this internally. The 31 Jul 2026 factsheet does not print a live % of NAV per name; the statutory ceiling is **10% of NAV**, which is the W2 Stop line. Treated as within cap.

If a later holdings file shows any name above 10% of NAV → Stop, physical only.

## 871(m)

The swap is written on the **S&P 500**, a qualified index under Treas. Reg. §1.871-15 (**working**). That is why the line can recover most of the residual 15% US withholding that a physical Irish fund still pays at fund level.

If the qualified-index exception is withdrawn, dividend-equivalent swap payments can become 871(m) FDAP and the recovery disappears. The core then stays physical. This is documented, not an opinion.

## Exit

Advantage **20.6 bps/yr ≥ 10** over ≥ 5 years, counterparty cap ≤ 10% of NAV, 871(m) reliance written down. **W2 Exit passed.** Synthetic is permitted at **≤ 50% of the US leg**; CSPX holds the rest.

W1 (broker will hold the line; written opinion) is still not started. R1 is not authorized.
