# RT Cost Realism Re-Derivation — STOP-MEMO (v1)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Single-variable round-trip `c` re-derivation; floors as `k × c`; Horizon A+B re-measure under locked v2 defaults  
**Status:** **STOP-MEMO — cost charter CLOSED**; dual-judge **ACCEPT STOP WITH REVISIONS** — next = path-density charter  
**Date:** 2026-08-13  
**Charter:** [rt-cost-realism-re-derivation-charter.md](rt-cost-realism-re-derivation-charter.md)  
**Authority:** [cascade-cost-horizon-physics-charter.md](cascade-cost-horizon-physics-charter.md)  
**Outcome judges:** [Claude Sonnet](9f8909d2-7a13-474b-b3cf-532e73c906e0), [Gemini Flash](ee0ccc6e-8060-463f-8e06-d82a83e9e76a)  
**Depends on:** [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md) (path-EV STOP), [triple-barrier-verdict.md](../triple-barrier-verdict.md) (v3 `c` amend)  
**Trigger:** Peek 1 under signed `c*=20` — Short dual-fold H5 FAIL; H4 negative both sleeves; ladder forbids auto-promote to 15  
**A+B peeks spent:** **1 / 3** — remaining budget **frozen unused** (do not spend on 15/10)

---

## One-line

Signed working friction **`c*=20` bps** is more realistic than archive 30, but **does not clear** dual-fold Horizon economics — stop cost search; next charter = **path density**.

---

## What was proven / disproven

| Claim | Outcome |
|---|---|
| 30 bps is a stress floor, not typical liquid Nifty-100 MIS | **Supported** — Step 0 statutory+broker ~5–6 bps across Zerodha/Groww/Kotak; liquid/mid total ~15–20 |
| `c*=20` + floors `60/50/30` is a valid working identity | **Signed** (dual-judge); kept as friction lock |
| Lowering `c` alone clears dual-fold economics / H4≥0 | **Disproven** on peek 1 |
| Promote ladder to 15 after peek-1 FAIL | **Rejected** — ladder requires 20 to clear first |
| Single-`c` is secretly all-liquid Top-K | **Disproven** — ADVt ~30–36% Top-K mass in thin tercile |
| Horizon-path PASS / cascade-ready from cost change | **Forbidden / unproven** |

---

## Terminal evidence (peek 1)

**Logs:** `logs/horizon_cost_c20_peek1_fold_a.txt` · `logs/horizon_cost_c20_peek1_fold_b.txt`

| Gate | Long A | Long B | Short A | Short B | Dual-fold |
|---|---|---|---|---|---|
| **H5** | PASS | PASS | **FAIL** | **FAIL** | Long PASS · **Short FAIL** |
| H2 | FAIL | PASS | PASS | PASS | Long FAIL · Short PASS |
| H4 @ 20 | −17 bps | −14 bps | −13 bps | −16 bps | **neg** |
| H4arch @ 30 | −27 bps | −24 bps | −23 bps | −26 bps | neg |
| Top-K TB+1 | 10.9% | 8.9% | 12.8% | 13.0% | ≪ ship |
| ADVt lo share | 36% | 30% | 33% | 33% | ~⅓ thin |

Short H5 **gate flipped** PASS→FAIL vs Horizon v2 peek-3 baseline under 30 bps (re-labeled path-EV + new floors; CIs overlap — not a large demonstrated regression).

---

## Dual-judge outcome verdict (2026-08-13)

**Judges:** [Claude Sonnet](9f8909d2-7a13-474b-b3cf-532e73c906e0), [Gemini Flash](ee0ccc6e-8060-463f-8e06-d82a83e9e76a)

| Axis | Gemini | Claude | Consensus |
|---|---|---|---|
| Overall | **ACCEPT STOP** | **ACCEPT STOP WITH REVISIONS** | **ACCEPT STOP WITH REVISIONS** |
| STOP discipline | 10/10 | 8/10 | Keep freeze; fix ladder vs stop-criteria contradiction |
| Peek-1 read | 9.5/10 | 7/10 | Economics not cleared; Long H5 under real `c` still leaves thin Top-K/H4 |
| Keep `c*=20` | 9.5/10 | 8/10 | **Keep 20** working; 30 archive — do not revert |
| Next workstream | path-density | path-density | **Path-density new charter** (primary) |

| Lock | Decision |
|---|---|
| STOP | **Accepted** — peeks 2/3 stay frozen |
| `ROUND_TRIP_COST` | **Keep 0.0020** (friction-realism input, not ship threshold) |
| 15 / 10 / 25 | **REJECT** under this charter |
| Primary next | **Path-density new dual-judge charter** |
| Not next | Liquidity-tier `c`, Precision WS2, Regime, cost shopping |

**Reject (next 30 days):** cost ladder reopen · revert to 30 as working · Horizon feature/label reopen on this authority · Regime/Precision reopen · cascade-ready / Horizon-path PASS claims · Short lever re-chase from v2 reject list · pooled Long+Short / Fold C / hyperparam grid

**Claude MUST-FIX (done or tracked):** reconcile “may promote 15” vs ladder (done in charter); soften Short “regressed” language (done); cascade overview H=6 (done); label `c*=20` as friction input not economics clear (done in `triple_barrier.py`).

---

## Locked carry-forward

| Item | Lock |
|---|---|
| Working `c*` | **0.0020 (20 bps)** — signed friction identity |
| Archive stress `c` | **0.0030 (30 bps)** companion (`ARCHIVE_ROUND_TRIP_COST`) |
| Floors | Long TP **60** / Short TP **50** / SL **30** (`3× / 2.5× / 1.5×`) |
| Multiples / H=6 / Horizon v2 feature locks | **Frozen** — unchanged |
| Cost peek ledger | **1/3 spent; 2/3 frozen** — no peek 2 at 15, no peek 3, no 10 |
| Regime / Precision WS2 | **CLOSED / blocked** |
| Economics clear under cost charter | **NO** |

---

## Escalate / leave open

1. **Path-density new dual-judge charter** — **primary next** (dual-judge locked 2026-08-13) → **OPEN:** [horizon-path-density-charter.md](horizon-path-density-charter.md). Long clears H5 under realistic `c` while Top-K TB+1 ~9–13% and H4 stay negative → binding leak is path travel density, not friction calibration.  
2. Precision Phase 1 book re-measure — still **blocked** until upstream path gates clear under a future charter.  
3. Liquidity-tiered `c` — **not** next; would need pre-registered ADV rule in a separate new charter (post-hoc tiers still forbidden).

---

## Explicit do-not (post-stop)

- Peek 2 at **15** or silent jump to **10**  
- Spend remaining cost-charter peek budget on this ledger  
- Reopen Horizon v2 features / labels / H / exhausted v2 peeks  
- Reopen Regime or Precision WS2  
- Invent new TP/SL multiples  
- Claim cascade-ready / Horizon-path PASS / book PnL from `c*=20` alone  
- Soft-edit this memo into REVISE — it is **terminal for this cost charter**

---

## Code posture

| Constant | Value | Role |
|---|---|---|
| `ROUND_TRIP_COST` | `0.0020` | Signed working friction |
| `ARCHIVE_ROUND_TRIP_COST` | `0.0030` | Stress companion (H4arch) |
| Derived floors | `3× / 2.5× / 1.5×` | Auto from working `c` |

Eval extras `H4arch` / `ADVt` stay report-only. Production path uses working `c*` floors; do not treat peek-1 FAIL as a reason to silently revert to 30 without a new charter.
