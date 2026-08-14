# Cascade Selectivity Tweak Plan — PnL & Trade Filtering

**Market:** NSE India, Nifty 100, intraday MIS cash  
**Date:** 2026-08-08 (rev. Tier 3 next-focus judge review)  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Depends on:** [cascade-strategy-overview.md](../cascade-strategy-overview.md), [precision-tier3-verdict.md](../precision-tier3-verdict.md), [horizon-tier2-verdict.md](../horizon-tier2-verdict.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md)  
**Judges:** Gemini Flash, Claude Sonnet  
**Status:** Phase 0–2 **closed as scoped** (#8–#10 measured); Phase 3 **outside Tier 3**; WS0/WS1 **closed (Fold A)** — see [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md); escalate Horizon/Regime  
**Evidence runs (baseline rules, pre–Phase 1):**

| Fold | Train → Test | Precision run | Horizon IC (L / S) |
|---|---|---|---|
| **A** | 2015–2017 → 2018 | `644e6f85` / `1b8205da` | 0.068 / 0.057 |
| **B** | 2016–2018 → 2019 | `026964e8` / `1b28b706` | 0.074 / 0.028 |
| **C** | 2017–2019 → 2020 | `1a319f64` | 0.020 / 0.019 |

**Phase 1 base runs:** A `702c1820` · B `3f8d7a95`  
**Phase 2 no-chase runs:** ranks 1–2 `448e7112` / `af36e64f` · pooled k=5 `70f21f1c` / `235a8985`  
**Phase 2 adverse-abort (closed):** X=15 `e788d784` / `7c9dac02` · X=10 `8d5a29ea` / `45086803`  
**Phase 2 #10 rank-skip (NO-LOCK):** stacked on no-chase pooled `74812843` / `7efd10c3`

---

## Summary

| Decision | Locked choice |
|---|---|
| Primary lever | **Selectivity** — skip bad trades; do not widen barriers or chase larger swings |
| Build posture | **REVISE** (both judges, Tier 3 next-focus) — Phase 2 closed; meta not headline yet |
| Phase 0 / 1 | **Shipped + locked as base** — do **not** claim acceptance gates met |
| Phase 3 | **Outside Tier 3** — portfolio / kill-switch; not Precision fire logic |
| Experiment arms | **Q4 / LSO / SLL / adverse-abort — closed + removed**; **no-chase / #10 — NO-LOCK** (CLI kept) |
| Cycle goal | Raise mean gross on *fired* trades toward ≥30 bps so net can clear friction |
| Cascade contract | Unchanged — narrow-only; frozen TB; no LLM live gate; Long ≠ Short |
| Replication | Continuous thresholds need **A+B** sign + rough magnitude; **C is not a Precision lock window** |
| Next Tier 3 focus | **(1) A-Short decompose → (2) meta spike offline** |

Ablation: Phase 1 ≈ **+1.6 / +0.5** bps; no-chase pooled ≈ **+3.2 / +3.9** vs Phase 1; #10 stacked ≈ **+3.5 / +2.1** vs no-chase pooled (best blended **−9.5 / −8.8**). Absolute ≥0 unmet. **Do not claim rules exhausted** while A-Short decompose is open. Meta allowed as **offline scaffolding**, not primary headline until that closes.

---

## Multi-fold evidence snapshot

### Headline (fires only; net = gross − 30 bps)

| Fold | fires | fire% | gross | net | TP / SL / TIMEOUT |
|---|---:|---:|---:|---:|---|
| **A** 2018 | 4449 | 72.1% | +12.2 | **−17.8** | 487 / 1154 / 2543 |
| **B** 2019 | 4848 | 71.1% | +14.7 | **−15.3** | 583 / 1145 / 2874 |
| **C** 2020 | **44** | 81.5% | +7.2 | **−22.8** | 1 / 7 / 36 |

### Sleeve diagnostics

| Fold | Slice | n | gross | net | TP% | SL% | TO% |
|---|---|---:|---:|---:|---:|---:|---:|
| A | Long | 2798 | +5.1 | **−24.9** | 8.8 | 31.8 | 50.0 |
| A | Short | 1651 | +24.1 | **−5.9** | 14.5 | 16.1 | 69.2 |
| B | Long | 2977 | +15.5 | **−14.5** | 12.6 | 28.6 | 50.8 |
| B | Short | 1871 | +13.5 | **−16.5** | 11.2 | 15.8 | 72.8 |
| C | Long | **0** | — | — | — | — | — |
| C | Short | 44 | +7.2 | −22.8 | 2.3 | 15.9 | 81.8 |

### Entry / rank (A + B; C omitted — underpowered)

| Slice | A n | A net | B n | B net |
|---|---:|---:|---:|---:|
| Setup | 423 | −17.0 | 459 | **−11.1** |
| Fallback | 4026 | −17.9 | 4389 | −15.7 |
| Rank 1–2 | 842 | **−22.8** | 844 | **−22.0** |
| Rank 3–5 | 1925 | **−14.4** | 2503 | **−12.7** |
| Rank 6–8 | 1682 | −19.2 | 1501 | −15.9 |

**Cross-fold read (locked interpretation):**

1. **Selectivity still primary** — gross never clears 30 bps on A or B.  
2. **Long ≠ always the worse sleeve** — A: Long −24.9 vs Short −5.9; B: Long −14.5 vs Short −16.5 (flip with *zero* rule change). Hard Long-only daily gate is **2018-contaminated**.  
3. **TOP_K 8→5 replicates** — ranks 6–8 worse than 3–5 on A (−19.2 vs −14.4) and B (−15.9 vs −12.7).  
4. **Rank 1–2 worst net replicates** (−22.8 / −22.0) — elevate chase/no-chase experiment; do **not** invert size; do **not** lock blunt skip yet.  
5. **Setup vs fallback** — composition audit shows setup is **100% Long**; A/B setup flip is Long-regime, not entry-quality. Setup-or-skip unlocked.  
6. **Fold C** — n=44, Long=0, Horizon IC collapsed (~0.02) → Regime/Horizon COVID stress / sample starvation. **Quarantine from Precision threshold locks.**  
7. **Score floors** — cite only `edge_score`; Q4 Long n fails ≥300–500 gate on measured arms.

**Replication caveat (both judges):** Fold A (train 2015–17) and Fold B (train 2016–18) share **2 of 3 training years** and adjacent tests (2018/2019). A+B agreement is **directionally consistent**, not fully independent replication. Prefer a later disjoint holdout (e.g. post–Fold-C Regime audit) before calling continuous thresholds durable.

---

## Phase 0+1 measurement (post-ship)

### Headline vs pre–Phase 1 baseline

| Fold | | fires | fire% | gross | net | Long n/net | Short n/net |
|---|---|---:|---:|---:|---:|---|---|
| **A** | baseline `1b8205da` | 4449 | 72.1 | +12.2 | **−17.8** | 2798 / −24.9 | 1651 / −5.9 |
| | Phase 0+1 `702c1820` | 2265 | 69.5 | +13.8 | **−16.2** | 1353 / −23.3 | 912 / −5.5 |
| **B** | baseline `1b28b706` | 4848 | 71.1 | +14.7 | **−15.3** | 2977 / −14.5 | 1871 / −16.5 |
| | Phase 0+1 `3f8d7a95` | 2771 | 67.0 | +15.2 | **−14.8** | 1656 / −14.1 | 1115 / −15.8 |

### Slice read (Phase 0+1 fires)

| Slice | A n / net | B n / net | Read |
|---|---|---|---|
| Rank 1–2 | 840 / **−23** | 821 / **−22** | Still worst — chase diagnostic → no-chase experiment |
| Rank 3–5 | 1425 / −12 | 1950 / −12 | Better than 1–2; still below friction |
| Setup | 218 / **−5** | 235 / **−20** | **Directional flip** — 100% Long; do not lock setup-or-skip |
| Fallback | 2047 / −17 | 2536 / −14 | Dominates volume |
| `edge_score` Q4 pooled | 495 / **+8** | 301 / **+5** | Pocket only; not a default |
| Long Q4 | 77 / +3 | 109 / +29 | **Fails ≥300–500 n gate** — not a lock |

Phase 0 polarity: `rank_polarity_ok=True`, 0 violations on A and B.

### Acceptance after Phase 1

| Gate | A | B | Result |
|---|---|---|---|
| Blended net ≥ 0 | −16.2 | −14.8 | **Fail** |
| Long net ≥ 0 | −23.3 | −14.1 | **Fail** |
| Short no regression vs baseline | −5.5 ≥ −5.9 | −15.8 ≥ −16.5 | **Pass** |
| Fire rate ~25–45% if net improves | 69.5% | 67.0% | Not reached; net barely improved |

---

## Ablation 2×2 + flag-matrix measurement (2026-08-08) — **DONE**

Population-matched where noted. Net = mean net bps on fires (gross − 30 bps). Experiment arms below are **gate ON** (stacked on Phase 1 base) unless labeled otherwise.

### Ablation matrix (net bps)

| Config | A run | A net | A Long / Short | B run | B net | B Long / Short |
|---|---|---:|---|---|---:|---|
| Baseline k=8 gate-OFF | `1b8205da` | **−17.8** | −24.9 / −5.9 | `1b28b706` | **−15.3** | −14.5 / −16.5 |
| k=8 gate-ON | `ec773807` | **−17.6** | −25.1 / −5.3 | `65761575` | **−14.7** | −14.2 / −15.6 |
| k=5 gate-OFF | `1adc40bb` | **−17.3** | −24.5 / −6.4 | `0669bae0` | **−15.5** | −14.9 / −16.2 |
| Phase 1 k=5 gate-ON | `702c1820` | **−16.2** | −23.3 / −5.5 | `3f8d7a95` | **−14.8** | −14.1 / −15.8 |

**Matched deltas (locked read):**

| Lever | A | B |
|---|---:|---:|
| Gate ON vs OFF @ k=5 | **+1.1** (−16.2 vs −17.3) | **+0.7** (−14.8 vs −15.5) |
| TOP_K 8→5 @ gate ON | **+1.4** (−16.2 vs −17.6) | **−0.1** (−14.8 vs −14.7) |
| Combined vs baseline | **+1.6** | **+0.5** |

Effects are small, additive, and cross-fold consistent. **Do not** describe as closing most of the gap — ~14–16 bps to blended ≥0 remains.

### Gate-ON experiment arms vs Phase 1

Lock rule (unchanged): Long net must improve on **both** A and B; Short must not regress materially.

| Arm | A run | A net (Δ) | A Long (Δ) | A Short | B run | B net (Δ) | B Long (Δ) | B Short | Call |
|---|---|---:|---:|---:|---|---:|---:|---:|---|
| Phase 1 base | `702c1820` | −16.2 | −23.3 | −5.5 | `3f8d7a95` | −14.8 | −14.1 | −15.8 | **LOCK base** |
| Q4 on median | `0835ca5f` | −11.1 (**+5.1**) | −20.3 (+3.0) | **+8.8** | `fdf384c0` | −13.9 (+0.9) | −12.9 (+1.2) | −15.0 | **NO-LOCK** |
| LSO alone | `6afdefa2` | −14.2 (+2.0) | −23.0 (+0.3) | −5.5 | `68fb6fb7` | −14.9 (−0.1) | −14.1 (0) | −15.8 | **NO-LOCK** |
| SLL alone | `2f23f55a` | −15.7 (+0.5) | −23.3 (0) | −5.5 | `7cd33bc3` | −14.2 (+0.6) | −13.1 (+1.0) | −15.8 | **NO-LOCK** |
| LSO+SLL | `6cb3050f` | −13.8 (+2.4) | −23.0 (+0.3) | −5.5 | `299302df` | −14.2 (+0.6) | −12.6 (+1.5) | −15.8 | **NO-LOCK** |

**Arm reads (both judges):**

- **Q4** — fire% 39.5 / 31.2; Long Q4 n **77 / 109** fails ≥300–500; on-median ≈ identical to prior Q4 gate-OFF (`6bd34169` / `dcf0bfa3`). A blended lift is almost entirely A-Short (−5.5→**+8.8**, n=408); B-Short only +0.8 — treat as 2018-specific artifact, not a lock.  
- **LSO** — fails dual-fold Long lift (+0.3 / 0). A blended +2.0 is volume/composition, not Long quality.  
- **SLL** — fails dual-fold Long lift (0 / +1.0).  
- **LSO+SLL** — thin additive; A Long still **−23.0**. Does not rescue Long.  
- **LSO+SLL+Q4 gate-ON** — **not required** this cycle (singles failed; prior gate-OFF A −5.3 was Short-driven / Long Q4 n=33).

### Rank 1–2 / setup diagnostics (logged on flag runs)

| Contrast | Rank 1–2 | Rank 3–5 |
|---|---|---|
| Net | ~−20 to −23 | better, still ≤0 |
| `fresh_flip_share` | ~31–34% | ~18–22% |
| `mean_bars_since_flip` | ~6 | ~14–22 |
| SL / TP | higher SL, lower TP | healthier mix |

Setup fires are **100% Long** across diagnostic runs → A setup −5 vs B setup −20 is the Long-sleeve fold flip.

---

## Critical prerequisite — score polarity in diagnostics

Unchanged. Both judges still flag raw `horizon_score` quartiles as **untrustworthy**.

```
edge_score = horizon_score          # long
edge_score = -horizon_score         # short
```

Cite only `edge_score` quartiles / floors. Per-sleeve n ≥300–500 before any continuous score floor lock.

---

## Judge scores (multi-fold review — pre–Phase 1)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---:|---:|---|
| Multi-fold interpretation | 9.5 | 7.0 | **A+B usable; C quarantined; A/B not fully independent** |
| Selectivity design | 9.0 | 7.5 | **Ship mechanical cuts first** |
| Long / Short asymmetry | 7.5 | 6.5 | **Demote Long SUPPORTIVE-only hard lock** |
| Rank / TOP_K policy | 9.5 | 7.0 | **Lock TOP_K→5; elevate 1–2 chase experiment, don’t lock skip** |
| Entry / fallback | 8.5 | 6.0 | **Shared conviction gate; setup-or-skip still conditional** |
| Overfit / replication | 9.5 | 6.5 | **Require A+B; caveat overlap; no C locks** |
| PnL realism vs 30 bps | 9.0 | 6.0 | **Selectivity first; Claude: spike meta feasibility in parallel** |
| Cascade coherence | 10 | 9.0 | Keep narrow-only |
| Overall | **REVISE** | **REVISE** | **ACCEPT with revisions** (Phase 1 plan) |

### Judge scores (post–Phase 0+1 measurement)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---:|---:|---|
| Phase 1 measurement interpretation | 9.5 | 6.5 | **Base shipped, not goal-met; ablate TOP_K vs gate before citing Δbps** |
| Rank 1–2 priority | 10 | 8.5 | **Priority diagnostic; reject size invert** |
| edge_score floor / Q4 experiment | 9.5 | 4.5 | **Hypothesis only — not a default; per-sleeve n gate** |
| Setup-or-skip deferral | 10 | 8.5 | **Do not lock** |
| Meta spike timing | 9.0 | 6.0 | **Spike parallel; behind Phase 2 eng priority** |
| Overfit / replication | 9.5 | 6.0 | **A+B non-independence applies to every new claim** |
| Cascade coherence | 10 | 9.0 | Keep narrow-only |
| Overall | **REVISE** | **REVISE** | **REVISE** — ship base; revise next-step framing |

### Judge scores (flag-matrix review — 2026-08-08)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---:|---:|---|
| Flag-matrix / ablation interpretation | 9.5–9.8 | 7.5–8.5 | **2×2 complete; small additive lifts; gap remains** |
| Experiment lock discipline | 10 | 8.5 | **Close Q4 / LSO / SLL / LSO+SLL as defaults** |
| Next-step priority | 9.5 | 6.5 | **Phase 2 no-chase first; not blunt rank skip** |
| Overfit risk awareness | 9.7 | 7.0 | **Q4 A-Short +8.8 is fold-specific red flag** |
| Overall | **REVISE** | **REVISE** | **REVISE** — lock Phase 1 base; pivot Phase 2 |

### Judge scores (Phase 2 no-chase review — 2026-08-08)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---:|---:|---|
| Phase2 measurement interpretation | 9.5 | 7.5 | **Relative pass / absolute fail; pooled > ranks 1–2** |
| No-chase lock discipline | 10 | 8.0 | **NO-LOCK as production default** |
| Pooled vs ranks-1–2 preference | 9.5 | 6.0 | **Prefer pooled for stacking; qualify A-Short carry** |
| Rank 1–2 skip timing | 9.0 | 8.0 | **Not triggered — no-chase helped** |
| Adverse-abort priority | 8.0 | 5.0→ahead | **Next eng priority (#8)** |
| Meta spike timing | 8.5 | 7.0 | **Parallel, behind #8 + stack** |
| Overfit / replication | 9.5 | 6.0 | **A-Short pooled +0.3 is the red flag** |
| Cascade coherence | 10 | 9.0 | Keep narrow-only |
| Overall | **REVISE** | **REVISE** | **REVISE** — adverse-abort next |

---

## Where judges disagreed → locked choice

### Multi-fold plan (pre–Phase 1)

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Long daily SUPPORTIVE-only | Demote to experiment | On/off flag; not default | **Experiment — measured; failed dual-fold Long lift → NO-LOCK** |
| Rank 1–2 skip | Promote front-line | Root-cause first; do not lock | **Diagnostic done → prefer no-chase experiment over blunt skip** |
| Short acceptance gate | Phase 1 ≥ −5 then ≥ 0 | No regression vs fold baseline | **Phase 1:** no regression (held). **Long-run:** ≥ 0 then ≥ +5 |
| Meta-filter timing | Staged after rules | Parallel spike OK | **Spike parallel; behind Phase 2 no-chase** |
| Stricter Long liquidity | Keep cheap filter | Test separately | **Measured alone + with LSO → NO-LOCK** |

### Post–Phase 1 next steps → flag-matrix close-out

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Phase 1 status | Lock as revised base | Lock as shipped base, not goal-met | **LOCK Phase 1 mechanical base** (`TOP_K=5` + median gate) |
| Q4 floor | Reject / close | NO-LOCK; A-Short unreplicated | **NO-LOCK / closed as default** — flags may remain for research |
| LSO / SLL / LSO+SLL | Reject | NO-LOCK (fail Long both-fold rule) | **NO-LOCK / closed as defaults** |
| Rank 1–2 | No-chase / adverse abort before hard skip | No-chase filter first; skip not default | **Next: no-chase experiment** (`bars_since_regime_flip` / fresh_flip). Hard skip stays unlocked |
| Setup-or-skip | Unlock | Unlock + composition (now: 100% Long) | **Unlocked** — composition explains fold flip; no lever change |
| Short-Q4 isolation | Deprioritize vs Phase 2 | Optional secondary check with n | **Optional / low priority** — do not block no-chase |
| LSO+SLL+Q4 gate-ON | Skip | Skip if singles fail | **Skip** this cycle |
| Meta spike | Parallel, non-blocking | Behind 1–3 | **Unchanged** — behind Phase 2 |

### Phase 2 no-chase review → adverse-abort pivot

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| No-chase ranks 1–2 | NO-LOCK | NO-LOCK | **NO-LOCK** — keep `--no-chase` flag |
| No-chase pooled | NO-LOCK; preferred arm | NO-LOCK; qualify A-Short | **NO-LOCK** — preferred for stacking; do not promote |
| Promote no-chase to default | NO-LOCK | REJECT this cycle | **Phase 1 base stays sole default** |
| Rank 1–2 hard skip (#10) | Monitor; unlocked | Not triggered | **Measured NO-LOCK** — stacked on no-chase pooled; absolute fail; CLI kept |
| Adverse-abort (#8) | Build next | Build next (ahead of meta) | **Measured NO-LOCK @15/10; closed + removed** |
| A-Short pooled +0.3 | Overfit warning | Cycle red flag (Q4-shaped) | **Do not cite as durable; decompose** |
| Meta spike | Parallel OK | Behind #8 + stack | **Behind #10 / A-Short decompose** |

Unchanged consensus locks: Phase 0 `edge_score`; TOP_K 8→5; shared median conviction gate; reject size invert; reject wait 5→8m; risk kill-switch stays outside Precision fire logic; Fold C not for threshold lock.

---

## Locked implementation sequence

### Phase 0 — Diagnostics integrity (blocker) — **DONE**

1. Add `edge_score` (direction-normalized) to Precision trades / summary.  
2. Re-print by-score and by-sleeve floors on `edge_score` for **Folds A and B**.  
3. Confirm registry rank polarity matches live inference.

### Phase 1 — Mechanical selectivity — **LOCKED AS BASE (not accepted-to-goal)**

| # | Change | Owner tier | Rationale |
|---|---|---|---|
| 1 | **`TOP_K`: 8 → 5** — drop ranks 6–8 (skip, do not micro-size) | Precision / Horizon registry | Ablation A+B: ≈ +1.4 / −0.1 bps |
| 2 | **Keep size schedule** 1–2 → 1.0×, 3–5 → 0.7× (no rank 6–8) | Precision | Do not invert |
| 3 | **Shared conviction gate** on setup *and* fallback: `edge_score` ≥ cross-sectional median of that bar’s eligible K names (per sleeve) | Precision | Ablation A+B: ≈ +1.1 / +0.7 bps |

**Experiment flags — measured then removed from CLI (NO-LOCK):**

| # | Change | Result |
|---|---|---|
| 4 | Long daily `SUPPORTIVE`-only (`--long-supportive-only`) | **Closed + removed** — fails dual-fold Long lift |
| 5 | Stricter Long liquidity (`--strict-long-liquidity`) | **Closed + removed** — fails dual-fold Long lift |
| 4+5 | LSO+SLL combined | **Closed** — A Long still −23 |
| 6 | Rank 1–2 skip | **Still unlocked** — prefer no-chase first |
| 6b | `edge_score` Q4 floor (`--edge-q4-floor`) | **Closed + removed** — Long n-gate fail; A lift Short-driven |

Ablation CLI retained: `--top-k`, `--no-conviction-gate`.

Short sleeve: keep daily ∈ `{SUPPORTIVE, AMBIGUOUS}`; still subject to TOP_K=5 + conviction gate.

### Phase 2 — Entry quality — **#8 CLOSED; #9/#10 NO-LOCK (CLI kept)**

| # | Change | Notes |
|---|---|---|
| 7 | **Fallback / setup composition audit** | **Done** — setup = 100% Long; fold flip = Long-regime. Setup-or-skip unlocked |
| 8 | **Adverse-move abort in wait** | **NO-LOCK / closed + removed.** Alone X=15 fails dual-fold Long (A −1.2 / B +1.8); X=10 worse (−2.4 / −6.1). No stack |
| 9 | **No-chase / fresh-flip filter** | **Measured NO-LOCK.** Ranks 1–2 +1.6/+1.6; pooled +3.2/+3.9 vs Phase 1. Absolute ≥0 fail. Keep CLI off-by-default |
| 10 | **Rank 1–2 hard skip** | **Measured NO-LOCK / closed.** Stacked on no-chase pooled: A/B −9.5/−8.8 (**+3.5/+2.1** vs pool); Long ↑ both folds; Short no regression; absolute ≥0 fail. Keep `--skip-rank-1-2` off-by-default; do not promote |

### Phase 3 — Risk layer (parallel, above Precision)

| # | Change | Notes |
|---|---|---|
| 11 | Max concurrent positions; prefer higher `edge_score` when capacity binds | Not a Precision rule |
| 12 | Daily heat / loss kill-switch | Operational; must not mask Phase 1–2 measurement |

### Phase 4 — Meta-filter

13. LightGBM take/skip on TB path success + 1m features; purged + embargoed CV — **production** only if rules selectivity still leaves mean gross on fires < ~30 bps.  
14. **Parallel feasibility spike allowed** — offline, purged CV. Eng priority **behind** A-Short decompose. Not primary headline until that finishes. Do **not** claim rules exhausted.

### Parallel — Fold C Regime / Horizon audit (non-blocking)

15. Diagnose 2020 fire starvation: HMM state occupancy (`HIGH_VOL` / `NO_TRADE` / absence of `TREND_UP`) vs over-blocking vs TB eligibility wipeout under collapsed IC. **Does not gate Phase 2.**

---

## Explicitly out of scope this cycle

- Widening TP/SL or lowering cost floors  
- Trailing stops  
- Retraining Horizon **solely** for this tweak (selectivity first)  
- L2 / OBI / CVD / news NLP  
- CHOP mean-reversion sleeve  
- Extending wait 5→8 minutes  
- Inverting rank size (1–2 down, 3–5 up)  
- Putting portfolio kill-switches inside Precision’s per-name fire logic  
- Locking any continuous threshold from Fold C  
- Promoting Q4 / LSO / SLL / adverse-abort as production defaults  

---

## Acceptance metrics

| Metric | Gate |
|---|---|
| Mean net on fires (blended) | ≥ **0 bps** (from −17.8 / −15.3; Phase 1 still −16.2 / −14.8) |
| Mean net **Long alone** | ≥ **0 bps** — Short must not hide a broken Long |
| Mean net **Short alone** (Phase 1) | **No regression vs fold baseline** (held on Phase 1 + arms) |
| Mean net **Short alone** (long-run) | ≥ **0**, then ≥ **+5** once meta / later phases land |
| Min fires per sleeve / window | ≥ **300–500** before locking new thresholds (**C fails — excluded**; Q4 Long fails) |
| Fire rate | No fixed target; **~25–45%** acceptable if net improves |
| Exit-mix sanity | Selectivity must not only delete TIMEOUT names — watch TP/SL mix |
| Replication | Continuous thresholds need **A+B** sign + rough magnitude; *directionally consistent* until disjoint-train holdout |
| Score diagnostics | Cite only `edge_score` quartiles after Phase 0 |
| Fold C | Informational / Regime audit only — **never** a lock input |

---

## Overfit warning (both judges)

2018 was a hostile Indian equity tape; 2019 flipped Long vs Short drag without rule changes. Hyper-tight Long filters tuned on A alone risk learning “don’t trade Long in 2018.” Fold C’s near-zero fire count is a separate cascade-upstream failure mode — do not “fix” it with Precision selectivity knobs. Mitigation: lock only parameter-free cuts early (`TOP_K`); gate continuous thresholds and Long-only daily rules behind Phase 0 + A+B; quarantine C.

**Post–Phase 1 / flag-matrix addenda:** (1) Global/`Q4` floors are a higher overfit class than bar-relative median — **closed as default**; A-Short Q4 +8.8 does not replicate on B. (2) Ablated Phase 1 closed only ~0.5–1.6 bps — **not** exhaustion while Phase 2 no-chase is untried. (3) Setup A vs B opposite signs explained by Long-only composition — don’t average away; don’t lock setup-or-skip. (4) A+B non-independence applies to every new continuous threshold.

---

## Mapping to cascade docs

| Existing lock | This plan |
|---|---|
| Narrow-downward | All filters only skip / size-down — no re-rank or direction flip |
| Frozen TB geometry | Unchanged |
| Rules-first Precision; meta staged | Meta production still Phase 4; feasibility spike parallel OK, behind Phase 2 no-chase |
| Rank-based size | Schedule kept; K tightened; 1–2 skip still experiment not invert |
| Separate Long / Short | Asymmetry **measured** per fold — LSO/SLL demoted after measurement |
| Cost first-order | Selectivity replaces barrier surgery |

---

## Next build step (Tier 3 cascade — both judges)

**Phase 3 portfolio/risk is outside Tier 3.** Phase 0–2 rules cycle closed as scoped (absolute ≥0 unmet).  
**WS0/WS1 Fold A verdict:** [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md) — escalate Horizon/Regime; skip WS2; demote meta headline.

1. **Decompose A-Short pooled +0.3** — **DONE (Fold A):** not top-decile artifact on A; morning-skewed; need B for durability.  
2. **Written no-chase / #10 non-promotion** — **LOCKED**; Phase 1 base remains sole default.  
3. **Meta spike (Phase 4)** — offline only; **behind** Horizon/Regime (`tb_label=+1` rare in admitted book).  
4. **Fold C + A/B Regime/Horizon audit** — **elevated**; never a Precision lock input.

**Must not:** promote no-chase or #10; reopen Q4/LSO/SLL/adverse-abort; claim rules exhausted; put Phase 3 kill-switches inside Precision fire logic; open a new open-ended asymmetric-rules campaign this cycle before upstream path quality improves.

### Must not lock yet

- Global / Q4 `edge_score` floor as default  
- No-chase ranks 1–2 or pooled as production default  
- Rank 1–2 hard skip as production default (#10 closed NO-LOCK)  
- Setup-or-skip  
- Long SUPPORTIVE-only / Long liquidity / LSO+SLL / adverse-abort as defaults  
- Production meta  
- Anything from Fold C  
- Claim blended ≥0 is close (−9.5 / −8.8 best case vs 0)  
- Claim A-Short pooled +0.3 (or Q4 A-Short +8.8) is a durable edge without B-scale replication  
- Claim rules-first selectivity is exhausted  

---

## Locked consensus (flag-matrix — both judges)

Gate-ON ablation confirms Phase 1’s two mechanical levers are small, additive, and cross-fold consistent (`TOP_K` 8→5 ≈ +1.4/−0.1 bps, conviction gate ≈ +1.1/+0.7 bps on A/B, summing to the shipped +1.6/+0.5 bps), but leave blended and Long net far short of ≥0 (A −16.2, B −14.8). None of the four gate-ON experiment arms clears the lock rule that Long must improve on **both** A and B: LSO and SLL move Long by ≤0.3 and ≤1.0 bps on at most one fold; LSO+SLL fails to rescue A Long (−23.0); Q4’s headline A lift (+5.1 blended) is driven by Short (+8.8) that fails the Long n-gate (n=77/109) and does not replicate on B-Short (+0.8). All four stay **NO-LOCK**; Phase 1 mechanical base remains the shipped default. Rank 1–2 diagnostics (fresh_flip ~31–34% vs ~18–22%, bars_since_flip ~6 vs 14–22, worse SL/TP) point to regime-flip **chase proximity**, so the next experiment is a targeted **no-chase** filter, not a blunt rank-1–2 skip. Setup-or-skip stays unlocked (setup = 100% Long). Posture: **REVISE** — pivot engineering to Phase 2 entry quality.

---

## Locked consensus (Phase 2 no-chase — both judges)

No-chase (#9) is measured and directionally real on both folds: ranks 1–2 only recovers **+1.6 / +1.6** bps blended (A −14.6, B −13.2); pooled `rank_max=5` recovers **+3.2 / +3.9** (A −13.0, B −10.9). Relative lock rule **passes** both arms (Long ↑ on A+B, Short no regression, n≥300–500); absolute gates **fail** everywhere (best blended −10.9; Long still −11.2 to −21.7). Both arms stay **NO-LOCK** as production defaults; Phase 1 mechanical base remains the sole locked default. Pooled beats ranks-1–2-only on every headline metric, but Claude flags (Gemini concurs on scrutiny) that pooled’s largest single Δ is A-Short −5.5→**+0.3** (n=695, Δ+5.8) while B-Short lands at −10.4 (Δ+5.4) — Q4-shaped, do not treat as “Short fixed.” Setup-or-skip stays unlocked. Posture: **REVISE**.

---

## Locked consensus (Phase 2 #10 rank 1–2 hard skip)

Hard-skip ranks ≤2 stacked on no-chase pooled (`--no-chase --no-chase-rank-max 5 --skip-rank-1-2`): A `74812843` −9.5 / B `7efd10c3` −8.8 blended (**+3.5 / +2.1** vs pool; **+6.7 / +6.0** vs Phase 1). Long −19.7 / −8.9 (**+2.0 / +2.3** vs pool); Short +4.9 / −8.8 (no regression). Fire% 36.2 / 40.2; ranks 1–2 fires = 0 by construction. Relative lock **passes**; absolute ≥0 **fails** (best −8.8; Long A still −19.7; gross ~20–21 ≪ 30). **Call: NO-LOCK / closed permanently as production default; keep `--skip-rank-1-2` CLI off-by-default** (same class as no-chase). Do not reopen as an open experiment.

---

## Locked consensus (Phase 2 adverse-abort close-out)

Adverse-move abort (#8) alone fails the relative lock rule at both tested continuous thresholds. **X=15:** A −18.2 (−2.0 vs Phase 1), B −13.7 (+1.1); Long −24.5 (−1.2) / −12.3 (+1.8) — A Long regresses. **X=10:** A −17.4 (−1.2), B −18.4 (−3.6); Long −25.7 / −20.2 — both folds worse. Fire% collapses (69.5/67.0 → 46.6/49.0 @15 → 37.5/36.4 @10) while A gross falls at X=15 — selectivity deletes good trades. Tighter X is strictly worse; no stack with no-chase. **Call: NO-LOCK / closed as default; `--adverse-abort` removed** (same close-out class as Q4 / LSO / SLL). Phase 1 base remains sole production default.

---

## Judge scores (Tier 3 next-focus review — 2026-08-08)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---:|---:|---|
| Phase2 close-out interpretation | 9.5 | 8.5 | **Accurate; absolute ≥0 unmet** |
| Rules-exhaustion claim | 3.0 | 3.5 | **REJECT — A-Short + #10 still open** |
| Meta as primary Tier3 path | 4.0 | 3.0 | **Offline only until close-out finishes** |
| #10 timing | 8.5 | 7.0 | **One-shot then permanent close** |
| A-Short decompose priority | 10 | 8.5 | **#1 next** |
| No-chase leave-as-flag | 10 | 9.0 | **NO-LOCK / CLI-only** |
| Fold C priority | 9.5 | 9.0 | **Parallel non-blocking** |
| Cascade coherence | 10 | 9.0 | Phase 3 outside Tier 3 |
| Overall | **REVISE** | **REVISE** | **REVISE** — close leftovers before meta headline |

### Where judges disagreed → locked choice

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Meta timing | Offline spike OK; not primary | Scaffolding OK; not headline until 1–3 | **Offline / behind A-Short + #10** |
| #10 | Leave unlocked; don’t waste compute first | One bundled measure then close | **One-shot after A-Short; then close** |
| New asymmetric rules campaign | Promote next | Not prioritized | **Behind close-out; not this-cycle headline** (closed arms already failed many Long asymmetries) |
| Rules exhausted | REJECT | REJECT (implied by meta-primary) | **REJECT** |

---

## Locked consensus (Tier 3 next focus — both judges)

Phase 0–2 are closed as scoped: Phase 1 base remains the sole production default; no-chase is a real relative lift (**+3.2 / +3.9** pooled) that still fails absolute ≥0 and stays **NO-LOCK** / CLI-only; #10 stacked hard-skip adds **+3.5 / +2.1** vs pool (best **−9.5 / −8.8**) with the same absolute fail → **NO-LOCK** / CLI-only / permanently closed as experiment; adverse-abort / Q4 / LSO / SLL stay closed + removed. Phase 3 portfolio risk stays **outside** Tier 3. Gross ~20–21 bps still ≪30, so a Phase 4 meta spike is **allowed offline**, but must not be the headline while A-Short pooled **+0.3** (n=695, Q4-shaped) is undecomposed. **Do not claim rules exhausted.** Locked Tier 3 sequence: (1) decompose A-Short pooled +0.3; (2) written no-chase/#10 non-promotion; (3) meta harness + purged/embargoed CV offline against a frozen rules baseline; (4) Fold C Regime/Horizon audit parallel / non-blocking. Posture: **REVISE**.

---

## Related

| Doc | Role |
|---|---|
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Cascade contracts |
| [precision-tier3-verdict.md](../precision-tier3-verdict.md) | Entry / exit / size v1 |
| [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) | Score sign / ranking |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | Cost & barrier locks |
| [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md) | WS0/WS1 Fold A verdict — escalate Horizon/Regime |
