# Tier 1 Regime — v1.1 Revision (proposal)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Proposed revisions to Daily / Intraday Regime **strategy** after Tier-1 eval  
**Status:** **HANDOFF — Daily / D2′ / emission cycle closed here; Intraday architecture continues in [regime-tier1-v12-revision.md](regime-tier1-v12-revision.md)**  
**Judges:** Gemini Flash, Claude Sonnet  
**Date:** 2026-08-10  
**Depends on:** [regime-tier1-verdict.md](../regime-tier1-verdict.md) (locked v1 — do not edit for this cycle), [regime-tier1-eval-verdict.md](../regime-tier1-eval-verdict.md)  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Continues in:** [regime-tier1-v12-revision.md](regime-tier1-v12-revision.md) (**CLOSED — A0**; see [stop memo](regime-tier1-stop-memo.md))
---

> **Continuity:** v1.1 is the archive for O1–O8, D2′, I1 harness fix, I5 diagnostics, and emission tries (O5 / `adr_15` / HL/CO). Emission-add search is **CLOSED**. Intraday architecture try (A1) completed in **[regime-tier1-v12-revision.md](regime-tier1-v12-revision.md)** and terminated via **[A0 stop memo](regime-tier1-stop-memo.md)**. Do not reopen closed cycles here.

---

## How to use this doc

1. Keep [regime-tier1-verdict.md](../regime-tier1-verdict.md) frozen as the shipped v1 contract.  
2. Land candidate changes, ablations, and judge notes **here** for the Daily / emission cycle only. **Intraday architecture → [v1.2](regime-tier1-v12-revision.md).**  
3. When a change clears A+B gates and is accepted, **merge** that slice into the locked verdict and mark it **MERGED** below.  
4. Do not retune Daily/HMM thresholds against D2/I1/I5 on the same fold used for Tier 2/3 selection without a fresh A+B check.

---

## Summary

| Decision | Working choice (not merged) |
|---|---|
| Overall posture | **HANDOFF to v1.2** — emissions CLOSED; architecture lock recorded; A1 implementation continues in v12 |
| Root cause (updated) | Daily exhausted; triad+HMM saturated; 4th emissions collapse occupancy/edge; corrected I1 = noise |
| O1 / O3 / D2′ / O5 / adr_15 / HL/CO / A2 | Closed/reverted/rejected; nothing MERGED |
| Ship / merge | **Nothing** in v1.1 |
| Sequence next | → **[regime-tier1-v12-revision.md](regime-tier1-v12-revision.md)** — frozen A1 → H1+H2 → merge or stop-memo |
| Reject this cycle | O2, O3 hard gate, D2′ search, O6/O7, IndexTB floors, Daily reopen, more emissions, A2, quantile search, merge-on-H1-alone, “HMM has partial signal” |

**One-line:** v1.1 closed at dual-judge architecture lock (emissions CLOSED; A1 working lock) — **continue in [v1.2](regime-tier1-v12-revision.md)**.


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
| **I1** | **FAIL gate** (corrected Edge ≈ +3–7pp; not Long+Short on A+B) | Weighting fixed; residual side×fold CI miss |
| **I5** | **FAIL** (`p_adm` ~0–1% IndexTB+1; CI LB ≤ 0) | Admitted book not better than rejected |
| I4 | ASD TREND ~5–7, flip ~2–2.5% | Not the failure mode |

Illustrative D2 long index points (pre-O1 baseline):

| Fold | SUPPORTIVE | AMBIGUOUS | HOSTILE |
|---|---|---|---|
| 2018 | 0.0003 | 0.0011 | 0.0016 |
| 2019 | 0.0007 | 0.0010 | 0.0022 |

**Root cause (both judges, post-O1/O3):** v1 `SUPPORTIVE` = calm + non-negative trend was the first read. After O1 still fails identically, judges lock a sharper diagnosis: **D2 OpportunityScore is a max over overlapping session windows**, so it is mechanically inflated by realized intraday variance. Elevated-vol `HOSTILE` outscores orderly `SUPPORTIVE` by construction — Daily feature knobs cannot flip that.

---

## Judge scores (v1.1 package — initial)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | 9.5/10 | 8/10 | Calm ≠ capturable under 30 bps |
| Daily opts | 9/10 | 6/10 | **O1 lock; O2 stay confirmatory this cycle** |
| Intraday opts | 8.5/10 | 5/10 | **O5 lag-1 only after O1; reject O6/O7** |
| Cascade-contract safety | 9.5/10 | 6/10 | O3 needs diagnostic + explicit re-lock |
| Overfitting risk | 10/10 | 5/10 | **Isolate levers; no A+B threshold search** |
| Overall | REVISE | REVISE | **REVISE — O1 alone first** |

---

## Judge scores (post-O1/O3 validation — 2026-08-11)

Judges: [Gemini Flash](4bc32ee7-a35e-4d08-b6d7-588416fcc85d), [Claude Sonnet](74fcc8b3-d65c-4092-ab81-93471cd26bc9)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity (post) | 10/10 | 7/10 | Numbers correct; failure is **D2 operator**, not Daily knobs |
| O1 implementation fidelity | 9/10 | 9/10 | Clean isolation; train-only prior; no D2 search |
| O3 diagnostic design | 8/10 | 6.5/10 | Keep as diagnostic; all-session OK for power (label scope) |
| Cascade-contract (no hard gate) | 10/10 | 9/10 | **Correct** — Long inverted; Short not dual-fold |
| Overfitting / process | 10/10 | 8/10 | Extend O8: pre-register any D2 redesign before A/B peek |
| Overall next posture | **REVISE** | **REVISE** | **Freeze Daily; redesign D2; do not run O2 now** |

### Metric validation (both judges)

| Claim | Verdict |
|---|---|
| O1 D2 still H≳A≳S, CI(S−H) LB&lt;0 both folds | **Validated** |
| O3 Long inverted / Short A-only CI+ → no hard gate | **Validated** |
| O1 alone cannot clear current D2 | **Validated** — structural, not under-tuned |
| O2 would likely fail the same way against current D2 | **Agreed** — do not spend the cycle |
| Current D2 is unfit as Daily gate while = max-window opportunity | **Agreed stop signal** |

### O3 universe note (Claude)

All-session O3 answers “does trend sign carry market-wide side opportunity?” — **not** “would side-tilting the admitted S+A book help?” Correct for power given SUPPORTIVE already requires `trend≥0`; any future gate re-test must slice the **admitted book** specifically.

---

## Candidate ledger

| ID | Change | Gemini | Claude | Working lock | Merge status |
|---|---|---|---|---|---|
| **O1** | Redefine `SUPPORTIVE` via **trend_strength** (ATR-scaled EMA20 slope or ADX14); flat green → `AMBIGUOUS` | ACCEPT | ACCEPT | Tried; no lift vs v1 on D2′ | **REVERTED** — cascade back on locked v1 |
| O2 | Promote `breadth_div` → primary veto | REVISE (was ACCEPT) | **REJECT this cycle** | **Do not run** against current D2 | BLOCKED |
| O3 | Side-aware admission (`market_trend` sign) | REJECT hard gate | ACCEPT diagnostic-closed | Diagnostic done; **no hard gate** | CLOSED (diag) |
| O4 | Tighten `NO_TRADE` / cut coverage; `expiry_flag` | ACCEPT expiry diag | ACCEPT report-only | `expiry_flag` / D4 report-only | OPEN |
| O5 | HMM emission `r_autocorr` | REJECT until harness fix | ACCEPT if corrected FAIL | Tried; I1/I5 not cleared; HIGH_VOL starved | **REVERTED** |
| **I1 fix** | Same-weight Edge (bar HitRate − bar null) | ACCEPT | ACCEPT | **IMPLEMENTED** — re-baseline logged | N/A |
| O6 | HMM `rv_delta` | REJECT | REJECT | **REJECT** | REJECTED |
| O7 | Force 3-bar TREND min dwell | REJECT | REJECT | **REJECT this cycle** | REJECTED |
| O8 | No D2/I1/I5 threshold search on A+B; no supervised labels | ACCEPT | ACCEPT + extend | **LOCK** + pre-register D2 redesign before peek | N/A |
| **D2′** | Redesign Daily gate metric (not a Daily feature) | ACCEPT (trend efficiency) | ACCEPT (fixed-rule first) | Fixed-rule **implemented**; A+B FAIL for O1 and v1 | IMPLEMENTED — **gate FAIL A+B** (not MERGED) |

---

## D2′ pre-registration (LOCKED 2026-08-11 — before A/B peek)

Per dual-judge stop signal: replace max-window OpportunityScore before more Daily work.

| Item | Locked construction |
|---|---|
| Name | **D2′** / harness metric `D2p[series]` |
| Entry | First 15m bar with `time ≠ open-bleed (09:30)` and `time ≤ MIS last-entry` (Long/Short cutoffs) |
| Exit | Exactly **H=4** bars later (same session; drop session if incomplete) |
| Score | `side * (exit/entry − 1) − ROUND_TRIP_COST` (**signed**, not floored at 0) |
| Aggregate | Mean score by DailyRegime × side; NO_TRADE reported only |
| Gate | `S ≥ A ≥ H` and session-bootstrap 95% CI(S−H) LB > 0; N≥30 per cell; Long ≠ Short; A+B independent |
| Compare | One-shot `D2p_v1` vs O1 done (both FAIL); compare path **removed** from harness |
| Legacy | `D2max` = old max-window OpportunityScore — **diagnostic only**, not ship-gated |
| Fallback (not this pass) | Gemini trend-efficiency / capture-ratio — only if fixed-rule D2′ still structurally broken |
| Forbidden | Searching alternate D2′ formulae until S≥A≥H appears on A/B |
| Multi-window addendum | **D2p_mw** one-shot on Fold B then **removed from harness** (results kept in iteration log) |

---

## Build order (working — post I1/I5 judge lock)

Dual-judge after v1 I1/I5 re-baseline ([Gemini](66d3c4e2-a238-4a18-863a-a1ff17347549), [Claude](a4533e9e-e0f5-4b9c-913e-70237dc944b5)):

1. **Fix I1 weighting** — Edge = bar-pooled HitRate − bar-pooled TOD null; session-block bootstrap keeps bar weights. **Done** (2026-08-11).  
2. **I5 diagnostics (not new ship gate):** TOD-stratified `I5tod` + signed-60m `I5r` companions. **Done** — FAIL not TOD-driven; R60 lift tiny / not dual-fold CI+. Keep Δ gate; no floor redesign.  
3. **Re-baseline I7→I1→I5** under corrected harness. **Done** — I1 not dual-fold Long+Short; I5 FAIL both folds.  
4. **O5 only** (lag-1 `r_autocorr`); isolate; re-run I7→I1→I5. **Done — FAIL; REVERTED** to triad emissions.  
5. **Intraday breadth (`adr_15`)** isolated. **Done — FAIL on Fold A (I1+I5); REVERTED** (Fold B not required after A reject).  
6. **HL/CO candle** — one isolated 4th emission. **Done — FAIL on Fold A (I1+I5; short TREND empty); REVERTED** (Fold B skipped after A reject).  
7. **Emission-add search CLOSED** (locked language, 2026-08-11). No more raw 4th HMM features on this structure.  
8. **Dual-judge architecture lock** ([Gemini](34249fc1-129e-4313-afb6-d68e83133148), [Claude](1eb07b19-7f27-41c8-ba06-cca3d71b580e)). **Done** — see judge section below.  
9. **Handoff → [regime-tier1-v12-revision.md](regime-tier1-v12-revision.md)** — implement frozen A1 → H1+H2 → stop-memo if FAIL. **(Active work lives in v1.2.)**


---

## Acceptance before merge

A candidate merges into [regime-tier1-verdict.md](../regime-tier1-verdict.md) only when:

- D2 / D2′ (for Daily changes): `S ≥ A ≥ H` per side on **both** A and B; CI(S−H) LB > 0; cell N ≥ 30  
- I1 / I5 (when their turn): CI LB > 0 per side on both folds; Long ≠ Short  
- One structural change per re-eval cycle  
- 2018 vs 2019 point dispersion reported; large dispersion is a stop signal even if CIs pass  
- **D2′ construction pre-registered** before any A/B peek under the new formula (O8 extension)

---

## Explicit do-not (this revision cycle)

- Edit [regime-tier1-verdict.md](../regime-tier1-verdict.md) until a row above is marked **MERGED**  
- Run **O2** or further Daily knobs against the **current** max-window D2  
- Wire O3 as a runtime hard gate  
- Grid-search D2′ until S≥A≥H appears on A/B — pre-register first  
- Bundle D2′ + O2 + O5 into one re-eval  
- Add `rv_delta` or force min-dwell while I4 is healthy  
- Declare victory on a single fold or pooled A+B / Fold C  

---

## Where judges disagreed

| Topic | Gemini Flash | Claude Sonnet | Working lock |
|---|---|---|---|
| Breadth primary now | Was ACCEPT → now REVISE | REJECT this cycle | **Do not run O2 now** |
| O3 hard gate | Reject after diag | Diagnostic-closed | **No hard gate** |
| D2′ shape | Trend efficiency / path smoothness | **Fixed entry→H=4 rule first**; capture-ratio second | **Fixed-rule D2′ first** |
| I1 timing | After Daily D2′ passes | Parallel baseline OK (no O5); decouple from Daily forever-block | **I1 baseline parallel; O5 later** |
| O5 timing | Hold until Daily clears | Separate labeled track | Hold O5 |
| Build bundling | Isolate | Isolate | Isolate |

---

## Iteration log

| Date | Change | Result | Next |
|---|---|---|---|
| 2026-08-10 | Dual-judge package O1–O8 drafted from A+B eval fails | REVISE; O1 first | Implement O1; re-run D2 A+B |
| 2026-08-11 | **O1 code** — `trend_strength` = ATR-scaled 5d EMA20 slope (pre-open); SUPPORTIVE = `market_trend≥0` + `\|ts\|≥` train-median + breadth; calm **not** required for SUPPORTIVE; flat → AMBIGUOUS. Locked verdict untouched. | Code landed | Re-run D2 A+B |
| 2026-08-11 | **O1 D2 re-eval A+B** (thr A=0.610 / B=0.654) | **D2 FAIL both folds** — still H≳A≳S; CI(S−H) LB &lt; 0. Occupancy: S~30–33% (was ~50%). D5/I7 PASS. I1/I5 still FAIL (expected; not this cycle). | O3 diagnostic (Claude step 2) |
| 2026-08-11 | **O3 diagnostic** — `O3[series]` in eval harness: session OpportunityScore sliced by `market_trend` sign (all sessions; no runtime gate) | **No hard gate.** Long aligned−mis **CI− / inverted** on A+B (trend− days have *higher* long opportunity). Short aligned−mis **CI+ on A only**, ~0 / CI straddles 0 on B. | Dual-judge validation |
| 2026-08-11 | Dual-judge validate O1/O3 metrics + next posture ([Gemini](4bc32ee7-a35e-4d08-b6d7-588416fcc85d), [Claude](74fcc8b3-d65c-4092-ab81-93471cd26bc9)) | **REVISE:** freeze Daily; **D2′ redesign** next (fixed-rule first); **block O2** against current D2; O3 hard gate closed; O5 held | Pre-register D2′; re-run A+B on v1 vs O1 Daily |
| 2026-08-11 | **D2′ implemented + A+B** — fixed-rule score gated as `D2p`; legacy max-window as `D2max` diagnostic; `D2p_v1` compare; I1 baseline under O1 cascade | **D2p FAIL** both folds for O1 and v1 (means ≈ −30 bps; no reliable S≥A≥H). Vol-trap gone (D2max still inverted). **I1 FAIL** both folds. | Freeze Daily/O2; do not search D2′ formulae; next Regime question is **I1** (hold O5 until deliberate) |
| 2026-08-11 | **Revert cascade Daily to locked v1** — O1 `trend_strength` not better than v1 under D2′ and never MERGED; restore calm+trend+breadth SUPPORTIVE; drop O1 feature/threshold plumbing | Code matches [regime-tier1-verdict.md](../regime-tier1-verdict.md); D2′ harness kept | I1 path; do not re-litigate O1 thresholds |
| 2026-08-11 | Dual-judge validate D2′ + cascade policy ([Gemini](b50b8e2e-9eed-4913-99e9-fc2c1c440aa3), [Claude](3e488b5a-5146-418d-a56d-8e1c71fee4b6)) | **Both: move to Intraday; do not keep optimizing Daily.** Continue cascade with Daily frozen as soft overlay; D2′ FAIL is **not** a hard stop. Gemini: elevate I1/I5 as primary gates. Claude: same + optional one-shot multi-window D2′ power addendum; **I5** decides if Daily-as-filter earns keep | Re-baseline I1 under v1; run I5; hold O5 |
| 2026-08-11 | **D2p_mw Fold B** (v1 Daily) — mean of non-overlapping H=4 windows | Index L/S **FAIL**; ew100 long **FAIL**; ew100 short **PASS** (CI LB≈0.0001). Means still ≈ −30 bps. Does **not** clear dual-side Daily gate | **Removed from harness**; proceed to I1 under v1 |
| 2026-08-11 | **I1/I5 re-baseline under locked v1** — Fold A+B; Daily frozen soft overlay; no O5 | **I7 PASS** both. **I1 FAIL** both sides A+B (bar hit ~52–57%; session Edge ≤ 0 vs TOD null). **I5 FAIL** both sides A+B (`p_adm` ~0–1%; CI LB ≤ 0; B short CI entirely ≤ 0). I4 healthy (ASD TREND ~5–7, flip ~2–2.5%) | Dual-judge validate before O5 / architecture |
| 2026-08-11 | Dual-judge validate I1/I5 + Intraday next steps ([Gemini](66d3c4e2-a238-4a18-863a-a1ff17347549), [Claude](a4533e9e-e0f5-4b9c-913e-70237dc944b5)) | **REVISE harness first.** Both: I1 Edge mixes session-equal mean vs bar-weighted null — fix before locking FAIL. Both: I5 absolute `p_adm` is stock-floor-on-index geometry caveat; Δ remains informative (Claude: B-short still red). **Disagree:** Gemini claims bar-level edge already +3–7pp → likely PASS after fix / hold O5; Claude: fix then re-read, **ACCEPT O5 if still FAIL**. Consensus: Daily frozen; no O6/O7; no architecture yet | Fix I1 weighting → re-baseline → O5 only if still FAIL |
| 2026-08-11 | **I1 weighting fix** — Edge = bar HitRate − bar null; session-block boot keeps bar weights (`i1_directional_hit_rate`) | **Corrected re-baseline:** bar Edge ≈ +3–7pp. A long **PASS** / short **FAIL**; B long **FAIL** / short **PASS** — not dual-fold Long+Short. I5 still **FAIL** both sides A+B. I7 PASS | I5 diagnostics then O5 |
| 2026-08-11 | **I5 diagnostics** — `I5r` signed-60m admitted−rejected; `I5tod` morning/midday/afternoon IndexTB Δ (report-only) | **I5r:** A long CI LB>0 tiny (~3bps); A short ~0; B both straddle 0 — not dual-fold CI+. **I5tod:** no bucket clears CI+; B buckets point ≤0 — pooled I5 FAIL **not** a single-TOD artifact. Gated I5 unchanged FAIL | **O5 next**; no IndexTB floor redesign |
| 2026-08-11 | **O5** — lag-1 `r_autocorr` = `r_15_t * r_15_{t−1}` within session; HMM 4th emission; state map still r/rv/vwap | **FAIL.** I1 Edge collapsed (~0–1pp, both sides A+B FAIL) vs corrected triad +3–7pp. I5 not dual-fold (B short PASS only; A FAIL). I7 PASS but emit_r_up≈0.02–0.03; **HIGH_VOL occupancy 0**; TREND_DOWN thinned (n~220–260). | **REVERTED** to triad; next **`adr_15` breadth** |
| 2026-08-11 | **adr_15** — Nifty-100 mean(sign Δclose) at 15m; open-bleed nulled; HMM 4th emission | **Fold A FAIL** (sufficient to reject): I1 L/S FAIL (Edge +0.010 / −0.017); I5 L/S FAIL; I4 degraded (flip≈9.8%, ASD TREND_UP≈1.9). I7 PASS. Fold B not run after A reject. | **REVERTED** to triad; dual-judge next steps |
| 2026-08-11 | Dual-judge validate full Intraday package ([Gemini](cdb81c91-7052-482b-9139-af65c7f3f2be), [Claude](3d59cc05-44b6-435c-9131-51662465c01b)) | **REVISE.** Metrics validated. Corrected I1 2/4 PASSes = **noise**, not signal. Emission search **not** exhausted after two tries. **Both: one isolated HL/CO next.** Then close emissions; architecture only with pre-registered fresh holdout. Skip-B-on-A-quad-fail OK if codified. Reject floors/O6/O7/Daily reopen | **HL/CO only** |
| 2026-08-11 | **HL/CO** — TOD-normalized `(H−L)/\|C−O\|` (`hl_co`; body floor 1e-4); HMM 4th emission; state map still r/rv/vwap | **Fold A FAIL** (sufficient to reject): I7 PASS; I1 L FAIL / S thin (TREND_DOWN n=0); I5 L/S FAIL (short adm=0); I4 TREND_DOWN empty, flip=0. Fold B not run. | **REVERTED** to triad; **emission-add search CLOSED** |
| 2026-08-11 | Dual-judge architecture package ([Gemini](34249fc1-129e-4313-afb6-d68e83133148), [Claude](1eb07b19-7f27-41c8-ba06-cca3d71b580e)) | **Disagree A0 vs A1.** Both: HL/CO validated; emissions CLOSED; A2 REJECT; stop-memo terminal after architecture FAIL. Gemini: **A0 demote now**. Claude: **A1 one frozen try** then stop. Working lock = A1. | **Handoff → [v1.2](regime-tier1-v12-revision.md)** |
| 2026-08-11 | Opened [regime-tier1-v12-revision.md](regime-tier1-v12-revision.md); v1.1 marked HANDOFF | Continuity pointer + A1/H1/H2 spec moved to live working doc | Iterate in v1.2 |

---

## Judge scores (post-HL/CO architecture package — 2026-08-11)

Judges: [Gemini Flash](34249fc1-129e-4313-afb6-d68e83133148), [Claude Sonnet](1eb07b19-7f27-41c8-ba06-cca3d71b580e)

Team proposals reviewed: **A0** demote-now; **A1** deterministic rule taxonomy (primary); **A2** soft-prior HMM; holdout H1=2018–2020→2021 / H2=2019–2021→2022.

| Question | Gemini Flash | Claude Sonnet | Consensus / working lock |
|---|---|---|---|
| HL/CO metrics validated? | Yes | Yes (raw log; short = occupancy collapse not just CI-miss) | **Validated** |
| Emission search closed? | Yes | Yes | **CLOSED** |
| A0 demote Regime now? | **ACCEPT** | **REJECT this round** (prior sequence already locked architecture try) | **Disagree** — working = defer A0 to FAIL path |
| A1 rule taxonomy? | **REJECT** (quantile chase risk) | **ACCEPT** with fully frozen numeric spec | **Working ACCEPT A1** under Claude freeze (addresses Gemini risk) |
| A2 soft-prior HMM? | **REJECT** | **REJECT** outright (not fallback) | **REJECT** |
| Holdout H1/H2 2021/2022? | **REJECT/SKIP** (keep pristine for Horizon) | **REVISE** — years OK; require **both** folds to merge; disclose 2020 S/A % | **Working: run H1+H2**; merge only if both clear; disclose 2020 admission % |
| Stop-memo after FAIL? | ACCEPT (immediate via A0) | ACCEPT (after A1 FAIL) | **ACCEPT** — terminal after architecture path ends |
| Overall | REJECT architecture / REVISE demotion | REVISE → ACCEPT-with-locked-spec | **Working: one A1 try, then terminal** |

### Disagreement note

Gemini would stop now and quarantine 2021–2022 from Regime. Claude requires completing the previously locked architecture step with a non-searchable rule formula. Working lock prefers Claude’s sequence completion: **A0 becomes the outcome if A1 fails**, not a skip of the pre-registered try. Gemini’s threshold-search concern is bound by freezing p80/p50 and forbidding any post-peek quantile change.

### Frozen A1 spec (Claude; working lock — implement exactly)

**Inputs:** triad only (`r_15`, `rv_15`, `vwap_dist`). No new features.

**Fit population:** `cascade_valid_intraday()` train window only (SUPPORTIVE/AMBIGUOUS, non-open-bleed, finite). Recompute thresholds per fold; never carry across folds.

**Train-only thresholds (linear-interpolation quantile):**
- `rv_hi = quantile(rv_15, 0.80)`
- `r_lo = quantile(|r_15|, 0.50)`

**Per-bar classify (top-down, first match):**
```
if rv_15 >= rv_hi: HIGH_VOL
elif r_15 >= r_lo and vwap_dist > 0: TREND_UP
elif r_15 <= -r_lo and vwap_dist < 0: TREND_DOWN
else: CHOP
```

**Unchanged:** `_hysteresis_block` (2-bar TREND_UP↔TREND_DOWN), `override_intraday_regime`, Daily cascade gate, I1/I5 definitions, MIN_BARS=100, N_BOOT=500, 0.30% RT.

**I7:** report-only for A1 (trivially true by construction); do not gate.

**Occupancy pre-check (before I1/I5 bootstrap):** on TEST, each of 4 states ≥3% bar occupancy and ≥100 admitted bars. Collapse → automatic FAIL (do not bootstrap).

**Forbidden without new judge round:** changing 0.80/0.50; dropping `vwap_dist` sign agreement; adding `vwap_dist` magnitude floor; side-specific `r_lo`; 5th label; A2 fallback; merge on H1 alone.

### Locked next sequence (working) — **moved to v1.2**

Frozen A1 spec, holdouts H1/H2, and executable build order are the live working content of **[regime-tier1-v12-revision.md](regime-tier1-v12-revision.md)**. The copy below is retained for continuity only; **do not update it further — edit v1.2**.

1. Implement A1 exactly as frozen above (replace HMM predict path; no HMM).  
2. Run **H1** train 2018–2020 → test **2021**: occupancy → I7 report → I1 → I5 → I4; disclose 2020 S/A admission %.  
3. Run **H2** train 2019–2021 → test **2022** same gates — **mandatory on pass path** (no merge on H1 alone). H1 quad-fail may still skip H2 only for *reject* compute; if H1 clears, H2 required.  
4. Merge only if **both** H1 and H2 clear I1+I5 Long **and** Short with CI LB>0 (real margin, not LB≈0 coin-flip).  
5. Else → **stop-Tier-1-Regime memo** (terminal); escalate Horizon/Precision; no A2 / no more emissions / no third holdout.

### Standing process rule (unchanged)

Fold-A **quad-fail** (I1 long+short and I5 long+short all FAIL) is sufficient to **reject** a candidate without Fold B. Never skip B on a partial/accept path. For A1 holdouts: same reject-early rule; accept path always needs both H1 and H2.

---

### adr_15 Fold A snapshot (before revert)

| Metric | Side | value | CI LB | Gate | note |
|---|---|---:|---:|---|---|
| I7 | — | 1.260 | — | PASS | emit_r_up=1.213 emit_r_down=−0.047 |
| I1 | long | +0.010 | −0.047 | **FAIL** | hit=0.511 null=0.501 n=460 |
| I1 | short | −0.017 | −0.074 | **FAIL** | hit=0.473 null=0.490 n=620 |
| I5 | long | +0.001 | −0.002 | **FAIL** | p_adm=0.002 |
| I5 | short | −0.007 | −0.013 | **FAIL** | CI entirely ≤0 |
| I4 | flip | 0.098 | — | — | ASD UP≈1.9 / DOWN≈3.4 |

**Read:** Breadth emission did not lift path prediction; dwell/flip worsened vs triad. Isolate-and-revert.

### HL/CO Fold A snapshot (before revert)

| Metric | Side | value | CI LB | Gate | note |
|---|---|---:|---:|---|---|
| I7 | — | 0.082 | — | PASS | emit_r_up=0.045 emit_r_down=−0.037 |
| I1 | long | +0.021 | −0.018 | **FAIL** | hit=0.526 null=0.505 n=1959 |
| I1 | short | — | — | **FAIL** | thin; TREND_DOWN n=0 |
| I5 | long | −0.0015 | −0.0046 | **FAIL** | p_adm=0.001 |
| I5 | short | — | — | **FAIL** | adm=0 rej=2970 |
| I4 | flip | 0.000 | — | — | ASD UP≈4.3; DOWN empty; HIGH_VOL ASD≈2.9 |

**Read:** Candle HL/CO starved TREND_DOWN entirely; short sleeve unusable. Isolate-and-revert. **Emission-add search closed.**

### O5 A+B snapshot (before revert)

| Fold | Metric | Side | value | CI LB | Gate | note |
|---|---|---|---:|---:|---|---|
| A 2018 | I7 | — | 0.413 | — | PASS | emit_r_up=0.024 |
| A 2018 | I1 | long | +0.007 | −0.037 | **FAIL** | hit=0.513 null=0.507 |
| A 2018 | I1 | short | +0.008 | −0.064 | **FAIL** | hit=0.506 n=263 |
| A 2018 | I5 | long | −0.002 | −0.006 | **FAIL** | |
| A 2018 | I5 | short | +0.025 | −0.007 | **FAIL** | |
| B 2019 | I7 | — | 0.468 | — | PASS | emit_r_up=0.033 |
| B 2019 | I1 | long | +0.001 | −0.040 | **FAIL** | hit=0.502 |
| B 2019 | I1 | short | +0.052 | −0.041 | **FAIL** | n=218 |
| B 2019 | I5 | long | −0.002 | −0.004 | **FAIL** | |
| B 2019 | I5 | short | +0.091 | +0.027 | **PASS** | thin admit |

**Read:** O5 did not improve path prediction; it scrambled sleeve occupancy (no HIGH_VOL, thin DOWN). Isolate-and-revert — do not bundle with breadth.

### D2p_mw Fold B snapshot (v1 Daily, 2019)

| Series | Side | S | A | H | mono | CI LB | Gate |
|---|---|---:|---:|---:|---|---:|---|
| index | long | −0.0031 | −0.0033 | −0.0026 | no | −0.0011 | FAIL |
| index | short | −0.0029 | −0.0027 | −0.0034 | no | ~0 | FAIL |
| ew100 | long | −0.0034 | −0.0034 | −0.0028 | no | −0.0012 | FAIL |
| ew100 | short | −0.0026 | −0.0026 | −0.0032 | yes | +0.0001 | PASS |

**Read:** Multi-window adds a thin short/ew100 PASS but not a dual-side clear — Claude’s one-shot power check does not reopen Daily optimization.

### I1 / I5 re-baseline under locked v1 (2026-08-11)

#### Pre-fix (superseded — session-equal Edge vs bar null)

| Fold | Metric | Side | value | CI LB | CI UB | n | Gate | note |
|---|---|---|---:|---:|---:|---:|---|---|
| A 2018 | I7 | — | 0.584 | — | — | 4 | **PASS** | emit_r_up=0.305 emit_r_down=−0.280 |
| A 2018 | I1 | long | −0.011 | −0.076 | 0.056 | 749 | **FAIL** | hit=0.570 null=0.502 |
| A 2018 | I1 | short | −0.051 | −0.106 | 0.008 | 889 | **FAIL** | hit=0.524 null=0.491 |
| A 2018 | I5 | long | +0.003 | −0.001 | 0.008 | 749 | **FAIL** | p_adm=0.004 p_rej=0.001 |
| A 2018 | I5 | short | +0.004 | −0.008 | 0.018 | 889 | **FAIL** | p_adm=0.010 p_rej=0.006 |
| B 2019 | I7 | — | 0.597 | — | — | 4 | **PASS** | emit_r_up=0.308 emit_r_down=−0.289 |
| B 2019 | I1 | long | −0.063 | −0.131 | 0.009 | 696 | **FAIL** | hit=0.573 null=0.507 |
| B 2019 | I1 | short | −0.045 | −0.101 | 0.014 | 1032 | **FAIL** | hit=0.553 null=0.491 |
| B 2019 | I5 | long | −0.001 | −0.003 | ~0 | 696 | **FAIL** | p_adm=0.000 p_rej=0.001 |
| B 2019 | I5 | short | −0.014 | −0.029 | −0.002 | 1032 | **FAIL** | p_adm=0.007 p_rej=0.021 |

#### Post I1 weighting fix (honest v1 baseline)

| Fold | Metric | Side | value | CI LB | CI UB | n | Gate | note |
|---|---|---|---:|---:|---:|---:|---|---|
| A 2018 | I7 | — | 0.584 | — | — | 4 | **PASS** | unchanged |
| A 2018 | I1 | long | +0.068 | +0.015 | 0.113 | 749 | **PASS** | hit=0.570 null=0.502 |
| A 2018 | I1 | short | +0.034 | −0.016 | 0.078 | 889 | **FAIL** | hit=0.524 null=0.491 |
| A 2018 | I5 | long | +0.003 | −0.001 | 0.009 | 749 | **FAIL** | p_adm=0.004 p_rej=0.001 |
| A 2018 | I5 | short | +0.004 | −0.009 | 0.019 | 889 | **FAIL** | p_adm=0.010 p_rej=0.006 |
| B 2019 | I7 | — | 0.597 | — | — | 4 | **PASS** | unchanged |
| B 2019 | I1 | long | +0.067 | −0.008 | 0.125 | 696 | **FAIL** | hit=0.573 null=0.507 |
| B 2019 | I1 | short | +0.063 | +0.014 | 0.115 | 1032 | **PASS** | hit=0.553 null=0.491 |
| B 2019 | I5 | long | −0.001 | −0.003 | ~0 | 696 | **FAIL** | p_adm=0.000 p_rej=0.001 |
| B 2019 | I5 | short | −0.014 | −0.027 | −0.002 | 1032 | **FAIL** | p_adm=0.007 p_rej=0.021 |

I4 diagnostic (not gated): A flip=2.6% ASD TREND_UP≈6.7 / TREND_DOWN≈5.4; B flip=2.1% ASD≈6.1 / 5.5.

**Read:** Weighting fix restores the locked Edge definition. Point Edges are positive (~+3–7pp) as Gemini flagged, but **CI(Edge) LB > 0 fails to clear Long and Short on both A and B** (sides flip which fold passes). I5 Δ still FAIL — B short CI entirely ≤ 0. Per judge lock: **O5 unlocked**; do not declare I1 PASS; do not reopen Daily.

### I5 diagnostics (Step 2 — 2026-08-11)

Report-only. Gated `I5` unchanged. Buckets: morning &lt;11:00, midday 11:00–13:30, afternoon ≥13:30 (bar-end).

#### I5r — sleeve-signed R60 (admitted − rejected)

| Fold | Side | Δ | CI LB | CI UB | n_adm | Read |
|---|---|---:|---:|---:|---:|---|
| A 2018 | long | +0.0003 | +0.0001 | +0.0006 | 749 | tiny +; CI+ |
| A 2018 | short | +0.0003 | ~0 | +0.0005 | 889 | tiny +; CI~0 |
| B 2019 | long | +0.0003 | ~0 | +0.0007 | 696 | straddles 0 |
| B 2019 | short | +0.0001 | −0.0002 | +0.0004 | 1032 | straddles 0 |

#### I5tod — IndexTB+1 Δ by TOD (illustrative)

| Fold | Side/bucket | Δ | CI LB | note |
|---|---|---:|---:|---|
| A | long/morning | 0 | 0 | both p≈0 |
| A | long/midday | +0.004 | −0.002 | straddles |
| A | long/afternoon | +0.002 | −0.005 | straddles |
| A | short/morning | +0.024 | ~0 | thin power |
| A | short/midday | −0.001 | −0.019 | straddles |
| A | short/afternoon | −0.009 | −0.020 | ≤0 |
| B | long/* | ≤0 | ≤0 | all buckets |
| B | short/* | ≤0 | ≤0 point or CI | no rescue |

**Read:** Absolute `p_adm`~0 stays a stock-floor-on-index caveat. Continuous `I5r` shows only ~0–3 bps admitted lift and does **not** clear dual-fold CI+. TOD cuts do **not** isolate the FAIL to one clock bucket — especially Fold B. Keep gated I5 Δ; **do not** redesign IndexTB floors this cycle; proceed to **O5**.

---

## Judge scores (post I1/I5 re-baseline — 2026-08-11)

Judges: [Gemini Flash](66d3c4e2-a238-4a18-863a-a1ff17347549), [Claude Sonnet](a4533e9e-e0f5-4b9c-913e-70237dc944b5)

| Question | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| I1/I5 numbers as printed | Validated | Validated | **Validated** |
| Lock “escalate Intraday / O5 now”? | **No** — thermometer broken | **No** — fix I1 first | **Harness fix first** |
| I1 issue | Session-equal Edge vs bar-weighted null; bar hit−null ≈ +3–7pp | Same weighting bug; don’t trust “TOD confound” narrative yet | **Fix same-weight Edge; re-run** |
| I5 absolute `p_adm`~0 | Stock floors on index → starved | Agree — geometry caveat | **Diagnostic only** |
| I5 Δ / CI FAIL | Dismiss as noise from sparsity; prefer continuous signed R60 or re-floored IndexTB | Δ still valid (floor cancels); B-short CI entirely ≤0 is real cascade read; add TOD-stratified diagnostic | **Keep Δ gate; add diagnostics; pre-register any floor change** |
| Daily freeze | Keep | Keep | **Frozen** |
| O5 next? | **REJECT this cycle** until corrected baseline | **ACCEPT** if corrected I1/I5 still FAIL | **O5 only after re-baseline FAIL** |
| O6 / O7 / Daily reopen | REJECT | REJECT | **REJECT** |
| Architecture rethink | REJECT this cycle | REVISE — only after O5 + one emission + pre-registered holdout | **Not yet** |

### Candidate ledger update (Intraday)

| ID | Change | Gemini | Claude | Working lock |
|---|---|---|---|---|
| I1 fix | Same-weight Edge (bar HitRate − bar null; session bootstrap for CI) | ACCEPT (mandatory) | ACCEPT (mandatory) | **DONE** |
| I5 diag | TOD-stratified cut; signed-60m admitted−rejected (already in eval verdict) | ACCEPT (or re-floor) | ACCEPT TOD + signed; floor change only if pre-registered | **DONE** — no floor redesign |
| **O5** | lag-1 `r_autocorr` emission | REJECT until harness clean | ACCEPT if still FAIL after fix | **REVERTED** (FAIL) |
| Breadth `adr_15` | Ideal HMM emission | REJECT this cycle | ACCEPT as fallback #2 after O5 | **REVERTED** (Fold A FAIL) |
| HL/CO candle | Ideal | **ACCEPT** (final isolated) | **ACCEPT** one shot | **REVERTED**; emissions **CLOSED** |
| Architecture rethink | — | ACCEPT after HL/CO | REVISE — after HL/CO + pre-registered holdout | **HANDOFF → [v1.2](regime-tier1-v12-revision.md)** |
| **A0** demote now | Soft overlay + stop memo | **ACCEPT** | **REJECT this round** | **FAIL path** (see v1.2) |
| **A1** rule taxonomy | Non-hidden triad rules | **REJECT** | **ACCEPT** frozen p80/p50 | **ACTIVE in [v1.2](regime-tier1-v12-revision.md)** |
| **A2** soft-prior HMM | Anchored HMM | **REJECT** | **REJECT** outright | **REJECT** |
| Architecture holdout | H1=2021 / H2=2022 | SKIP (quarantine) | REVISE (both required to merge) | **See v1.2** |
| IndexTB floors | — | REJECT | REJECT | **REJECT** |
| O6 / O7 | rv_delta / force dwell | REJECT | REJECT | **REJECT** |
| Daily reopen | — | REJECT | REJECT | **REJECT** |

### Cascade / Intraday policy lock (both judges)

1. Daily stays **locked v1**, frozen.  
2. I1 Edge now matches locked HitRate definition (post-fix).  
3. Do **not** treat I5 absolute `p_adm` alone as Regime failure; gate on Δ (+ signed-return companion).  
4. Corrected A+B still fails dual-fold I1 Long+Short and I5 → **O5 unlocked**.  
5. No Daily retune against I1/I5 (O8).

---

## Judge scores (post-D2′ / cascade policy — 2026-08-11)

Judges: [Gemini Flash](b50b8e2e-9eed-4913-99e9-fc2c1c440aa3), [Claude Sonnet](3e488b5a-5146-418d-a56d-8e1c71fee4b6)

| Question | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| D2′ / O1-revert reads | Validated | Validated | **Validated** |
| Keep optimizing Daily? | **No** — exhausted | **No** feature knobs (half-agree “exhausted”) | **Freeze Daily** |
| Move to Intraday? | **Yes** — I1/I5 primary | **Yes** — I1 primary; I5 is cascade-value test | **Yes — Intraday** |
| Continue cascade if D2′ fails? | **Yes** — Daily demoted to soft macro filter | **Yes** — Daily frozen veto/admission; failing D2′ ≠ hard stop | **Yes — continue** |
| Hard stop signal | I1 **and** I5 fail under v1 overlay | **I5** fails (admitted≈rejected) | Prefer **I5** as Daily-as-filter verdict; I1+I5 both red → escalate Regime |
| Extra Daily metric work | None | Optional **one** pre-registered multi-window (non-max) D2′ | Optional / non-blocking; do not delay I1 |

### Cascade policy lock (both judges)

1. Daily stays **locked v1**, frozen — soft risk / admission overlay (`NO_TRADE`/`HOSTILE` veto; `S`/`A` open).  
2. D2′ FAIL does **not** block Intraday work or the rest of the cascade.  
3. Do **not** treat D2′ FAIL as “Daily validated.” Frozen-and-failing ≠ cleared.  
4. Ship gates for this phase: **I1** and especially **I5** under v1 Daily + current HMM (Long≠Short, A+B).  
5. No Daily retune against I1/I5 (O8).

---

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

### D2′ fixed-rule snapshot (gated `D2p` / compare `D2p_v1`)

Index long/short means and S−H gate (ew100 same qualitative FAIL):

| Fold | Daily | Side | S | A | H | mono | CI LB | Gate |
|---|---|---|---:|---:|---:|---|---:|---|
| A 2018 | O1 | long | −0.0032 | −0.0029 | −0.0028 | no | −0.0011 | FAIL |
| A 2018 | O1 | short | −0.0028 | −0.0031 | −0.0032 | yes | −0.0005 | FAIL |
| A 2018 | v1 | long | −0.0031 | −0.0029 | −0.0028 | no | −0.0010 | FAIL |
| A 2018 | v1 | short | −0.0029 | −0.0031 | −0.0032 | yes | −0.0005 | FAIL |
| B 2019 | O1 | long | −0.0035 | −0.0028 | −0.0031 | no | −0.0012 | FAIL |
| B 2019 | O1 | short | −0.0025 | −0.0032 | −0.0029 | no | −0.0004 | FAIL |
| B 2019 | v1 | long | −0.0032 | −0.0028 | −0.0031 | no | −0.0009 | FAIL |
| B 2019 | v1 | short | −0.0028 | −0.0032 | −0.0029 | no | −0.0007 | FAIL |

**I1 baseline (O1 cascade, superseded):** A long Edge −0.009 / short −0.051 FAIL; B long −0.061 / short −0.045 FAIL. I7 PASS both. **Superseded by locked-v1 I1/I5 re-baseline above** (same qualitative FAIL).

**Read:** D2′ removes max-window vol inflation (regime means collapse near −RT cost). Neither O1 nor locked v1 orders days under the pre-registered fixed rule. Daily feature work is exhausted for this metric; do **not** open Gemini capture-ratio as a search — only as a separately pre-registered experiment later if needed.

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
| Metric | Now uses D2′ fixed-rule scores by side × trend sign; bootstrap CI on aligned − misaligned |
| Hard gate | **Not wired** — dual-fold CI+ for Long **and** Short not met |

---

## D2′ implementation notes (working)

| Item | Choice |
|---|---|
| Code | `_day_fixed_rule_score` → `d2_prime_fixed_rule_separation` (`D2p`); legacy `_day_opportunity_max` → `D2max` diagnostic |
| Compare | One-shot `D2p_v1` completed then removed from harness |
| Cascade default | Locked v1 `classify_daily_regime` (O1 reverted) |
| Gate | S≥A≥H + CI(S−H) LB>0 — **not cleared** on A+B |

---

## Related docs

| Doc | Role |
|---|---|
| [regime-tier1-verdict.md](../regime-tier1-verdict.md) | Locked v1 — merge target only when locked |
| [regime-tier1-eval-verdict.md](../regime-tier1-eval-verdict.md) | Eval harness / gates |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Cascade contracts |
| [cascade-tier3-ws01-verdict.md](../cascade-tier3-ws01-verdict.md) | Why Regime was escalated |
