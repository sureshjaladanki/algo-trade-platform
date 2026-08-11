# Tier 1 Regime — v1.1 Revision (proposal)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Proposed revisions to Daily / Intraday Regime **strategy** after Tier-1 eval  
**Status:** **OPEN — iterate here; merge into [regime-tier1-verdict.md](regime-tier1-verdict.md) only when locked**  
**Judges:** Gemini Flash, Claude Sonnet  
**Date:** 2026-08-10  
**Depends on:** [regime-tier1-verdict.md](regime-tier1-verdict.md) (locked v1 — do not edit for this cycle), [regime-tier1-eval-verdict.md](regime-tier1-eval-verdict.md)  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  

---

## How to use this doc

1. Keep [regime-tier1-verdict.md](regime-tier1-verdict.md) frozen as the shipped v1 contract.  
2. Land candidate changes, ablations, and judge notes **here**.  
3. When a change clears A+B gates and is accepted, **merge** that slice into the locked verdict and mark it **MERGED** below.  
4. Do not retune Daily/HMM thresholds against D2/I1/I5 on the same fold used for Tier 2/3 selection without a fresh A+B check.

---

## Summary

| Decision | Working choice (not merged) |
|---|---|
| Overall posture | **REVISE** (both judges) — O1 first, isolated |
| Root cause | Calm `SUPPORTIVE` ≠ cost-netted opportunity → D2 inverted |
| Ship now | **O1 only** (`trend_strength` redefine of `SUPPORTIVE`) |
| Sequence next | O3 diagnostic → optional hard gate → O5 lag-1 autocorr |
| Reject this cycle | O6 `rv_delta`, O7 forced min-dwell, breadth primary, bundled multi-lever builds |

**One-line:** Fix Daily “calm = supportive” first; do not bundle HMM / side-gate / dwell into the same re-eval.

---

## Eval evidence (A+B)

Harness: `python -m src.experiments.eval_regime`

| Fold | Train → Test |
|---|---|
| A | 2015–2017 → 2018 |
| B | 2016–2018 → 2019 |

| Gate | Result (both folds) | Read |
|---|---|---|
| D5 / I7 | PASS | Instrumentation OK; strategy fails |
| **D2** | **FAIL inverted** (H > A > S on Long+Short, index+EW100) | Calm greens lose to high-vol HOSTILE on OpportunityScore |
| **I1** | **FAIL** (bar hit ~52–57%; session Edge ≤ 0 vs TOD null) | Labels more clock-correlated than path-predictive |
| **I5** | **FAIL** (`p_adm` ~0–1% IndexTB+1; CI LB ≤ 0) | Admitted book not better than rejected |
| I4 | ASD TREND ~5–7, flip ~2–2.5% | Not the failure mode |

Illustrative D2 long index points:

| Fold | SUPPORTIVE | AMBIGUOUS | HOSTILE |
|---|---|---|---|
| 2018 | 0.0003 | 0.0011 | 0.0016 |
| 2019 | 0.0007 | 0.0010 | 0.0022 |

**Root cause (both judges):** v1 `SUPPORTIVE` = calm + non-negative trend. D2 rewards realized cost-netted range, so elevated-vol `HOSTILE` mechanically outscores calm greens. Daily is also direction-agnostic while D2/I5 gate Long ≠ Short separately.

---

## Judge scores (v1.1 package)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | 9.5/10 | 8/10 | Calm ≠ capturable under 30 bps |
| Daily opts | 9/10 | 6/10 | **O1 lock; O2 stay confirmatory this cycle** |
| Intraday opts | 8.5/10 | 5/10 | **O5 lag-1 only after O1; reject O6/O7** |
| Cascade-contract safety | 9.5/10 | 6/10 | O3 needs diagnostic + explicit re-lock |
| Overfitting risk | 10/10 | 5/10 | **Isolate levers; no A+B threshold search** |
| Overall | REVISE | REVISE | **REVISE — O1 alone first** |

---

## Candidate ledger

| ID | Change | Gemini | Claude | Working lock | Merge status |
|---|---|---|---|---|---|
| **O1** | Redefine `SUPPORTIVE` via **trend_strength** (ATR-scaled EMA20 slope or ADX14); flat green → `AMBIGUOUS` | ACCEPT | ACCEPT | **SHIP FIRST (alone)** | IMPLEMENTED — **D2 FAIL A+B** (not MERGED) |
| O2 | Promote `breadth_div` → primary veto | ACCEPT | REVISE | Stay confirmatory; revisit only if O1 fails D2 | OPEN |
| O3 | Side-aware admission (`market_trend` sign) | REVISE (hard gate) | REVISE (measure first) | Diagnostic slice first; hard gate only after CI-positive + re-lock Daily≠direction in locked verdict | DIAGNOSTIC DONE — **no hard gate** (Long CI− both folds; Short CI+ A only) |
| O4 | Tighten `NO_TRADE` / cut coverage; `expiry_flag` | ACCEPT | SPLIT | `expiry_flag` diagnostic only; occupancy via D4 — do not retune with O1 | OPEN |
| O5 | HMM emission `r_autocorr` | ACCEPT | REVISE | lag-1 only, after O1 clears D2 | OPEN |
| O6 | HMM `rv_delta` | REJECT | REJECT | **REJECT** | REJECTED |
| O7 | Force 3-bar TREND min dwell | REVISE | REJECT | **REJECT this cycle** (I4 healthy) | REJECTED |
| O8 | No D2/I1/I5 threshold search on A+B; no supervised labels; no full ideal dump | ACCEPT | ACCEPT | **LOCK** (process) | N/A |

---

## Build order (working)

Claude isolation wins over Gemini’s single bundled pass:

1. **O1 only** — add Daily `trend_strength`; redesign `SUPPORTIVE`/`AMBIGUOUS` from a **train-period design prior** (not a D2 grid search); re-run D2 on A **and** B independently.  
2. **O3 diagnostic** — slice D2_long/short by `market_trend` sign under new O1 Daily; no runtime gate yet.  
3. **Gate decision** — if step 2 CI-positive, re-lock “Daily may tilt side” in the **locked** verdict, then wire hard admission; re-run D2/I5.  
4. **`expiry_flag` + D4** — report-only this cycle.  
5. **O5 lag-1 autocorr** — isolated I1 re-test only after steps 1–4 land.

---

## Acceptance before merge

A candidate merges into [regime-tier1-verdict.md](regime-tier1-verdict.md) only when:

- D2 (for Daily changes): `S ≥ A ≥ H` per side on **both** A and B; CI(S−H) LB > 0; cell N ≥ 30  
- I1 / I5 (when their turn): CI LB > 0 per side on both folds; Long ≠ Short  
- One structural change per re-eval cycle  
- 2018 vs 2019 point dispersion reported; large dispersion is a stop signal even if CIs pass  

---

## Explicit do-not (this revision cycle)

- Edit [regime-tier1-verdict.md](regime-tier1-verdict.md) until a row above is marked **MERGED**  
- Bundle O1+O3+O5+O7 into one build-then-eval pass  
- Promote breadth / expand to ideal ~10 Daily features this cycle  
- Add `rv_delta` or force min-dwell while I4 is healthy  
- Declare victory on a single fold or pooled A+B  

---

## Where judges disagreed

| Topic | Gemini Flash | Claude Sonnet | Working lock |
|---|---|---|---|
| Breadth primary now | ACCEPT | Stay confirmatory | Confirmatory |
| O3 hard gate immediately | Yes (runtime) | Diagnostic → re-lock → gate | Diagnostic first |
| O5 timing | With O1 build | After O1 clears D2 | After O1 |
| O7 min dwell | 3-bar | Leave alone | Leave alone |
| Build bundling | Side-gate + Daily + HMM + hysteresis then eval | Isolate each lever | Isolate |

---

## Iteration log

| Date | Change | Result | Next |
|---|---|---|---|
| 2026-08-10 | Dual-judge package O1–O8 drafted from A+B eval fails | REVISE; O1 first | Implement O1; re-run D2 A+B |
| 2026-08-11 | **O1 code** — `trend_strength` = ATR-scaled 5d EMA20 slope (pre-open); SUPPORTIVE = `market_trend≥0` + `\|ts\|≥` train-median + breadth; calm **not** required for SUPPORTIVE; flat → AMBIGUOUS. Locked verdict untouched. | Code landed | Re-run D2 A+B |
| 2026-08-11 | **O1 D2 re-eval A+B** (thr A=0.610 / B=0.654) | **D2 FAIL both folds** — still H≳A≳S; CI(S−H) LB &lt; 0. Occupancy: S~30–33% (was ~50%). D5/I7 PASS. I1/I5 still FAIL (expected; not this cycle). | O3 diagnostic (Claude step 2) |
| 2026-08-11 | **O3 diagnostic** — `O3[series]` in eval harness: session OpportunityScore sliced by `market_trend` sign (all sessions; no runtime gate) | **No hard gate.** Long aligned−mis **CI− / inverted** on A+B (trend− days have *higher* long opportunity). Short aligned−mis **CI+ on A only**, ~0 / CI straddles 0 on B. | Do **not** re-lock Daily side tilt; do **not** wire hard admission. Next isolated lever: **O2** (breadth) or stop and revisit D2 metric fit |

### O1 D2 snapshot (post-change)

| Fold | Series | Side | S | A | H | S−H CI LB | Gate |
|---|---|---|---:|---:|---:|---:|---|
| A 2018 | index | long | 0.0002 | 0.0007 | 0.0016 | −0.0018 | FAIL |
| A 2018 | index | short | 0.0005 | 0.0008 | 0.0018 | −0.0019 | FAIL |
| A 2018 | ew100 | long | 0.0008 | 0.0011 | 0.0025 | −0.0024 | FAIL |
| A 2018 | ew100 | short | 0.0015 | 0.0012 | 0.0028 | −0.0022 | FAIL |
| B 2019 | index | long | 0.0006 | 0.0009 | 0.0022 | −0.0028 | FAIL |
| B 2019 | index | short | 0.0010 | 0.0012 | 0.0012 | −0.0007 | FAIL |
| B 2019 | ew100 | long | 0.0008 | 0.0016 | 0.0027 | −0.0038 | FAIL |
| B 2019 | ew100 | short | 0.0014 | 0.0020 | 0.0018 | −0.0010 | FAIL |

**Read:** Strength floor shrinks SUPPORTIVE and moves flat greens to AMBIGUOUS, but HOSTILE still wins OpportunityScore (range-driven). Do **not** merge O1 into locked verdict. Do **not** retune the median prior against D2 on A/B.

### O3 diagnostic snapshot (aligned − misaligned)

Long aligned = `market_trend ≥ 0`; short aligned = `market_trend ≤ 0`. All sessions; N = min(aligned, misaligned).

| Fold | Series | Side | aligned | misaligned | Δ | CI LB | Evidence |
|---|---|---|---:|---:|---:|---:|---|
| A 2018 | index | long | 0.0004 | 0.0017 | −0.0013 | −0.0019 | FAIL (inverted) |
| A 2018 | index | short | 0.0017 | 0.0006 | +0.0011 | +0.0006 | PASS |
| A 2018 | ew100 | long | 0.0009 | 0.0025 | −0.0016 | −0.0024 | FAIL (inverted) |
| A 2018 | ew100 | short | 0.0026 | 0.0014 | +0.0012 | +0.0004 | PASS |
| B 2019 | index | long | 0.0008 | 0.0019 | −0.0011 | −0.0021 | FAIL (inverted) |
| B 2019 | index | short | 0.0012 | 0.0011 | ~0 | −0.0006 | FAIL |
| B 2019 | ew100 | long | 0.0014 | 0.0023 | −0.0009 | −0.0023 | FAIL |
| B 2019 | ew100 | short | 0.0018 | 0.0017 | ~0 | −0.0006 | FAIL |

**Read:** Side-sign does **not** clear dual-fold CI+ for both Long and Short. Long is anti-aligned with OpportunityScore (same range/HOSTILE mechanism). **No contract re-lock; no hard gate.**

---

## O1 implementation notes (working)

| Item | Choice |
|---|---|
| Feature | `trend_strength = (EMA20 − EMA20_{t−5}) / ATR14`, shifted to T−1 (pre-open) |
| Lookback | 5 sessions (design prior; not D2-searched) |
| SUPPORTIVE floor | Train-period median `\|trend_strength\|` via `design_trend_strength_threshold`; fallback `0.5` |
| Rule change | `SUPPORTIVE` = `market_trend ≥ 0` + `|trend_strength|` floor + breadth confirmatory; **calm no longer required** for SUPPORTIVE (HOSTILE/NO_TRADE still own vol crisis). Flat/weak strength → `AMBIGUOUS` |
| Not changed | HOSTILE / NO_TRADE; breadth confirmatory; HMM |

---

## O3 implementation notes (working)

| Item | Choice |
|---|---|
| Scope | **Diagnostic only** in `o3_side_trend_diagnostic` — no cascade / admission change |
| Universe | All sessions (tradeable-only was thin: SUPPORTIVE already requires `market_trend ≥ 0`) |
| Metric | Mean OpportunityScore by side × trend sign; bootstrap CI on aligned − misaligned |
| Hard gate | **Not wired** — dual-fold CI+ for Long **and** Short not met |

---

## Related docs

| Doc | Role |
|---|---|
| [regime-tier1-verdict.md](regime-tier1-verdict.md) | Locked v1 — merge target only when locked |
| [regime-tier1-eval-verdict.md](regime-tier1-eval-verdict.md) | Eval harness / gates |
| [cascade-strategy-overview.md](cascade-strategy-overview.md) | Cascade contracts |
| [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md) | Why Regime was escalated |
