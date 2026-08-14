# Tier 2 Horizon — Long Stop Memo (v1.1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Sleeve:** **Long** Horizon ranker only (Short stopped separately)  
**Status:** **TERMINAL this cycle — Long soft-H3 / cascade-ready search CLOSED**  
**Date:** 2026-08-11  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Depends on:** [horizon-tier2-v11-revision.md](horizon-tier2-v11-revision.md), [horizon-tier2-verdict.md](../horizon-tier2-verdict.md) (v1 freeze), [horizon-tier2-eval-verdict.md](../horizon-tier2-eval-verdict.md), [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md)  
**Trigger:** L1 A+B FAIL dual-fold soft-H3; L2 report-first does not support gated emission threshold  
**Harness:** `python -m src.experiments.eval_horizon`  
**A+B peeks spent this cycle (Fold A+B pair):** **7** — baseline, D1, D2, S1, L1, S2 report-first, L2 report-first. Carry into any new charter as the multiplicity baseline; do not silently re-peek these folds for L1/L2 retunes.

---

## One-line

Long clears confirmatory gates as a **Horizon ranker only** with **soft H3 unresolved** (`m12` &lt; `m3k` both folds) and Top-K TB+1 ~7–9% — **not cascade-ready**; L1/L2 do not close soft mono this cycle; keep frozen v1; do not say bare “Long ship.”

---

## What failed (terminal evidence)

| Item | Result |
|---|---|
| Baseline Long A+B | H1/H2/H3/H5 **PASS** both folds — H3 **soft** (`m12` &lt; `m3k`) both folds |
| Soft H3 (baseline) | A: m12=0.0004 &lt; m3k=0.0006; B: 0.0006 &lt; 0.0009 |
| Absolute Top-K TB+1 | ~7–9% — provisional 15% unmet; H4 always &lt; 0 under 30 bps |
| **L1** (rank-3 floor on ranks 1–2) | A+B **FAIL** soft close — A still soft; B closes (`m12=m3k`) — `logs/horizon_l1_fold_*.txt` |
| L1 side effects | H2/H5 gates still PASS (no “fix mono by killing signal”) |
| **L2** (1×c mean Top-K floor, report-first) | Keep ~3% of bars; A keep H5 **worse** than drop; B keep thin — `logs/horizon_s2l2_fold_*.txt` |
| Cascade / WS1 echo | Rank 1–2 toxicity + low TB+1 — Precision cannot clear 30 bps on this book |

---

## Locked outcomes (Long)

| Lock | Decision |
|---|---|
| Horizon-ranker language | **PASS** confirmatory gates — always qualify; **not cascade-ready** |
| Soft H3 this cycle | **Unresolved** — two soft folds keep H3 gated; do not demote to diagnostic |
| L1 transform | **OFF** (`APPLY_L1_LONG=False`) — measured, not merged |
| L2 gated A+B | **Do not charter** this cycle |
| v1 features / hyperparams | Stay frozen — D0 honored |
| Gated K | **Stay Long K=5** (D2: K=8 dilutes H5) |
| Cascade / Precision claim | **Forbidden** from Horizon gates alone (anti-pattern #11) |
| Merge into locked verdict | **Nothing** from v1.1 Long levers |

---

## Escalate / leave open

1. **Short** — see [horizon-tier2-short-stop-memo.md](horizon-tier2-short-stop-memo.md) (H5 ship fail; ranking skill retained).  
2. **Precision** — do not open WS2 to “fix” upstream soft mono / low TB+1.  
3. Further Long mono / path-density work only under a **new dual-judge charter** (not silent L1/L2 reopen).

---

## Explicit do-not (post-stop)

- Claim “Long ship” without **Horizon-ranker** qualifier and soft-H3 caveat  
- Retune L1 (e.g. softer blend) on the same A+B folds used for selection  
- Promote L2 1×c floor to a gated lever from the report-first peek  
- Hyperparam / feature grid on A+B to chase soft H3 or TB+1 15%  
- Treat trainer purged-WF IC as acceptance  
- Re-run L1/L2 peeks on Folds A/B without a new charter + peek budget  
- Edit this memo into REVISE — it is **terminal for Long soft-H3 / cascade-ready claims this cycle**

---

## Code posture

L1 / L2 diagnostics remain in `src/horizon/eval/` for reporting. Production Long path stays frozen v1 (no L1 floor). Evidence logs: `logs/horizon_l1_fold_*.txt`, `logs/horizon_s2l2_fold_*.txt`, baseline / D2 Long rows in the v1.1 revision.
