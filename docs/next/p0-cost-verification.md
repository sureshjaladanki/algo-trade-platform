# P0 — Cost and tax verification

Date: 2026-09-05
Milestone: P0
Substitution: **no live contract notes**. Reference is the Zerodha published charges page and brokerage calculator ([zerodha.com/charges](https://zerodha.com/charges/#tab-equities)), plus a hand-worked Tax Year 2026-27 computation. Residuals are in rupees. H1 requires ≤ ₹1 per trade.

Exchange transaction rates in `src/costs.py` are the Zerodha published figures as of 2026-09-05 (NSE cash 0.00307%, NSE futures 0.00183%, NSE options 0.03553% of premium). Those sit at the upper end of the NSE ranges in the blueprint (0.00297–0.00307% cash, 0.00173–0.00183% futures). GST is 18% of (brokerage + exchange + SEBI), matching Zerodha; not on STT, stamp, or IPFT.

STT from 1 April 2026: Finance Act, 2026 (Presidential assent 30 March 2026); NSE member circulars restating sale of futures 0.05%, sale of options 0.15% of premium, exercise 0.15% of intrinsic (purchaser). Delivery 0.10% both legs and equity-oriented fund units 0.001% sell-only are unchanged.

## 1. Cash equity delivery — ₹1,00,000 NSE, 1 ISIN sold

| Line | Zerodha schedule | `costs` |
|---|---|---|
| STT 0.10% buy + sell | ₹200.00 | ₹200.00 |
| Stamp 0.015% buy | ₹15.00 | ₹15.00 |
| Exchange 0.00307% × 2 | ₹6.14 | ₹6.14 |
| SEBI ₹10/crore × 2 | ₹0.20 | ₹0.20 |
| IPFT 0.0001% × 2 | ₹0.20 | ₹0.20 |
| Brokerage | ₹0 | ₹0.00 |
| GST 18% on (0 + 6.14 + 0.20) | ₹1.14 | ₹1.14 |
| DP (1 ISIN) | ₹15.34 | ₹15.34 |
| **Total** | **₹238.02** | **₹238.02** |
| Residual | | **₹0.00** |

Blueprint §2.2 used NSE cash 0.00297% and totalled ₹237.82. Residual to that worked example: ₹0.20, inside ₹1.

## 2. ETF delivery (NIFTYBEES class) — ₹1,00,000 NSE, 1 ISIN sold

Same stack as delivery except STT sell 0.001%, STT buy nil.

| Line | `costs` |
|---|---|
| STT | ₹1.00 |
| Stamp | ₹15.00 |
| Exchange | ₹6.14 |
| SEBI | ₹0.20 |
| IPFT | ₹0.20 |
| Brokerage | ₹0.00 |
| GST | ₹1.14 |
| DP | ₹15.34 |
| **Total** | **₹39.02** |
| Residual vs blueprint ₹38.82 | **₹0.20** |

## 3. Cash equity intraday — ₹1,00,000 NSE, 2 orders

| Line | `costs` |
|---|---|
| STT 0.025% sell | ₹25.00 |
| Stamp 0.003% buy | ₹3.00 |
| Exchange | ₹6.14 |
| SEBI | ₹0.20 |
| IPFT | ₹0.20 |
| Brokerage ₹20 × 2 (floor binds; 0.03% would be ₹30/order) | ₹40.00 |
| GST 18% on (40 + 6.14 + 0.20) | ₹8.34 |
| DP | ₹0.00 |
| **Total** | **₹82.88** |

STT is tagged deductible (`BookKind.SPECULATIVE`).

## 4. Index futures — 1 Nifty lot, notional ₹15,52,000 (65 × 23,877)

| Line | `costs` | Blueprint §2.3 (0.00173% exchange, GST on IPFT) |
|---|---|---|
| STT 0.05% sell | ₹776.00 | ₹776.00 |
| Stamp 0.002% buy | ₹31.04 | ₹31.04 |
| Exchange | ₹56.80 | ₹53.70 |
| SEBI | ₹3.10 | ₹3.10 |
| IPFT | ₹15.52 | ₹15.52 |
| Brokerage ₹20 × 2 | ₹40.00 | ₹40.00 |
| GST | ₹17.98 | ₹20.22 |
| **Total** | **₹940.44** | ₹939.58 |
| Residual vs blueprint | | **₹0.86** |
| Residual vs Zerodha schedule | | **₹0.00** (this *is* the schedule) |

## 5. Index options — Nifty weekly ATM straddle, 1 lot

Sell 90 points × 2 legs × 65 = ₹5,850 per sell order, two sells. Buy back 45 points × 2 × 65 = ₹2,925 per buy order, two buys. Four orders.

| Line | `costs` | Blueprint §2.4 |
|---|---|---|
| STT 0.15% of premium sold | ₹17.56 | ₹17.55 |
| Exchange 0.03553% of premium traded | ₹6.24 | ₹6.24 |
| Stamp 0.003% on buy premium | ₹0.18 | ₹0.18 |
| SEBI | ₹0.02 | ₹0.11 SEBI+IPFT combined |
| IPFT | ₹0.08 | |
| Brokerage ₹20 × 4 | ₹80.00 | ₹80.00 |
| GST | ₹15.53 | ₹15.54 |
| **Total** | **₹119.61** | ₹119.62 |
| Residual | | **₹0.01** |

## 6. Exercised index option

Intrinsic 200 Nifty points × 65 × 1 lot = ₹13,000. Exercise STT = 0.15% × ₹13,000 = **₹19.50** (`costs.stt`, purchaser).

`exercise_or_square_off(200, 65, 1)` → **exercise** (₹19.50 vs square-off ₹23.60 of one ₹20 options order + GST).

`exercise_or_square_off(1000, 65, 1)` → **square_off** (exercise STT ₹97.50 vs ₹23.60). Matches blueprint §1.8.

## 7. Hand-worked Tax Year 2026-27 (`tax`)

Tax Year 2026-27 = 1 April 2026 – 31 March 2027 (`tax_year`). New-regime slabs s.202. Cess 4%. No surcharge (book below ₹50 lakh of income). Capital-gains surcharge cap 15% is encoded but unused here.

| Leg | Facts | Computation | `tax` |
|---|---|---|---|
| Delivery held 14 months | Acquired 1 Apr 2025, sold 1 Jun 2026, gain ₹2,00,000 | s.198: (2,00,000 − 1,25,000) × 12.5% × 1.04 | **₹9,750.00** |
| Delivery held 5 months | Acquired 1 Oct 2026, sold 1 Mar 2027, gain ₹80,000 | s.196: 80,000 × 20% × 1.04, no exemption | **₹16,640.00** |
| Intraday equity | Loss ₹40,000 | s.66 speculative; not offsettable against CG or F&O; carry **4** years | tax ₹0.00, carry ₹40,000 through TY 2030-31 |
| Index F&O | Loss ₹1,20,000 | s.66 non-speculative; carry **8** years | tax ₹0.00, carry ₹1,20,000 through TY 2034-35 |
| **Capital-gains tax due** | | 9,750 + 16,640 | **₹26,390.00** |

Residual versus the hand-worked sheet: **₹0.00**. Ledgers are separate: a later F&O profit does not consume the speculative carry.

Audit turnover (W10): absolute sum of P&L plus option premium sold unless the premium is already inside the broker P&L. Flags at ₹1 crore and ₹10 crore.

## H1

Both legs of H1 are met under the stated substitution. Re-verify against a live contract note at L0.
