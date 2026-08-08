# Tier 3 Precision Strategy — Feature & Timing Verdict

**Market:** NSE India, Nifty 100 universe, intraday equities (MIS cash)  
**Scope:** Tier 3 precise entry / exit timing on **1-minute** bars (Tier 1 / 2 locks unchanged)  
**Judges:** Gemini Flash, Claude Sonnet  
**Date:** 2026-08-05  
**Depends on:** [Tier 1 Regime](regime-tier1-verdict.md), [Tier 2 Horizon](horizon-tier2-verdict.md), [Triple-Barrier](triple-barrier-verdict.md)  
**Friction lock:** **0.30%** round-trip (inherited — do not re-derive)

---

## Summary

| Decision | Locked choice |
|---|---|
| Method | **Hybrid rules-first** — deterministic 1m timing + exits; ML meta-filter **staged after** rules baseline |
| Role | **Narrow** Tier 2 top-K / bottom-K — skip, delay fill, or size down; **never** re-rank or re-forecast direction |
| Timeframe | **1m** for entry timing; TP / SL / `H` / eligibility **frozen from Tier 2 triple-barrier** (15m decision bar) |
| Long vs Short | **Separate** strategies — asymmetric windows, squeeze / cover gates, no-reentry on shorts |
| Exit geometry | Reuse TB: Long `max(2.5×rv_15_mean, 90bps)` / `max(1.0×rv_15_mean, 45bps)`; Short `max(2.0×rv_15_mean, 75bps)` / `max(0.9×rv_15_mean, 45bps)`; hard `H=4` (`atr_pct` column = TOD `rv_15_mean`) |
| Trailing stop | **Reject in v1** — static TP / SL / timeout only |
| Build posture | Accept with revisions; ship pure-rules v1; stage meta-label LightGBM later |

Tier 1 owns the regime gate. Tier 2 owns which names to trade. Tier 3 owns **when** (within a few 1m bars) to fill and **how** exits fire — using the same barrier math Tier 2 already labeled.

---

## Judge scores (proposal)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Method (rules / ML / hybrid) | 9.5 — hybrid w/ meta in v1 | 8.5 — hybrid; rules v1, meta optional | **Rules-first v1**; meta staged |
| Cascade coherence | 10 | 9 | Narrow-only; no re-rank |
| Feature set / overfit | 8 (OBI/CVD heavy) | 7.5 (parsimonious TB+1m) | **TB-centric + light 1m**; drop L2 |
| Long / Short asymmetry | 10 | 8.5 | Separate sleeves; short tighter |
| Exit / trail | Trail @ 50%/40% to BE | Static TB only in v1 | **Static TB in v1**; trail → ideal |
| NSE production realism | 9 | 8 | MIS / bleed / PIT / no lookahead |
| Overall | **REVISE** (force meta in v1) | **ACCEPT** + minor | **ACCEPT with revisions** |

---

## Locked design (v1)

### Method: rules-first hybrid

| Option | Verdict |
|---|---|
| **(A) Pure rules on 1m** | **v1 ship path** — auditable, backtestable, matches user preference (no LLM) |
| **(B) Pure ML timing on 1m** | **Reject** — NSE 1m SNR is low; overfits auction / MIS / illiquid prints |
| **(C) Hybrid rules + meta-filter** | **Target architecture** — rules own trigger + exits; LightGBM answers only **take / skip** using TB labels |
| LLM | **Reject** at Tier 3 — same reasons as Tier 1 gate |

**Staging (locked):** implement **(A)** first and measure win rate / PF vs what `tb_label_*` implies. Add **(C)** meta-filter only if rules leave TB-eligible paths under-monetized. Do not ship meta-label without purged walk-forward + embargo matching Tier 2.

---

### Cascade contract

Tier 3 **narrows** — it never widens the universe or overrides Tier 1 / 2.

| Source | Fields | Tier 3 use |
|---|---|---|
| Tier 1 | `daily_regime`, `intraday_regime` (post-hysteresis) | Hard gate passthrough: Long only `TREND_UP` + daily ∈ `{SUPPORTIVE, AMBIGUOUS}`; Short only `TREND_DOWN` + same |
| Tier 1 | `HIGH_VOL` / pause | Block **new** entries; open positions keep frozen TB exits (ATR already absorbs vol) |
| Tier 2 | `horizon_rank`, `horizon_score`, sleeve direction | Defines the only names Precision may touch; score/rank drives size |
| Tier 2 / TB | `atr_pct`, `long_tp_w` / `long_sl_w`, `short_tp_w` / `short_sl_w`, `tb_eligible_long` / `tb_eligible_short` | Exit geometry — **copied verbatim**, frozen at the 15m decision bar |
| Session | `long_entry_ok_expr` / `short_entry_ok_expr` / auction bleed | TOD gates reused as-is |

**Outputs:**

| Field | Meaning |
|---|---|
| `precision_fire` | bool — accept this Tier-2 name now |
| `entry_bar_1m`, `entry_px` | Actual 1m fill vs 15m decision bar |
| `tp_px`, `sl_px`, `vertical_deadline` | Absolute levels / time, frozen at entry |
| `size_mult` | 0–1 from Tier 2 rank / score |
| `exit_reason` | `TP` \| `SL` \| `TIMEOUT` \| `REGIME_FLIP` \| `MIS_FLATTEN` |
| `meta_label_pass` | Optional (ideal) — take / skip |

```
Tier 1 Regime ──gate──► Tier 2 Horizon (top-K / bottom-K)
                              │
                              │ registry + TB widths + scores
                              ▼
                     Tier 3 Precision (1m timing)
                              │
                              ▼
                     fill / skip / size → TB exits
```

---

### Locked feature set (v1) — Long (~12)

Prefer **triple-barrier metrics already captured at Tier 2**, plus light 1m timing features. No L2 / OBI / CVD in v1 (clean tick lineage unavailable; Tier 1 already excluded order book).

| Feature | Definition | Role |
|---|---|---|
| `tb_eligible_long` | From TB builder — vol TP clears 90 bps floor | Hard gate |
| `long_tp_w` / `long_sl_w` | ATR% widths with cost floors (frozen at 15m bar) | Exit geometry |
| `dist_to_tp_bps` | `(tp_px / last_1m − 1) × 1e4` | Room-to-target; reject if collapsed |
| `dist_to_sl_bps` | `(last_1m / sl_px − 1) × 1e4` | Reject if already inside SL buffer |
| `bars_to_vertical` | Minutes left until `min(decision_bar + 60m, MIS_FLAT_BY ≈ 15:00)` | Skip near-zero runway |
| `m1_pullback_depth` | % retrace of last 1m up-leg vs prior swing | Buy the dip, not the chase |
| `m1_range_compression` | `ATR_1m(5) / atr_pct` (TB atr) | Skip gap / halt-distorted bars |
| `vwap_dist_1m` | % dist of 1m close to session TWAP / VWAP (ATR-scaled) | Avoid extended prints |
| `consec_green_1m` | Count of consecutive up closes (cap 5) | Micro confirmation |
| `horizon_rank` | Tier 2 passthrough | Universe + size |
| `horizon_score` | Tier 2 passthrough (calibrated) | Size |
| `spread_proxy_bps` | `(high_1m − low_1m) / close × 1e4` | Liquidity / impact skip |

**Hard gates (not model features):** `long_entry_ok_expr`, auction bleed exclude, `tb_eligible_long == True`, name in Tier 2 top-K registry, not halted / circuit-pinned.

---

### Locked feature set (v1) — Short (~12, asymmetric)

| Feature | Shared? | Definition / note |
|---|---|---|
| `tb_eligible_short` | Gate | Hard — TP clears ~75 bps floor |
| `short_tp_w` / `short_sl_w` | TB | Frozen at 15m decision bar |
| `dist_to_tp_bps` | Shared idea | Room to short TP |
| `dist_to_sl_bps` | Shared idea | Reject near-SL |
| `bars_to_vertical` | Shared | **Shorter effective window** via earlier last entry |
| `m1_bounce_depth` | **Short** | % retrace of last down-leg — short the bounce, not chase breakdown |
| `m1_range_compression` | Shared | Same as Long |
| `vwap_dist_1m` | Shared | Avoid shorting already-extended-down prints |
| `consec_red_1m` | **Short** | Down-close confirmation |
| `afternoon_cover_risk` | **Short** | `time ≥ 13:00` and declining index / stock `rv` — squeeze tightener |
| `horizon_rank` / `horizon_score` | Shared | Universe + size |
| `spread_proxy_bps` | Shared | **Stricter ceiling** than Long |

**Short-only hard rules:** `short_entry_ok_expr` (last entry ≤ ~14:00 bar-end); after 13:00 require `consec_red_1m ≥ 2`; **no re-entry same symbol same session after one SL**; halt / circuit skip.

---

## Entry / Exit / Size rules (v1)

### Long (`TREND_UP` sleeve)

**Entry (bounded wait, deterministic):**

1. Name in Tier 2 top-K; `tb_eligible_long`; inside `long_entry_ok_expr`; past 9:30.
2. From the 15m decision bar, wait **up to 5 minutes** of 1m bars for a **pullback-then-reclaim**:
   - Prefer: 1m close within ~10–15 bps of session VWAP/TWAP **or** ≥ ~30–50% retrace of the last micro up-leg, then reclaim prior 1m high.
   - Liquidity: `spread_proxy_bps` below a fixed ceiling (tune on ADV tier).
3. If no clean setup by minute 5 → **fallback market/limit at then-current ask** (do not leave signals unfilled forever — that biases the sample).
4. Live preference: passive limit at bid with short cancel window; backtests must model fill probability, not assume perfect passive fills.

**Exit (frozen TB — no trail in v1):**

| Exit | Rule |
|---|---|
| TP | `entry_px × (1 + long_tp_w)` (+ 2 bps penetration for fill realism, matching TB) |
| SL | `entry_px × (1 − long_sl_w)` — stop on touch |
| Timeout | `min(15m_decision_bar + 60m, MIS_FLAT_BY ≈ 15:00 wall)` — clock from **decision bar** (bar-end / actionable), not delayed 1m entry |
| Regime flip | Optional soft flatten on post-hysteresis leave of `TREND_UP` (ideal if dwell logic is live) |

**Size:** `size_mult` from Tier 2 rank — e.g. rank 1–2 → 1.0×, 3–5 → 0.7×, 6–8 → 0.4×, else skip. Skip (not micro-size) if spread ceiling breached. Portfolio heat cap (e.g. max 5 concurrent) sits in a risk layer; Precision emits `size_mult` only.

### Short (`TREND_DOWN` sleeve)

**Entry (asymmetric):**

1. Name in Tier 2 bottom-K; `tb_eligible_short`; inside `short_entry_ok_expr` (≤ ~14:00 bar-end).
2. Bounded 5m wait for **bounce-then-breakdown**: ask/close ≥ ~15 bps above micro EMA / last swing, then break prior 1m low; `spread_proxy` ceiling **tighter** than Long.
3. After **13:00**: require `consec_red_1m ≥ 2` **or** skip (`afternoon_cover_risk`).
4. Fallback at minute 5 same as Long (mirrored). No second attempt same name after an SL that session.

**Exit:**

| Exit | Rule |
|---|---|
| TP | `entry_px × (1 − short_tp_w)` (− penetration) |
| SL | `entry_px × (1 + short_sl_w)` |
| Timeout | Same `H=4` / MIS flatten as TB; last entry already earlier than Long |
| No overnight | Cash shorts — vertical barrier never assumes next session |

**Size:** same rank scheme as Long, additionally ×0.5 when `afternoon_cover_risk` is set.

---

## Gate mapping (full cascade)

| Daily | Intraday | Tier 2 | Tier 3 |
|---|---|---|---|
| `NO_TRADE` | any | Flat | Flat |
| `HOSTILE` | `HIGH_VOL` | Flat / micro | Flat — no new Precision |
| `HOSTILE` | `CHOP` / `TREND_*` | Defensive / optional | Off for momentum Precision v1 |
| `AMBIGUOUS` / `SUPPORTIVE` | `TREND_UP` | Long LightGBM ON | **Long Precision ON** (top-K only) |
| `AMBIGUOUS` / `SUPPORTIVE` | `TREND_DOWN` | Short LightGBM ON | **Short Precision ON** (bottom-K only) |
| `AMBIGUOUS` / `SUPPORTIVE` | `CHOP` | MR sleeve (out of scope) | Out of scope |
| `AMBIGUOUS` / `SUPPORTIVE` | `HIGH_VOL` | Pause momentum | No new entries |

---

## Where judges disagreed

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Meta-filter in v1 | Required (≥55% P(TP)) | Optional after rules baseline | **Rules v1**; meta → measured follow-up |
| Order book / CVD | `obi_3m`, CVD divergence | Skeptical; prefer TB + light 1m | **Exclude L2/OBI/CVD in v1** |
| Trailing stop | BE trail @ 50% (L) / 40% (S) of TP path | Reject v1 (label mismatch) | **Reject trail in v1** |
| Entry style | Pullback to VWAP/EMA + 30s passive | Micro-breakout + 5m wait + fallback | **Pullback/reclaim within 5m + fallback** |
| Sizing owner | Meta-prob scaling | Tier 2 rank / score | **Rank/score in v1**; meta sizing later |
| Short hard flatten | Soft 14:45 exit preference | MIS 15:00 live + earlier last entry | **Keep TB/session locks** (`SHORT_LAST_ENTRY` ~14:00 bar-end, `MIS_FLAT_BY` 15:00 wall, `MIS_EXIT_BAR_END` 15:15 for 15m labels) + afternoon confirmation gate |
| Overall | REVISE | ACCEPT + minor | **ACCEPT with revisions** |

---

## Must exclude (both judges / consensus)

- Re-ranking or direction override of Tier 1 / 2  
- Recomputing ATR / TP / SL from post-decision 1m data (lookahead)  
- Picking the “best” 1m bar using future bars in backtests  
- Entries in **9:15–9:30** auction bleed  
- Ignoring **MIS ~15:00** live flatten  
- L2 order book / OBI / CVD / news NLP in v1  
- Trailing stops, multi-parameter 1m ML search, sector peer filters in v1  
- Same-day re-entry after SL on shorts without cooldown  
- Halted / circuit-band names  
- LLM as timing engine  
- Training any meta-filter without purged + embargoed walk-forward  

---

## NSE production constraints (Tier 3)

1. **1m pipeline** must be causal — features from closed 1m bars only; decision clock remains the 15m Tier 2 bar-end stamp.  
2. **Freeze TB geometry** at the 15m decision bar; 1m only chooses fill time / skip.  
3. Vertical timeout measured from **decision bar + H**, not from delayed entry (keeps labels and live exits aligned).  
4. Model **fills realistically** — do not assume perfect passive bid fills in research.  
5. Shorts: earlier last entry, afternoon confirmation, no same-session SL re-chase.  
6. Point-in-time Nifty 100 + ADV liquidity ceilings carry through from Tier 2.  
7. If meta-filter is added later: same purge/embargo discipline as Horizon; binary target = TB path success (`tb_label_* == +1` vs not), not a new return model.

---

## 80% lift priority

| Rank | Gemini Flash | Claude Sonnet | Consensus first build |
|---|---|---|---|
| 1 | Passive limit execution | Reuse TB TP/SL + eligibility verbatim | **Freeze TB exits + eligibility gates** |
| 2 | Meta-filter LightGBM | Rank/score size from Tier 2 | **Rank-based size; meta staged** |
| 3 | Asymmetric short cutoffs | Bounded-wait 1m entry + fallback | **5m pullback/reclaim + fallback; short asymmetry** |

---

## Ideal expansions (not v1 — staged later)

| Item | Source | Note |
|---|---|---|
| Meta-label LightGBM take/skip | Both | On TB outcomes + 1m features; purged CV; only after rules baseline |
| Breakeven / partial trail | Gemini | After live path-quality vs TB labels is validated |
| Shrink-only `H` under `HIGH_VOL` | Claude / TB doc | Port deferred TB hybrid — do not invent a second H regime early |
| L2 / multi-depth OBI | Gemini | Only with clean tick lineage |
| Portfolio vol-targeted sizing | Claude | Above Precision, not inside it |
| F&O routing for shorts | Gemini | Bypass cash short limits — separate product decision |
| Sector peer confirmation | Claude | Correlated-signal filter |

---

## Related: triple-barrier reuse (explicit)

Tier 3 does **not** redefine barriers. It consumes:

| TB artifact | Precision use |
|---|---|
| `long_tp_w` / `long_sl_w` / `short_*_w` | Absolute `tp_px` / `sl_px` at fill |
| `tb_eligible_*` | Hard skip |
| `H = 4`, MIS cutoffs | `vertical_deadline` |
| `c = 0.003`, 90 bps TP floor | Already inside eligibility / widths |
| `tb_label_*` / `tb_excess_ret_*` | Ideal meta-label training target only |

Primary stock selection remains Tier 2 excess-return LightGBM. Precision monetizes **path quality** by refusing bad fills and enforcing the same exits the labels assumed.

---

## Next build step

1. 1m feature builder for Precision Long / Short (tables above) joined to Tier 2 registry + TB widths.  
2. Rules engine: cascade gates → bounded-wait entry → frozen TP/SL/timeout → exit_reason logging.  
3. Backtest harness with causal 1m fills, MIS / bleed masks, and rank-based `size_mult`.  
4. Compare rules-only PnL / hit rate to TB label expectations on the same episodes.  
5. (Later) Optional meta-label LightGBM take/skip with purged walk-forward — only if step 4 shows under-monetization.

**Post-baseline (2026-08-07):** rules v1 is live and still ~−18 bps net after 30 bps friction. Selectivity / PnL optimization for the next cycle is locked in [cascade-selectivity-tweak-plan.md](cascade-selectivity-tweak-plan.md) (TOP_K 8→5, Long SUPPORTIVE-only, `edge_score` conviction gate; meta still staged).

Mean-reversion under `CHOP` remains a separate sleeve, not this verdict.
