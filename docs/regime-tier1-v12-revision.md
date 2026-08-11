# Tier 1 Regime — v1.2 Revision (Intraday architecture)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** **Intraday Regime architecture redesign** — frozen A1 rule taxonomy vs triad HMM; one-shot holdouts H1/H2  
**Status:** **OPEN — iterate here; merge into [regime-tier1-verdict.md](regime-tier1-verdict.md) only when locked**  
**Judges:** Gemini Flash, Claude Sonnet  
**Date:** 2026-08-11  
**Continues from:** [regime-tier1-v11-revision.md](regime-tier1-v11-revision.md) (Daily / D2′ / emission cycle — handoff)  
**Depends on:** [regime-tier1-verdict.md](regime-tier1-verdict.md) (locked v1 — do not edit until MERGED), [regime-tier1-eval-verdict.md](regime-tier1-eval-verdict.md)  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  

---

> **Prior cycle (v1.1):** Daily / D2′ / I1 harness / I5 diagnostics / emission tries (O5, `adr_15`, HL/CO) and the dual-judge architecture lock live in **[regime-tier1-v11-revision.md](regime-tier1-v11-revision.md)** (status: HANDOFF). Do not reopen those cycles here — this doc owns only the A1 architecture try and its H1/H2 outcome (or stop-memo).

---

## How to use this doc

1. Keep [regime-tier1-verdict.md](regime-tier1-verdict.md) frozen as the shipped v1 contract.  
2. Land A1 implementation notes, H1/H2 results, and judge notes **here**.  
3. Historical Daily / emission / harness work stays in [regime-tier1-v11-revision.md](regime-tier1-v11-revision.md) — do not reopen those cycles here.  
4. When A1 clears H1+H2 (or the stop memo is written), merge that slice into the locked verdict and mark **MERGED** / **CLOSED** below.

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

| Decision | Working choice (not merged) |
|---|---|
| Overall posture | **REVISE — one frozen A1 try**, then terminal stop-memo if FAIL |
| Architecture candidate | **A1** deterministic rule taxonomy (non-hidden); replaces GaussianHMM decode |
| Ship / merge | **Nothing** until A1 clears **both** H1 and H2 (I1+I5 Long+Short, CI LB>0) |
| Sequence next | Implement A1 → H1 (2021) → H2 (2022) → merge or **stop-Tier-1-Regime memo** |
| Reject this cycle | Quantile search, A2, more emissions, Daily reopen, merge-on-H1-alone, new metrics for architecture |

**One-line:** v1.2 = single pre-registered Intraday architecture shot (A1 rules on triad) on never-touched test years 2021/2022; FAIL → demote Regime (A0 path) and escalate Horizon/Precision.

---

## Dual-judge handoff (2026-08-11)

Judges: [Gemini Flash](34249fc1-129e-4313-afb6-d68e83133148), [Claude Sonnet](1eb07b19-7f27-41c8-ba06-cca3d71b580e)

| Question | Gemini | Claude | Working lock |
|---|---|---|---|
| A0 demote now | **ACCEPT** | **REJECT this round** | Defer to A1 **FAIL** path |
| A1 rule taxonomy | **REJECT** (quantile chase) | **ACCEPT** frozen p80/p50 | **ACCEPT A1** under frozen spec |
| A2 soft-prior HMM | **REJECT** | **REJECT** | **REJECT** |
| Holdout 2021/2022 | Skip / quarantine | Run; both required to merge | **H1+H2**; both to merge |

**Disagreement:** Gemini would stop and quarantine 2021–2022 for Horizon. Working lock completes the prior architecture step with a non-searchable formula; A0 is the outcome if A1 fails.

---

## Frozen A1 spec (implement exactly — no further judge round)

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
| **H1** | 2018–2020 → **2021** | Test year never used as Regime I1/I5 test (A=2018, B=2019, C=2020 quarantine) |
| **H2** | 2019–2021 → **2022** | Same; mandatory on accept/merge path |

**Harness:** `python -m src.experiments.eval_regime --train-period … --test-period …`  
(Wire A1 behind the same CLI; banner should note `intraday=A1`.)

**Gates:** occupancy pre-check → I7 (report) → I1 → I5 (Long ≠ Short) → I4 diagnostic.

**Merge:** only if **both** H1 and H2 clear I1+I5 Long **and** Short with CI LB > 0 (real margin, not LB≈0).

**Reject-early:** H1 quad-fail may skip H2 for reject compute only. If H1 clears any accept path, H2 is required.

---

## Build order (working)

1. Implement A1 classifier (replace HMM fit/predict path for this try; triad features unchanged).  
2. Run **H1** (2018–2020 → 2021); log occupancy, I1, I5, I4 + 2020 S/A %.  
3. Run **H2** (2019–2021 → 2022) — required if not reject-early.  
4. If both clear → dual-judge validate → merge path into locked verdict.  
5. Else → write **stop-Tier-1-Regime memo** (terminal); escalate Horizon/Precision; restore triad HMM as frozen soft overlay (A0 outcome).

---

## Candidate ledger

| ID | Change | Gemini | Claude | Working lock | Merge status |
|---|---|---|---|---|---|
| **A1** | Deterministic triad rule taxonomy (p80 `rv` / p50 `\|r\|` + vwap sign) | REJECT | ACCEPT frozen | **← ACTIVE** | OPEN |
| A0 | Demote Regime soft overlay + stop memo | ACCEPT now | ACCEPT after A1 FAIL | **FAIL path** | PENDING |
| A2 | Soft-prior / anchored HMM | REJECT | REJECT | **REJECT** | REJECTED |

---

## Explicit do-not (this revision cycle)

- Edit [regime-tier1-verdict.md](regime-tier1-verdict.md) until MERGED  
- Reopen Daily features, D2′ formula search, emission-add search, O6/O7, IndexTB floors  
- Run A2 or any second architecture candidate after A1  
- Change frozen quantiles after seeing H1/H2  
- Merge on a single holdout  
- Invent new ship gates to make A1 look better than HMM  
- Treat I7 PASS as evidence of a healthy A1 state map  

---

## Iteration log

| Date | Change | Result | Next |
|---|---|---|---|
| 2026-08-11 | Opened v1.2 from v1.1 handoff; A1 + H1/H2 pre-registered | Spec frozen in this doc | Implement A1 |

---

## Acceptance before merge

- Occupancy pre-check PASS on H1 and H2  
- I1 and I5: CI LB > 0 per side on **both** H1 and H2; Long ≠ Short  
- No quantile / threshold change after peek  
- Dual-judge validate before editing locked [regime-tier1-verdict.md](regime-tier1-verdict.md)  
