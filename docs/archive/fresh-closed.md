# Fresh closed — event-causal cash MIS

**Market:** NSE India, Nifty 100, intraday cash MIS  
**Status:** **CLOSED.** Blueprint §14 capability FAIL for directional Nifty-100 MIS under the fresh hypothesis.  
**Date of close:** 2026-08-16 (M4R-b)  
**This branch:** summary only. `src/horizon/fresh/` is not present.

Fresh replaced the production ranker with event-causal rules (first-crosses, rejects, fades), opportunity gating, and vertical-only disaster stops. The question was whether a *selected* sleeve could pay 20 bps. It could not.

---

## What was established

India **fades** intraday rather than continues. Every continuation rule tested negative. Reversion rules were fold-consistent in sign.

The fade is **real and too small**.

| Rule (authority M4R) | Side | Drift | CI upper bound |
|---|---|---|---|
| `prior_day_high_reject` | Short | **+6.2 / +7.8 bps** | ≈ +16.3 / +16.8 |
| `gap_fill_short` | Short | +6.8 / +4.4 bps | below hurdle |
| `vwap_loss` | Short | +3.2 / +5.2 bps | below hurdle |

Best CI upper bound ≈ **+17 bps** against a **20 bps** round trip. Validation power was not the issue (K4 MDE 9–13 bps on 8/8 folds). The effect is about a third of the friction it must pay.

---

## M4R-b — the capability FAIL

Pre-registered falsification on the winning sleeve (`prior_day_high_reject` Short), vertical-only, disaster SL 500 bps, folds A+B.

| Gate | Result |
|---|---|
| Selector IC | **0.022 / 0.023** vs required **0.054** to breakeven at 20 bps (~40% of need) |
| Admitted gross K4 | Fold A PASS (pool property — all-events also PASS); Fold B INCONCLUSIVE |
| EV_net at row-level `c_eff` | Neither fold clears CI LB > 0, even though median `c_eff` is **~7–8 bps** (liquid tail is cheaper than 20) |

Lowering the tax is not enough when selection cannot concentrate the +7 bps drift. Capacity on the liquid tail is feasible and irrelevant.

An earlier M5 K3/K4 FAIL was **vacated** (harness could not have passed: Stage C had no directional feature, scrambled clock, missing calibrator). The repaired Long-continuation stop and M4R-b stand on better ground.

---

## Two design findings that outlive the product

**Tight barriers destroy thin drift.** On identical rows, barrier-race gross was −10.6 / −5.3 bps against barrier-free drift of −5.3 / +4.7 bps. A 100 bps stop inside ~125 bps session σ is triggered by noise. Event books on this desk use **disaster clips and position caps**, not tight stops.

**Per-fold 95% LB>0 was unpassable at the intended fire rate.** A true +10 bps \(EV_{net}\) needed ~1,150 clustered trades (~4.6 fires/session) against a 1–4/day design. Authority moved to a **pooled** session-block CI plus a fold sign test.

---

## Transferable sentence

Fade is the Indian intraday fact. It does not pay cash-MIS friction, and a selector with IC 0.022 cannot close a 13 bps gap. Do not reopen Stage C, geometry grids, or Precision-as-bailout on this contract.

**Do not:** scan other event types in the same peek; treat M5's vacated FAIL as market evidence; remount continuation.
