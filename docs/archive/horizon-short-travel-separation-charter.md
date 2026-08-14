# Horizon Short Ranking / Travel-Separation — Nifty-100 MIS v1

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Test whether a **novel Short-only** ranking or selection lever can create **Top−Rest travel separation** and/or clear **Short H5** under locked `c*=20` / `H=6` / floors — **without** remounting the Short reject list or handing the deficit to Precision  
**Status:** **STOP-MEMO** — peeks **1/2** · remaining peek **closed** — see [stop-memo](horizon-short-travel-separation-stop-memo.md)  
**Authority (prior):** TP-floor STOP next-workstream residual ([stop-memo](horizon-tp-floor-recalibration-stop-memo.md)); path-density Short SEP null ([stop-memo](horizon-path-density-stop-memo.md)); MFE-decay / Long density / Long TP-floor ledgers **CLOSED**  
**Judges (this charter):** [Claude Sonnet](e92ffac4-5360-4452-9959-8e0cc89d41a7), [Gemini Flash](353cb364-9dd8-46df-9269-3f298f7842e1)  
**Date:** 2026-08-13  
**Depends on:** [horizon-tp-floor-recalibration-stop-memo.md](horizon-tp-floor-recalibration-stop-memo.md), [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md), [horizon-path-density-charter.md](horizon-path-density-charter.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md), [horizon-tier2-v11-short-stop-memo.md](horizon-tier2-v11-short-stop-memo.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md), [cascade-strategy-overview.md](../cascade-strategy-overview.md)  
**Does not reopen:** Cost ladder · Regime · Precision WS2 · primary `H=6` · Long TP/SL · Long L1/E1/E2 · path-room-on · Short aux-excess · Short `stock_r_15` demote · S1 circuit/UC · S2 TOD hard cut · L3 sequential waive · Long TP-floor grid

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | Long 15m levers exhausted (path-density L1, MFE-decay E1/E2, TP-floor T1 — all no-merge). TP-floor STOP deferred **Short ranking / travel-separation** to a fresh dual-judge charter. Short is the remaining Horizon sleeve with an **unspent novel-lever** surface under locked friction |
| Diagnosis to test | Short Top-K **does not** concentrate unfinished downside travel vs Rest (path-density SEP **FAIL** both folds) while Abs MFE ~**1.01×** Short TP — paths *can* travel; **ranking does not select them**. Under `c*=20`, Short **H5 FAIL** dual-fold while **H2 PASS** — XS skill without StockTB+1 bridge |
| Single degree of freedom | **Short ranking / selection only** — one novel variable per peek. Long frozen companion. Barriers / `c` / H frozen |
| Tier ownership | **Horizon owns Short path EV.** Precision stays blocked; B1 Short Precision stays inactive until Short dual-fold H5 under locked geometry |
| Sleeve posture | **Short-only peeks**; Long = Step 0 / gate companion report only (no Long lever spend) |
| Peek budget | **Max 2** Short Fold A+B; Step 0 mandatory; hard-stop @ 0/2 if no falsifiable signal |
| Precision | **Out of scope** — no bailout; no B1 activate |
| Build posture | **CLOSED** — stop-memo at 1/2; C1 flag-gated off defaults |

**One-line:** Ask whether Short can create Top−Rest travel (or H5) separation with a **novel** ranking/selection lever under locked `c*=20` / `H=6` — or stop cleanly when Step 0 shows nothing left to lever.

---

## Dual-judge scores (charter design) — 2026-08-13

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Diagnosis fidelity | 9/10 | 9/10 | **ACCEPT** — Short SEP null + H5 FAIL / H2 PASS is the right residual after Long exhaustion |
| Scope / freeze | 9/10 | 8/10 | **ACCEPT** — Short-only; Long / cost / H / barriers / Precision frozen |
| Peek budget / hard-stop | 7/10 | 6/10 | **REVISE→LOCK** — raise ρ bar; pre-register S1b; numeric S-K + S1a cuts |
| Gate design | 9/10 | 8/10 | **ACCEPT** — Short H5 primary; no H1/H2/H3 regression |
| Reject hardness | 9/10 | 8/10 | **ACCEPT** — reject registry stands |
| Metrics / results fidelity | 10/10 | 9/10 | **ACCEPT** — TP-floor + path-density + cost cites verified |
| Overall | ACCEPT WITH REVISIONS | ACCEPT WITH REVISIONS | **ACCEPT WITH REVISIONS → OPEN** |

**Judge one-liners**

- Gemini: Short is correct next residual; kill open S1b feature fishing; tighten ρ; lock S1a percentile on train only; S-K only with min-N.  
- Claude: Architecture sound; hard-stop too easy to waive at ρ≥0.05; S-K “≪” is qualitative gate-shopping; S1a must not fit threshold on holdout; S1b needs non-duplication vs rejects.

**Revisions applied (MUST_FIX consensus)**

1. **Pre-register S1b candidates (max 2)** — no post-hoc scan of all `SHORT_FEATURES` to pick the peek feature (Gemini #1; Claude #4).  
2. **Tighten feature→travel bar** — holdout \|ρ\| vs Abs MFE ≥ **0.10** on a pre-registered candidate, sign-consistent both folds (both). Full `SHORT_FEATURES` ρ table stays **report-only**.  
3. **S1a threshold = train-only + fixed percentile rule** — exclude `bounce_risk_zscore` ≥ train P90; never fit on holdout (both).  
4. **Numeric S1a anti-selection cut** — Top mean MFE ≤ Rest − **0.05×** Short TP both folds (Claude #5).  
5. **Numeric S-K trigger** — rank-1 MFE ≤ mean(ranks 2–3) − **0.10×** Short TP both folds; plus K=2 holdout Top-K trade count ≥ **150** / fold (Claude #1; Gemini #4).  
6. **S1b non-duplication** — candidate must have \|corr\| &lt; **0.70** vs reject-listed columns (`stock_r_15`, path-room composites if present, Long `tod_mfe_frac_60`) on train (Claude #4).

---

## Authority from TP-floor STOP (do not reopen Long)

From [stop-memo](horizon-tp-floor-recalibration-stop-memo.md):

| Fact | Implication |
|---|---|
| Near-miss [50,60) ~6% both folds; SL-contam ~8–9% | Convertible Long mass was real |
| T1 Long TP 60→50: H5 hold; **H3-B regress**; TB+1 flat; H4 −14/−15 | Long TP floor alone fails economics |
| Long TP stays **60 bps** | Frozen this charter |
| Deferred residual | **Short ranking / travel-separation levers** (this charter) |
| Precision / cost / H cut / E1/E2/L1 remount | Still **forbidden** |

**Long residual lock:** entry density, exit timing, and Long TP floor are exhausted under locked geometry. This charter does **not** re-litigate Long.

**Dual-judge confirm (a):** both judges **PASS** TP-floor STOP metrics fidelity and endorse Short as the correct next residual.

---

## Authority from path-density Short SEP (binding)

From [path-density Step 0](horizon-path-density-charter.md) (`logs/horizon_path_density_step0_ab.txt`):

| Sleeve · Fold | MFE Top−Rest | Abs MFE top/rest | EXIT TP Top−Rest | SEP |
|---|---|---|---|---|
| Short A | +0.014 [−0.050, 0.080] FAIL | 1.01 / 1.00 | +0.002 [−0.017, 0.023] FAIL | **FAIL** |
| Short B | −0.014 [−0.067, 0.040] FAIL | 1.01 / 1.03 | +0.014 [−0.002, 0.031] FAIL | **FAIL** |

| Cost peek-1 @ `c*=20` (companion) | Short A | Short B |
|---|---|---|
| H5 | **FAIL** | **FAIL** |
| H2 | PASS | PASS |
| H4 @20 | −13 bps | −16 bps |

**Implication lock:** A Long-style “Top already travels farther — add travel feature” story is **not** available for Short. Any peek must be justified by a **new** Step 0 pattern (anti-selection, pre-registered feature→travel, or numeric rank-tier inversion) — not by remounting v2/v1.1 rejects.

---

## Rejected-levers registry (carry-forward — do not remount)

| Lever | Ledger | Outcome | Code posture |
|---|---|---|---|
| Path-room features | Horizon v2 peek 2 | Ablation **helped**; demoted | Off defaults both sleeves |
| Short aux-excess (`w=0.5`) | Horizon v2 peek 4 | Short A H5 PASS→FAIL | Aux weight **0** |
| Short `stock_r_15` demote | Horizon v2 peek 5 | Short A H5 FAIL (worse) | **Keep** Short `stock_r_15` |
| S1 circuit/UC exclude | v1.1 Short | Dual-fold H5 FAIL; H10 regress B | `APPLY_S1_SHORT=False` |
| S2 TOD afternoon cut | v1.1 Short | PM H5 ≥ AM — cut would hurt | Reject hard cut |
| Long L1 `tod_mfe_frac_60` | Path-density | H2-B regress; H4 neg | Flag only; **not** transplant to Short defaults |
| Long E1/E2 | MFE-decay | TB+1 collapse | Rejected / removed |
| Long TP 50 | TP-floor | H3-B regress; economics null | Long TP stays 60 |
| Cost ladder 15/10/25 | Cost | REJECT | `c*=20` locked |
| Precision-as-H4-bailout / B1 | Cross-charter | Forbidden | Precision blocked; B1 inactive |

---

## Tier responsibility lock (hard)

| Tier | Owns | Does **not** own |
|---|---|---|
| **1 Regime** | Sleeve open/close | Stock pick / Short path bridge |
| **2 Horizon + TB** | Short name rank + **path EV under frozen geometry** — this charter may amend **Short ranking/selection only** | Dumping underwater Short books onto Tier 3; silent barrier/H/cost edits |
| **3 Precision** | 1m fill on a **shipped** Short Top-K | Recovering Short H5 / H4; rewriting barriers; activating B1 early |

**Anti-goal:** “Precision / B1 bridges Short H5 FAIL” → **FAIL charter intent**.

---

## Carry-forward locks

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** — frozen |
| Floors | Long TP **60** / Short TP **50** / SL **30** — frozen |
| Vol multiples | Long `2.5/1.0`; Short `2.0/0.9` — frozen |
| Primary H | **H=6 / 90m** — frozen |
| MIS cutoffs | Long ~13:45 / Short ~13:30 — frozen |
| K | Long **5** / Short **3** — change only via **S-K** if numeric rank-tier cut fires |
| Long features / peeks | Frozen companion; **0** Long peeks |
| `tod_mfe_frac_60` / path-room / E1/E2 / S1/S2 | Stay demoted / flag-replay / off |
| Regime / Precision WS2 / B1 | CLOSED / blocked / inactive |

**Single degree of freedom this charter:** one **novel** Short ranking or selection variable per peek (pre-registered feature add, eligibility screen, or K — contingent on Step 0). No barrier / cost / H edits.

---

## Process locks

| Lock | Rule |
|---|---|
| Dual-judge gate | **DONE** — ACCEPT WITH REVISIONS applied; Step 0 unlocked |
| Step 0 (no peek) | Publish Short travel / anti-selection / feature→travel diagnostics A+B — see below |
| Hard stop @ 0 peeks | If **no** Step 0 pattern authorizes a novel lever (table below) → **STOP at 0/2** |
| Peek budget | **Max 2** Short-only Fold A+B; Long peeks = 0 |
| Single-variable | One lever per peek; no grid; no pooled Long+Short |
| Sequential | Peek 2 only if Peek 1 clears Short H5 dual-fold **without** regressing Short H1/H2/H3 vs cost peek-1 Short baseline |
| Multiplicity | **New ledger** — cannot borrow v2’s 5, cost’s frozen peeks, path-density, MFE-decay, or TP-floor |
| Precision / B1 | No experiments; no activate |
| Stop | Exhaust 2 **or** hard-stop @ 0 **or** clean Short H5 hold with no regression → stop-memo |

---

## Gates

| Role | Metric | Rule |
|---|---|---|
| **Primary (peek)** | Short H5 (Top−Rest StockTB+1) | Dual-fold CI LB > 0 |
| **Anti-goal** | Breaking Short H5 / H2 to lift report-only abs TB+1 / H4 | **FAIL** |
| **Anti-goal** | Remounting reject-list levers or cutting H / shopping cost | **FAIL** |
| Report-only | Abs Top-K TB+1, H4 @20, H4arch @30, H1/H2/H3, ADVt lo share, Step-0 SEP / feature→travel | Never soft-promote H4≥0 / TB+1≥15% to ship without fresh dual-judge |
| Long companion | Long H5/H1–H4 | Report-only; must not regress via accidental shared-code change |

---

## Step 0 — Short travel / ranking diagnostic (no peek)

**Required before peek 1.** **Short primary.** Long companion publish-only. Fold A and B calendars (same as cost / path-density).  
**CI methodology:** session-block bootstrap — **inherited unchanged** from [path-density charter](horizon-path-density-charter.md).

Locked geometry: entry at decision bar-end; path `t+1 … t+H` with `H=6`; Short TP **50** / SL **30**; working `c*=20`; current Short `SHORT_FEATURES` + path-EV label (aux=0).

| Diagnostic | What to publish |
|---|---|
| **SEP reconfirm** | Top−Rest mean MFE/TP-floor + Top−Rest TP-share (session-block CI) — expect FAIL; publish anyway |
| **Anti-selection** | Top−Rest mean MFE; whether Top ≤ Rest − **0.05×** TP both folds |
| **Abs MFE (bps)** | Top-K vs Rest mean Abs MFE; P(≥50 bps) vs Short TP floor |
| **Exit mix** | Top vs Rest TP / SL / timeout |
| **Rank tier** | Rank-1 vs mean(ranks 2–3) MFE gap in ×TP units; TB+1 by rank |
| **Extension / bounce** | Top−Rest on `bounce_risk_zscore`, `stock_r_15`, `pct_from_52w_high`, `downside_acceleration` |
| **Feature→travel (gated)** | Holdout Spearman of **pre-registered S1b candidates only** (below) vs Abs MFE — authorize S1b iff \|ρ\| ≥ **0.10**, sign-consistent both folds, and non-duplication pass |
| **Feature→travel (report-only)** | Full `SHORT_FEATURES` ρ vs Abs MFE / StockTB+1 (train report; holdout publish) — **never** used to pick an unregistered S1b |
| **ADV** | Top-K ADVt lo share; MFE by ADV tercile (report) |
| **K=2 sample (report)** | Holdout Top-K trade count at K=2 (needed if S-K implicated) |

### Pre-registered S1b candidates (max 2 — locked before Step 0)

| ID | Feature | Definition | Why novel |
|---|---|---|---|
| **C1** | `tod_mfe_frac_50_short` | Causal same-clock mean of prior-session Short Abs MFE / **50 bps** floor; lookback 60; `shift(1)` within `(symbol, time_only)` | Short-side travel-adequacy analog — **not** Long `tod_mfe_frac_60` transplant into defaults; new column, off `SHORT_FEATURES` until peek |
| **C2** | `unfinished_downside_z` | Causal z of distance-to-session-low / same-clock TOD `rv_15_mean` (no forward path; **not** `tp_room_atr` / `sl_room_atr`) | Unfinished downside room without path-room reject remount |

**Non-duplication (C1/C2):** on train window, \|corr\| with `stock_r_15`, `tod_mfe_frac_60` (if present), and any path-room column must be **&lt; 0.70**. Fail → that candidate is **ineligible** (do not spend S1b on a renamed reject).

**Hard-stop cuts (pre-registered — OR across cuts; fire → STOP @ 0/2):**

| Cut | Meaning |
|---|---|
| SEP still FAIL **and** no anti-selection (Top mean MFE &gt; Rest − 0.05×TP on either fold) **and** neither C1 nor C2 clears holdout \|ρ\| ≥ **0.10** sign-consistent both folds **and** S-K numeric gap does not fire | Nothing novel to lever → STOP |
| Abs Top-K MFE **&lt; 0.70×** Short TP (35 bps) both folds | Paths do not reach economic zone → STOP (geometry, not ranking) |
| Only “winning” Step 0 pattern is a **reject-list remount** (aux / chase demote / path-room / S1 / S2) | Forbidden → STOP |

**Implication gate (if hard-stop does not fire):**

| Step 0 pattern (numeric) | Authorized lever |
|---|---|
| Anti-selection: Top mean MFE ≤ Rest − **0.05×** Short TP **both** folds | **S1a** |
| C1 or C2: holdout \|ρ\| vs Abs MFE ≥ **0.10**, sign-consistent both folds, non-duplication pass | **S1b** (exactly one winner; if both clear, higher \|ρ\| wins — no second feature peek) |
| Rank-tier: rank-1 MFE ≤ mean(2–3) − **0.10×** Short TP **both** folds **and** K=2 holdout Top-K trades ≥ **150** / fold | **S-K** |
| Multiple patterns | Tie-break: **S1a → S1b → S-K** (spend ≤2) |

**Harness (proposed):** `python -m src.experiments.analyze_horizon_short_travel --folds A,B`  
**Log (proposed):** `logs/horizon_short_travel_step0_ab.txt`

---

## Pre-registered Short lever ladder (contingent on Step 0)

Execute in order; spend ≤2 peeks total. **No reject-list remount. No feature grid.**

| Order | Lever | Single variable | Usable only if Step 0 shows |
|---|---|---|---|
| **S1a** | Max-extension / bounce eligibility screen | Exclude names with `bounce_risk_zscore` ≥ **train-fold P90** (threshold frozen from train before peek; grade on holdout only) | Anti-selection numeric cut |
| **S1b** | Append **one** of {C1, C2} to `SHORT_FEATURES` | Winner of gated ρ race (one on/off) | C1/C2 ρ + non-duplication |
| **S-K** | Short K **3→2** | `K` only | Rank-tier numeric cut + min-N |

**Peek gates (if Step 0 clears):**

| Item | Lock |
|---|---|
| Sleeve | Short only |
| Baseline | Cost peek-1 Short under `c*=20` (`logs/horizon_cost_c20_peek1_fold_*.txt`) |
| Gate | Short H5 dual-fold CI LB > 0; no Short H1/H2/H3 regression vs that baseline |
| Report-only | Abs TB+1, H4@20, H4arch@30, SEP delta vs Step 0, ADVt, S1a drop-rate / K=2 trade count |
| Merge | Only via stop-memo + dual-judge; default **off** until then |
| Ship language | Do **not** claim Short Horizon-path PASS / B1-ready from H5 alone without H4 / dual-judge |

---

## Forbidden moves

- Remounting path-room, Short aux-excess, Short chase demote, S1, S2, Long L1/E1/E2, Long TP 50  
- Cost shopping or reverting `c` to 30  
- Cutting primary `H=6` or changing Short/Long floors or vol multiples  
- Any Long feature / floor / K peek under this ledger  
- Scanning all `SHORT_FEATURES` to pick an unregistered S1b after seeing holdout ρ  
- Fitting S1a threshold on holdout / pooled A+B test  
- Hyperparam grid on A+B; Fold C locks; pooled Long+Short  
- Soft-promoting H4 ≥0 / TB+1 ≥15% to ship gates  
- Activating Precision WS2 / B1 or claiming cascade Short readiness  
- Treating path-density Short SEP FAIL as license to skip Step 0  
- Inventing F&O-active membership mid-peek  

---

## Build sequence

1. **Dual-judge sign-off** on this charter design → **DONE** (ACCEPT WITH REVISIONS; locks applied).  
2. **Step 0** — Short travel / anti-selection / gated C1–C2 ρ A+B.  
3. **Hard gate** — OR cuts → STOP @ 0/2 or authorize S1a / S1b / S-K.  
4. **Peek 1** — first authorized lever Short A+B.  
5. **Peek 2** — only if sequential gate clears.  
6. **Stop-memo** — merge or no-merge; Precision / B1 still blocked unless Short H5 + economics dual-judge clear.

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-tp-floor-recalibration-stop-memo.md](horizon-tp-floor-recalibration-stop-memo.md) | Why Short is next — Long TP-floor CLOSED |
| [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md) | Short SEP FAIL; Long density exhausted |
| [horizon-exit-mfe-decay-stop-memo.md](horizon-exit-mfe-decay-stop-memo.md) | Long exit timing CLOSED |
| [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | Short H5 FAIL @ `c*=20`; friction lock |
| [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md) | Short aux / chase demote rejects |
| [horizon-tier2-v11-short-stop-memo.md](horizon-tier2-v11-short-stop-memo.md) | S1/S2 terminal; B1 inactive |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | Locked geometry |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Tier jobs — Precision inherits geometry |
| [precision-tier3-verdict.md](../precision-tier3-verdict.md) | Deferred — juice only after Horizon viable |
| [horizon-short-travel-separation-stop-memo.md](horizon-short-travel-separation-stop-memo.md) | This charter CLOSED — C1 no-merge |
