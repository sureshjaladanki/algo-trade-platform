# Tier 2 Horizon Strategy — Feature & Hyperparameter Verdict

**Market:** NSE India, Nifty 100 universe, intraday equities  
**Scope:** Tier 2 Long / Short LightGBM stock-selection models (Tier 3 out of scope)  
**Judges:** Gemini Flash, Claude Sonnet  
**Date:** 2026-07-31  
**Depends on:** [Tier 1 Regime Verdict](regime-tier1-verdict.md)  
**Related:** [Triple-Barrier Verdict](triple-barrier-verdict.md) — vertical timeout, TP/SL, 0.30% cost  
**Escalation (2026-08-11):** Tier 1 Regime search **CLOSED** ([A0 stop memo](regime-tier1-stop-memo.md)) — Regime is a frozen soft overlay; **Horizon is active** for path quality / selection.

---

## Summary

| Decision | Locked choice |
|---|---|
| Model family | **Two separate LightGBM models** — Long and Short (not one symmetric model) |
| Role | Cross-sectional stock selection / ranking — **does not re-forecast market direction** |
| Activation | Long only on `TREND_UP`; Short only on `TREND_DOWN` (daily not `NO_TRADE` / hard block) |
| Target | **Excess return vs Nifty** (regression v1; LambdaRank later) |
| Primary horizon | **60 minutes (4 × 15m bars)**; 90m as secondary robustness check |
| Path labels (related) | Triple barrier: hard `H=4`, ATR TP/SL, **0.30%** round-trip cost — see [triple-barrier-verdict](triple-barrier-verdict.md) |
| Build posture | Accept with revisions; stage ideal expansions later |

Tier 1 owns the regime gate and sleeve routing. Tier 2 ranks which Nifty 100 names best express the active momentum sleeve.

---

## Judge scores (proposal)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Long features | 9/10 | 8/10 | Shared RS core + confirmation; ~14–15 feats |
| Short features | 9/10 | 7/10 | Shared core + short-only asymmetry set |
| Long hyperparams | 9.5/10 | 8/10 | Shallow, regularized; Huber/binary TBD below |
| Short hyperparams | 9/10 | 7/10 | Tighter than Long; scarcer `TREND_DOWN` sample |
| Target / horizon | 9/10 (binary @ 60m) | 8/10 (regression @ 90m) | **Regression @ 60m primary** |
| Training protocol | 9.5/10 | 8/10 | Purged walk-forward + regime-matched samples |
| Cascade fit | 10/10 | 9/10 | Tier 2 stays conditional / cross-sectional |
| Overall | **REVISE** 8.5/10 | **ACCEPT + minor** 7/10 | **ACCEPT with revisions** |

---

## Locked design (v1)

### Target & horizon

| Item | Locked choice | Notes |
|---|---|---|
| Objective | Regression on forward **excess return vs Nifty** | Gemini preferred binary outperformance; Claude preferred regression. **Consensus: regression** — preserves rank info for stock selection; binary threshold is arbitrary at 15m noise. |
| Label (Long) | \(R_{stock,t\to t+H} - R_{nifty,t\to t+H}\) on cascade-valid `TREND_UP` bars | Optionally soft-threshold by ~1× round-trip cost buffer for evaluation, not hard binarization of training labels |
| Label (Short) | Same excess return on `TREND_DOWN` bars; **more negative = better short** | At inference: rank ascending (most underperforming predicted names first) |
| Primary \(H\) | **4 bars / 60 minutes** | Gemini lock; safer vs MIS square-off. Claude wanted 90m primary — demoted to secondary check |
| Secondary \(H\) | 6 bars / 90 minutes | Robustness / ensemble check only in v1 |
| Last entry cutoff | Horizon must resolve before broker ~15:15; live flatten ~15:00 | 15m bar-end: Long ≈ 14:15, Short ≈ 14:00 (H=4 exit stamp ≤ `MIS_EXIT_BAR_END` 15:15). 90m secondary: pull entries earlier by one bar. |
| Inference | Cross-sectional top-K / bottom-K ranking of calibrated scores | Not trade every name above a fixed probability |

Loss: prefer **Huber** (or MAE) over plain L2 — fat-tailed NSE intraday returns. Stage **LambdaRank** grouped by `(date, regime-episode)` after enough episodes exist.

---

### Cascade sample filter (critical)

| Model | Train / predict only when |
|---|---|
| Long | `daily_regime ∈ {SUPPORTIVE, AMBIGUOUS}` **and** `intraday_regime == TREND_UP` (post-hysteresis) |
| Short | `daily_regime ∈ {SUPPORTIVE, AMBIGUOUS}` **and** `intraday_regime == TREND_DOWN` (post-hysteresis) |

Do **not** train momentum models on `CHOP` / `HIGH_VOL` / `HOSTILE` / `NO_TRADE` bars. Do not use pre-hysteresis raw HMM states for labels or features.

Exclude entry bars in the **09:15–09:30** auction bleed (bar-end stamp **09:30**). Exclude any entry whose label window crosses the live MIS flatten zone (~15:00 wall).

---

### Locked feature set (v1) — Long model (~15)

Stock-level + relative-to-index + regime-context. All lookahead-safe; no raw price/volume.

| Feature | Definition | Role |
|---|---|---|
| `rel_ret_15_vs_nifty` | Stock TOD-norm `r_15` − Nifty `r_15` (same bar) | Core relative strength |
| `rel_ret_60_vs_nifty` | Stock − Nifty return over trailing 4 bars | Persistence of RS |
| `stock_r_15` | Stock TOD-normalized signed 15m return | Absolute momentum confirm |
| `stock_rv_15` | Stock TOD-normalized range % | Vol intensity / noise filter |
| `stock_volz_15` | Stock volume z vs TOD bucket | Participation confirm |
| `stock_vwap_dist` | % dist to session VWAP / prior-day ATR% | Intraday trend location |
| `sector_rel_strength` | Stock − sector-index return (trailing 60m) | Within-sector leadership |
| `dist_to_prev_day_high` | (Close − prior session high) / prior ATR14 | Lookahead-safe breakout proxy |
| `orb_breakout_flag` | 1 if cleared 9:15–9:30 OR high | Uses open range as *reference*, not as live feature bar |
| `rolling_beta_60d` | 60d OLS beta vs Nifty (trailing) | Amplification of index trend |
| `trend_strength_daily` | Stock daily ADX14 or EMA20 slope R² | Structural daily trend |
| `pct_from_20d_high` | (Close − 20d high) / 20d high | Multi-day momentum context |
| `adv_rank_20d` | Trailing 20d ADV percentile in Nifty 100 | Execution / liquidity filter |
| `bars_since_regime_flip` | Bars since post-hysteresis entry to `TREND_UP` | Momentum age / chase risk |
| `tod_sin` / `tod_cos` | Cyclic encoding of minutes from open | TOD effects without hard-coding clock |

**Regime context (pass-through, not categorical state):** `vol_regime_ratio` (Tier 1 daily), `index_vwap_dist` (Tier 1 HMM emission). Do **not** feed `intraday_regime` as a one-hot — it is constant inside each model's training slice.

---

### Locked feature set (v1) — Short model (~15)

**11 shared** with Long (same definitions; signs interpreted by the Short model). **Asymmetric / Short-only** below.

| Feature | Shared? | Definition / note |
|---|---|---|
| `rel_ret_15_vs_nifty` | Shared | Relative weakness when negative |
| `rel_ret_60_vs_nifty` | Shared | Persistent underperformance |
| `stock_r_15` | Shared | Absolute downside momentum |
| `stock_rv_15` | Shared | Panic / expansion |
| `stock_volz_15` | Shared | Weaker prior than for longs — let tree learn |
| `stock_vwap_dist` | Shared | Below VWAP = structural weakness |
| `rolling_beta_60d` | Shared | High-beta falls harder |
| `trend_strength_daily` | Shared | Structural daily downtrend |
| `adv_rank_20d` | Shared | **More critical** — squeeze / gap risk |
| `bars_since_regime_flip` | Shared | Age of `TREND_DOWN` episode |
| `tod_sin` / `tod_cos` | Shared | MIS timing awareness |
| `sector_rel_weakness` | **Short** | Sector return − stock return (60m) — lagging within sector |
| `dist_to_prev_day_low` | **Short** | Breakdown proxy (mirror of prior-day high) |
| `orb_breakdown_flag` | **Short** | Cleared 9:15–9:30 OR low |
| `pct_from_52w_high` | **Short** | Fresh crash from highs vs stale grind |
| `bounce_risk_zscore` | **Short** | Z of trailing 3-bar cum return — avoid over-extended shorts |
| `downside_acceleration` | **Short** (Gemini) | Down-range / total range over last 4 bars |

Optional short context: `resistance_dist` (distance to 5d high / ATR) if feature budget allows; else stage to ideal.

---

## LightGBM hyperparameters (v1 starting points)

Philosophy (both judges): **shallow trees, strong regularization, early stopping**. NSE 15m SNR is low; Short has scarcer `TREND_DOWN` samples and forced same-day flatten.

### Long

| Param | Value | Rationale |
|---|---|---|
| `objective` | `huber` (α ≈ 0.9) | Fat-tail robust excess-return regression |
| `metric` | `mae` + Spearman IC on val folds | IC is the ranking metric that matters |
| `learning_rate` | 0.03 | Slow enough for noisy finance; Gemini preferred 0.015 for binary — keep 0.03 for Huber |
| `num_leaves` | 15 | Shallow (`2^4 − 1`) |
| `max_depth` | 4 | Cap interaction order |
| `min_child_samples` | 300 | Smooth per-bar noise |
| `n_estimators` | 1000 (early stop) | Ceiling; ES cuts short |
| `subsample` | 0.75 | Bag correlated stock-day bars |
| `colsample_bytree` | 0.7 | Decorrelate TOD feature family |
| `reg_alpha` | 0.5 | Mild L1 |
| `reg_lambda` | 5.0 | Primary overfit guard |
| `early_stopping_rounds` | 50 | On purged validation only |

### Short

| Param | Value | Rationale |
|---|---|---|
| `objective` | `huber` (α ≈ 0.7) or `regression_l1` | Crash-day tails dominate L2; lower Huber α / MAE |
| `metric` | `mae` + Spearman IC | Same as Long |
| `learning_rate` | 0.025 | Slightly slower than Long (Claude); Gemini wanted faster for binary panic — rejected for regression scarcity |
| `num_leaves` | 15 | Shallower ceiling acceptable: 7–15; start 15, shrink if ES overfits |
| `max_depth` | 3–4 | Start **3** if `TREND_DOWN` bar count is thin |
| `min_child_samples` | 400 | **Higher than Long** relative to dataset size |
| `n_estimators` | 600 (early stop) | Smaller ceiling |
| `subsample` | 0.65 | More aggressive bagging |
| `colsample_bytree` | 0.65 | Same |
| `reg_alpha` | 1.0 | Stronger L1 |
| `reg_lambda` | 8.0–10.0 | Squeeze / small-sample protection |
| `early_stopping_rounds` | 30–50 | Tighter than Long |

**NSE short asymmetry (locked rationale):** cash shorts are intraday-only (no overnight breathe); downside is sharper/shorter than up-grinds; bad shorts cost more than missed shorts under MIS. Do **not** copy Long hyperparams with a sign flip.

---

## Training protocol (locked)

1. **Purged + embargoed walk-forward** (López de Prado). Embargo ≥ horizon (4 bars) **plus ≥ 1 trading day** at every train/val boundary.
2. **Roll:** ~18–24m train → embargo → 1m validate → 1–3m test; mirror `regime_pipeline.py` period args.
3. **Universe:** point-in-time Nifty 100 only — never today's list applied retroactively.
4. **Imbalance:** fix at **episode/date level** (span multiple genuine downtrends: 2020, 2022, …). Reject naive row oversampling for Short.
5. **Calibration:** isotonic on purged val only; monitor top-vs-bottom decile spread and per-fold Spearman IC.
6. **Inference:** score all eligible names each bar → top-K long / bottom-K short.

---

## Ideal expansions (not v1 — staged later)

| Theme | Gemini | Claude | Consensus |
|---|---|---|---|
| Ranking objective | — | LambdaRank by episode | Add after episode count is healthy |
| Multi-horizon | — | 30/60/90/120 ensemble | Secondary 90m first; full ensemble later |
| XS rank features | — | Live percentile of RS within Nifty 100 | Add |
| F&O OI / short buildup | Option PCR/OI | Short buildup (highest Short lift) | **Ideal only** — same lineage rigor as Tier 1 OI exclusion |
| Order book | OBI | Exclude from v1 | Ideal / exclude until clean tick lineage |
| Delivery % | Prior-day delivery ratio | F&O long buildup | Add lagged EOD |
| Borrow / SLB | SLB rates | SLB availability flag | Short ideal |
| Squeeze guard | Short-interest + volume squeeze indicator | Crash-vs-grind meta-model | Short ideal |
| Shared trunk | — | Shared embedding, regime heads | Defer — v1 wants separate auditable models |

---

## Must exclude (both judges)

- Raw price / raw volume  
- Absolute (non-excess) return as the sole target  
- Unpurged K-fold / horizon-overlapping train-val  
- Training Long/Short on `CHOP` / `HIGH_VOL` / blocked daily regimes  
- Categorical `intraday_regime` as a feature inside its own sleeve  
- Non-causal (forward-looking) HMM smoothing for labels  
- Today's Nifty 100 list over history (survivorship)  
- One-hot stock identity  
- News / NLP in v1  
- F&O OI / PCR / order-book in v1  
- Naive row oversampling to "fix" Short scarcity  

---

## Where judges disagreed

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Target type | Binary XS outperformance | Excess-return regression (→ LambdaRank) | **Regression** (rank-preserving) |
| Primary horizon | 60m | 90m (+ 60m check) | **60m** (+ 90m secondary) |
| Long LR | 0.015 (binary) | 0.03–0.05 (Huber) | **0.03** Huber |
| Short LR | 0.03 (faster panic) | 0.02–0.03 (slower, scarce) | **0.025** — scarcity wins over panic-speed |
| Short-only feats | `resistance_dist`, `downside_acceleration` | `pct_from_52w_high`, `bounce_risk_zscore`, ORB low | **Union lite:** ORB low + prev-day low + 52w + bounce + downside accel |
| Spread / microstructure | `spread_z` in v1 | Not emphasized | Stage to ideal unless spread data is clean |
| Overall posture | REVISE | ACCEPT + minor | **ACCEPT with revisions** |

---

## Gate mapping (Tier 1 → Tier 2)

| Daily | Intraday | Tier 2 |
|---|---|---|
| `NO_TRADE` | any | Flat — hard block |
| `HOSTILE` | `HIGH_VOL` | Flat / micro — no Tier 2 |
| `HOSTILE` | `CHOP` / `TREND_*` | Defensive / reduced size; Tier 2 optional later |
| `AMBIGUOUS` / `SUPPORTIVE` | `TREND_UP` | **Long LightGBM ON**; Short OFF |
| `AMBIGUOUS` / `SUPPORTIVE` | `TREND_DOWN` | **Short LightGBM ON**; Long OFF |
| `AMBIGUOUS` / `SUPPORTIVE` | `CHOP` | Mean-reversion sleeves — **out of Tier 2 momentum scope** |
| `AMBIGUOUS` / `SUPPORTIVE` | `HIGH_VOL` | Pause momentum Tier 2 |

---

## NSE production constraints (Tier 2)

1. **TOD-normalize** stock returns, range, and volume — same U-shaped clock trap as Tier 1 HMM.  
2. Down-weight / exclude auction-bleed (**09:30** bar-end); never let a live position cross **`MIS_FLAT_BY` ~15:00**; 15m label exits may use stamp ≤ **`MIS_EXIT_BAR_END` ~15:15** (same physical 15:00–15:15 candle).  
3. Shorts are **same-day only** in cash — no overnight breathe; Short model must respect flatten cutoff.  
4. **Point-in-time universe** + trailing `adv_rank_20d` — non-negotiable for live transfer.  
5. Retune Short `min_child_samples` / `num_leaves` after measuring actual post-filter `TREND_DOWN` bar counts.  
6. Tier 2 must not re-litigate Tier 1 direction — only rank within the open sleeve.

---

## 80% lift priority

| Rank | Gemini Flash | Claude Sonnet | Consensus first build |
|---|---|---|---|
| 1 | Regime-conditioned train filter | Causal sample alignment + purge/embargo | **Cascade-matched samples + purged WF** |
| 2 | XS relative outperformance target | Shared RS trio (`rel_ret_15`, sector RS, VWAP dist) | **Excess-return label + shared RS feature trio** |
| 3 | TOD-normalized stock features | Point-in-time universe + liquidity rank | **TOD stock features + PIT universe / ADV** |

---

## Related: triple-barrier labeling

Path-dependent exits and cost-aware labels are **not** specified in full here. They are locked in [triple-barrier-verdict.md](triple-barrier-verdict.md). Summary for Tier 2 builders:

| Item | Locked (see full verdict) |
|---|---|
| Third barrier | **Vertical / time** — hard timeout, not vol- or sector-scaled `H` |
| `H` | **4 bars / 60m** (aligned with this doc’s primary horizon) |
| Vol conditioning | Sizes **TP/SL width** (ATR), not hold duration |
| Round-trip cost | **`c = 0.30%`** in barrier floors **and** net-of-cost labels |
| TP floor | ≥ **90 bps** (3×c); skip entry if cost cannot clear |
| Role vs this doc | Tier 2 primary target remains excess-return regression; triple barrier feeds meta-labeling / entry quality |

---

## Next build step

Implement:

1. Horizon label builder — 60m excess return vs Nifty; MIS-safe entry filter; optional 90m secondary  
2. Stock feature pipeline (shared Long/Short core + Short asymmetry set) on 15m constituents  
3. Cascade join: Tier 1 daily + post-hysteresis intraday → sample masks for Long / Short  
4. LightGBM trainers with locked hyperparams, purged walk-forward, isotonic calibration  
5. Inference: top-K / bottom-K ranking under active sleeve  
6. (Related) Triple-barrier path labels per [triple-barrier-verdict.md](triple-barrier-verdict.md) — hard `H=4`, ATR TP/SL, 0.30% cost  

Tier 3 remains out of scope. Mean-reversion under `CHOP` is a separate sleeve, not this verdict.
