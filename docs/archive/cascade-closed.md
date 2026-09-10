# Cascade closed — Regime, Horizon, Precision

**Market:** NSE India, Nifty 100, intraday cash MIS  
**Status:** **CLOSED as a product.** Production map frozen. Do not remount Top-K, 90-minute vertical, or 60/30 barriers.  
**Date of close:** 2026-08-16 (EV-net rebuild hard-stop); Regime search closed 2026-08-11  
**This branch:** summary only. The cascade source tree is not present.

The cascade asked whether a three-tier stack — daily/intraday regime, cross-sectional ranker, 1-minute timing — could pay cash-MIS friction on Nifty 100 names. It could not. Lowering cost, redrawing barriers, and tightening admission all failed to produce a book.

---

## Architecture (frozen map, not a build plan)

| Tier | Role | Outcome |
|---|---|---|
| **1 Regime** | Pre-open daily rules + 15m Nifty HMM sleeve routing | Architecture search **CLOSED**. Demoted to a frozen soft overlay. Not a cleared edge engine. |
| **2 Horizon** | Long/Short LightGBM rankers, Top-K, triple-barrier labels | Path quality never cleared economics. Unconditional eligible \(EV_{net}\) **−20…−22 bps**. |
| **3 Precision** | 1m fill / skip on the Top-K registry | Could not monetize a registry that rarely supplied winning paths. Escalated upstream; no further Precision knobs. |

Friction settled at working **20 bps** round trip (archive stress 30). Statutory+broker cash MIS is ~5–6 bps; liquid/mid total ~15–20. Cutting the haircut did not clear the book.

---

## What failed, in order

### Regime (A0, 2026-08-11)

Intraday architecture shot A1 failed holdout 2021 on both long and short I1/I5. Emission-add search already closed. Daily stayed a soft overlay. **Do not reopen Regime search** to rescue a later book.

### Precision (WS0/WS1)

On Fold A, Phase-1 net was **−16 bps**. No-chase lifted that by ~3 bps and still missed absolute zero. ~88–93% of fires had a non-winning triple-barrier label. The 1-minute layer was not under-monetizing good paths; the registry was not supplying them.

### Horizon levers (all closed, no merge)

Each charter spent one peek (or zero) and stopped. None is a salvage path.

| Ledger | Question | Answer |
|---|---|---|
| Cost realism | Does `c*=20` (vs archive 30) clear dual-fold economics? | **No.** Stop cost search. |
| Path density | Does a travel-adequacy feature densify Top-K paths? | Travel is real; economics fail; sequential freeze. |
| TP-floor | Does Long TP 60→50 capture near-miss MFE? | H3-B regresses; TB+1 flat; H4 still ~−14 bps. |
| Short architecture | Listwise / two-head / coarser universe for Short H5? | Listwise **FAIL** on holdout. Short sleeve stays disabled. |
| Admission | Can a conviction floor narrow Top-K? | **Tautology** — P80 rejected 0 Top-K rows. |
| Path-quality veto | Can `P(SL)` reject the worst Top-K names? | Rejects mass, does **not** raise admitted vs rejected TB+1. |
| **EV-net rebuild** | Is any of ≤3 Long geometries feasible after 20 bps? | **Hard-stop @ 0/3 peeks.** CI UB of unconditional \(EV_{net}\) **≤ −17 bps** on every candidate. |

The EV-net stop is the cascade's terminal economics: travel exists (mean MFE ~43–54 bps); after 20 bps the eligible pool is still deeply negative. Geometry redraw on the same contract is forbidden.

---

## Transferable sentence

A high-turnover cash-MIS book on liquid Indian names cannot outrun 15–20 bps of friction with a 5–8 bps drift. Rankers, vetoes, and 1-minute timing do not change the numerator. See [inherited-learnings.md](inherited-learnings.md) for the required-skill identity this programme published too late.

**Do not:** remount production Top-K / H=6 / 60–30; spend Precision peeks on a moving book; treat any cascade gate PASS as cascade-ready.
