# Triple-Barrier Labeling — Vertical Barrier & Cost Verdict

**Market:** NSE India, Nifty 100 universe, intraday equities (MIS cash)  
**Scope:** Third barrier (time) + TP/SL design for path-dependent labels on top of Tier 2  
**Judges:** Gemini Flash, Claude Sonnet (v1); v2 amend via [horizon-tier2-v2-verdict.md](horizon-tier2-v2-verdict.md)  
**Date:** 2026-07-31 · **v2 amend:** 2026-08-12  
**Friction lock:** **0.30% (30 bps) round-trip** (brokerage + STT + fees + slippage)  
**Depends on:** [Tier 1](regime-tier1-verdict.md), [Tier 2 v1](horizon-tier2-verdict.md), [Tier 2 path pivot v2](horizon-tier2-v2-verdict.md)

---

## Summary

| Decision | Locked choice |
|---|---|
| Third barrier | **Vertical / time barrier** (max hold) |
| Primary timeout (**v2**) | **Hard timeout** `H = 6` bars (**90 minutes**) |
| Secondary timeout | Hard `H = 4` bars (**60 minutes**) — robustness / MIS-stress only; not ship-primary |
| Vol-based timeout | **Reject as primary** — do not vary `H` by stock/sector vol |
| Where vol goes | **Horizontal barriers** — TOD absolute `rv_15_mean`-scaled TP & SL (not daily ATR; not intensity ratio) |
| Sector-conditioned `H` | **None** (stock TOD rv already absorbs sector vol) |
| Cost `c` | **0.30%** enters barrier floors **and** net-of-cost labels |
| TP/SL floors | **Unchanged** — Long ≥90 / ≥45 bps; Short ≥75 / ≥45 bps |
| Vol multiples | **Frozen this charter** — no soft reopen when expanding `H` |
| Build posture | v1 ACCEPT hard timeout + vol TP/SL; **v2 amends vertical H only** |

**Direct answer (current):** Prefer a **hard 90m timeout** so economic TP floors remain reachable at upper-quartile path travel. Use volatility to size **TP/SL width**, not duration. Factor **0.3%** into both barrier geometry and labels. Do **not** lower TP to P50.

---

## v2 amend (2026-08-12) — primary vertical `H = 6`

**Authority:** [horizon-tier2-v2-verdict.md](horizon-tier2-v2-verdict.md) dual-judge lock (Gemini ACCEPT / Claude REVISE→process hardened).  
**Why:** Cascade Top-K StockTB+1 ~7–11% under H=4 + 90/75 bps floors is largely **physics** — at 60m, 90 bps sits at/above P75 absolute moves for most Nifty 100 sectors. Expanding time (not cutting floors) is the allowed degree of freedom.  
**MIS sample-loss precondition:** **PASS** — see v2 verdict step 1 (`logs/horizon_mis_sample_loss_ab.txt`); ~11–16% sleeve-bar loss; no Fold A/B min-N breach.

| Item | v1 (historical lock below) | **v2 current lock** |
|---|---|---|
| Primary `H_max` | 4 bars / 60m | **6 bars / 90m** |
| Secondary `H` | 90m was Tier 2 check only | **4 bars / 60m** (diagnostic / robustness) |
| Long last entry | ≈ 14:15 bar-end | ≈ **13:45 bar-end** |
| Short last entry | ≈ 14:00 bar-end | ≈ **13:30 bar-end** |
| Exit / flatten clocks | `MIS_EXIT_BAR_END` 15:15 · `MIS_FLAT_BY` 15:00 | **Unchanged** |
| Long TP / SL | `max(2.5×rv, 90bps)` / `max(1.0×rv, 45bps)` | **Unchanged floors + multiples** |
| Short TP / SL | `max(2.0×rv, 75bps)` / `max(0.9×rv, 45bps)` | **Unchanged floors + multiples** |
| Cost `c` / dead zone | 0.30% / ±30 bps | **Unchanged** |
| Sector-scaled `H` | None | **None** |
| Eligibility | Skip if vol TP cannot clear cost floor at H | Same rule at **H=6** |

```
H_max = 6 bars  (90 minutes)   # matches Tier 2 v2 path-strategy primary horizon
H_actual = min(H_max, bars_until_MIS_safe_exit)
# H=4 retained as secondary label / diagnostic columns only (step 3 builders)
```

**Explicit non-changes (forbid soft reopen):**

- Do **not** lower Long TP below 90 bps or Short TP below 75 bps while friction stays 30 bps.  
- Do **not** retune ATR/rv multiples inside this amend — report-first only under a separate note.  
- Do **not** invent sector-specific `H_max` tables.  
- Do **not** claim cascade path density is fixed by this amend alone — builders + path-model A+B still required.

**Code cutoffs:** `src/utils/eval_common.py` — `H_BARS = 6`; derived MIS entries in `src/horizon/session.py` (`LONG_LAST_ENTRY` / `SHORT_LAST_ENTRY` = 13:45 / 13:30).

---

## Judge scores (v1, with 30 bps)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Hard vs vol timeout | Hard only (9.5); pure vol-H = 1/10 | Hybrid shrink-only (8) | **Hard `H=4` in v1**; shrink-only → ideal |
| TP/SL pairing | 9.5 — raise TP to clear cost | 9 — `max(vol, cost floor)` | **ATR TP/SL + cost floors** |
| Sector conditioning | 1/10 | 4/10 | **None for v1** |
| 30 bps impact | Hard H mandatory; TP↑; 90 bps TP floor | `H_min`↑; eligibility screen | **Cost is first-order** |
| Overall | REVISE vol-timeout → hard | ACCEPT hybrid (cost-bounded) | **ACCEPT hard timeout + vol TP/SL** |

---

## What is the third barrier?

The **vertical (time) barrier** — a max holding period independent of price.

| Barrier | Trigger | Role |
|---|---|---|
| Upper (TP) | Price hits profit target | Path-dependent win |
| Lower (SL) | Price hits stop | Path-dependent loss |
| Vertical (timeout) | Clock / bar count hits `H` | Path-independent stopwatch — exit if neither TP nor SL hit |

On timeout: resolve at market (bar `t+H` close) and assign label from realized path return (net of cost). Common discrete coding: `+1` TP-first, `-1` SL-first, `0` timeout / dead-zone.

---

## Locked design (v1) — historical

> Preserved as the v1 contract. **Superseded for primary `H` and MIS entry cutoffs by the [v2 amend](#v2-amend-2026-08-12--primary-vertical-h--6) above.** Floors, cost channels, and vol scale from this section remain in force.

### Vertical barrier — hard timeout (v1)

```
H_max = 4 bars  (60 minutes)   # matched Tier 2 v1 primary horizon
H_actual = min(H_max, bars_until_MIS_safe_exit)
```

| Rule | Value (v1) |
|---|---|
| Long last entry | ≈ **14:15 bar-end** (same physical candle as old 14:00 bar-start; H=4 exit stamp 15:15) |
| Short last entry | ≈ **14:00 bar-end** (same physical candle as old 13:45 bar-start) |
| 15m label exit stamp | ≤ **`MIS_EXIT_BAR_END` ≈ 15:15** (bar-end stamp of the 15:00–15:15 candle) |
| Live / 1m MIS flatten | **`MIS_FLAT_BY` ≈ 15:00** wall-clock (before broker ~15:15 square-off) |
| Expand `H` above 4? | **No in v1** (90m stayed Tier 2 secondary check only) — **lifted in v2 amend** |

**Why not vol-based / sector-based `H` (still current)**

1. **Cross-sectional ranking / path selection** needs a uniform label horizon — mixed `H` across names breaks LightGBM comparability (Gemini).  
2. **30 bps** needs time to clear — shrinking `H` in high vol often kills the trade before it can cover cost (Gemini, reinforced by cost revision).  
3. **Sector vol** is already absorbed by **stock-level TOD `rv_15_mean`** on TP/SL width; separate sector `H_max` tables add parameters without lift (both judges).

### Horizontal barriers — vol-scaled TP/SL + cost floors

Let `c = 0.0030` (30 bps). Use **trailing** vol only — **locked vol scale (2026-08-06):** causal same-clock absolute **`rv_15_mean`** (typical `(H−L)/close` for that TOD bucket, prior sessions only). Do **not** use daily ATR14 (unreachable on short intraday H) or the dimensionless `stock_rv_15` intensity ratio (wrong units for barrier %).

Column name `atr_pct` is retained for downstream compatibility; its value is `rv_15_mean`.

| Side | TP | SL |
|---|---|---|
| **Long** | `max(2.5 × atr_pct , 3c = 90 bps)` | `max(1.0 × atr_pct , 1.5c = 45 bps)` |
| **Short** | `max(2.0 × atr_pct , ~2.5c ≈ 75 bps)` | `max(0.9 × atr_pct , ~1.5c = 45 bps)` |

Multiples lean toward Gemini’s post–30 bps revision (wider TP to restore net R:R). Floor multiples lean toward Claude’s `max(vol, cost×k)` rule. Vol clock leans toward Claude’s TOD-`rv` reading (absolute baseline, not the ratio).

**Eligibility screen (both judges, cost-aware):** if at the active primary `H` the vol-based TP cannot clear the **90 bps** floor (or `3c`), **skip the entry** — do not force a sub-economic trade into training. Low-vol sectors (e.g. FMCG) self-filter without a sector timeout axis. (**v2:** evaluate eligibility at **H=6**.)

### Where 0.30% enters (locked — all three)

| Channel | Rule |
|---|---|
| 1. Barrier floors | TP/SL = `max(vol distance, cost-derived floor)` |
| 2. Labels | Path return **minus 0.30%** (and excess vs Nifty over the same hold): `Label = R_path_stock − R_nifty_same_window − 0.003` |
| 3. Dead zone | Paths resolving within **±30 bps** of entry → timeout / `0`, not a soft win/loss |

Do **not** treat 30 bps as eval-only PnL haircut after training on gross labels.

### Tier 1 interaction

| Regime | Timeout / barriers |
|---|---|
| `HIGH_VOL` | Tier 1 already pauses/reduces momentum; **do not invent a second H regime**. ATR-widened TP/SL absorb vol. (Claude’s extra `×0.75` H shrink → ideal only.) |
| `CHOP` | Out of scope — mean-reversion sleeve, not this momentum triple barrier |
| Quiet `TREND_*` | Keep hard primary `H` (v2: **H=6**); tighter TOD `rv_15_mean` → narrower TP/SL automatically |

### Long vs Short asymmetry (time)

- Shorts: earlier last entry; same `H_max` as Long but one-bar earlier cutoff (squeeze buffer).  
- Do not copy Long TP/SL with a sign flip.  
- Cash shorts: same-session only — vertical barrier never assumes overnight.

---

## Ideal expansions (staged later)

| Item | Source | Note |
|---|---|---|
| Shrink-only hybrid `H` | Claude | `H = clamp(H_base / vol_ratio, H_min, H_base)` — only after hard-H baseline is stable; never expand past primary `H_max` without a fresh charter |
| Volume/tick time warping | Gemini | Natural compression in busy periods without breaking calendar MIS clip |
| Sector ATR denominator | Claude | Soft upgrade; not sector-specific `H_max` |
| Meta-label early-exit model | Gemini | Tier 3–adjacent |
| Learned barriers | Claude | Joint `H`/TP/SL model — ideal only |

---

## Must avoid

- Lookahead vol (same-bar or future ATR)  
- Vol- or sector-varying `H` while training a single cross-sectional path/rank model  
- SL tighter than round-trip cost  
- Gross labels with 30 bps only subtracted in final PnL  
- Ignoring MIS / short afternoon squeeze window  
- Unlimited hold  
- 9:15–9:30 entries seeding barrier vol  
- Assuming perfect barrier fills on exact high/low (require small penetration / tick buffer)  
- Lowering TP floors to ~P50 moves under 30 bps friction  
- Soft-retuning vol multiples in the same amend that expands `H`

---

## Where judges disagreed (v1)

| Topic | Gemini Flash | Claude Sonnet | Locked |
|---|---|---|---|
| Vertical `H` | Fixed 4 only | Hybrid shrink-only (`H_min` 3 under 30 bps) | **Hard 4 in v1**; hybrid → ideal; **v2 primary → 6** (path charter) |
| TP Long multiple | 2.5× ATR | 1.5× σ_H then cost floor | **~2.5× ATR + 90 bps floor** |
| TP min width | 90 bps (3×c) | 45 bps (1.5×c) | **90 bps** (stricter under 30 bps) |
| HIGH_VOL shrinks H? | No — widen ATR barriers | Yes ×0.75 | **No** |
| Sector `H` | Reject | Reject (implicit via stock vol) | **Reject** |

---

## 80% lift priority

1. **Cost-adjusted path labels** — `R_path − R_nifty − 0.003` with barriers resolving the path.  
2. **Hard primary `H=6` + MIS entry cutoffs** (Long ~13:45 / Short ~13:30 bar-end; live flatten ~15:00); keep H=4 secondary columns.  
3. **TOD `rv_15_mean` TP/SL + 90 bps TP floor + eligibility skip** when cost cannot clear (at H=6).

---

## Next build step

1. ~~Triple-barrier label builder: fixed vertical `H=4`…~~ → **DONE** — primary `H=6` (`build_horizon_features`).  
2. Wire `c = 0.003` into label construction (not just backtest PnL) — already in force.  
3. Eligibility filter on min TP width / rv at active H — already in force at H=6.  
4. Tier 2 path-EV primary (v2 step 5); triple-barrier feeds path labels / H5 bridge — excess-return ranker remains v1 baseline comparator only.

Tier 3 remains out of scope for this verdict.
