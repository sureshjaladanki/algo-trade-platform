# GL0 — Cliff, settlement and session calendar

| | |
|---|---|
| **Date** | 2026-09-14 |
| **Spend** | $0 |
| **Status** | **Exit passed.** March-2028 receipt dates are derived. Alien R1 may be dated against this file. |
| **Book T** | `src/settlement.py` plus this artefact. No `src/books/cliff.py`. |
| **Taxpayer cliff** | Consumed from [residency-calendar.md](../residency-calendar.md). Not redefined here. |

This file is handed to the alien desk **in writing** as an input to **R1**. This programme does not place the step-up. W1 written opinion and custodian LSE access remain R1 dependencies, not tax conclusions of this milestone.

---

## Decision for R1

| Item | Working fact |
|---|---|
| RNOR cliff | **31 Mar 2028 (Friday)** |
| ROR from | **1 Apr 2028** |
| Latest safe trade date (GS1) | **17 Mar 2028 (Friday)** — 14 calendar days of margin |
| Settlement cycle in force at the cliff | LSE **T+1** if the 11 Oct 2027 switch holds; **T+2** if it slips. **17 Mar 2028 works under both.** |
| 30 Mar 2028 LSE at T+2 | Receipt **3 Apr 2028** — **straddles** the cliff. R1 must not arm that date. |
| Sell-to-repurchase gap (GS2) | **≤ 5 business days**. Hygiene against FEMA Reg 7 (G2) and market risk. Not a legal conclusion. |
| Receipt location (N6) | US account. No override. |
| US-situs cap (N5) | **$60,000**. Unchanged. |

A 17 Mar 2028 LSE trade at T+2 receipts on **21 Mar 2028**, inside FY 2027–28. At T+1 it receipts on **20 Mar 2028**. Both are ≥ 14 calendar days of trade-date margin before the cliff.

---

## Settlement cycle (G20)

| Venue | Cycle | Source |
|---|---|---|
| India (NSE) | **T+1** | In force |
| US | **T+1** | In force (May 2024) |
| LSE | **T+2**, switch to **T+1** targeted **11 Oct 2027 (working)** | UK draft SI (Nov 2025); EU CSDR amendment; CH aligned. Tagged working until the day occurs |

Code: `src/settlement.py` `receipt_date`. `straddles_cliff` checks LSE at **T+2** while the switch date is working, so R1 cannot arm on an assumed T+1.

---

## March 2028 holidays and BST (G20, G21)

| Fact | Date | Tag |
|---|---|---|
| US EDT start (2nd Sunday of March) | **12 Mar 2028** | Computed |
| DST-gap weeks (windows start **13:30** London) | **12–25 Mar 2028** (and last Sunday Oct–first Sunday Nov) | G21, GS9 |
| UK BST start (last Sunday of March) | **26 Mar 2028** | Computed; matches G20 |
| 29–31 Mar 2028 overlap | Normal **14:30–16:30** London | After BST |
| LSE Good Friday / Easter Monday 2028 | **14 Apr / 17 Apr 2028** | LSE business-days calendar |
| **Final week of March 2028 (27–31)** | **No LSE holiday. No NSE holiday** on the table below | NSE 2028 circular not yet published — **(working)**; Holi is **Sat 11 Mar 2028**; next weekday NSE holiday on the working table is Ram Navami **4 Apr 2028** |

17 Mar 2028 and 30 Mar 2028 are LSE and NSE business days. Easter 2028 does not sit in the cliff week, so a T+2 receipt from 30 Mar 2028 is **Monday 3 Apr 2028**, not delayed by a holiday.

---

## Session windows (GS9, G21)

| Exposure class | London window | DST-gap start |
|---|---|---|
| US-exposure (CSPX; US sleeve of VWRA) | **14:30–16:20** | **13:30** |
| Ex-US developed (XUSE) | **14:30–15:30** | **13:30** |

Enforced in `src/execute.py` as a refusal. Logged, reasoned override only. **GL-H3 cliff margin outranks the window** on the latest safe trade date. N6 and N5 outrank everything and have **no override**.

listing-basis and session-overlap arbitrage is closed as measured and negative — a 2–6 bps gap against an 8–15 bps round trip, with a comfortable MDE. This file retains the overlap as an execution rule, not as alpha.

---

## Venue-fee arithmetic (G14 GL0 rows, GS6)

G14 working: added-venue market data ≈ **$30/month** for three venues; IBKR spot FX ~0.2 bps with a **$2** minimum. Own-fill spread measurement is **GL5** (G22).

| Book size | $360/yr as bps |
|---|---|
| $25,000 floor | **144 bps** |
| Marked book $354,097 | **10.2 bps** |
| $500,000 | **7.2 bps** |

GL-H4 is judged at the **$25,000 floor**. No new venue bucket is authorized. USD-line FX is **0 bps** (`src/costs.py`). LSE round-trip stays on the wrapper module, not in `ProductBucket`.

---

## Register items this milestone records

Numbers below are consumed from [global-financial-market-analysis.md](global-financial-market-analysis.md) Appendix A. Unsourced facts stay **(working)**. This is not a W1 opinion and not a composition choice (CSPX+XUSE vs VWRA is **GL2**).

| # | Recorded |
|---|---|
| **G8** | UK IHT nil-rate band **£325,000**, **40%** above **(working)**. UK-situs = UK register. Irish-incorporated LSE-listed shares sit outside it. `uk_register = true` is a refusal in `src/situs.py`. |
| **G9** | Local transaction taxes **(working)**: UK SDRT **0.5%**; HK stamp **0.1%/side**; CH **0.15/0.30%**; FR **0.3%**; IT **0.1%**; ES **0.2%**; SG scripless nil. |
| **G10** | Treaty dividend WHT for an Indian resident **(working)**: JP 10%, DE 10%, FR 10%, NL 10%, CH 10% after reclaim from 35%, AU 15%, CA 15%, UK 0%, HK/SG 0%. Dead cost during RNOR if received outside India. |
| **G11** | Luxembourg *taxe d'abonnement* **0.05%**, **passive ETFs exempt**; Circular L.G.-A. 61 (24 Dec 2024) lists the USA as no-CoTR for SICAV/SICAF. Sourced. Ireland vs Lux on the US leg is the treaty, not the subscription tax. |
| **G14** | Venue-fee rows above. FX ~0.2 bps / $2 min **(working)**. |
| **G18** | Gold ~**$4,000/oz** and ~**₹1,10,000/10g** in 2026 **(working)**; MGC 10oz ≈ **$40,000**; MCX Gold Mini 100g ≈ **₹11 lakh**. Indivisibility; products stay closed. |
| **G19** | USD/INR 1-year forward points ≈ **200 bps/yr** by covered parity **(working)**. Hedge remains closed. |
| **G20** | Cycle, holidays, BST, T+1 date — this file and `src/settlement.py`. |
| **G21** | DST-gap weeks; 13:30 London start — this file and `session_window`. |
| **G23** | σ_ann and T inputs, published below before any peek (N3). |
| **G25** | Offshore portfolio bond / unit-linked wrapper all-in **100–150 bps/yr (working)**; s.10(10D) unavailable for a foreign insurer. Closed. |
| **G26** | Whether an Indian resident may acquire GDRs of Indian companies in the secondary market under FEMA remains **(working)**. Product is closed on three grounds regardless (Reg S/144A clips, conversion headroom, FX-plus-conversion gap). |

G12 and G13 (index tracking / India weight) are **GL2**, not this file.

### G23 — σ_ann and T (working)

`MDE_ann = 2.80 σ_ann / √T`. Owner: GL0. No peek.

| Candidate | σ_ann active | T usable |
|---|---|---|
| Country selection / regional tilt | 6.0% | 40 yr |
| Cross-country momentum | 9.0% | 40 yr |
| Cross-country value | 8.0% | 40 yr |
| G10 FX carry | 10.0% | 40 yr |
| Global term-premium timing | 6.0% | 40 yr |
| Global credit-spread carry | 5.0% | 30 yr |
| Commodity roll / carry | 16.0% | 30 yr |
| Dollar / currency trend | 8.0% | 40 yr |
| Listing-basis / session overlap | 40 bps/event | 1,250 events |

---

## Idle offshore cash (GS7)

Alert **120** days, limit **180** days. `src/ops.py`. Satisfied by directly held T-bills during RNOR. Operational reading of G2; W1 confirms whether Reg 7 reaches s.6(4) assets.

---

## What R1 still needs that this file is not

- W1 written cross-border opinion (already authorized on the alien desk). Scope includes the custodian’s ability to deal LSE. **If the custodian cannot, an account transfer precedes R1.**
- Placement of the step-up. Alien-owned under that plan’s Lock 7.
