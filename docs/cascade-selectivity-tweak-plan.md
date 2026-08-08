# Cascade Selectivity Tweak Plan — PnL & Trade Filtering

**Market:** NSE India, Nifty 100, intraday MIS cash  
**Date:** 2026-08-08 (rev. Phase 0+1 measured)  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Depends on:** [cascade-strategy-overview.md](cascade-strategy-overview.md), [precision-tier3-verdict.md](precision-tier3-verdict.md), [horizon-tier2-verdict.md](horizon-tier2-verdict.md), [triple-barrier-verdict.md](triple-barrier-verdict.md)  
**Judges:** Gemini Flash, Claude Sonnet  
**Status:** Phase 0 **DONE**; Phase 1 defaults **shipped — measured, not accepted-to-goal**  
**Evidence runs (baseline rules, pre–Phase 1):**

| Fold | Train → Test | Precision run | Horizon IC (L / S) |
|---|---|---|---|
| **A** | 2015–2017 → 2018 | `644e6f85` | 0.068 / 0.057 |
| **B** | 2016–2018 → 2019 | `026964e8` | 0.074 / 0.028 |
| **C** | 2017–2019 → 2020 | `1a319f64` | 0.020 / 0.019 |

---

## Summary

| Decision | Locked choice |
|---|---|
| Primary lever | **Selectivity** — skip bad trades; do not widen barriers or chase larger swings |
| Build posture | **REVISE** (both judges on post–Phase 1 review) — mechanical base ships; economics not met |
| Phase 0 / 1 | **Shipped as base** — do **not** claim acceptance gates met |
| Cycle goal | Raise mean gross on *fired* trades toward ≥30 bps so net can clear friction |
| Cascade contract | Unchanged — narrow-only; frozen TB; no LLM live gate; Long ≠ Short |
| Replication | Continuous thresholds need **A+B** sign + rough magnitude; **C is not a Precision lock window** |

Phase 1 cut fires ~45% but blended net barely moved (**A −17.8→−16**, **B −15.3→−15**). Short no-regression holds; blended/Long ≥0 fails. Rank 1–2 still toxic (~−22/−23). `edge_score` Q4 is the first net-positive pocket (+8 / +5) but is an **experiment hypothesis**, not a lock. Setup flipped across folds (A −5 vs B −20) — setup-or-skip stays unlocked.

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
4. **Rank 1–2 worst net replicates** (−22.8 / −22.0) — elevate experiment priority; do **not** invert size; diagnose before default skip.  
5. **Setup vs fallback** — A nearly tied; B setup better by ~4.6 bps. Shared conviction gate first; setup-or-skip still conditional.  
6. **Fold C** — n=44, Long=0, Horizon IC collapsed (~0.02) → Regime/Horizon COVID stress / sample starvation. **Quarantine from Precision threshold locks.**  
7. **Score Q1/Q4 still untrustworthy** until `edge_score` (Q4 n=91 on A vs 944 on B).

**Replication caveat (both judges):** Fold A (train 2015–17) and Fold B (train 2016–18) share **2 of 3 training years** and adjacent tests (2018/2019). A+B agreement is **directionally consistent**, not fully independent replication. Prefer a later disjoint holdout (e.g. post–Fold-C Regime audit) before calling continuous thresholds durable.

---

## Phase 0+1 measurement (post-ship)

### Headline vs pre–Phase 1 baseline

| Fold | | fires | fire% | gross | net | Long n/net | Short n/net |
|---|---|---:|---:|---:|---:|---|---|
| **A** | baseline `644e6f85` | 4449 | 72.1 | +12.2 | **−17.8** | 2798 / −24.9 | 1651 / −5.9 |
| | Phase 0+1 | 2265 | 69.5 | +14 | **−16** | 1353 / −23 | 912 / −5 |
| **B** | baseline `026964e8` | 4848 | 71.1 | +14.7 | **−15.3** | 2977 / −14.5 | 1871 / −16.5 |
| | Phase 0+1 | 2771 | 67.0 | +15 | **−15** | 1656 / −14 | 1115 / −16 |

**Caveat (Claude, locked):** episode counts shrank with `TOP_K` 8→5 (A ~6170→3258; B ~6820→4137). Headline net deltas are **not population-matched**. Run ablations (`TOP_K=5` gate off; `TOP_K=8` gate on) before citing “Phase 1 closed X bps.”

### Slice read (Phase 0+1 fires)

| Slice | A n / net | B n / net | Read |
|---|---|---|---|
| Rank 1–2 | 840 / **−23** | 821 / **−22** | Still worst — diagnostic before skip |
| Rank 3–5 | 1425 / −12 | 1950 / −12 | Better than 1–2; still below friction |
| Setup | 218 / **−5** | 235 / **−20** | **Directional flip** — do not lock setup-or-skip |
| Fallback | 2047 / −17 | 2536 / −14 | Dominates volume |
| `edge_score` Q4 pooled | 495 / **+8** | 301 / **+5** | First net+ pocket; experiment only |
| Long Q4 | 77 / +3 | — | **Fails ≥300–500 n gate** — not a lock |

Phase 0 polarity: `rank_polarity_ok=True`, 0 violations on A and B.

### Acceptance after Phase 1

| Gate | A | B | Result |
|---|---|---|---|
| Blended net ≥ 0 | −16 | −15 | **Fail** |
| Long net ≥ 0 | −23 | −14 | **Fail** |
| Short no regression vs baseline | −5 ≥ −5.9 | −16 ≥ −16.5 | **Pass** |
| Fire rate ~25–45% if net improves | 69.5% | 67.0% | Not reached; net barely improved |

---

## Critical prerequisite — score polarity in diagnostics

Unchanged. Both judges still flag raw `horizon_score` quartiles as **untrustworthy**.

```
edge_score = horizon_score          # long
edge_score = -horizon_score         # short
```

Re-run quartile / floor diagnostics on `edge_score` (per sleeve and pooled) on **A and B** before any score floor. Do **not** cite Q1/Q4 narratives from raw pooled scores.

---

## Judge scores (multi-fold review — pre–Phase 1)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---:|---:|---|
| Multi-fold interpretation | 9.5 | 7.0 | **A+B usable; C quarantined; A/B not fully independent** |
| Selectivity design | 9.0 | 7.5 | **Ship mechanical cuts first** |
| Long / Short asymmetry | 7.5 | 6.5 | **Demote Long SUPPORTIVE-only hard lock** |
| Rank / TOP_K policy | 9.5 | 7.0 | **Lock TOP_K→5; elevate 1–2 skip experiment, don’t lock** |
| Entry / fallback | 8.5 | 6.0 | **Shared conviction gate; setup-or-skip still conditional** |
| Overfit / replication | 9.5 | 6.5 | **Require A+B; caveat overlap; no C locks** |
| PnL realism vs 30 bps | 9.0 | 6.0 | **Selectivity first; Claude: spike meta feasibility in parallel** |
| Cascade coherence | 10 | 9.0 | Keep narrow-only |
| Overall | **REVISE** | **REVISE** | **ACCEPT with revisions** (Phase 1 plan) |

### Judge scores (post–Phase 0+1 measurement)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---:|---:|---|
| Phase 1 measurement interpretation | 9.5 | 6.5 | **Base shipped, not goal-met; ablate TOP_K vs gate before citing Δbps** |
| Rank 1–2 priority | 10 | 8.5 | **Priority diagnostic this week; reject size invert** |
| edge_score floor / Q4 experiment | 9.5 | 4.5 | **Hypothesis only — not a default; per-sleeve n gate; stack on median** |
| Setup-or-skip deferral | 10 | 8.5 | **Do not lock** — B setup regressed to −20 |
| Meta spike timing | 9.0 | 6.0 | **Spike allowed parallel; behind Phase 2 diagnostics in eng priority** |
| Overfit / replication | 9.5 | 6.0 | **A+B non-independence applies to every new claim** |
| Cascade coherence | 10 | 9.0 | Keep narrow-only |
| Overall | **REVISE** | **REVISE** | **REVISE** — ship base; revise next-step framing |

---

## Where judges disagreed → locked choice

### Multi-fold plan (pre–Phase 1)

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Long daily SUPPORTIVE-only | Demote to experiment (Phase 2 arm) | Demote to on/off flag; not default | **Experiment flag — not Phase 1 default.** Ship only if Long net improves on **both** A and B without material Short regression / fire-count breach |
| Rank 1–2 skip | Promote to front-line Phase 1/2 experiment | Front of Phase 2 queue + **root-cause first**; do not lock | **Priority experiment after Phase 1 mechanical base.** Mandatory diagnostic (fallback share, TP/SL/TO, chase proxies) before any default. **Reject** invert size |
| Short acceptance gate | Phase 1 ≥ −5 bps, then ≥ 0 | Phase 1 = **no regression vs fold baseline**; +5 is long-run only | **Phase 1:** Short net must not regress vs each fold’s baseline; interim target ≥ −5 welcome. **Long-run:** ≥ 0 then ≥ +5 after meta if needed |
| Meta-filter timing | Stay staged after rules | Feasibility spike **now** in parallel | **Rules Phase 1 ships first.** Parallel **feasibility spike** (purged CV) allowed — no production meta until rules baseline measured |
| Stricter Long liquidity | Keep cheap Long filter | Bundle / test separately; untested | **Experiment arm** with Long SUPPORTIVE-only (separable where possible) — not an automatic Phase 1 default |

### Post–Phase 1 next steps

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Phase 1 status | Base shipped; not goal-met | Same + population-match caveat | **Shipped as base.** Ablate TOP_K vs gate before claiming “closed X bps” |
| Rank 1–2 | Immediate diagnostic + skip path | Diagnostic mandatory; skip not default yet | **This-week priority: diagnostic.** Skip remains experiment until root-cause favors it |
| Stricter `edge_score` / Q4 floor | Push Q4 floor backtest hard (fire% may fall to ~25–30%) | Demote — Long Q4 n=77 fails n-gate; double-conditioned; not lock candidate | **Experiment flag only.** Stack on median gate; log per-sleeve n; **do not** promote to default this cycle |
| Meta spike priority | Strong parallel priority (rules flat) | Timing OK; “rules closed 1–2 bps” is confounded — don’t pull eng off Phase 2 | **Spike allowed offline/parallel.** Engineering priority **behind** rank 1–2 + setup composition audits. Production meta still Phase 4 |
| Setup-or-skip | Strong defer | Strengthen — composition audit on thin n | **Unlocked.** Audit setup cohort composition (rank / direction / TOD) on A vs B before touching lever |

Unchanged consensus locks: Phase 0 `edge_score`; TOP_K 8→5; shared median conviction gate; reject size invert; reject wait 5→8m; risk kill-switch stays outside Precision fire logic; Fold C not for threshold lock.

---

## Locked implementation sequence

### Phase 0 — Diagnostics integrity (blocker) — **DONE**

1. Add `edge_score` (direction-normalized) to Precision trades / summary.  
2. Re-print by-score and by-sleeve floors on `edge_score` for **Folds A and B**.  
3. Confirm registry rank polarity matches live inference.

### Phase 1 — Mechanical selectivity — **SHIPPED (measured, not accepted-to-goal)**

| # | Change | Owner tier | Rationale |
|---|---|---|---|
| 1 | **`TOP_K`: 8 → 5** — drop ranks 6–8 (skip, do not micro-size) | Precision / Horizon registry | Replicates A+B; parameter-free |
| 2 | **Keep size schedule** 1–2 → 1.0×, 3–5 → 0.7× (no rank 6–8) | Precision | Do not invert |
| 3 | **Shared conviction gate** on setup *and* fallback: `edge_score` ≥ cross-sectional median of that bar’s eligible K names (per sleeve) | Precision | Symmetric; survives Long/Short flip between A and B |

**Not Phase 1 defaults (experiment flags only):**

| # | Change | Notes |
|---|---|---|
| 4 | Long daily `SUPPORTIVE`-only | On/off; require A **and** B Long net lift + Short not materially worse |
| 5 | Stricter Long liquidity | Test with / near (4); do not assume benefit |
| 6 | Rank 1–2 skip | Priority experiment **after** (1)+(3); root-cause diagnostic required before lock |
| 6b | Stricter `edge_score` / Q4 floor | **Hypothesis only** (post–Phase 1). Stack on median; per-sleeve n ≥300–500; not a default this cycle |

Short sleeve: keep daily ∈ `{SUPPORTIVE, AMBIGUOUS}`; still subject to TOP_K=5 + conviction gate.

### Phase 2 — Entry quality (after Phase 1 measured) — **ACTIVE**

| # | Change | Notes |
|---|---|---|
| 7 | **Fallback / setup composition audit** | Setup flipped A (−5) vs B (−20). Audit cohort mix before any setup-or-skip. No soft dump |
| 8 | **Adverse-move abort in wait** | Skip if adverse move >X bps during wait — continuous X needs A+B |
| 9 | **Long no-chase experiment** | `bars_since_regime_flip <= 1` — behind rank 1–2 diagnostic |
| 10 | **Rank 1–2 skip lock decision** | Only if still toxic after Phase 1 base + diagnostic favors skip over chase-fix |

### Phase 3 — Risk layer (parallel, above Precision)

| # | Change | Notes |
|---|---|---|
| 11 | Max concurrent positions; prefer higher `edge_score` when capacity binds | Not a Precision rule |
| 12 | Daily heat / loss kill-switch | Operational; must not mask Phase 1–2 measurement |

### Phase 4 — Meta-filter

13. LightGBM take/skip on TB path success + 1m features; purged + embargoed CV — **production** only if rules selectivity still leaves mean gross on fires < ~30 bps.  
14. **Parallel feasibility spike allowed** — offline, purged CV. Eng priority **behind** Phase 2 diagnostics this week. Do **not** treat “rules closed ~1–2 bps” as proof rules are exhausted (population-mismatched; Phase 2 untried).

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

---

## Acceptance metrics

| Metric | Gate |
|---|---|
| Mean net on fires (blended) | ≥ **0 bps** (from −17.8 / −15.3) |
| Mean net **Long alone** | ≥ **0 bps** — Short must not hide a broken Long |
| Mean net **Short alone** (Phase 1) | **No regression vs fold baseline** (A −5.9 / B −16.5); interim stretch ≥ **−5** welcome |
| Mean net **Short alone** (long-run) | ≥ **0**, then ≥ **+5** once meta / later phases land |
| Min fires per sleeve / window | ≥ **300–500** before locking new thresholds (**C fails this — excluded**) |
| Fire rate | No fixed target; **~25–45%** acceptable if net improves (from ~71–72%) |
| Exit-mix sanity | Selectivity must not only delete TIMEOUT names — watch TP/SL mix |
| Replication | Continuous thresholds need **A+B** sign + rough magnitude; label as *directionally consistent* until a disjoint-train holdout exists |
| Score diagnostics | Cite only `edge_score` quartiles after Phase 0 |
| Fold C | Informational / Regime audit only — **never** a lock input |

---

## Overfit warning (both judges)

2018 was a hostile Indian equity tape; 2019 flipped Long vs Short drag without rule changes. Hyper-tight Long filters tuned on A alone risk learning “don’t trade Long in 2018.” Fold C’s near-zero fire count is a separate cascade-upstream failure mode — do not “fix” it with Precision selectivity knobs. Mitigation: lock only parameter-free cuts early (`TOP_K`); gate continuous thresholds and Long-only daily rules behind Phase 0 + A+B; quarantine C.

**Post–Phase 1 addenda:** (1) Global/`Q4` floors stacked on the median gate are a higher overfit class than the bar-relative median — keep as experiment only. (2) Do not cite “rules closed ~1–2 bps” as exhaustion while Phase 2 levers are untried and TOP_K vs gate are unablated. (3) Setup A vs B opposite signs on n≈220 each is thin-sample instability — audit composition, don’t average away.

---

## Mapping to cascade docs

| Existing lock | This plan |
|---|---|
| Narrow-downward | All filters only skip / size-down — no re-rank or direction flip |
| Frozen TB geometry | Unchanged |
| Rules-first Precision; meta staged | Meta production still Phase 4; feasibility spike parallel OK, behind Phase 2 eng priority |
| Rank-based size | Schedule kept; K tightened; 1–2 skip is experiment not invert |
| Separate Long / Short | Asymmetry **measured** per fold — hard Long daily gate demoted |
| Cost first-order | Selectivity replaces barrier surgery |

---

## Next build step (post–Phase 1 — judge consensus)

1. **Ablate** `TOP_K=5` / gate-off and `TOP_K=8` / gate-on on A+B — isolate contributions; stop citing unmatched Δbps.  
2. **Rank 1–2 root-cause diagnostic** on A+B (TP/SL/TO, `entry_reason` mix, gate-pass rate, chase proxies) — mandatory before any skip default.  
3. **Setup vs fallback composition audit** — why A setup −5 vs B setup −20 on thin n.  
4. Experiment arms: Long SUPPORTIVE-only + Long liquidity on A+B (both-fold lock rule unchanged).  
5. `edge_score` Q4 / stricter floor as **flagged experiment only** — stacked on median; log per-sleeve n; not a default candidate.  
6. Meta feasibility spike (purged CV, offline) — parallel but **behind** steps 2–3 in eng priority.  
7. Fold C Regime/Horizon audit — non-blocking.  
8. Update [precision-tier3-verdict.md](precision-tier3-verdict.md) `TOP_K`/size lines as **Phase 1 base shipped**, not acceptance-met.

### Must not lock yet

- Global / Q4 `edge_score` floor as default  
- Rank 1–2 skip as default (diagnostic pending)  
- Setup-or-skip  
- Long SUPPORTIVE-only / Long liquidity as defaults  
- Adverse-abort continuous X  
- Production meta  
- Anything from Fold C  
- Claim that blended ≥0 is close (−16 / −15 vs 0)

---

## Related

| Doc | Role |
|---|---|
| [cascade-strategy-overview.md](cascade-strategy-overview.md) | Cascade contracts |
| [precision-tier3-verdict.md](precision-tier3-verdict.md) | Entry / exit / size v1 |
| [horizon-tier2-verdict.md](horizon-tier2-verdict.md) | Score sign / ranking |
| [triple-barrier-verdict.md](triple-barrier-verdict.md) | Cost & barrier locks |
