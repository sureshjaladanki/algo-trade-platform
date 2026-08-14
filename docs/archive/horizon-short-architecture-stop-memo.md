# Horizon Short Architecture — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Test whether a pre-registered architecture change — jointly-trained two-head, true listwise redesign, or coarser Short universe — can clear dual-fold Short H5 under locked `c*=20` / `H=6` / floors  
**Status:** **STOP-MEMO — architecture charter CLOSED**; peeks **1 / 2** · A2 FAIL · **no remaining authorized lever** — **no merge**  
**Date:** 2026-08-14  
**Charter:** [horizon-short-architecture-charter.md](horizon-short-architecture-charter.md)  
**Depends on:** [horizon-short-ev-tb-bridge-stop-memo.md](horizon-short-ev-tb-bridge-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md)  
**Trigger:** Phase 1 authorized A2 only; Peek 1 A2 failed Short H5 dual-fold (and H1/H2 regression); A1/A3 not authorized  
**A+B peeks spent:** **1 / 2** — remaining slot unused (no next authorized class)

---

## One-line

Path-EV already overlaps the TB-probe and already has positive val H5-proxy; a true listwise NDCG@3 redesign (`rank_xendcg`, not closed `lambdarank`) **fails holdout H5 and regresses H1/H2** — **stop**; Short H5 is not recoverable via the architecture classes tested this ledger; next = Long-only cascade economics; Short sleeve stays disabled.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| Holdout Short H5 FAIL / H2 PASS @ `c*=20` is still the residual | **Supported** — Phase 1 reprint (H5 FAIL/FAIL; H2 PASS/PASS; ADVt lo 33%/33%) |
| Two-head complementarity (A1): low Jaccard + TB-only hit lift + neither head val H5-proxy ≤ 0 | **Disproven dual-fold** — Jaccard 0.636 / 0.397; TB-only hit **below** EV-only both; path-EV val H5-proxy **+3.3 / +3.5 pp** |
| Closed-O1 TB-probe is weak / Fold A negative | **Supported** — probe val IC_tb **−0.014 / +0.038** (do not read Fold A noise as complementarity) |
| Listwise geometry (A2): mean-N ≥ 50, non-degenerate grades, path-EV NDCG@3 − null ≥ +0.030 | **Supported on val** — mean-N 51.8 / 60.5; TP/TO/SL present; NDCG lift +0.153 / +0.142 |
| A2 holdout listwise (`rank_xendcg`, grades 2/1/0, `label_gain=[0,1,3]`, `eval_at=[3]`) clears Short H5 | **Disproven** — H5 FAIL/FAIL; H1 A FAIL; H2 FAIL/FAIL |
| Coarser universe (A3): PIT Nifty-50 or train ADV≥P50 lifts val Top−Rest TB=+1 by ≥ +0.020 with H2-proxy > 0 | **Disproven** — Nifty-50 ΔH5 **0.000 / 0.000**; ADV≥P50 **−0.037 / −0.009** (min-N CLEAR both masks; K=3 never cut) |
| Precision / B1 / Regime-inside-Horizon / O1 `lambdarank` remount may bridge Short H5 | **Forbidden** |

**Residual lock after this charter:** Short H5 is **not recoverable via the architecture classes tested this ledger** (A2 peeked and failed; A1 and A3 **not authorized** — not untested-authorized). Next = **Long-only cascade economics re-check**. Short momentum sleeve stays **disabled / flat** in live/paper cascade.

---

## Terminal evidence

### Phase 1 (0 peeks)

**Log:** `logs/horizon_architecture_phase1_ab.txt`  
**Harness:** `python -m src.experiments.analyze_horizon_architecture --folds A,B`

Holdout H5 / H2 / ADVt = **frozen reprint** (cost peek-1). Authorization = last-fold **train/val** + numeric cuts.

| Diagnostic | Fold A | Fold B | Cut / read |
|---|---|---|---|
| Holdout min-N (reprint) | 779 bars / 125 sess | 920 / 133 | ≥150 / ≥30 **CLEAR** |
| Holdout H5 / H2 (reprint) | FAIL / PASS | FAIL / PASS | not a Phase 1 gate |
| Holdout H5 point [CI] | 0.0019 [−0.018, 0.022] | 0.0143 [−0.002, 0.034] | FAIL/FAIL |
| ADVt lo (reprint) | 33% | 33% | publish-only |
| Val Jaccard(path-EV, TB-probe) | **0.636** | 0.397 | A1 needs &lt; 0.40 |
| TB-probe val IC_tb | **−0.014** | +0.038 | reused O1 family; A negative |
| TB=+1 hit EV-only / TB-only | 0.125 / **0.085** | 0.080 / **0.069** | TB-only not +2.0 pp |
| Val H5-proxy EV / probe | **+0.033 / +0.017** | **+0.035 / +0.020** | A1 needs both ≤ 0 |
| Mean eligible names/bar | 51.8 | 60.5 | A2 ≥ 50 **CLEAR** |
| Grade mass TP/TO/SL | 360 / 1860 / 1196 | 208 / 2344 / 1864 | non-degenerate **CLEAR** |
| Path-EV NDCG@3 − shuffled null | **+0.153** | **+0.142** | A2 ≥ +0.030 **CLEAR** |
| PIT Nifty-50 val ΔH5 / H2-proxy | 0.000 / +0.0013 | 0.000 / +0.0012 | A3 Δ ≥ +0.020 **FAIL** |
| Train ADV≥P50 val ΔH5 / H2-proxy | **−0.037** / +0.0001 | **−0.009** / +0.0002 | A3 **FAIL** |
| Mask holdout min-N | N50 772/124; ADV 764/124 | N50 919/133; ADV 912/133 | CLEAR (K=3 held) |

**Hard gate:** authorized ladder **[A2]**. A1/A3 numeric FAIL both folds. Peek 1 = A2. Peek 2 unused (no next authorized class).

### Peek 1 — A2 true listwise

**Log:** `logs/horizon_architecture_peek1_a2_ab.txt`  
**Harness:** `python -m src.experiments.analyze_horizon_architecture --folds A,B --peek a2`

Locked spec: bar-level groups; grades TP=2 / TO=1 / SL=0; `label_gain=[0,1,3]`; `eval_at=[3]`; objective **`rank_xendcg`** (LightGBM approx-NDCG; **not** `lambdarank`; YetiRank not in LightGBM 4.7). Same `SHORT_FEATURES` / tree family. Short eval sign-flip preserved.

| Gate | Fold A | Fold B | vs cost peek-1 Short |
|---|---|---|---|
| **H5** | 0.011 [−0.008, 0.029] **FAIL** | 0.005 [−0.013, 0.025] **FAIL** | primary **FAIL/FAIL** |
| H1 | −0.003 **FAIL** | 0.022 PASS | **A regress** |
| H2 | −0.0001 **FAIL** | 0.0001 **FAIL** | **regress both** |
| H3 | PASS | PASS | held |
| H4 @20 | −21 bps | −19 bps | still neg |
| Top-K TB+1 | 13.7% | 12.0% | report-only; do not soft-promote |
| Val IC_tb (trainer) | 0.037 (5 folds) | 0.047 (5 folds) | not a gate |

**Peek 2:** skipped — A1/A3 not authorized.

---

## Phase 1 decision (pre-registered)

| Lever | Dual-fold authorize? | Why |
|---|---|---|
| **A1** two-head | **No** | Jaccard not &lt; 0.40 both (A 0.636); TB-only hit &lt; EV-only; path-EV val H5-proxy &gt; 0 both |
| **A2** true listwise | **Yes** | mean-N, grades, NDCG lift, holdout H5 reprint FAIL |
| **A3** coarser universe | **No** | neither mask ΔH5 ≥ +0.020 (Nifty-50 flat; ADV P50 worse) |

Tie-break A1→A2→A3 → Peek 1 = **A2**.

---

## Verdict

| Item | Lock |
|---|---|
| Peek ledger | **1 / 2 spent** — A2 FAIL; leftover slot **closed** |
| Merge A2 listwise / two-head / Nifty-50 or ADV mask into Short defaults | **No** |
| Path-EV GBM + `SHORT_FEATURES` | Unchanged |
| C1 / aux / path-room / S1 / S2 / O1 `lambdarank` | Stay rejected / flag-only / forbidden remount |
| Precision / B1 | **Still blocked** |
| Horizon-path PASS / cascade Short-ready | **Forbidden / unproven** |
| Short momentum sleeve | **Disabled / flat** in live or paper cascade pending Long-only economics |

**Capability sentence (FAIL path, as pre-registered):** Short H5 is **not recoverable via the architecture classes tested this ledger** (A2). A1 (two-head) and A3 (coarser universe) were **not authorized** by Phase 1 numeric cuts — they are not authorized-but-untested. Next = **Long-only cascade economics re-check** — **not** another Short-only remount, **not** Regime-inside-Horizon, **not** Precision bailout.

---

## Code / harness artifacts

A2 never entered defaults. Phase 1 + peek harness stays as flag-gated replay (`--peek a2`); production Short remains path-EV LightGBM.

| Path | Role |
|---|---|
| `logs/horizon_architecture_phase1_ab.txt` | Phase 1 A+B numeric gate |
| `logs/horizon_architecture_peek1_a2_ab.txt` | Peek 1 A2 holdout |
| `src/horizon/eval/architecture.py` | Phase 1 authorize + A2 listwise (off defaults) |
| `src/horizon/eval/nifty50_pit.py` | PIT Nifty-50 mask (A3 diagnosis only) |
| `src/experiments/analyze_horizon_architecture.py` | Phase 1 / A2 peek CLI |
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

- Remounting A2 as `lambdarank` or stacking A1/A3 after this 1-authorize FAIL  
- Hybrid λ; feature expansion; A3 K-cut; mid-charter mask switch  
- Remounting path-room / aux / chase / S1 / S2 / C1 merge / S1a / S-K / O1/P1/E1  
- Cost shopping or cutting `H=6`  
- Activating Precision WS2 / B1 as Short H5 bailout  
- Regime-inside-Horizon; another Short-only architecture remount on this residual  

---

## Next workstream (outside this ledger)

**No further Short peek on this ledger.** Fresh dual-judge **Long-only cascade economics** charter. Short sleeve stays disabled / flat. Precision stays blocked.
