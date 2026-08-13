# Tier 2 Horizon — Short Stop Memo (v1.1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Sleeve:** **Short** Horizon ranker only (Long stopped separately)  
**Status:** **TERMINAL this cycle — Short ship / path-bridge search CLOSED**  
**Date:** 2026-08-11  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Depends on:** [horizon-tier2-v11-revision.md](horizon-tier2-v11-revision.md), [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) (v1 freeze), [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md), [cascade-tier3-ws01-verdict.md](../cascade-tier3-ws01-verdict.md)  
**Trigger:** S1 A+B FAIL dual-fold H5 (+ H10 regress on B); S2 report-first does not support gated activation  
**Harness:** `python -m src.experiments.eval_horizon`  
**A+B peeks spent this cycle (Fold A+B pair):** **7** — baseline, D1, D2, S1, L1, S2 report-first, L2 report-first. Carry into any new charter as the multiplicity baseline; do not silently re-peek these folds for S1/L1 retunes.

---

## One-line

Short keeps **ranking skill** (H1/H2) but **fails the StockTB+1 path bridge** on Fold A; pre-registered hygiene (S1) and TOD report-first (S2) do not clear dual-fold H5 — **stop Short ship / B1 activate this cycle**; do not delete the sleeve.

---

## What failed (terminal evidence)

| Item | Result |
|---|---|
| Baseline Fold A H5 | 0.020 [**−0.001**, 0.043] **FAIL** — `logs/horizon_d1_fold_a.txt` / baseline table in v1.1 |
| Baseline Fold B H5 | 0.039 [0.019, 0.060] PASS |
| Ranking skill | H1/H2 **PASS** both folds (path translation fail, not null IC) |
| **S1** (circuit/UC exclude) | A+B **FAIL** — A H5 CI LB still ≤0; B **H10 regress** → gated Short unscorable — `logs/horizon_s1_fold_*.txt` |
| **S2** (TOD report-first) | PM H5 ≥ AM both folds — afternoon cut would **hurt** H5 — `logs/horizon_s2l2_fold_*.txt` |
| **S3 / X1** | **DEFER** — not opened after S1 exhaust |
| **B1** (Precision Short K=3) | Spec locked only — **do not activate** against unshipped Short H5 |
| Absolute Top-K TB+1 | ~11% both folds — provisional 15% floor unmet (report-only) |

D1 showed circuit contamination ~1% and clean-slice H5 ≈ pooled H5 — Fold A fail is **not** a flat-bar density story.

---

## Locked outcomes (Short)

| Lock | Decision |
|---|---|
| Short ship this cycle | **NO** — dual-fold H5 not cleared |
| S1 mask | **OFF** (`APPLY_S1_SHORT=False`) — measured, not merged |
| S2 hard cut | **REJECT** promotion to gated A+B |
| F&O-active hard filter | **Blocked** until a real membership list exists (no invented coverage) |
| Gated K | **Stay Short K=3** — D2 sweep must not retune K from Fold A peek (O8) |
| B1 live | **Do not activate** until a new charter clears Short dual-fold H5 |
| Sleeve deletion | **Do not** delete Short — ranking skill remains real |
| v1 features / hyperparams | Stay frozen in [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) |

---

## Escalate / leave open

1. **Long** — see [horizon-tier2-long-stop-memo.md](horizon-tier2-long-stop-memo.md) (decoupled; Horizon-ranker PASS with soft H3 unresolved).  
2. **Precision** — do not open WS2 to monetize an unshipped Short Top-K path density.  
3. New Short work only under an **explicit new dual-judge charter** (fresh folds / levers), not a silent reopen of S1–S3.

---

## Explicit do-not (post-stop)

- Retune S1 `CIRCUIT_RANGE_EPS` / forward window to chase Fold A H5  
- Promote S2 afternoon cut or S3 episode weights without a new charter  
- Change gated Short K from the D2 diagnostic sweep  
- Activate B1 / claim cascade Short readiness from Horizon H1/H2 alone  
- Pool Long+Short into one “Horizon PASS”  
- Re-run S1/S2 peeks on Folds A/B without a new charter + peek budget  
- Edit this memo into REVISE — it is **terminal for Short ship this cycle**

---

## Code posture

S1 / S2 diagnostics remain in `src/horizon/eval/` for reporting. Production Short mask stays baseline v1 (no S1). Evidence logs: `logs/horizon_s1_fold_*.txt`, `logs/horizon_s2l2_fold_*.txt`, D1/D2 Short slices in the v1.1 revision.
