# 3-Tier Cascading Algo Strategy — Overview

**Market:** NSE India, Nifty 100 universe, intraday equities (MIS cash)  
**Date:** 2026-08-05  
**Friction lock:** **0.30%** round-trip cost  

This document is the **high-level map** of how Regime → Horizon → Precision work together. Feature lists, hyperparameters, and judge debates live in the tier verdicts linked below.

---

## One-sentence roles

| Tier | Name | Owns | Does **not** own |
|---|---|---|---|
| **1** | **Regime** | *Whether* and *which sleeve* to trade (market state) | Which stock, or exact fill time |
| **2** | **Horizon** | *Which* Nifty 100 names best express the open sleeve | Market direction, or 1m fill timing |
| **3** | **Precision** | *When* to fill and *how* exits fire (within Tier 2 picks) | Re-ranking names or overriding regime |

Each lower tier may only **narrow** what the tier above allowed — never widen the universe or reverse direction.

---

## Cascade flow

```
                    Pre-open (~9:08–9:15)
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│  TIER 1a — Daily Regime (rules)                           │
│  SUPPORTIVE | AMBIGUOUS | HOSTILE | NO_TRADE              │
│  Risk gate for the session                                │
└───────────────────────────────────────────────────────────┘
                            │
            session open; every 15m (post-hysteresis)
                            ▼
┌───────────────────────────────────────────────────────────┐
│  TIER 1b — Intraday Regime (HMM on Nifty 15m)             │
│  TREND_UP | TREND_DOWN | CHOP | HIGH_VOL                  │
│  Sleeve routing: long mom / short mom / MR / pause        │
└───────────────────────────────────────────────────────────┘
                            │
              only if sleeve is open for momentum
                            ▼
┌───────────────────────────────────────────────────────────┐
│  TIER 2 — Horizon (separate Long / Short LightGBM)        │
│  Cross-sectional rank on 15m stock bars                   │
│  Top-K longs  OR  bottom-K shorts                         │
│  + Triple-barrier TP/SL/H widths & eligibility            │
└───────────────────────────────────────────────────────────┘
                            │
                    registry of K names + frozen barriers
                            ▼
┌───────────────────────────────────────────────────────────┐
│  TIER 3 — Precision (rules on 1m; meta-filter later)      │
│  Bounded-wait entry → fill / skip / size                  │
│  Exit: frozen TB TP / SL / 60m timeout / MIS flatten      │
└───────────────────────────────────────────────────────────┘
```

---

## How the tiers connect

### 1. Regime decides the sleeve

| Daily | Intraday HMM | Cascade posture |
|---|---|---|
| `NO_TRADE` | any | **Flat** — hard block |
| `HOSTILE` | `HIGH_VOL` | Flat / micro only |
| `HOSTILE` | other | Defensive / reduced size |
| `SUPPORTIVE` / `AMBIGUOUS` | `TREND_UP` | **Long momentum ON** |
| `SUPPORTIVE` / `AMBIGUOUS` | `TREND_DOWN` | **Short momentum ON** |
| `SUPPORTIVE` / `AMBIGUOUS` | `CHOP` | Mean-reversion sleeve (separate; not v1 momentum path) |
| `SUPPORTIVE` / `AMBIGUOUS` | `HIGH_VOL` | Pause new momentum entries |

Daily is a **pre-open risk gate** (rules, not LLM). Intraday HMM routes **style and direction** on Nifty 15m emissions (`r_15`, `rv_15`, TWAP-`vwap_dist`), with hysteresis so sleeves do not flip every bar.

→ Detail: [regime-tier1-verdict.md](regime-tier1-verdict.md)

### 2. Horizon picks the names

Given an open momentum sleeve, Tier 2 does **not** re-forecast the market. It ranks Nifty 100 stocks by predicted **excess return vs Nifty** over **60 minutes** (`H = 4` × 15m bars).

| Sleeve | Model | Activation | Inference |
|---|---|---|---|
| Long | LightGBM (Huber) | `TREND_UP` + daily ∈ `{SUPPORTIVE, AMBIGUOUS}` | Top-K by score |
| Short | Separate LightGBM (tighter regs) | `TREND_DOWN` + same daily filter | Bottom-K (most negative excess) |

Shared relative-strength core; Short adds breakdown / bounce-risk / squeeze-aware features. Training uses **only** cascade-valid bars (purged walk-forward).

→ Detail: [horizon-tier2-verdict.md](horizon-tier2-verdict.md)

### 3. Triple-barrier defines path economics

On top of Horizon’s rank target, path labels fix **where** a trade should win, lose, or time out — and bake in **0.30%** cost:

| Barrier | Lock |
|---|---|
| Vertical (time) | Hard **60m** (`H = 4`); MIS-safe entry cutoffs |
| Horizontal TP/SL | TOD `rv_15_mean`-scaled + cost floors (Long TP ≥ **90 bps**) |
| Eligibility | Skip if vol-based TP cannot clear the cost floor |
| Labels | Path excess vs Nifty **minus 0.30%**; dead zone ±30 bps |

These widths and flags are **passed down** to Precision as frozen exit geometry — Tier 3 does not reinvent them.

→ Detail: [triple-barrier-verdict.md](triple-barrier-verdict.md)

### 4. Precision times the fill and fires the exits

Tier 3 watches only the Tier 2 registry on **1-minute** bars:

1. **Gate** — same Regime + TB eligibility + session masks (no 9:15–9:30; Long last entry ~14:00; Short ~13:45; flat by ~15:00).
2. **Entry** — up to ~5 minutes for a pullback/reclaim (Long) or bounce/breakdown (Short); then a deterministic fallback so signals are not left hanging.
3. **Size** — scale by Horizon rank/score (not a new direction model).
4. **Exit** — frozen TB TP / SL / timeout; no trailing stop in v1. Shorts are stricter (afternoon cover gate, no same-session re-entry after SL).

v1 is **rules-first**. An optional LightGBM **take/skip** meta-filter (trained on TB outcomes) is staged only after a rules baseline exists.

→ Detail: [precision-tier3-verdict.md](precision-tier3-verdict.md)

---

## Design principles (locked across tiers)

1. **Narrow downward** — each tier filters; none expands or reverses the tier above.  
2. **Separate Long and Short** — NSE cash MIS is asymmetric (no overnight short breathe, afternoon cover/squeeze). Do not sign-flip one model.  
3. **No LLM in the live gate** — rules / HMM / LightGBM / rules. LLMs were judged unfit for primary gates (latency, cost, non-reproducible history).  
4. **Cost is first-order** — 30 bps enters barrier floors, eligibility, and net labels — not only end-of-day PnL haircuts.  
5. **MIS and clock** — auction bleed excluded; TOD-normalize vol/return features; hard flatten before broker square-off.  
6. **Point-in-time universe** — historical Nifty 100 membership, never today’s list applied retroactively.  
7. **Auditability** — Regime and Precision v1 are deterministic; Horizon is a ranker with purged validation; Precision exits match the labels Horizon/TB assumed.

---

## Timeframes at a glance

| Layer | Clock | Cadence |
|---|---|---|
| Daily Regime | Pre-open | Once per session |
| Intraday Regime | Nifty 15m | Every 15m (hysteresis) |
| Horizon rank + TB widths | Stock 15m | Every 15m when sleeve open |
| Precision entry | Stock 1m | Within ~5m of decision bar |
| Hold / exit | Same session | ≤ 60m or TP/SL/MIS |

---

## Out of scope for the v1 momentum path

- Mean-reversion under `CHOP` (separate sleeve)  
- Trailing stops, L2/order-book features, news/NLP  
- Vol- or sector-scaled hold times (hard `H=4` only)  
- Overnight holds / positional book  
- Using Precision or Horizon to second-guess Regime direction  

---

## Document index

| Doc | Scope |
|---|---|
| **This file** | Cascade overview and contracts |
| [regime-tier1-verdict.md](regime-tier1-verdict.md) | Daily rules + intraday HMM features / states |
| [horizon-tier2-verdict.md](horizon-tier2-verdict.md) | Long/Short LightGBM features, hyperparams, training |
| [triple-barrier-verdict.md](triple-barrier-verdict.md) | Vertical `H`, ATR TP/SL, 0.30% cost |
| [precision-tier3-verdict.md](precision-tier3-verdict.md) | 1m timing rules, Long/Short Precision features, exits |

Judges for the tier verdicts: **Gemini Flash** and **Claude Sonnet**.
