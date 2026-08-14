# Horizon Exit Timing / MFE-Decay — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Step 0 MFE peak/giveback/exit-clock + ≤2 Long Tier-2 exit/hold peeks under locked `c*=20`  
**Status:** **STOP-MEMO — MFE-decay charter CLOSED**; peeks **2 / 2** exhausted — no merge  
**Date:** 2026-08-13  
**Charter:** [horizon-exit-mfe-decay-charter.md](horizon-exit-mfe-decay-charter.md)  
**Depends on:** [horizon-path-density-stop-memo.md](horizon-path-density-stop-memo.md), [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md)  
**Trigger:** Peek budget exhausted; both E1 and E2 hold Long H5 dual-fold without H1/H2/H3 regression but **worsen** abs Top-K TB+1 and leave H4 deeply negative — no economics-relevant hold  
**A+B peeks spent:** **2 / 2** — ledger **closed**

---

## One-line

Long Top-K **does** peak early (~bar 2.3) and **give back** ~0.39–0.43× TP inside `H=6`, but neither eval-only earlier flatten (`H_eff=3`) nor giveback-hold (`0.20×`) clears Horizon economics — **stop at 2/2**; Precision stays blocked.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| Intra-horizon peak/giveback is measurable (not just a name) | **Supported** — Step 0 dual-fold; hard-stop did **not** fire |
| Never-approaches-TP + null giveback → STOP @ 0/2 | **Disproven** — Abs MFE ~0.89–0.91×; giveback ~0.39–0.43× |
| Early peak implicates E1 `H_eff=3` | **Supported** as selection lock; **failed** as economics lever |
| Material giveback implicates E2 hold @ 0.20 | **Supported** as selection lock; **failed** as economics lever |
| Exit-policy peeks recover H4 / abs TB+1 | **Disproven** — TB+1 collapsed; H4 unchanged (~−17/−14 bps) |
| Precision may recover Horizon deficit | **Forbidden** — out of scope; still blocked |
| Merge `H_eff` or giveback-exit into production | **No** |

---

## Terminal evidence

### Step 0 (no peek)

**Log:** `logs/horizon_mfe_decay_step0_ab.txt`  
**Harness:** `python -m src.experiments.analyze_horizon_mfe_decay --folds A,B`

| Sleeve | Abs Top-K MFE | Giveback | Peak-bar med | Early 1–3 share | HARDSTOP |
|---|---|---|---|---|---|
| Long A | 0.913 | 0.432 | 2.29 | 0.705 | no |
| Long B | 0.894 | 0.392 | 2.40 | 0.671 | no |
| Short A/B | ~1.02 | ~0.44 | ~2.7 | ~0.65 | companion only |

**Implication lock (pre-peek):** E1 `H_eff=3` (median peak ≤3 both folds); E2 threshold `0.20` = pooled Top-K giveback mean (~0.41) / 2. Tie-break → **E1 first**.

Exit clock (Long Top-K): ~55–60% mass at bar-6 timeout; early exits dominated by SL.

### Peek 1 — E1 `H_eff=3` (eval exit only)

**Logs:** `logs/horizon_mfe_decay_e1_peek1_fold_a.txt` · `logs/horizon_mfe_decay_e1_peek1_fold_b.txt`  
**Baseline:** cost peek-1 Long @ `c*=20`

| Gate | E1 A | E1 B | vs cost Long |
|---|---|---|---|
| **H5** | PASS · 0.022 [0.010, 0.033] · p_top **4.6%** | PASS · 0.017 [0.008, 0.027] · p_top **3.7%** | Hold gate; **TB+1 collapse** (was 10.9 / 8.9) |
| H1 | PASS | PASS | Hold |
| H2 | FAIL | PASS | Hold (same pattern) |
| H3 | FAIL | PASS soft | Hold |
| H4 @20 | −17 bps | −14 bps | Unchanged (fwd-excess H4) |

Sequential Peek 2 **authorized** (H5 dual-fold + no H1/H2/H3 regression). Economics not improved.

### Peek 2 — E2 giveback-exit `0.20` (eval exit only)

**Logs:** `logs/horizon_mfe_decay_e2_peek2_fold_a.txt` · `logs/horizon_mfe_decay_e2_peek2_fold_b.txt`

| Gate | E2 A | E2 B | vs cost Long |
|---|---|---|---|
| **H5** | PASS · 0.017 [0.005, 0.027] · p_top **4.1%** | PASS · 0.013 [0.004, 0.021] · p_top **3.3%** | Hold gate; TB+1 still collapsed |
| H1/H2/H3 | same pattern | same pattern | Hold |
| H4 @20 | −17 bps | −14 bps | Unchanged |

---

## Verdict

| Item | Lock |
|---|---|
| Peek ledger | **2 / 2 spent — CLOSED** |
| E1 `H_eff` merge | **No** — CLI removed; primary H=6 unchanged |
| E2 giveback-exit merge | **No** — flag/CLI only |
| E3 TOD screen | **Not spent** — late-peak pattern did not dominate; budget exhausted on E1→E2 |
| Precision | **Still blocked** until Horizon H4 / path economics clear under locked geometry |
| Horizon-path PASS / cascade-ready | **Forbidden / unproven** |

**Diagnosis residual after this charter:** travel density is real and peak/giveback is real, but **15m eval-exit policy alone** does not convert that shape into better Top-K TB+1 or non-negative H4. Do not hand the deficit to Precision as a bailout.

---

## Code / harness artifacts

| Path | Role |
|---|---|
| `src/labels/triple_barrier.py` | Report-only `mfe_peak_bar_*`, `giveback_frac_*`, `tb_exit_h_*` (diagnostics stay). **E2 giveback-exit demoted / removed from labeler.** |
| `src/horizon/eval/mfe_decay.py` | Step 0 diagnostics; rejected E1/E2 locks cited only |
| `src/experiments/analyze_horizon_mfe_decay.py` | Step 0 CLI |
| `src/experiments/eval_horizon.py` | E1/E2 CLI **removed** (ledger closed; no ship defaults). |

---

## Next workstream (outside this ledger)

**Primary (dual-judge OPEN):** [horizon-tp-floor-recalibration-charter.md](horizon-tp-floor-recalibration-charter.md) — Long TP floor **60→50 bps** (`3.0×c → 2.5×c`) under locked `c*=20` / `H=6` / SL; Step 0 absolute MFE crossing first; max **1** peek; no H cut; no E1/E2 remount.  
→ **CLOSED:** [horizon-tp-floor-recalibration-stop-memo.md](horizon-tp-floor-recalibration-stop-memo.md) — T1 no merge; Long TP stays 60.

Still deferred / forbidden without a separate charter:

- Short ranking / travel-separation levers → **OPEN:** [horizon-short-travel-separation-charter.md](../horizon-short-travel-separation-charter.md)  
- Precision juice **after** Horizon book is non-negative under locked (or dual-judge-amended) TB  
- Soft reopen of path-density L1, cost ladder, or Precision-as-Horizon-bailout
