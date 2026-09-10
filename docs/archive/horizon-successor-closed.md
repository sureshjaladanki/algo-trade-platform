# Horizon Successor closed — remaining-session vol and fade

**Status:** **Product hunt STOPPED** (2026-08-18). Not the dual-FAIL sentence of an earlier draft; microstructure plus a cost ladder was enough.  
**This branch:** summary only. Successor / M9 source is not present.

Successor asked whether the one Fresh finding that *was* real — fade, plus a remaining-session range forecast — could be monetized after cash MIS was closed. Range **yes**. Premium **no**. Futures fade **no**. Multi-day fade **inconclusive**, not a product.

---

## Range science (kept as a forecast, not a trade)

A remaining-session range head is incremental to VIX and to HAR, and incremental to name-level ATM IV (M9 V1 dual-fold PASS). Selected remaining-session range versus implied (V2p-c):

| | Result |
|---|---|
| Pooled paired CI | **[+19.6, +32.6] bps** |
| Mean | **+26.1 bps** |
| Sign | 2/2 folds |

This says: on selected days, this afternoon's **Nifty range** is smaller than VIX-implied session range. It does not say a short-premium book makes money.

On this desk the head is **position sizing and event-day skip only**. It never picks a side and never sells premium.

---

## What did not print as a product

### P1 — remaining-session short vol (last-trade V2)

Same selected sessions, 09:45→15:15 ATM straddle, **spread set to zero** (bid = ask = last-trade).

| | Result |
|---|---|
| Pooled mean | **+0.6 bps** |
| Pooled CI | **[−1.9, +3.1] bps** |
| Fold B (2019 weeklies) | **+0.1 bps** |

Quoted mids are not expected to move that CI by the ~2–3 bps needed for a lower bound above zero. Round-trip spread would then kill a V3. **Do not buy vendor option marks** to audit this. Index-option acquisition (S4-P1) is not the next spend.

### P2 — same-session fade at futures friction

Sleeve: `prior_day_high_reject` Short, disaster clip (not drop), pooled `k5`.

| Haircut | Pooled CI | Verdict |
|---|---|---|
| c = 3 bps | [+1.5, +8.9] | PASS (historical C0 only) |
| c = 5 bps | [−0.5, +6.9] | pooled LB FAIL |
| c = 8 bps | [−3.5, +3.9] | FAIL |

**`c_max` ≈ 4.5 bps.** Forward single-stock / index futures round trip after April 2026 STT is **~5–12 bps**, above that bound. Sample-era futures STT was half of today's — do not reprint 2017–2022 costs as a live hurdle. **Do not download an SSF panel.**

### S6 — same rule held to T+3

T+3 at c = 6 bps: pooled CI **[−20.5, 0]**, MDE **10.2** ≥ 6 → **INCONCLUSIVE**. Sign 2/6. Companions T+1/T+2/T+5 are the same sign family. The interval sits on the non-positive side; do not add years or buy futures to manufacture power.

---

## Transferable sentence

The range forecast is a sizing tool. It is not a remaining-session option sleeve, and the fade does not survive futures friction or a T+3 hold. Cash directional, remaining-session vol, and same-session fade are **closed**. Do not spend a peek on Stage C, geometry grids, name-option marks, or futures history.

**Do not:** fill a quote store from last-trade or bhavcopy; open S5; retune V2p-c to salvage V2; treat S6 INCONCLUSIVE as a pass.
