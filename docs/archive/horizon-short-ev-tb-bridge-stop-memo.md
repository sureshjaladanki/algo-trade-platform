# Horizon Short EV–TB Bridge — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Diagnose Short path-EV vs StockTB=+1 discordance; gated peeks on TB-aware ranking loss / parsimony / score-quantile eligibility under locked `c*=20` / `H=6` / floors  
**Status:** **STOP-MEMO — EV–TB bridge charter CLOSED**; peeks **0 / 2** · **hard-stop @ 0** — **no merge**  
**Date:** 2026-08-14  
**Charter:** [horizon-short-ev-tb-bridge-charter.md](horizon-short-ev-tb-bridge-charter.md)  
**Depends on:** [horizon-short-travel-separation-stop-memo.md](horizon-short-travel-separation-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md)  
**Trigger:** Phase 1 dual-fold val gate authorizes none of O1 / P1 / E1  
**A+B peeks spent:** **0 / 2** — both closed (not paused; reopen needs a fresh dual-judge architecture charter)

---

## One-line

Last-fold train/val already ranks some TB/travel under path-EV, while a same-family lambdarank toward StockTB **loses** val TB Spearman to that path-EV model — **stop at 0/2**; do not peek O1/P1/E1; Precision / B1 stay blocked; next = architecture.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| Holdout Short H5 FAIL / H2 PASS @ `c*=20` is still the residual | **Supported** — cost peek-1 reprint (H5 FAIL/FAIL; H2 PASS/PASS) |
| Min-N + TB=+1 counts clear before any lever | **Supported** — holdout bars 788/921, sess 125/133; train TB=+1 5556/5568 |
| Score ranks path-EV but **not** TB=+1 / TP-share on **val** (O1 license) | **Disproven dual-fold** — val IC_ev 0.19/0.29; val IC_tb 0.06/0.16; Fold B TB Spearman is not weak vs EV; val Top−Rest TP-share +3pp both |
| Last-fold lambdarank toward TB exit order improves val TB-rank vs path-EV | **Disproven** — full TB-ranker val IC_tb **−0.025 / +0.016** vs path-EV **+0.064 / +0.157** |
| Pre-registered P1 top-N (smallest N that lifts TB-rank without H2-proxy collapse) dual-fold | **Disproven** — Fold A N=12/16 CLEAR; Fold B none (H2-proxy collapse); no common N |
| Top ≈ Rest travel + exit mix → E1 keep-rate | **Disproven** — val MFE spread +0.11 / +0.16 (Top travels); not a keep-rate pattern |
| Hybrid λ / F1 novel feature / C1 remount | **Not tested** — rejected / struck / forbidden |
| Precision / B1 may bridge Short H5 | **Forbidden** — still blocked |

**Residual lock after this charter:** holdout Short H5 FAIL under locked geometry is a **generalization / architecture** gap, not a train/val objective-swap that Phase 1 licensed. Single path-EV LightGBM under current Short feature physics remains insufficient for Short H5 — same capability sentence as the charter FAIL path, reached at 0 peeks.

---

## Terminal evidence

### Phase 1 (0 peeks)

**Log:** `logs/horizon_ev_tb_bridge_phase1_ab.txt`  
**Harness:** `python -m src.experiments.analyze_horizon_ev_tb_bridge --folds A,B`

Holdout H5 / SEP / ADVt = **frozen reprint** (cost peek-1 + short-travel STOP). Authorization used last-fold **train/val only**.

| Diagnostic | Fold A | Fold B | Cut / read |
|---|---|---|---|
| Holdout min-N (reprint) | 788 bars / 125 sess | 921 / 133 | ≥150 / ≥30 **CLEAR** |
| Holdout H5 / H2 (reprint) | FAIL / PASS | FAIL / PASS | not a Phase 1 gate |
| Holdout SEP / Abs MFE (reprint) | FAIL / 50.4 bps | FAIL / 50.4 bps | cite short-travel; do not remount |
| ADVt lo (reprint) | 33% | 33% | publish-only |
| Train TB=+1 n | 5556 | 5568 | published |
| Val TB=+1 n | 360 | 208 | published |
| Val Spearman(score, path-EV) | **0.188** | **0.288** | ranks EV |
| Val Spearman(score, TB=+1) | 0.064 | **0.157** | B not “no TB rank” |
| Val Top−Rest TP-share | +0.033 | +0.035 | some TP concentration |
| Val Top−Rest MFE | +0.105 | +0.158 | Top travels on val |
| Val H2 proxy | +0.0013 PASS | +0.0012 PASS | XS skill holds |
| Isotonic vs TB order | scrambles (raw–iso ρ=0.91) | preserves (0.97) | report-only |
| Full TB-ranker val IC_tb | **−0.025** | **+0.016** | **worse than path-EV** |
| P1 N∈{8,12,16} CLEAR | 12, 16 | none | no common N |
| E1 Top≈Rest + tail | no (MFE not tied) | no | tail is worse, but Top already separates |

**Leave-one-family (val, no merge):** dropping **structure** hurts most (A ΔIC_ev −0.038; B −0.088 and ΔIC_tb −0.148). RS drop is mixed. Do **not** merge or drop families from this table.

**Hard-stop:** fired. Authorized ladder **[]**. Peek 1/2 not spent.

### Peeks

**None.** Sequential rule never opened.

---

## Phase 1 decision (pre-registered)

| Lever | Dual-fold authorize? | Why |
|---|---|---|
| **O1** rank-loss | **No** | Val discordance not both folds; TB-ranker val IC_tb < path-EV both folds |
| **P1** top-N | **No** | No common N; B H2-proxy collapse at 8/12/16 |
| **E1** train P25 keep | **No** | Val Top ≉ Rest on travel / exit mix |
| **F1** | Struck | — |

Tie-break O1→P1→E1 never engaged.

---

## Verdict

| Item | Lock |
|---|---|
| Peek ledger | **0 / 2 spent — both closed** |
| Merge ranker / parsimony / E1 into Short defaults | **No** |
| Path-EV GBM + `SHORT_FEATURES` | Unchanged |
| C1 / aux / path-room / S1 / S2 | Stay rejected / flag-only |
| Precision / B1 | **Still blocked** until Short dual-fold H5 + economics under a **new architecture charter** |
| Horizon-path PASS / cascade Short-ready | **Forbidden / unproven** |

**Capability sentence (FAIL path, as pre-registered):** single path-EV LightGBM under current Short feature physics is **insufficient for Short H5**. Next = **architecture** charter (two-head / true listwise redesign / coarser Short universe) — **not** Regime-inside-Horizon, **not** Precision bailout, **not** C1 merge, **not** a silent O1 holdout peek after a 0-authorize Phase 1.

**Forward pointer (non-binding, from charter):** if a later architecture charter also fails Short H5, escalate includes Long-only cascade economics re-check rather than open-ended Short-only remounts.

---

## Code / harness artifacts

Phase 1 diagnostic harness was **reverted after STOP** (no merge; O1/P1/E1 never entered defaults). Results live in the log and this memo.

| Path | Role |
|---|---|
| `logs/horizon_ev_tb_bridge_phase1_ab.txt` | Phase 1 A+B report (label-gate, forensic, parsimony, hard gate) |
| `src/horizon/horizon_model.py` | Unchanged — path-EV `GBMHorizonModel` + `SHORT_FEATURES` |

---

## Locked carry-forward

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors / H / multiples / K | Unchanged (Short K stays **3**) |
| Defaults | Current `SHORT_FEATURES` + path-EV label; aux=0; C1 flag-only |
| Soft ship floors (H4≥0 / TB+1≥15%) | Still **not** primary |

---

## Reject (next 30 days)

- Spending O1/P1/E1 on holdout after this 0-authorize Phase 1  
- Hybrid λ path_EV+TB blend; jointly-trained multi-head without a new charter  
- Remounting path-room / aux / chase demote / S1 / S2 / C1 merge / S1a / S-K  
- Unnamed F1 / Abs-MFE ρ fishing / full `SHORT_FEATURES` holdout ρ menu  
- Cost shopping or cutting `H=6`  
- Activating Precision WS2 / B1 as Short H5 bailout  

---

## Next workstream (outside this ledger)

**No peek on this ledger.** Fresh dual-judge **architecture** charter: [horizon-short-architecture-charter.md](horizon-short-architecture-charter.md) (**CLOSED** — [stop-memo](horizon-short-architecture-stop-memo.md); A2 FAIL @ 1/2). Precision stays blocked.
