# Tier 2 Horizon — Path-Strategy Pivot Verdict (v2)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Horizon Long / Short **path-strategy pivot** after v1 ranker + v1.1 hygiene stop  
**Status:** **STOP-MEMO** (peek budget 5/5 exhausted) — path-EV pivot partially advanced; Horizon-path PASS not achieved  
**Judges:** [Gemini Flash](41001860-7bb4-4fb9-9d1a-89f097d6a8d8), [Claude Sonnet](c88b3b0b-d573-4aab-826d-07d815dca8ff)  
**Date:** 2026-08-12  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Depends on:** [horizon-tier2-verdict.md](horizon-tier2-verdict.md) (v1 freeze), [horizon-tier2-eval-verdict.md](horizon-tier2-eval-verdict.md), [horizon-tier2-v11-revision.md](archive/horizon-tier2-v11-revision.md), [horizon-tier2-v11-long-stop-memo.md](archive/horizon-tier2-v11-long-stop-memo.md), [horizon-tier2-v11-short-stop-memo.md](archive/horizon-tier2-v11-short-stop-memo.md), [triple-barrier-verdict.md](triple-barrier-verdict.md), [cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md), [regime-tier1-stop-memo.md](archive/regime-tier1-stop-memo.md)  
**Does not reopen:** Regime search, Precision WS2, v1.1 hygiene levers (L1/L2/S1)

---

## Summary

| Decision | Locked choice |
|---|---|
| Why pivot | Cascade FAIL: Top-K StockTB+1 ~**7–11%**; H4 ≈ **−22 to −25 bps**; XS edge ~5–8 bps ≪ 30 bps |
| What failed | v1 LightGBM is a **working XS ranker**, not a path-density engine — excess IC ≠ TB+1 density |
| What not to do | More ranker hygiene; Precision monetization; Regime reopen; TP→P50 at H=4 |
| Pivot role | **Path-quality selector** inside Regime sleeve — primary = net path EV; XS aux default **off** |
| Primary horizon | **H = 6 bars / 90 minutes** (MIS sample-loss **PASS** — step 1) |
| TP posture | Keep cost floors (**Long ≥90 bps**, **Short ≥75 bps**); P75 is **reachability physics**, not a floating TP |
| Labels | Separate Long/Short; primary = **net path EV** `R_path − R_nifty − c`; aux excess weight **0** unless pre-registered |
| Features | Shared RS core (causal TOD-rv); Long continuation; Short anti-extension; **path-room demoted** (peek 2) |
| Build posture | **CHARTER STOPPED** — peek budget **5/5** exhausted; freeze locked demotions below; no Horizon-path PASS |

**One-line:** Pivot Horizon from ranking relative outperformance at 60m to selecting names whose **own path can clear economic TP within 90m** — the cascade leak is path density, not ordering skill.

---

## Dual-judge scores

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity vs evidence | 10/10 | 8/10 | **ACCEPT** — path density leak; soft-H3 stays foregrounded; “path factory” aspirational until measured |
| TP at P75 vs P50 | 10/10 | 8/10 | **ACCEPT** — P75 = reachability physics; floors stay cost-identity (90/75) |
| Vertical H→90m | 9.5/10 | 6/10 | **ACCEPT** — H=6 primary; MIS sample-loss **PASS** (step 1) |
| Rank 1–2 < 3–5 explanation | 10/10 | 7/10 | **ACCEPT as working hypothesis** — explains soft H3 / WS1; not proof until path scores clear mono |
| Path-label pivot | 9/10 | 5/10 | **REVISE→LOCK** — single primary: **path EV regression**; no A-or-B sprawl |
| Feature pivot | 9.5/10 | 4.5/10 | **REVISE→LOCK** — path-room OK iff causal TOD-rv + non-circularity / H10 audit |
| TB geometry pivot | 10/10 | 7/10 | **ACCEPT** floors; **explicit amend** to triple-barrier for H=6; no soft multiple reopen |
| Eval / ship gates | 9.5/10 | 5.5/10 | **REVISE→LOCK** — H5 primary lift; absolute TB+1 ≥15% and H4≥0 stay **report/diagnostic** |
| Reject-list / process | 10/10 | 4/10 | **ACCEPT rejects**; **LOCK peek budget = 5** + multiplicity vs v1.1’s 7 peeks |
| Overall | **ACCEPT** 9.7 | **REVISE** 6.2 | **ACCEPT WITH REVISIONS** |

**Judge one-liners**

- Gemini: expanding time to 90m and shifting to absolute path-quality selection is the only physically/economically sound way to clear 30 bps.  
- Claude: diagnosis and reject-list are evidence-true; do not lock until peek budget, single path label, non-circular path-room features, and H=6 sample-loss are hardened.

---

## Why the original Horizon strategy cannot meet cascade goals

### Evidence chain (locked)

| Fact | Implication |
|---|---|
| Regime I1/I5 FAIL | Never cleared as an economic gate — demotion correct; Regime CLOSED |
| Horizon H1/H2 PASS, Top-K TB+1 still ~7–11% | Inside admitted sleeves, **name/path selection** is the broken piece |
| WS1 “escalate Horizon / Regime” | Written before A0 + Horizon v1.1; A0 closed Regime → pointed at Horizon |
| Horizon v1.1 stop (L1/L2/S1 hygiene FAIL) | Hygiene on the current ranker failed; gap is **path density**, which Horizon owns |
| Precision WS0/WS1 | Not under-monetizing; ~9/10 admitted fires are non-`TB=+1` |

**Bottom line:** Cascade fails because ~9/10 admitted names are not `TB=+1` paths, while XS edge is only ~5–8 bps before 30 bps cost. Precision already showed it isn’t the leak. Horizon’s current LightGBM is a working ranker, not a path-density engine.

### Critical questions — locked answers

#### 1. Should take-profit goals be closer to P50 or P75 of market/stock moves?

**Aim near P75 of absolute moves at the chosen vertical H for reachability — not P50. Do not float TP to a percentile; cost floors stay fixed.**

| Why not P50 | Why P75 (physics only) |
|---|---|
| Median 60m stock moves are ~**28–50 bps** across sectors — **below** Long 90 / Short 75 floors | A cost-aware TP must sit in the **upper quartile of achievable path travel** inside `H`, else `TB=+1` is structurally rare |
| P50 ≈ noise + cost dead-zone under 30 bps | Cascade needs paths that can clear **≥3×c** (Long) / **~2.5×c** (Short) with non-trivial hit rate |
| Lowering TP to P50 without cutting cost **destroys economics** | Keep floors; change **H and selection**, not the economic TP identity |

Sector backing (absolute % move; ATR multiples tight across sectors):

| Window | Typical P50 | Typical P75 | ATR mult P50 / P75 |
|---|---:|---:|---:|
| **60m** | ~0.28–0.50% | ~0.55–1.03% | ~0.68–0.75 / ~1.4–1.5 |
| **90m** | ~0.36–0.65% | ~0.68–1.28% | ~0.87–0.95 / ~1.8–1.9 |

Reading vs cascade TP:

- At **60m**, Long **90 bps** sits **at or above P75** for most Nifty-100 sectors (Pvt Bank / IT / Auto / FMCG P75 ≪ 90 bps; only high-vol sleeves approach it). → structural `TB=+1` rarity (~7–11%) is **physics**, not just model misspecification.
- At **90m**, P75 % moves and ~1.8× ATR14 put **90 bps** closer to a **reachable upper-quartile path** for a larger slice of the universe — still selective, no longer near-impossible for mid-vol names.

#### 2. Should the vertical timeout be > 60 minutes if TP stays ~90 bps?

**Yes — primary vertical barrier → H = 6 (90m).** MIS sample-loss **PASS** (step 1). Formalized in [triple-barrier-verdict.md](triple-barrier-verdict.md) v2 amend.

| Keep H=4 + 90 bps TP | Move H→6 + keep 90 bps TP |
|---|---|
| Asks for a ~P75–P90 event in a quiet book | Aligns economic TP with upper-quartile 90m travel |
| Explains TIMEOUT-dominated exits and dead-zone mass | Buys time for vol-scaled barriers without lowering cost floors |
| MIS OK at H=4, economics fail | MIS: pull last entries earlier (Long ≈ **13:45**, Short ≈ **13:30** bar-end) |

**Precondition (Claude lock):** before treating H=6 as ship-primary, quantify eligible-bar / session / episode loss vs H=4 on Fold A/B calendars — especially Short (~½ Long bars already). If Short episodes collapse below min-N, either (a) keep H=6 Long-primary / Short dual-report, or (b) escalate sample design — do **not** silently discover this on peek #1.

Do **not** lower Long TP below 90 bps / Short below 75 bps while friction stays 30 bps. Do **not** invent sector-scaled `H` tables. Horizontal vol multiples stay frozen until a **separate** report-first note; no soft reopen inside this charter.

#### 3. Why do ranks 1–2 perform worse than ranks 3–5?

**Working hypothesis (gated until disproven under path scores): XS excess ranking rewards extension; barrier success rewards unfinished travel with room.**

| Mechanism | Effect on ranks 1–2 |
|---|---|
| Label = forward excess vs Nifty | Top scores = already-winning RS / breakdown extremes |
| Features amplify chase | Rank 1–2 = **most extended** names in the sleeve |
| TB needs further absolute travel to hit 90/75 bps before SL/timeout | Extended names **mean-revert or timeout** → soft H3 + WS1 rank inversion |
| Mid-ranks (3–5) | Often still have **path room** → better barrier economics despite lower XS score |

L1 FAIL supports “not an inference patch.” Soft-H3 language remains **mandatory** on every Long claim until path scores clear `m12 ≥ m3k` dual-fold — explanation ≠ resolution.

---

## Pivot charter — Horizon as path-quality selector

### Role change

| v1 (frozen) | v2 pivot |
|---|---|
| Cross-sectional stock **ranker** on excess return | Cross-sectional **path-quality selector** |
| Success = IC / Top-K−Rest excess (H1/H2) | Success = **H5 lift** + rising absolute Top-K TB+1 (readout); H1/H2 secondary non-null checks |
| Does not re-forecast Regime direction | Unchanged — still conditional on Regime sleeve |
| “Horizon-ranker ship” | **“Horizon-path PASS on A+B”** — never cascade net ≥ 0 from Horizon alone |

Forbidden language until measured: “path factory,” “cascade-ready,” “Horizon closed the cascade leak.”

### Horizon strategy goals (v2)

| Goal | Lock |
|---|---|
| Primary objective | Maximize Top-K **net path EV** and **H5** (Top-K − Rest StockTB+1) under frozen cost, inside Regime sleeve |
| Primary H | **6 × 15m = 90 minutes** (sample-loss PASS; step 1 closed) |
| Long K / Short K | Keep **5 / 3**; K-sweep diagnostic only |
| Absolute Top-K TB+1 ≥15% | **Report-only** until post-baseline dual-judge promotes it |
| H4 (Top-K − 30 bps) | **Diagnostic** — may stay negative even if path density rises; not a ship substitute |
| Anti-goal | Do not optimize H1/H2 at the expense of TB+1 density |

### Triple-barrier goals (v2 alignment)

| Item | v1 lock | v2 pivot |
|---|---|---|
| Cost `c` | 0.30% | **Unchanged** |
| Long TP / SL floors | ≥90 bps / ≥45 bps | **Unchanged floors** |
| Short TP / SL floors | ≥75 bps / ≥45 bps | **Unchanged floors** |
| Vol scale | TOD `rv_15_mean` | **Unchanged**; multiples frozen this charter |
| Vertical `H` | Hard **H=4** | Primary **H=6** (explicit amend to [triple-barrier-verdict](triple-barrier-verdict.md)); H=4 compare archived in step 1 log only |
| Sector-scaled H | None | **None** |
| Eligibility | Skip if vol TP cannot clear cost floor | Same at **H=6** |
| Dead zone | ±30 bps on timeout | Unchanged |
| MIS cutoffs | Long ~14:15 / Short ~14:00 (H=4) | Long ~**13:45** / Short ~**13:30** bar-end (H=6) |

**Design rule:** economic TP identity stays at cost multiples; **time budget expands** to match P75 path physics.

---

## Features & labels — Long vs Short

### Labels (v2) — single primary locked

| Model | Primary label (LOCKED) | Auxiliary | Inference |
|---|---|---|---|
| **Long** | Regression on net path EV: `R_path_stock − R_nifty_same_window − c` over H=6 under cascade-valid `TREND_UP` | Excess-only / TB=+1 head: **weight = 0** unless a pre-registered ablation turns them on with chase monitors | Rank by calibrated path score; Top-K |
| **Short** | Same net path EV on `TREND_DOWN` (more negative EV = better short actionable score after side adjust) | Same aux default **off** | Separate Short gates; B1 stays inactive until Short dual-fold H5 under **this** charter |

**Also locked:**

1. No soft “classification or regression” choice at build time — **path EV regression is primary**.  
2. Pre-register imbalance / episode weighting **before peek #1** (TB=+1 rarity; unweighted binary was rejected as primary).  
3. Long ≠ Short separate models; do not sign-flip Long into Short.  
4. Short Fold-A H5 FAIL history stays in the charter — do not subsume under optimism.

### Features — shared path core

| Feature | Role | vs v1 |
|---|---|---|
| `tp_room_atr` | Distance to economic TP floor / causal TOD `rv_15_mean` | **New** — requires non-circularity lock below |
| `sl_room_atr` | Distance to SL floor / same causal rv | **New** — same audit |
| `bars_to_mis_exit` | Remaining bars until MIS-safe exit / H | **New** |
| `range_compress_4` | Trailing range vs TOD baseline | **New** |
| `path_efficiency_4` | \|net\| / sum\|r\| over last 4 bars | **New** |
| `rel_ret_15_vs_nifty` | RS / RW core | Keep |
| `rel_ret_60_vs_nifty` | Persistence | Keep; **winsorize / XS-rank** extremes |
| `stock_r_15` | Absolute momentum confirm (v1) | **Demoted Long (peek 3)**; **kept Short (peek 5 reject)** |
| `stock_rv_15` / `stock_volz_15` | Intensity + participation | Keep |
| `stock_vwap_dist` | VWAP location | Keep |
| `adv_rank_20d` | Liquidity | Keep (critical Short) |
| `bars_since_regime_flip` | Episode age | Keep |
| `tod_sin` / `tod_cos` | Clock | Keep |
| `vol_regime_ratio` / `index_vwap_dist` | Tier 1 pass-through | Keep |

**XS rank features:** live percentile of RS within eligible sleeve — prefer **rank** over raw extreme magnitude.

### Path-room non-circularity lock (Claude)

`tp_room_atr` / `sl_room_atr` are **barrier-geometry transforms**, not free alpha:

1. Use **only** causal same-clock absolute `rv_15_mean` (same definition as TB builder).  
2. Must **not** use same-bar realized range that encodes the forward path, daily ATR, or any quantity computed from the label window.  
3. Pre-first-peek **H10-style audit**: scores must not be monotone reconstructions of TB eligibility / horizontal barriers; if lift vanishes when path-room features are ablated from the *label side* only, treat as tautology.  
4. First build may include them; first gated claim requires the audit note. Forbid treating path-room as proven “path skill” without that note.

### Features — Long-only

| Feature | Role |
|---|---|
| `pullback_depth_atr` | Continuation with room, not breakout chase |
| `dist_to_prev_day_high` | Breakout proxy — pair with `tp_room_atr` |
| `orb_breakout_flag` | Reference; down-weight if already far through ORB |
| `sector_rel_strength` | Within-sector leadership |
| `trend_strength_daily` / `rolling_beta_60d` | Structural context |
| `pct_from_20d_high` | **Winsorize** — extreme proximity = chase risk |

### Features — Short-only

| Feature | Role |
|---|---|
| `bounce_risk_zscore` | **Promote** — anti-extension |
| `downside_acceleration` | Panic quality |
| `sector_rel_weakness` | Lagging within sector |
| `dist_to_prev_day_low` / `orb_breakdown_flag` | Breakdown + room check |
| `pct_from_52w_high` | Fresh vs stale crash |

F&O-active Short filter remains **blocked** until a point-in-time membership list exists (carry from v1.1 D1). Optional build step: freeze that list; do not invent coverage mid-peek.

### Explicit demotions

- Raw chase magnitude without path-room.  
- Pure excess as primary when evaluating on TB+1.  
- Inference patches (L1/L2) as substitutes for label/feature pivot.  
- F&O OI / order book in first v2 build.

---

## What stays frozen from v1

| Frozen | Rationale |
|---|---|
| Regime CLOSED soft overlay | A0 stop memo |
| Separate Long / Short models | Asymmetry + scarcity |
| Cascade sample filter | No CHOP / HIGH_VOL / NO_TRADE training |
| Purged + embargoed WF | Embargo ≥ **H=6** + 1 trading day |
| Point-in-time Nifty 100 + ADV | Live transfer |
| Auction bleed exclude; MIS flatten discipline | NSE constraints |
| Friction 30 bps; TP/SL **floors** | Do not reopen cost debate |
| Precision Phase 1 / no WS2 | Upstream must move first |
| v1 ranker artifacts | Baseline comparator only — do not edit v1 verdict for v2 |

---

## Eval / ship gates (locked)

| Gate | Role under v2 |
|---|---|
| **H5** Top-K vs Rest StockTB+1 (H=6 geometry, naive close) | **PRIMARY lift gate** — Long and Short separately |
| Absolute Top-K TB+1 | **Report-only** (15% aspirational readout); promote only via fresh dual-judge after baseline |
| **H4** | Diagnostic companion — not ship |
| H1 / H2 | Secondary — must not go null; insufficient alone |
| H3 | Stay gated until soft 1–2 < 3–K clears under **path scores** |
| H10 + universe | Preconditions |
| Short dual-fold H5 | Required for any Short “Horizon-path PASS”; B1 inactive until then |
| Long soft-H3 | Unresolved until cleared — qualifier mandatory |

**Ship language:** “Horizon-path PASS on A+B” ≠ cascade net ≥ 0. Re-measure Precision Phase 1 book only after upstream A+B.

---

## Process locks (peek budget)

| Item | Lock |
|---|---|
| Prior burn | v1.1 spent **7** Fold A+B peeks — multiplicity baseline |
| v2 budget | **Max 5** harness Fold A+B invocations this charter (baseline counts as 1) |
| Fold policy | Same A/B calendars allowed **with** multiplicity accounting; no silent extra peeks |
| Stop | Exhaust budget or dual-fold path gates clear — then stop-memo / merge slice; no grid search |
| Forbidden | Hyperparam grid on A+B; pooled Long+Short; Fold C locks; Precision fills in H5; cascade PnL claims |

---

## Rejected alternatives (locked)

| Alternative | Why reject |
|---|---|
| More v1.1 hygiene (L1/L2/S1 retunes) | Measured FAIL |
| Lower TP to ~P50 at H=4 | Fails 3×c economics under 30 bps |
| Keep H=4 + 90 bps + better RS features only | Physics: 90 bps ≳ P75@60m for most sectors |
| Precision WS2 / meta headline | Cannot monetize non-+1 paths |
| Reopen Regime | I1/I5 closed; not the Top-K path leak |
| Pooled Long+Short gate | Long ≠ Short |
| Sector-specific vertical H | Parameter sprawl |
| Soft-promote 15% TB+1 or H4≥0 to ship | Gate creep — Claude veto |

---

## Build sequence

1. Pre-build: **MIS sample-loss report** (H=6 cutoffs vs H=4) on Fold A/B calendars — Long and Short. → **DONE** (below)  
2. Explicit amend note on [triple-barrier-verdict.md](triple-barrier-verdict.md): primary vertical **H=6**; floors unchanged. → **DONE** (2026-08-12)  
3. TB builder + Horizon labels: H=6 primary. → **DONE** (2026-08-12)  
4. Feature pipeline + path-room **non-circularity / H10 note**. → **DONE** (below)  
5. Train separate Long/Short path-EV models (aux excess off). → **DONE** (below)  
6. Baseline A+B under revised gates (peek 1 of 5). → **DONE** (below)  
7. At most four further pre-registered levers within budget.
   - Free diagnostic (Spearman + S2 re-read) **DONE** — [horizon-path-room-h10-note.md](archive/horizon-path-room-h10-note.md); peek ledger untouched.
   - **Peek 2:** path-room ablation (`--ablate-path-room`) → **DONE** (below) — demote path-room (hurts H5; not tautology).
   - **Peek 3:** Long chase / soft-H3 bundle (`--long-chase-bundle`) → **DONE** (below) — Long dual-fold H5 PASS; H2 dual FAIL; demote Long `stock_r_15` + Long `episode_balanced=True`.
   - **Peek 4:** Short aux-excess (`--short-aux-excess`, w=0.5) → **DONE** (below) — **REJECT**; keep aux weight 0.
   - **Peek 5:** Short `stock_r_15` demote (`--short-chase-demote`) → **DONE** (below) — **REJECT**; keep Short `stock_r_15`.
   - **Charter STOP** — peek budget exhausted (5/5); see stop section below.
8. Precision Phase 1 book re-measure — **blocked** until a future charter clears Horizon-path PASS.

### Step 1 results — MIS sample loss (2026-08-12)

**Harness (archived):** `python -m src.experiments.analyze_horizon_mis_sample_loss --folds A,B` — script removed after PASS; do not re-run.  
**Log:** `logs/horizon_mis_sample_loss_ab.txt`  
**Cutoffs:** H4 Long 14:15 / Short 14:00 → H6 Long **13:45** / Short **13:30**  
**Mask:** cascade fit sleeve (tradeable daily ∩ TREND_* ∩ `valid_label_*`) — **no** feature `drop_nulls` (isolates MIS clock loss; absolute bar counts are not comparable 1:1 to v1.1 trainer H6 rows).  
**Regime runs:** Fold A `e9dbc994…` · Fold B `7fff95a9…` (same as Horizon A+B eval).

| Fold · split · side | H4 bars / sess / eps | H6 bars / sess / eps | Δ bars | Δ sess | Δ eps | Min-N |
|---|---:|---:|---:|---:|---:|---|
| A train Long | 176704 / 316 / 402 | 150533 / 280 / 349 | **14.8%** | 11.4% | 13.2% | OK |
| A train Short | 235021 / 400 / 627 | 208104 / 387 / 592 | **11.5%** | 3.2% | 5.6% | OK |
| A test Long | 68050 / 103 / 142 | 57495 / 96 / 128 | 15.5% | 6.8% | 9.9% | OK |
| A test Short | 80643 / 128 / 198 | 71481 / 125 / 176 | 11.4% | 2.3% | 11.1% | OK |
| B train Long | 193815 / 329 / 426 | 163814 / 298 / 380 | **15.5%** | 9.4% | 10.8% | OK |
| B train Short | 250996 / 421 / 652 | 222425 / 408 / 603 | **11.4%** | 3.1% | 7.5% | OK |
| B test Long | 64087 / 96 / 143 | 54585 / 93 / 126 | 14.8% | 3.1% | 11.9% | OK |
| B test Short | 94997 / 137 / 211 | 84771 / 133 / 197 | 10.8% | 2.9% | 6.6% | OK |

**Precondition verdict:** **PASS** — H=6 MIS pull-back costs ~**11–16%** sleeve bars (~3–11% sessions). Short train session loss is mild (~3%); Long loses more afternoon mass (~9–11% sessions). **No fold breaches** eval min-N floors (Long ≥100 bars / ≥30 sess; Short ≥150 / ≥30). Median bars/episode stays stable.

**Lock:** H=6 remains viable as **primary vertical H** for the path-model charter. Steps 2–6 **DONE**. Path-EV baseline (peek 1/5) is recorded below — **not** Horizon-path PASS.

### Step 6 results — path-EV A+B baseline (2026-08-12) — peek **1 of 5**

**Harness:** `python -m src.experiments.eval_horizon` (train path-EV + gated holdout).  
**Logs:** `logs/horizon_path_ev_baseline_fold_a.txt` · `logs/horizon_path_ev_baseline_fold_b.txt`  
**Locks in force:** H=6 TB; aux excess off; L1/S1 off; K=5/3; H5 primary; absolute TB+1 / H4 report-only.

| Gate | Long A | Long B | Short A | Short B | Dual-fold |
|---|---|---|---|---|---|
| universe / H10 | PASS | PASS | PASS | PASS | OK |
| H1 (XS IC) | 0.066 PASS | 0.070 PASS | 0.021 PASS | 0.031 PASS | secondary OK |
| H2 (Top−Rest excess) | 0.0009 PASS | 0.0004 PASS | 0.0002 **FAIL** | 0.0003 **FAIL** | Short FAIL |
| H3 | PASS soft (m12 0.0004 &lt; m3k 0.0008) | PASS soft (m12=m3k 0.0004) | PASS soft | PASS soft | soft unresolved |
| **H5** (primary) | 0.011 [−0.008, 0.033] **FAIL** | −0.010 [−0.029, 0.011] **FAIL** | 0.012 [−0.008, 0.033] **FAIL** | 0.030 [0.009, 0.053] PASS | **FAIL** both sleeves |
| Top-K TB+1 (report) | 8.1% | 4.9% | 13.9% | 13.6% | ≪ 15% aspirational |
| H4 (diag) | −21 bps | −26 bps | −28 bps | −27 bps | neg |

**Verdict:** **Horizon-path FAIL on A+B** at peek 1. Ranking skill (H1) still non-null on both sleeves; **primary H5 does not clear** dual-fold for Long or Short. Short also loses H2. Soft-H3 unresolved (Long A still m12 &lt; m3k). Absolute Top-K TB+1 stays single-digit Long / ~14% Short.

**Peek ledger:** **1 / 5** spent. Remaining ≤4 pre-registered levers only — no hyperparam grid; no Precision/Regime reopen.

### Step 7 / Peek 2 — path-room ablation A+B (2026-08-12) — peek **2 of 5**

**Harness:** `python -m src.experiments.eval_horizon --ablate-path-room`  
**Logs:** `logs/horizon_path_ev_ablate_path_room_fold_a.txt` · `logs/horizon_path_ev_ablate_path_room_fold_b.txt`  
**Free diag first:** [horizon-path-room-h10-note.md](archive/horizon-path-room-h10-note.md) — high |ρ| with eligibility expected; weak eligible→TB=+1 ρ.

| Gate | Long A | Long B | Short A | Short B | Dual-fold |
|---|---|---|---|---|---|
| H1 | 0.066 PASS | 0.061 PASS | 0.037 PASS | 0.028 PASS | OK |
| H2 | 0.0010 PASS | 0.0008 PASS | 0.0006 **PASS** | 0.0003 **FAIL** | Short H2 still soft |
| H3 | PASS soft (m12 0.0006 &lt; m3k 0.0007) | PASS (m12=m3k 0.0007) | PASS soft | PASS soft | Long soft unresolved on A |
| **H5** | 0.028 [0.008, 0.051] **PASS** | 0.001 [−0.017, 0.019] **FAIL** | 0.023 [0.003, 0.047] **PASS** | 0.040 [0.019, 0.063] **PASS** | Long FAIL · **Short H5 PASS** |
| Top-K TB+1 | 9.5% | 6.0% | 15.0% | 15.1% | Short ~15% readout |
| H4 | −20 bps | −22 bps | −24 bps | −27 bps | neg |

**vs baseline (peek 1, path-room on):** Long A H5 FAIL→PASS; Long B −1.0pp→+0.1pp (still FAIL); Short A FAIL→PASS; Short B 3.0pp→4.0pp PASS; Short A H2 FAIL→PASS. Absolute Top-K TB+1 rose on all four cells.

**Interpretation:** Path-room is **not** a useful tautology of TB skill — ablating it **improves** H5 / TB+1. Demote `PATH_ROOM_FEATURES` from the default Long/Short lists for all remaining peeks. Do **not** call this Horizon-path PASS: Long dual-fold H5 still FAIL; Short H2 Fold B still FAIL; soft-H3 unresolved; abs TB+1 / H4 stay report-only.

**Peek ledger:** **2 / 5** spent. Remaining ≤3. Next pre-registered: Long chase / soft-H3 bundle on path-room-off baseline.

### Step 7 / Peek 3 — Long chase bundle A+B (2026-08-12) — peek **3 of 5**

**Harness:** `python -m src.experiments.eval_horizon --long-chase-bundle`  
**Logs:** `logs/horizon_path_ev_long_chase_bundle_fold_a.txt` · `logs/horizon_path_ev_long_chase_bundle_fold_b.txt`  
**Lever (Long only):** demote `stock_r_15` + `episode_balanced=True`. Short = path-room-off baseline (unchanged vs peek 2).

| Gate | Long A | Long B | Short A | Short B | Dual-fold |
|---|---|---|---|---|---|
| H1 | 0.016 PASS | 0.053 PASS | 0.037 PASS | 0.028 PASS | OK (Long A weak) |
| H2 | −0.0002 **FAIL** | 0.0005 **FAIL** | 0.0006 PASS | 0.0003 **FAIL** | **Long H2 FAIL** · Short H2 soft |
| H3 | PASS soft (m12 −0.0008 &lt; m3k −0.0003) | PASS (m12 0.0008 &gt; m3k 0.0002) | PASS soft | PASS soft | Long soft unresolved on A; **B cleared** |
| **H5** | 0.029 [0.003, 0.055] **PASS** | 0.027 [0.008, 0.047] **PASS** | 0.023 [0.000, 0.046] **PASS** | 0.040 [0.019, 0.063] **PASS** | **Long H5 PASS** · **Short H5 PASS** |
| Top-K TB+1 | 9.9% | 8.7% | 15.0% | 15.1% | Long up vs peek 2 |
| H4 | −32 bps | −25 bps | −24 bps | −27 bps | neg |

**vs peek 2 (path-room off, chase on):** Long B H5 FAIL→**PASS** (dual-fold Long H5 clears for the first time). Long A H5 ≈ flat. Long H2 PASS→**FAIL** both folds; Long A H1 0.066→0.016. Soft-H3 clears on B only. Short identical to peek 2 (as designed).

**Interpretation:** Chase demotion + Long episode weighting trades XS Top−Rest excess (H2) for StockTB+1 lift (H5) — aligned with the anti-goal (do not optimize H1/H2 at TB+1 expense). **Lock for remaining peeks:** Long demote `stock_r_15`; Long `episode_balanced=True`. Short keeps `stock_r_15`. Do **not** claim Horizon-path PASS: Long H2 dual-fold FAIL; Long soft-H3 A unresolved; Short H2 B FAIL; H4 still negative.

**Peek ledger:** **3 / 5** spent. Remaining ≤2. Next: Short-targeted lever (H2 Fold B) on this locked baseline.

### Step 7 / Peek 4 — Short aux-excess A+B (2026-08-12) — peek **4 of 5**

**Harness:** `python -m src.experiments.eval_horizon --short-aux-excess`  
**Logs:** `logs/horizon_path_ev_short_aux_excess_fold_a.txt` · `logs/horizon_path_ev_short_aux_excess_fold_b.txt`  
**Lever (Short only):** mix `fwd_excess_ret` at pre-registered `SHORT_AUX_EXCESS_WEIGHT=0.5` into path-EV target. S2 PM-cut was rejected (free diag). Long = peek-3 locked defaults (unchanged). Chase monitors = H1/H2/H3 gated readout.

| Gate | Long A | Long B | Short A | Short B | Dual-fold |
|---|---|---|---|---|---|
| H1 | 0.016 PASS | 0.053 PASS | 0.023 PASS | 0.033 PASS | OK |
| H2 | −0.0002 **FAIL** | 0.0005 **FAIL** | 0.0003 **FAIL** | 0.0003 **PASS** | Long H2 FAIL · Short H2 A FAIL |
| H3 | PASS soft | PASS (m12&gt;m3k) | PASS (m12=m3k) | PASS (m12&gt;m3k) | — |
| **H5** | 0.029 PASS | 0.027 PASS | 0.013 [−0.010, 0.036] **FAIL** | 0.044 [0.022, 0.066] **PASS** | Long PASS · **Short H5 FAIL** |
| Top-K TB+1 | 9.9% | 8.7% | 14.4% | 15.5% | — |
| H4 | −32 bps | −25 bps | −27 bps | −27 bps | neg |

**vs peek 3 / peek-2 Short baseline:** Short A H5 PASS→**FAIL**; Short A H2 PASS→FAIL; Short B H5/H2 improve slightly (H2 FAIL→PASS). Classic A/B oscillation — not robust dual-fold skill.

**Interpretation:** Mixing XS excess back into the Short path-EV label **regresses** the primary H5 bridge on Fold A. **REJECT** — keep `AUX_EXCESS_WEIGHT=0` / do not enable Short aux by default. Confirms path-EV-primary lock: excess aux is not a free H2 patch.

**Peek ledger:** **4 / 5** spent. Remaining ≤1. Peek 5 = last shot (e.g. Short `stock_r_15` demote parallel to Long, or consolidator re-gate) else stop-memo.

### Step 7 / Peek 5 — Short chase demote A+B (2026-08-12) — peek **5 of 5**

**Harness:** `python -m src.experiments.eval_horizon --short-chase-demote`  
**Logs:** `logs/horizon_path_ev_short_chase_demote_fold_a.txt` · `logs/horizon_path_ev_short_chase_demote_fold_b.txt`  
**Lever (Short only):** demote `stock_r_15` (Long peek-3 parallel). Long = peek-3 locked defaults.

| Gate | Long A | Long B | Short A | Short B | Dual-fold |
|---|---|---|---|---|---|
| H1 | 0.016 PASS | 0.053 PASS | 0.038 PASS | 0.030 PASS | OK |
| H2 | −0.0002 **FAIL** | 0.0005 **FAIL** | 0.0003 **FAIL** | 0.0003 **PASS** | Long H2 FAIL · Short A FAIL |
| H3 | PASS soft | PASS (m12&gt;m3k) | PASS (m12&gt;m3k) | PASS soft | — |
| **H5** | 0.029 PASS | 0.027 PASS | −0.006 [−0.025, 0.014] **FAIL** | 0.045 [0.024, 0.067] **PASS** | Long PASS · **Short H5 FAIL** |
| Top-K TB+1 | 9.9% | 8.7% | 12.4% | 15.6% | Short A down |
| H4 | −32 bps | −25 bps | −27 bps | −27 bps | neg |

**vs peek-3 Short baseline (stock_r_15 on):** Short A H5 PASS→**FAIL** (point estimate negative); Short B ≈ flat/slightly up; Short A H2 PASS→FAIL. Demoting Short chase **hurts** Fold A path density — opposite of Long peek 3.

**Interpretation:** **REJECT** — keep `stock_r_15` on Short. Asymmetry lock stands (Long ≠ Short): Long chase demotion helped H5; Short chase demotion destroyed Fold A H5.

**Peek ledger:** **5 / 5** spent — budget exhausted.

---

## Charter stop (2026-08-12)

**Status:** **STOP-MEMO this v2 path-EV charter** — peek budget exhausted without Horizon-path PASS.

### Locked carry-forward (defaults)

| Item | Lock |
|---|---|
| H=6 / cost floors / Regime CLOSED / Precision WS2 blocked | Unchanged |
| Path-room features | **Demoted** (peek 2) |
| Long `stock_r_15` | **Demoted**; Long `episode_balanced=True` (peek 3) |
| Short `stock_r_15` | **Keep** (peek 5 reject) |
| Aux excess weight | **0** (peek 4 reject) |
| Best measured dual-fold H5 | Both sleeves PASS under peek-3 locked config |
| Horizon-path PASS | **NO** — Long H2 dual FAIL; Short H2 Fold B FAIL; Long soft-H3 A; H4 neg; abs TB+1 still ≪ ship |

### What was proven / disproven

| Claim | Outcome |
|---|---|
| Path density is the cascade leak; XS ranker ≠ path engine | Supported (H1 non-null while H5 hard) |
| H=6 + path-EV label is viable to train | Supported (sample-loss PASS; non-null CV ICs) |
| Path-room features are free path skill | **Disproven** — ablation helped |
| Long chase demotion lifts TB+1 | **Supported** for H5 dual-fold; costs H2 |
| Short aux-excess / Short chase demote clear H2 | **Disproven** — both regress Fold A H5 |
| Path-selector closes cascade leak this cycle | **Unproven** — stop |

### Forbidden next moves (carry)

No silent extra A+B peeks · no hyperparam grid · no Regime/Precision reopen · no lower TP / revert H=4 · no “Horizon-path PASS” / “cascade-ready” language · no B1 Short activate.

### Allowed next work (new charter only)

Fresh dual-judge charter with new peek budget if pursuing Horizon further (e.g. Long H2 repair without sacrificing H5; Short H2 Fold B without aux/chase levers already rejected). Otherwise escalate cascade docs: Horizon contributes partial path lift under locks above; book PnL still blocked upstream.

### Step 5 results — path-EV models (2026-08-12)

**Code:** `fit_horizon_gbm` trains on signed ``tb_excess_ret_*`` (net path EV); ``AUX_EXCESS_WEIGHT = 0``; Short ``target_sign = −1`` keeps ascending rank + eval side-flip.  
**Harness:** `python -m src.pipelines.horizon_pipeline` (train + holdout score; **not** gated eval — peek ledger untouched).  
**Logs:** `logs/horizon_path_ev_train_fold_a.txt` · `logs/horizon_path_ev_train_fold_b.txt`  
**Regime runs:** Fold A `e9dbc994…` · Fold B `7fff95a9…`

| Fold · side | Train bars / sess / eps | Val path-EV IC | CV test path-EV IC | Holdout rows |
|---|---:|---:|---:|---:|
| A Long | 115302 / 265 / 329 | 0.0398 | 0.0530 | 87887 |
| A Short | 37352 / 279 / 356 | 0.0948 | 0.1223 | 109308 |
| B Long | 118198 / 280 / 345 | 0.1643 | 0.1409 | 83101 |
| B Short | 35892 / 288 / 360 | 0.1857 | 0.1826 | 129004 |

**Read:** Both sleeves train under H=6 + TB-eligible path-EV with non-null CV ICs. Short train mass is thinner than Long (eligibility + MIS) but above min-N. Trainer IC is **diagnostic only** — not a ship gate.  
**Lock:** Proceed to step 6 gated A+B (H5 primary). Do **not** claim Horizon-path PASS from these ICs.

### Step 4 results — path-room features + H10 note (2026-08-12)

**Note:** [horizon-path-room-h10-note.md](archive/horizon-path-room-h10-note.md)  
**Code:** `src/features/horizon.py` · `PATH_ROOM_FEATURES` / updated `LONG_FEATURES` / `SHORT_FEATURES` in `src/horizon/horizon_model.py`

| Feature | Sleeve | Definition |
|---|---|---|
| `tp_room_atr_long` | Long | `90bps / rv_15_mean` (causal TOD) |
| `tp_room_atr_short` | Short | `75bps / rv_15_mean` |
| `sl_room_atr` | Both | `45bps / rv_15_mean` |
| `bars_to_mis_exit` | Both | `min(bars to 15:15, H_BARS)` |
| `range_compress_4` | Both | `rv_15_mean / 4-bar range%` |
| `path_efficiency_4` | Both | `\|net 4-bar\| / sum\|r\|` |
| `pullback_depth_atr` | Long | `(4-bar high − close) / rv_15_mean` |
| `rel_ret_15_xs_rank` | Both | XS percentile of RS at the bar |
| Chase demotion | Both | XS winsorize 1%/99% on `rel_ret_*`, `pct_from_20d_high` |

**Circularity lock:** path-room may ship in the first build; **first gated A+B claim** requires the H10 note + optional path-room ablation lever. Do not call path-room proven alpha.

### Step 3 results — label builders (2026-08-12)

| Surface | Primary (unscoped names) | Secondary |
|---|---|---|
| Horizon excess | `fwd_excess_ret`, `valid_label_*` at **H=6** | — |
| Triple barrier | `tb_label_*`, `tb_excess_ret_*` at **H=6** | — |
| MIS cutoffs | `LONG/SHORT_LAST_ENTRY` (13:45 / 13:30) | — |
| Cascade `H_BARS` | **6** in `src/utils/eval_common.py` (Regime / Horizon / Precision) | — |
| Precision `HORIZON_MINUTES` | `H_BARS × 15` (=90) from same module | — |
| Purged CV `embargo_bars` | **6** | — |

**Code:** `src/labels/horizon.py`, `src/labels/triple_barrier.py`, `src/pipelines/build_horizon_features.py`, `src/horizon/eval/common.py`, `src/precision/session.py`, `src/horizon/horizon_model.py`.

---

## Dangerous overclaims (forbid)

- “Path factory” / cascade leak **closed** before measured dual-fold H5 + TB+1 readout  
- “Cascade-ready” / bare “Long ship” / Horizon-path PASS ⇒ book PnL  
- Soft H3 explained ⇒ resolved  
- Absolute ≥15% TB+1 or H4→0 as de facto ship gates  
- `tp_room_*` as free path skill without circularity audit  
- H=6 solves rarity without sample-loss re-measure  
- Free A/B reuse after 7 prior peeks without the **5-peek** ledger  
- Blaming Precision / Regime as the main Top-K path leak

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-tier2-verdict.md](horizon-tier2-verdict.md) | v1 ranker lock (historical) |
| [horizon-tier2-v11-revision.md](archive/horizon-tier2-v11-revision.md) + stop memos | Hygiene cycle CLOSED — why pivot |
| [horizon-tier2-eval-verdict.md](horizon-tier2-eval-verdict.md) | Metric taxonomy |
| [triple-barrier-verdict.md](triple-barrier-verdict.md) | TB geometry — **v2 amend locked**: primary `H=6`, floors unchanged |
| [horizon-path-room-h10-note.md](archive/horizon-path-room-h10-note.md) | Step 4 path-room circularity / H10 audit lock |
| [cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md) | Why escalate upstream |
