# Tier 1 Regime — Evaluation Framework Verdict

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Tier-level **eval harness** for Regime only (Daily + Intraday) — feature set locked elsewhere  
**Judges:** Gemini Flash, Claude Sonnet  
**Date:** 2026-08-10  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Depends on:** [regime-tier1-verdict.md](regime-tier1-verdict.md), [cascade-strategy-overview.md](cascade-strategy-overview.md), [triple-barrier-verdict.md](triple-barrier-verdict.md), [cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md)  
**Status:** **REVISE → build harness** (philosophy + primary metrics locked; gates hardened before ship)

---

## Summary

| Decision | Locked choice |
|---|---|
| Role of eval | Measure Regime as a **filter** (opportunity discrimination + sleeve correctness) — **not** a PnL engine |
| Confounding | **Never** score Regime with Precision fire PnL or Horizon stock IC |
| Confirmatory / gated metrics | **D2, I1, I5 only** — everything else is diagnostic |
| Daily primary | **D2 Opportunity Separation** (cost-netted; Long ≠ Short; **NO_TRADE excluded** from monotonic order) |
| Intraday primary | **I1 Directional Hit Rate** vs TOD-matched null |
| Bridge primary | **I5 Cascade Admission Quality** — admitted vs rejected index TB+1 (Long ≠ Short) |
| Path series | **INDEX primary** for I1 / I5 / HMM diagnostics; **EW Nifty 100 basket confirmatory** for D2 / D3 only |
| Inference | Session / episode **block bootstrap** CIs — no bar-level binomial “significance” |
| Folds | Lock on **A + B**; **C informational only** (COVID / circuit-halt quarantine) |
| Build posture | **REVISE** (both judges) — build after must-fixes below |

**One-line:** Upstream path quality is failing Precision; evaluate Regime on index/basket opportunity and sleeve admission quality with hard separation from Tier 2/3 skill.

---

## Why this eval exists

WS0/WS1 ([cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md)) showed Tier 3 selectivity cannot clear 30 bps while admitted fires have `tb_tp_rate` only ~7–12%. Optimizing Precision alone on a toxic admitted book is a category error. Tier-level Regime evals answer: *does the gate admit bars where a directional 60m path is even economically plausible?*

---

## Judge scores

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Daily eval design | 9/10 | 7/10 | **Strong taxonomy; fix NO_TRADE ordering** |
| Intraday eval design | 9.5/10 | 8/10 | **I5 is the headline; add autocorrelation discipline** |
| Tier 2/3 separation | 10/10 | 7/10 | **Anti-patterns good; I5 formula must be unambiguous** |
| Practicality (Nifty100 MIS) | 8.5/10 | 7/10 | **Auction bleed + MIS cutoffs mandatory** |
| Acceptance-gate rigor | 8/10 | **4/10** | **Gates were the weak link — harden** |
| Overall | REVISE | REVISE | **REVISE → build** |

---

## Locked philosophy

1. **Regime is a filter**, not a strategy PnL attribution layer.  
2. Prefer **market-level / simple path economics** over cascade end-to-end PnL.  
3. **Long ≠ Short** — every confirmatory metric is a *separate, separately-gated* number. No pooled acceptance.  
4. **Only D2 / I1 / I5 gate ship decisions.** D1, D3–D6, I2–I4, I6–I7 are diagnostic (I7 is a **precondition** before trusting I1–I6).  
5. **Do not invent supervised “true regime” labels.**  
6. **Do not retune Daily/HMM thresholds against D2/I1/I5 on the same fold used for Tier 2/3 selection** without a fresh A+B check.

---

## Metric catalog

### Daily Regime

| ID | Metric | Role |
|---|---|---|
| **D2** | Opportunity Separation (cost-netted, Long/Short) | **PRIMARY / GATED** |
| D1 | Occupancy & calendar hygiene (state %, event clustering) | Diagnostic |
| D3 | Cascade gate purity (usable TREND share on open days) | Diagnostic |
| D4 | Kill-switch quality (`NO_TRADE` left-tail + counterfactual) | Diagnostic (owns `NO_TRADE`) |
| D5 | Leakage / causality audit (pre-open as-of) | Precondition (cheap, binary) |
| D6 | Fold stability (A/B monotonic; C informational) | Diagnostic |

### Intraday Regime

| ID | Metric | Role |
|---|---|---|
| **I1** | Directional hit rate vs TOD-matched null | **PRIMARY / GATED** |
| **I5** | Cascade admission quality (admitted vs rejected IndexTB+1) | **PRIMARY / GATED / BRIDGE** |
| I2 | Economic sleeve quality (index TB by state; CHOP = baseline only) | Diagnostic |
| I3 | Vol calibration (`HIGH_VOL` rv rank; ex-open) | Diagnostic |
| I4 | Persistence / hysteresis (dwell, UP↔DOWN flip rate) | Diagnostic |
| I6 | TOD occupancy + open-bleed `NO_TRADE` compliance | Diagnostic |
| I7 | HMM state-map stability + emission separation + OOS LL | **Precondition** before trusting I1–I6 |

---

## Primary metric definitions (locked)

### Clock windows (all forward-path metrics)

| Constraint | Lock |
|---|---|
| Exclude auction bleed | Bar-end stamp **09:30** out of I1 / I3 / I5 gates (report Full vs Ex-Open; **gate on Ex-Open**) |
| Long last decision bar | ≤ **~14:15** bar-end (match Tier 3 / TB) |
| Short last decision bar | ≤ **~14:00** bar-end |
| Horizon | **H = 4** bars (**60m**) — same as Tier 2 / TB |
| Cost | **c = 0.0030** netted into opportunity / TB floors |

### D2 — Opportunity Separation (Daily, PRIMARY)

For session `T`, side ∈ `{+1 long, −1 short}`, over realizable windows only:

```
OpportunityScore(T, side) =
  max over windows (t0, t1) with t1−t0 ≤ 60m,
      first tradable bar ≤ t0, t1 ≤ MIS-safe exit
  of  max(0, side · R(t0,t1) − c)

D2_long(X)  = mean(OpportunityScore(T,+1) | DailyRegime(T)=X),  X ∈ {SUPPORTIVE, AMBIGUOUS, HOSTILE}
D2_short(X) = mean(OpportunityScore(T,−1) | DailyRegime(T)=X),  X ∈ {SUPPORTIVE, AMBIGUOUS, HOSTILE}
```

**Series:** EW Nifty 100 basket **primary for D2**; also report index for divergence diagnostic vs `breadth_div`.

**Gate (A+B):**  
`D2_*(SUPPORTIVE) ≥ D2_*(AMBIGUOUS) ≥ D2_*(HOSTILE)` per side, with session-block-bootstrap 95% CI on **SUPPORTIVE − HOSTILE** having lower bound **> 0**.  
Minimum cell N (sessions): report-only if **N < 30**.

**Critical correction (Claude, locked):** **`NO_TRADE` is NOT in the D2 monotonic order.** Shock / VIX-spike days can have *large* moves; Regime vetoes them because they are not safely capturable. Score `NO_TRADE` only under **D4** (left-tail avoidance + counterfactual forced-trade cost).

### I1 — Directional Hit Rate (Intraday, PRIMARY)

On post-hysteresis, ex-bleed index bars inside MIS entry cutoffs:

```
R60(t) = (P(t+4) − P(t)) / P(t)     # index absolute path

HitRate_UP   = P(R60 > 0 | TREND_UP)
HitRate_DOWN = P(R60 < 0 | TREND_DOWN)

Null: TOD-matched circular shuffle of regime labels across sessions
      (same TOD bucket; day return path fixed); N≥1000

Edge_* = HitRate_* − HitRate_null_*
```

**Series:** **INDEX only** (HMM is fit on Nifty 15m).

**Gate (A+B):** lower bound of **session/episode-block-bootstrap** 95% CI on `Edge_UP` and on `Edge_DOWN` each **> 0**.  
Do **not** ship on a raw “≥53% hit rate” point estimate alone (autocorrelated dwell inflates naive tests).

Provisional diagnostic targets (not ship locks until baseline measured): hit ≥ ~53%, edge ≥ ~3 pp — Gemini’s numbers stay as **aspirational readouts**, Claude’s CI rule is the gate.

### I5 — Cascade Admission Quality (BRIDGE, PRIMARY)

Fix ambiguity: score **absolute index path** with locked TB geometry (not excess-vs-self):

```
IndexTB(t, side) ∈ {+1, −1, 0} over P(t..t+4)
  using TOD rv_15_mean-scaled TP/SL + cost floors from triple-barrier-verdict
  (Long TP floor ≥ 90 bps; Short floors per locked Short geometry)

Admitted_long  = Daily ∈ {SUPPORTIVE, AMBIGUOUS} ∧ TREND_UP
Rejected_long  = Daily ∈ {SUPPORTIVE, AMBIGUOUS} ∧ Intraday ≠ TREND_UP
                 (same daily-open days; CHOP / HIGH_VOL / TREND_DOWN)

I5_long  = P(IndexTB=+1 | Admitted_long) − P(IndexTB=+1 | Rejected_long)
I5_short = mirror
```

Also report mean signed 60m return (admitted − rejected) with the same CI method.

**Series:** **INDEX primary** for I5 (Claude). Do **not** use EW basket for I5 — that imports Horizon’s cross-sectional job into a Regime-only eval. Basket divergence vs index is a **diagnostic**, not an I5 gate.

**Gate (A+B):** `I5_long` and `I5_short` each have block-bootstrap 95% CI lower bound **> 0**; report absolute admitted TB+1 rate (anchor vs documented stock-level ~7–12% `tb_tp_rate` as context). Absolute floors (e.g. Gemini’s ≥20% / ≥8 pp) are **provisional diagnostics** until Fold A/B baselines exist — then promote concrete floors.

**CHOP:** reference / null baseline only in v1 momentum path — never scored as a directional TB class for gates (I2 diagnostic only).

---

## Path series division of labor

| Series | Use for | Do not use for |
|---|---|---|
| **Nifty index (`^NSEI`)** | I1, I5, I3, I4, I7 | Pretending it is the tradable book |
| **EW Nifty 100 (PIT membership)** | D2, D3 confirmatory; index↔basket divergence | I1 / I5 gates |

Basket must be **survivorship-free** historical membership + corporate-action adjusted, **independent** of Horizon eligibility filters.

---

## Acceptance gates (hardened)

### Confirmatory (must pass on Fold A **and** B)

| Gate | Rule |
|---|---|
| D5 leakage | Pass / fail binary before research metrics |
| I7 state-map | Stable UP/DOWN labels across retrains (emission-mean map); else discard I1–I6 |
| D2 | Monotonic S ≥ A ≥ H per side; CI(S−H) LB > 0; N≥30 per cell |
| I1 | CI(Edge) LB > 0 for UP and for DOWN (ex-open, MIS cutoffs) |
| I5 | CI(I5) LB > 0 for Long and for Short separately |

### Diagnostic (report; do not ship-lock alone)

| Check | Guidance |
|---|---|
| Coverage `SUPPORTIVE+AMBIGUOUS` | Report; Gemini prefers ~45–65% — **do not hard-lock** until baselines; Claude: loose 40–75% is not a gate |
| I4 dwell / flip | ASD(TREND_*) diagnostic; Gemini aspirational ASD ≥ 3 bars, DFR < 5% post-hysteresis |
| I3 HIGH_VOL | Median rv rank elevated vs non-HIGH_VOL on ex-open |
| D4 NO_TRADE | Left-tail avoidance + counterfactual cost; quantify over/under-veto (no free “prefer over-veto” rhetoric) |
| Fold C | Informational only — never a lock input |

### Minimum-N floor

Any cell with **< 30 sessions** (Daily) or **< 100 bars** (Intraday) → **insufficient data**, never gated.

---

## Top 5 to implement first (80% diagnostic value)

| Rank | Metric | Why |
|---|---|---|
| 1 | **I5** | Answers the WS0/WS1 escalation: is the admitted book better than rejected? |
| 2 | **I1** | Fail-fast: does TREND_UP/DOWN carry any directional information? |
| 3 | **D2** | Does Daily order days by cost-netted opportunity (Long/Short)? |
| 4 | **I7 + D5** | Preconditions — unstable HMM / leakage silently corrupt #1–#3 |
| 5 | **I4** (dwell/flip) | Whipsaw diagnostic before blaming Precision |

Second wave: D1, D3, D4, D6, I2, I3, I6.

---

## Anti-patterns (locked)

1. Scoring Regime with Precision fire PnL  
2. Using Horizon stock-picking IC as a Regime score  
3. Locking thresholds on Fold C  
4. Supervised regime accuracy vs hand labels  
5. Retuning Daily/HMM thresholds against D2/I1/I5 on the same selection data without a fresh A+B holdout  
6. Pooling Long+Short into one acceptance number  
7. Bar-level binomial tests ignoring episode autocorrelation  
8. Putting `NO_TRADE` on the D2 “lowest opportunity” ladder  
9. Scoring I5 on EW basket (Horizon confound)  
10. Crediting opportunity after MIS entry cutoffs  

---

## Where judges disagreed

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Overall | REVISE (enthusiastic) | REVISE (strict on gates) | **REVISE** |
| Gate rigor | Point hit-rate / fixed pp floors | CI LB > 0 + effect size; soft floors premature | **CI LB > 0 gates**; absolute floors provisional |
| D2 + `NO_TRADE` | Monotonic through `NO_TRADE` | Exclude — shock days ≠ low opportunity | **Exclude; D4 owns NO_TRADE** |
| I5 series | EW basket for economic I5 | Index-only for I5 | **Index for I5**; basket for D2/D3 |
| Coverage gate | Tighten to 45–65% | Not a confirmatory gate | **Diagnostic report only** |
| Significance | Binomial p < 0.05 | Session/episode block bootstrap | **Block bootstrap** |
| Top-5 #4/#5 | I4 dwell, I3 vol | I7 + D5 preconditions | **Preconditions before dwell/vol** |
| Long ≠ Short | Implied | Must wire into every gate | **Wired into every confirmatory gate** |

---

## NSE / India pitfalls (eval harness)

1. **Auction bleed** — exclude 09:30 bar-end from gated I1/I3/I5 (same as HMM fit).  
2. **MIS cutoffs** — Long ~14:15 / Short ~14:00 / live flat ~15:00 — no unrealizable forward windows.  
3. **VIX crush** (Budget / RBI / elections) — event calendar for D1/D4 false-negative `NO_TRADE`.  
4. **Expiry days** — report expiry vs non-expiry slices; don’t let weekly gamma pollute pooled gates.  
5. **EW basket integrity** — PIT membership, CA adjustments, circuits; no Horizon eligibility bleed.  
6. **Index vs basket divergence** — heavyweight-driven index TREND with weak breadth; validates `breadth_div`.  
7. **Fold C** — circuit-halt data-quality ≠ regime-quality; quarantine.  

---

## Implementation sequence

1. Path generators: index + PIT EW Nifty 100; MIS/auction masks; locked TB geometry on index.  
2. Preconditions: D5 leakage audit + I7 state-map stability.  
3. Primaries: **I5 → I1 → D2** on Folds A and B (Long/Short split, block-bootstrap CIs).  
4. Diagnostics: I4 dwell/flip, I3 vol, D1/D3/D4/D6.  
5. Promote absolute I5/I1 floors only after A+B baselines exist — not before.

**Harness (shipped):** `src/regime/eval/` (`daily_eval.py`, `intraday_eval.py`) + CLI  
`python -m src.experiments.eval_regime_tier1 --train-period 2015-2017 --test-period 2018-2018`  
(`--n-boot` default 500).

---

## Out of scope

- Redesigning Daily features / HMM emissions (see [regime-tier1-verdict.md](regime-tier1-verdict.md))  
- Horizon IC evals / Precision fire evals (separate tier harnesses)  
- Mean-reversion under `CHOP` as a gated path  
- Using this harness to claim cascade net ≥ 0 — that remains an end-to-end metric after upstream clears  

---

## Related docs

| Doc | Role |
|---|---|
| [regime-tier1-verdict.md](regime-tier1-verdict.md) | Locked features / states |
| [cascade-strategy-overview.md](cascade-strategy-overview.md) | Cascade contracts |
| [triple-barrier-verdict.md](triple-barrier-verdict.md) | H=4, cost floors, MIS clocks |
| [cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md) | Why escalate to Regime |
| [horizon-tier2-verdict.md](horizon-tier2-verdict.md) | Locked Tier 2 features / hyperparams |
