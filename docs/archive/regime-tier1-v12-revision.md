# Tier 1 Regime — v1.2 Revision (Intraday architecture)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** **Intraday Regime architecture redesign** — frozen A1 rule taxonomy vs triad HMM; one-shot holdouts H1/H2  
**Status:** **CLOSED — A0 terminal** ([stop memo](regime-tier1-stop-memo.md)); A0 demotion merged into [regime-tier1-verdict.md](../regime-tier1-verdict.md)  
**Judges:** Gemini Flash, Claude Sonnet  
**Date:** 2026-08-11  
**Continues from:** [regime-tier1-v11-revision.md](regime-tier1-v11-revision.md) (Daily / D2′ / emission cycle — handoff)  
**Depends on:** [regime-tier1-verdict.md](../regime-tier1-verdict.md), [regime-tier1-eval-verdict.md](../regime-tier1-eval-verdict.md)  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Terminal:** [regime-tier1-stop-memo.md](regime-tier1-stop-memo.md)

---

> **Prior cycle (v1.1):** Daily / D2′ / I1 harness / I5 diagnostics / emission tries (O5, `adr_15`, HL/CO) and the dual-judge architecture lock live in **[regime-tier1-v11-revision.md](regime-tier1-v11-revision.md)** (status: HANDOFF). Do not reopen those cycles here — this doc owns only the A1 architecture try and its H1/H2 outcome (or stop-memo).

---

## How to use this doc

1. Keep [regime-tier1-verdict.md](../regime-tier1-verdict.md) as the shipped contract (now includes **A0 demotion**).  
2. This file is the archive of the A1 try + H1 FAIL.  
3. Historical Daily / emission / harness work stays in [regime-tier1-v11-revision.md](regime-tier1-v11-revision.md).  
4. **CLOSED** via [stop memo](regime-tier1-stop-memo.md) — do not reopen A1 / A2 / emissions here.

---

## Inherited locks (from v1.1 — do not re-litigate)

| Lock | Status |
|---|---|
| Daily | Frozen locked v1 soft overlay (`NO_TRADE`/`HOSTILE` veto; `S`/`A` open) |
| D2′ | Kept as diagnostic; **FAIL A+B**; no formula search |
| I1 Edge | Bar HitRate − bar TOD null; session-block bootstrap |
| I5 | Δ gate; I5r/I5tod report-only; no IndexTB floor redesign |
| Emission-add search | **CLOSED** (O5, `adr_15`, HL/CO all FAIL+REVERTED) |
| O2 / O3 hard gate / O6 / O7 / Daily reopen | **REJECT** |
| A2 soft-prior HMM | **REJECT** (not a fallback after A1) |
| Corrected I1 2/4 PASSes | **Noise**, not signal |
| Standing reject-early | Fold/holdout **quad-fail** (I1 L+S + I5 L+S) may skip sibling fold for *reject only*; never skip on accept/merge path |

Full narrative + judge transcripts: [v1.1 revision](regime-tier1-v11-revision.md) (post-HL/CO architecture package).

---

## Summary

| Decision | Locked outcome |
|---|---|
| Overall posture | **CLOSED — A0** ([stop memo](regime-tier1-stop-memo.md)) |
| Architecture candidate | **A1 REJECTED** after H1 quad-fail |
| Ship / merge | **A0 demotion** into locked verdict; triad HMM restored as soft overlay |
| Sequence next | **Escalate Horizon / Precision** — no further Regime architecture search |
| Reject this cycle | Quantile search, A2, more emissions, Daily reopen, merge-on-H1-alone, new metrics for architecture |

**One-line:** v1.2 ran the single pre-registered A1 shot on 2021; **FAIL → A0** (demote Regime, restore triad HMM soft overlay, escalate Horizon/Precision).

---

## Dual-judge handoff (2026-08-11)

Judges: [Gemini Flash](34249fc1-129e-4313-afb6-d68e83133148), [Claude Sonnet](1eb07b19-7f27-41c8-ba06-cca3d71b580e)

| Question | Gemini | Claude | Working lock |
|---|---|---|---|
| A0 demote now | **ACCEPT** | **REJECT this round** | Defer to A1 **FAIL** path → **now taken** |
| A1 rule taxonomy | **REJECT** (quantile chase) | **ACCEPT** frozen p80/p50 | Ran under frozen spec; **FAIL** |
| A2 soft-prior HMM | **REJECT** | **REJECT** | **REJECT** |
| Holdout 2021/2022 | Skip / quarantine | Run; both required to merge | H1 run; H2 skipped on reject-early |

**Disagreement resolved by evidence:** Claude’s one frozen A1 try completed and failed; Gemini’s A0 demotion is the locked outcome.

---

## Frozen A1 spec (implement exactly — archive; do not re-open)

**Inputs:** triad only — `r_15`, `rv_15`, `vwap_dist` from `src/features/intraday_regime.py`. No new features.

**Fit population:** `cascade_valid_intraday()` on the **train** window only (`SUPPORTIVE`/`AMBIGUOUS`, non-open-bleed, finite). Recompute thresholds per fold; never carry across folds.

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

**Unchanged from current cascade:**
- `_hysteresis_block` (2 consecutive bars to flip TREND_UP ↔ TREND_DOWN)
- `override_intraday_regime` (open-auction bleed null)
- Daily cascade admission gate
- I1 / I5 definitions, MIN_BARS=100, N_BOOT=500, 0.30% RT

**I7:** report-only for A1 (trivially true by construction); do not gate.

**Occupancy pre-check (before I1/I5 bootstrap):** on TEST, each of 4 states ≥3% bar occupancy and ≥100 admitted bars. Collapse → automatic FAIL (do not bootstrap).

**Disclose with H1:** % of 2020 calendar days in train admitted as SUPPORTIVE/AMBIGUOUS (disclosure line, not a gate).

**Forbidden without a new judge round:** changing 0.80/0.50; dropping `vwap_dist` sign agreement; adding `vwap_dist` magnitude floor; side-specific `r_lo`; 5th label; A2 fallback; merge on H1 alone.

---

## Holdouts (pre-registered)

| Fold | Train → Test | Notes |
|---|---|---|
| **H1** | 2018–2020 → **2021** | **FAIL** (quad) — see stop memo |
| **H2** | 2019–2021 → **2022** | **Skipped** (reject-early) |

**Harness:** `python -m src.experiments.eval_regime --train-period … --test-period …`  
(A1 code removed after A0; H1 log retained at `logs/eval_a1_h1.txt`.)

**Gates:** occupancy pre-check → I7 (report) → I1 → I5 (Long ≠ Short) → I4 diagnostic.

**Merge:** only if **both** H1 and H2 clear I1+I5 Long **and** Short with CI LB > 0 — **not met**.

**Reject-early:** H1 quad-fail may skip H2 for reject compute only — **applied**.

---

## Build order (working) — COMPLETE

1. Implement A1 classifier — **DONE**  
2. Run **H1** (2018–2020 → 2021) — **DONE; FAIL**  
3. Run **H2** — **SKIPPED** (reject-early)  
4. If both clear → merge — **N/A**  
5. Else → **stop-Tier-1-Regime memo** + restore triad HMM soft overlay (A0) — **DONE** → [stop memo](regime-tier1-stop-memo.md)

---

## Candidate ledger

| ID | Change | Gemini | Claude | Working lock | Merge status |
|---|---|---|---|---|---|
| **A1** | Deterministic triad rule taxonomy (p80 `rv` / p50 `\|r\|` + vwap sign) | REJECT | ACCEPT frozen | Ran; H1 FAIL | **REJECTED** |
| **A0** | Demote Regime soft overlay + stop memo | ACCEPT now | ACCEPT after A1 FAIL | **← LOCKED** | **MERGED** |
| A2 | Soft-prior / anchored HMM | REJECT | REJECT | **REJECT** | REJECTED |

---

## Explicit do-not (this revision cycle)

- Reopen A1 / A2 / emissions after this CLOSE  
- Change frozen quantiles after peek  
- Merge on a single holdout  
- Invent new ship gates to make A1 look better than HMM  
- Treat I7 PASS as evidence of a healthy A1 state map  

---

## Iteration log

| Date | Change | Result | Next |
|---|---|---|---|
| 2026-08-11 | Opened v1.2 from v1.1 handoff; A1 + H1/H2 pre-registered | Spec frozen in this doc | Implement A1 |
| 2026-08-11 | Implemented A1 (`IntradayRuleRegimeModel`): train-only p80/p50, triad rules, hysteresis reuse; eval CLI `--intraday A1` + OCC pre-check + I7 report-only + 2020 S/A disclosure | Code ready | Run H1 (2018–2020 → 2021) |
| 2026-08-11 | **H1** A1 2018–2020→2021 (`logs/eval_a1_h1.txt`): OCC PASS; 2020 S/A=73.0%; **I1 L/S FAIL**; **I5 L/S FAIL** | **H1 FAIL** (quad) | Skip H2; write stop memo (A0) |
| 2026-08-11 | **A0** stop memo + demotion merged into locked verdict | **CLOSED** | Escalate Horizon / Precision |
| 2026-08-11 | Removed A1 code (`IntradayRuleRegimeModel`, CLI flag, OCC/I7 A1 hooks); triad HMM only | Cleanup | — |
