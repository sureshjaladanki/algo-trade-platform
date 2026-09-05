# L1 — Book L ledger arithmetic

Date: 2026-09-05
Milestone: L1
Pre-registration: [h0-prereg-book-l.md](h0-prereg-book-l.md)

Every rupee below is `src.tax.stcg` / `src.tax.ltcg` or `src.costs.round_trip_bps`. Gross 11%/yr is
W17 (assumption, not a forecast). Turnover is 60%/yr. Realised gain = capital × 0.60 × 0.11.

## Tax schedule delta (naive STCG vs LTCG with unused s.198 exemption)

| Capital | Realised gain | STCG | LTCG | Delta | bps of capital |
|---|---|---|---|---|---|
| ₹25,00,000 | ₹1,65,000 | ₹34,320 | ₹5,200 | ₹29,120 | 116.48 |
| ₹50,00,000 | ₹3,30,000 | ₹68,640 | ₹26,650 | **₹41,990** | **83.98** |
| ₹1,00,00,000 | ₹6,60,000 | ₹1,37,280 | ₹69,550 | ₹67,730 | 67.73 |

The ₹1.25 lakh exemption is 50 bps at ₹25 lakh, 25 bps at ₹50 lakh, 12.5 bps at ₹1 crore
(1/capital decay).

Full-year realisation at ₹50 lakh (turnover 100%): gain ₹5,50,000; delta **₹59,150** = 118.30 bps.

## Routing saving (ETF units vs cash-delivery constituents)

Round-trip on turnover notional = 60% of capital, one ISIN, NSE. DP nets out of the delta.

| Capital | Turnover notional | Delivery − ETF | bps of capital |
|---|---|---|---|
| ₹25,00,000 | ₹15,00,000 | ₹2,985 | 11.94 |
| ₹50,00,000 | ₹30,00,000 | **₹5,970** | **11.94** |
| ₹1,00,00,000 | ₹60,00,000 | ₹11,940 | 11.94 |

`etf_vs_constituents` routes through ETF while the quoted spread is inside the STT gap (~19.9 bps)
and **flips to constituents at a 20 bps quoted spread**.

## Combined delta vs 50 bps kill

| Capital | Tax + routing | bps | Kill |
|---|---|---|---|
| ₹25,00,000 | ₹32,105 | 128.42 | above |
| ₹50,00,000 | ₹47,960 | **95.92** | **above 50 bps — Book L stays open** |
| ₹1,00,00,000 | ₹79,670 | 79.67 | above |

## ETF vs direct index fund at ₹50 lakh

`etf_vs_index_fund` with NIFTYBEES-class TER 0.04%, direct index-fund TER 0.04%, quoted spread
11 bps, 1% exit load inside 15 days.

At **4 turns/year** the hold is ~91 days, so the exit load does not bind. Per-turn ETF extra is
spread + ETF round-trip friction from `costs`. With equal TERs the crossover is **0 turns**: any
positive turnover makes the fund cheaper. **Recommendation: hold the core in a direct Nifty 50
index fund**, not in ETF units, at ₹50 lakh and 4 turns/year. Use ETF only when a same-day spread
is inside the STT gap *and* the clip cannot wait for a fund subscription.

## Kill

Schedule delta at ₹50 lakh is 95.92 bps ≥ 50 bps. No `book-l-stop.md`.
