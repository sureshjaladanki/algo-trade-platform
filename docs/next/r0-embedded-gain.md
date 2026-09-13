# R0 — Embedded-gain and cliff-date ledger

**Date:** 2026-09-13
**Spend:** $0
**Status:** **Blocked.** Formula locked. Exit not scored.

Public sources can supply **USD/INR prescribed rates** (RBI reference / SBI TT buying on the lot dates) and **current USD marks**. They cannot supply the household lots. Those come only from broker statements and the investor's own records. The plan's 200k → 400k / 62 → 92 book is an illustration of the identity, not this desk's number.

## What is missing

| Input | Obtainable from public $0 sources? |
|---|---|
| Acquisition date, USD cost, USD market value per lot | **No** |
| INR rate on acquisition date and today (RBI / prescribed) | **Yes**, once dates exist |
| RNOR expiry date / last Indian tax year for R1 | **No** — `residency` is N0 and needs the investor's facts |

Do not invent a ledger. Do not treat the illustration as Exit.

## File to drop

Put the real book at `data/private/r0-lots.csv` (gitignored under `data/`). Columns:

```text
acquisition_date,usd_cost,usd_value,inr_per_usd_acquire,inr_per_usd_now
2019-03-12,50000.00,72000.00,69.40,88.10
```

Dates ISO-8601. USD cost is the lot's remaining basis. USD value is mark-to-market. INR columns are the RBI/prescribed rate on the acquisition date and on the scoring date — fill them from the rate card; the engine does not guess.

Also state, in writing, the **RNOR expiry date** (the last Indian tax year in which R1 can run). That is not in this file.

## Identity (locked)

INR cost = Σ USD cost × INR/USD at acquire.
INR value = Σ USD value × INR/USD now.
INR unrealised = INR value − INR cost.
FX accretion = Σ USD cost × (INR/USD now − INR/USD at acquire).
Tax after the cliff = 13.0% of INR gain on lots ≥ 24 months at the cliff date, ~31.2% on the rest.
Step-up worth (bps of capital) = tax / INR value × 10,000.

Illustration (plan text, **not Exit**): USD 200k → 400k, INR 62 → 92 → ₹2.44 crore INR gain, ₹0.60 crore FX accretion, tax ₹31.72 lakh = **862 bps** of current INR capital (the plan's ~863 is that figure rounded via ~USD 34,500). `r0_passes` is false until `data/private/r0-lots.csv` exists and scores ≥ 100 bps with `source="real"`.

## Exit / Stop

Exit: step-up ≥ **100 bps of capital** on the **real** ledger.
Stop: below 100 bps → drop the one-time action; R2's 24-month discipline stays.

Neither has fired. R0 is a **fail to score**, not the documented Stop.
