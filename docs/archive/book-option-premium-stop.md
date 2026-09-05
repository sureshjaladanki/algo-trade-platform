# STOP — Index option premium selling

Date: 2026-09-05
Closed at: H0
Author: agent

## What was claimed

Harvest the volatility risk premium by selling Nifty weekly defined or naked premium (ATM straddle
class). Hypothesised E_net **0.5–1.2%/yr** gross VRP. σ_ann 8%, T **0.43 yr** (current expiry / STT /
CAS regime).

## What was measured

**Nothing was measured; the book closed on arithmetic before any data access.**

MDE_ann at σ = 8% and T = 0.43 yr is **>30%/yr** against ½ × 0.5–1.2% = 0.25–0.6%. Fails H4 by
**≥50×.** Specs used 0 of 5.

Blueprint §2.4 friction on a 1-lot Nifty weekly ATM straddle: **~1.02% of premium sold** (~0.40%/yr
of notional), the same order of magnitude as the entire VRP at India VIX **10.97** (4 September
2026). A 4σ weekly move on one lot is **~1.66% of ₹50 lakh**.

## Why it closed

Three independent kills, any one of which is sufficient:

1. **Economics.** Friction ≈ VRP at India VIX 10.97.
2. **Measurability (H4).** T < 6 months of the current regime (one weekly per exchange from Nov 2024,
   Tuesday expiry, January 2026 lots, April 2026 STT 0.15% of premium, August 2026 CAS). No sample.
3. **Counterparty.** SEBI study released 20 August 2026: FY26, **87.7%** of individual equity
   derivatives traders lost money; aggregate net loss **₹91,685 crore**; options **92%** of losses;
   **₹25,000 crore of that ₹91,685 crore was transaction cost, not transfer** to a counterparty.
   Active individuals −18%, new entrants −40%, exits +76%. Index options premium ADTO −20% MoM (Aug
   2026) to a 19-month low.

## What would re-open it

**All** of the following, together, not separately:

- India VIX 30-day median **> 18** for a full quarter, **and**
- a defined-risk structure whose maximum loss per lot is under **2% of equity**, **and**
- **T ≥ 1 year** of a stable STT / expiry / lot regime, **and**
- after-cost expectancy clearing **H3**.

A higher VIX alone is not a reopen.

## What was deleted

No options-selling book module. Product remains on the P0 closed list (naked short options = 0).
