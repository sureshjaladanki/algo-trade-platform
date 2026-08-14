# Horizon Path-Density — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Step 0 MFE/exit travel diagnostic + ≤2 Long single-variable density peeks under locked `c*=20`  
**Status:** **STOP-MEMO — path-density charter CLOSED**; dual-judge **ACCEPT STOP** — remaining peek closed  
**Date:** 2026-08-13  
**Charter:** [horizon-path-density-charter.md](horizon-path-density-charter.md)  
**Outcome judges:** [Claude Sonnet](f9256c28-1e53-43be-acc3-cc3e9f6349e1), [Gemini Flash](5515a43a-2941-42c3-9ad2-9d31d4ecca71)  
**Depends on:** [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md), [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md), [triple-barrier-verdict.md](../triple-barrier-verdict.md)  
**Trigger:** Peek 1 (L1) holds Long H5 but regresses Fold B H2 vs cost baseline → sequential Peek 2 freeze; dual-judge rejects L3 waive  
**A+B peeks spent:** **1 / 2** — remaining peek **closed** (not paused; reopen needs a fresh charter)

---

## One-line

Long Top-K **does** travel farther than Rest under `c*=20`, but the first density lever (`tod_mfe_frac_60`) does not clear economics and violates the no-regression sequential rule — **stop at 1/2**; do not amend to L3.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| Path density is a measurable Top-K vs Rest travel leak (not just a name) | **Supported** — Step 0 Long MFE + EXIT separation dual-fold PASS |
| Short shares the same travel-separation shape | **Disproven** — Short SEP FAIL both folds; Short stays deferred |
| L2 (Long K 5→3) is implicated by rank-tier MFE decay | **Disproven** — Fold A 1–2 *worse* than 3–K |
| L1 travel-adequacy feature clears denser TB paths / economics | **Disproven / inconclusive** — H5 holds; abs TB+1 barely moves; H4 still neg; H2-B regresses |
| Waive sequential rule to spend Peek 2 on L3 | **Rejected** — dual-judge ACCEPT STOP (amend necessity low) |
| Merge `tod_mfe_frac_60` into default `LONG_FEATURES` | **No** |
| Horizon-path PASS / cascade-ready from this charter | **Forbidden / unproven** |

---

## Terminal evidence

### Step 0 (no peek)

**Log:** `logs/horizon_path_density_step0_ab.txt`

| Sleeve | Dual-fold SEP | Abs Top-K MFE / TP floor |
|---|---|---|
| Long | **PASS** (MFE + EXIT both folds) | ~0.89–0.92× (timeout ~50%) |
| Short | **FAIL** both folds | ~1.01× but no Top−Rest edge |

### Peek 1 — L1 `tod_mfe_frac_60`

**Logs:** `logs/horizon_path_density_l1_peek1_fold_a.txt` · `logs/horizon_path_density_l1_peek1_fold_b.txt`  
**Baseline:** cost peek-1 Long @ `c*=20`

| Gate | L1 A | L1 B | vs cost Long |
|---|---|---|---|
| **H5** | PASS · p_top 12.0% | PASS · p_top 9.0% | Hold (was 10.9 / 8.9) |
| H1 | PASS | PASS | Hold |
| H2 | PASS | **FAIL** | **B PASS→FAIL — sequential freeze trigger** |
| H3 | FAIL (soft) | PASS | Soft-H3 unresolved on A |
| H4 @20 | −12 bps | **−19 bps** | A −17→−12; **B −14→−19 (worse)** |
| ADVt lo | 28% | 28% | ≈30–36% baseline |

Do not cite only the H5 / A TB+1 uptick — H2-B regression + H3-A fail + H4-B degradation travel together.

---

## Dual-judge outcome (2026-08-13)

**Judges:** [Claude Sonnet](f9256c28-1e53-43be-acc3-cc3e9f6349e1), [Gemini Flash](5515a43a-2941-42c3-9ad2-9d31d4ecca71)

| Axis | Gemini | Claude | Consensus |
|---|---|---|---|
| Overall | **ACCEPT STOP** | **ACCEPT STOP** | **ACCEPT STOP** |
| Process discipline | 10/10 | 9/10 | Keep sequential freeze |
| Amend necessity (L3 waive) | 0/10 | 3/10 | **Do not amend** |
| Merge L1 | no | no | **Keep flag-gated; off defaults** |
| Remaining peek | closed | closed | **1/2 spent; 1 closed** |

**Judge one-liners**

- Gemini: L1 failed economics and broke H2-B sequential lock — L3 waive is post-hoc rule softening.  
- Claude: Sequential lock fired on swiss-cheese soft-gate pattern with H4 still deeply negative — that is the stop signal, not a reason to spend the last peek.

---

## Locked carry-forward

| Item | Lock |
|---|---|
| `ROUND_TRIP_COST` / archive | **0.0020 / 0.0030** |
| Floors / H / multiples | Unchanged |
| `tod_mfe_frac_60` | **Flag-gated only** (`--l1-travel-adequacy`); **not** in default `LONG_FEATURES` |
| Path-room / v2 rejects | Stay demoted / rejected |
| Short levers this ledger | **0**; Step 0 null separation stands |
| Peeks | **1/2 spent; remaining closed** — no resume on this ledger |
| Soft ship floors (TB+1≥20%, H4≥0) | Still **not** primary |

---

## Reject (next 30 days)

- L3 sequential waive without a **new** dual-judge charter  
- Merging L1 into defaults  
- Cost ladder / Regime / Precision WS2 / path-room-on reopen  
- Short lever re-chase from v2 reject list  
- Horizon-path PASS / cascade-ready claims from Step 0 or Peek 1  
- Treating remaining peek as “paused”

---

## Next workstream (consensus direction → draft charter)

| Judge | Recommendation |
|---|---|
| Claude | No-peek **exit-timing / MFE-decay within H=6** diagnostic — when Top-K travel peaks vs timeout; whether edge is given back before exit |
| Gemini | Tier 3 **Precision 1m entry-timing / exit-management** — can execution bridge the ~12–19 bps Horizon deficit |

**Shared read:** entry-side 15m density levers under locked geometry are exhausted for this ledger; next falsifiable layer is **exit / timing**, not another Long feature peek on this charter.

**Owner lock (post-STOP):** Claude track accepted; Gemini Precision-as-bailout **rejected** as tier bleed — Precision juices a viable Horizon book, does not recover H4 deficit.

**Next charter (dual-judge OPEN):** [horizon-exit-mfe-decay-charter.md](horizon-exit-mfe-decay-charter.md) — ACCEPT WITH REVISIONS applied; Step 0 unlocked.

---

## Related

| Doc | Role |
|---|---|
| [horizon-path-density-charter.md](horizon-path-density-charter.md) | Full record + Step 0 / Peek 1 tables |
| [horizon-exit-mfe-decay-charter.md](horizon-exit-mfe-decay-charter.md) | Next — exit / MFE-decay (**OPEN**, dual-judge locked) |
| [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | Why path density was next |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Cascade map |
