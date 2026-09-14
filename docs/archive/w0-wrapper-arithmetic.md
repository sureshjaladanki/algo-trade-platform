# W0 — Wrapper arithmetic

**Date:** 2026-09-13
**Spend:** $0
**Inputs:** published TERs / OCFs, Vanguard SEC yield, treaty withholding rates, IRC 2001(c) + NRA $13,000 unified credit
**Not in scope:** broker eligibility (W1), synthetic vs physical (W2), lot ledger (R0)

Gross equity return used as the 7.0%/yr working numerator from the blueprint. Yields convert a withholding *rate* into bps of NAV. Fund-level foreign withholding on the ex-US leg exists in both wrappers and is not counted as a saving.

## Candidate lines

| Line | Domicile | Policy | Replication | TER / OCF | US-situs | Withholding as fraction of gross income |
|---|---|---|---|---|---|---|
| VTI | US | distributing | physical | 0.03% | yes | 25% investor-level FDAP (W-8BEN) |
| VXUS | US | distributing | physical | 0.05% | yes | 25% investor-level FDAP on the RIC distribution |
| CSPX | Ireland | accumulating | physical | 0.07% | **no** | 15% Ireland–US treaty, at fund on US dividends |
| XUSE | Ireland | accumulating | physical | 0.15% | **no** | 0% investor-level; 0% US-source at fund |
| VWRA | Ireland | accumulating | physical | 0.14% OCF | **no** | 15% at fund on the US sleeve only (~61.6% of the fund) |

Sources locked in tests: VTI / VXUS prospectus TERs; CSPX 0.07% Acc Ireland; XUSE 0.15% Acc Ireland; VWRA 0.14% OCF; VTI SEC yield **1.02% as of 30 Jun 2026**; VXUS TTM yield 2.76% as of 9 Sep 2026. Irish units are the zero-situs path.

## Recurring-cost table (70/30 US / ex-US)

Measured yields (VTI SEC 1.02%, VXUS TTM 2.76%):

| | Naive US-listed (VTI + VXUS) | Irish physical acc (CSPX + XUSE) | Irish single-line acc (VWRA) |
|---|---|---|---|
| Blended TER | 3.6 bps | 9.4 bps | 14.0 bps |
| US-leg withholding | 25% → 17.85 bps | 15% at fund → 10.71 bps | 15% on US sleeve → 9.42 bps |
| Ex-US-leg **investor-level** withholding | **25% on US-source RIC distributions → 20.7 bps** | **0** | **0** |
| Total recurring wrapper cost | **42.15 bps/yr** | **20.11 bps/yr** | **23.42 bps/yr** |
| **RNOR after-tax core** | 6.58%/yr | **6.80%/yr** | 6.77%/yr |
| **ROR after-tax core** (ROR governs) | 6.48%/yr | **6.80%/yr** | 6.77%/yr |
| US estate-tax situs on the core | 100% | **0** | **0** |

Measured pair saving vs naive US-listed: **22.04 bps/yr**. VWRA saving: **18.73 bps/yr**. Both ≥ 15 bps/yr (N9).

The largest single leak on the US-listed core is the **ex-US double-withholding line** (20.7 bps/yr): VXUS already suffers foreign withholding inside the fund, then the RIC distribution is US-source FDAP withheld at 25%. The Irish ex-US line loses 0 bps at the investor.

Blueprint §0.2 working yields (US 1.3%, ex-US 2.9%) for sensitivity: US-listed total **48.1 bps**, Irish pair **23.05 bps**, saving **25.05 bps**. The blueprint's 23.5 bps used a ~10.9 bps Irish blended TER (ex-US ~0.20%); published XUSE 0.15% is cheaper, so the measured pair saving is not identical to 23.5 and does not need to be.

Chosen line for the core: **CSPX + XUSE** (70/30). VWRA is the permitted single-line substitute.

## Estate table

US-situs market value, IRC 2001(c) tentative tax minus the NRA $13,000 unified credit (the $60,000 exemption):

| US-situs market value | US estate tax | As % of that value |
|---|---|---|
| $60,000 | $0 | 0% |
| $100,000 | $10,800 | 10.8% |
| $200,000 | $41,800 | 20.9% |
| $500,000 | $142,800 | 28.6% |
| $1,000,000 | $332,800 | 33.3% |

Irish accumulating units are not US-situs, so the core path is **$0** estate tax at every size. The blueprint's working $500k cell was $122,400 / **24.5%**; the schedule in code produces $142,800 / 28.6%. The Exit uses the zero-situs path, not that percentage.

## ROR-cliff table

At ROR, India taxes foreign dividends at slab (~31.2%) with FTC for US FDAP already withheld (25%). Extra Indian tax is therefore 6.2% of gross dividends. An accumulating wrapper distributes nothing, so the annual dividend tax and Form 67 burden are zero; the dividend leg sits in NAV and is taxed later as 13.0% LTCG if and when realised after 24 months.

Measured yields:

| Wrapper | Annual Indian dividend tax | Form 67 | Dividend leg if converted to 13.0% CG |
|---|---|---|---|
| US-listed distributing (VTI+VXUS) | **9.56 bps/yr** | yes, forever | n/a (taxed as income each year) |
| Irish accumulating (CSPX+XUSE or VWRA) | **0** | no | 20.05 bps of NAV, deferred until realisation |

Working yields 1.3% / 2.9% reproduce the blueprint's **~11 bps/yr** extra Indian dividend tax on the distributing wrapper.

## LSE dealing cost, amortised over 20 years

Working LSE/UCITS round-trip (blueprint rung 3; no UK SDRT on Irish-incorporated shares; USD line, zero FX): 8–15 bps at small size, 4–8 bps at $100k+ clips. Midpoints 11.5 bps and 6.0 bps.

| Clip | Round-trip (working) | Amortised over 20-year hold |
|---|---|---|
| $25k (small) | 11.5 bps | **0.58 bps/yr** |
| $100k+ / $500k core buy | 6.0 bps | **0.30 bps/yr** |

Under 1 bp/yr in every clip the desk actually uses. Fill calibration is N0, not W0.

## Exit

Measured recurring wrapper saving **22.04 bps/yr ≥ 15 bps/yr**, and Irish accumulating units are a documented path to **zero** US-situs on the core. **W0 Exit passed.**

W1 (broker will hold these units; written opinion) is not started. R0 is not scored here: there is no lot file.
