# P0 — Desk posture

Date: 2026-09-05
Milestone: P0
Charter: [india-equity-architecture-blueprint.md](india-equity-architecture-blueprint.md)

This memo is the written lock so a later agent cannot quietly re-scope the desk.

## Capital

| | INR |
|---|---|
| Envelope floor | ₹25,00,000 |
| Design point | ₹50,00,000 |
| Envelope ceiling | ₹1,00,00,000 |

Own capital only. No client money, no pooled vehicle, no fee.

## Broker and API

**Intended broker: Zerodha** (Zerodha-class card: ₹0 equity delivery; ₹20 / 0.03% cap on intraday and futures; ₹20 flat on options; DP ₹15.34 per ISIN per sale day).

Why: published calculator matches the cost stack in `src/costs.py`; cash delivery is free; Kite Connect is the documented L0 API path.

**API spend is blocked until L0 exits (L7, L8).** Kite Connect is ₹500/month per key. Until L0, the desk uses ₹0 public data only. If at L0 a free-tier API (Fyers / Angel SmartAPI / Upstox) meets the run loop, prefer that over Kite.

No live capital before L0. Not one rupee, not a test position.

## Closed products (blueprint §6.1 / §2)

- **No leverage. No MTF.**
- **No single-stock derivatives.**
- **No naked short options.**
- Cash equity intraday, index option premium selling, and MTF remain closed books.

## SEBI algo posture (L4)

| Limit | Number the code will assert |
|---|---|
| Order-rate cap | **8 orders/second** (against TOPS 10 OPS) |
| Untagged order | **refused** — every order carries the exchange-issued algo ID or it is not sent |
| Auth | Static-IP-whitelisted OAuth with 2FA; daily token renewal is an explicit pre-run step |
| Family | Self, spouse, dependent children, dependent parents only |
| Perimeter | Never an algo provider, Research Analyst, or PMS |

## Risk limits the code will assert (blueprint §6.1)

| Limit | Number |
|---|---|
| Gross exposure | ≤ 100% of equity |
| Active / factor sleeve | ≤ 40% of equity |
| Single name | ≤ 6% of equity (₹3,00,000 at the ₹50 lakh design point) |
| Single sector | ≤ 25% of equity |
| Naked short options | 0 |
| Single-stock derivatives | 0 |
| 4σ overnight loss on any single position | ≤ 2% of equity |
| Index-futures overlay | ≤ 1 lot per ₹50 lakh equity, monthly cadence at most, and only if a live book's H2 surplus exceeds 2× overlay friction |
| Order rate | ≤ 8 / second in code (TOPS 10) |
| Annual STOP (H7) | After-tax return trails Nifty 50 TRI by more than **600 bps** in a tax year |

Sizing is always the broker margin endpoint plus a **25% buffer**. Never a hard-coded leverage multiple (L3). Peak margin is 100% upfront since 1 September 2021.

## Instruction lists (L12)

Every book must emit a printed, hand-placeable instruction list. A book that cannot be placed by hand is not permitted.

## AI (L10)

`ai.extract` may parse Indian results PDFs into typed numbers, and only if Book R ever opens. `ops` may write a prose note on a run log. No model output may enter a forecast, signal, weight, or size.
