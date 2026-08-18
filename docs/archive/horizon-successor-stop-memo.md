# Horizon Successor — STOP memo (2026-08-18)

**Decision:** **Stop the product hunt.** Do not buy vendor Nifty quotes. Do not open S5. Production cascade stays frozen.  
**Date:** 2026-08-18  
**Authority:** [horizon-successor-architecture-blueprint.md](../next/horizon-successor-architecture-blueprint.md) Rev 3  
**Last-trade peek:** [horizon-successor-s1-v2-zenodo-memo.md](horizon-successor-s1-v2-zenodo-memo.md) (`s1_v2_zenodo.log`)

This is **not** the locked dual-FAIL sentence (V2p-c FAIL **and** S6 FAIL). V2p-c **PASS**ed in range space. Quote V2 was never peeked. Last-trade V2 **FAIL (report)** plus microstructure judgment is enough to stop P1 as a remaining-session option sleeve and to waive S4-P1.

---

## What was earned vs what did not print

| Track | Verdict | Product? |
|---|---|---|
| Cash directional MIS (Fresh) | CLOSED | No |
| V1 / V1n (range head vs VIX / HAR) | PASS | Forecast, not a trade |
| V2p residual>0 | CLOSED (empty) | No |
| V2p-c (selected remaining-session range vs implied) | PASS, paired CI **[+19.6, +32.6] bps** | Range-space only |
| Last-trade V2 (same sessions, 09:45→15:15 ATM straddle, spread ≡ 0) | FAIL (report), pooled CI **[−1.9, +3.1] bps**, mean **+0.6** | No |
| C0 at 3 bps | PASS | Sleeve bound only |
| C0-ladder / SSF | P2 STOP, `c_max` ≈ **4.5 bps** < forward RT ≈ 5–10 | No |
| S6 T+3 at c=6 | INCONCLUSIVE, CI **[−20.5, −0.0]**, MDE 10.2 | No |

V2p-c and V2 are different objects. The head says this afternoon’s **Nifty range** is smaller than VIX-implied session range on the selected days. The option trade asks whether a **multi-day ATM contract** decays over 5.5 hours. It did not, even with bid = ask = last-trade. Fold B (2019 weeklies) was **+0.1 bps** — tenor mismatch is not a 2018-only excuse.

Quoted mids are not expected to move that CI by the **~2–3 bps** needed for LB > 0. Round-trip spread would then kill V3. Do not purchase the chain to audit that.

---

## What stops

- **S4-P1** vendor bid/ask and authority V2 / V3. Charter remains an acquisition spec; it is **not** the next spend.
- **S5** product book. There is no live instrument.
- **S4-P2** SSF panel (already unopened).
- Further S6 years or futures to manufacture power.
- Name-option V2, EOD bhavcopy as remaining-session V2, retuning V2p-c, 0-DTE / BankNifty / opposite-tercile long vol as salvage.

## What stays

- Production Regime → Horizon → Precision **frozen**. No Top-K / H=6 / 60–30 remount.
- V2p-c definition frozen. Zenodo parquet and harnesses stay as the audit trail.
- Range-head result (V1 / V1n / V2p-c) stays on the ledger as **range** science, not as a short-premium book.

A later remaining-session option product (true same-day / 0-DTE) needs a **new charter** and a later sample. That is not unfinished successor work.

---

## Forbidden next steps

Buy TrueData / GDFL / NSE-licensed 2018–19 quotes for this V2. Fill `nifty_option_snapshots.parquet` from last-trade or bhavcopy. Unblock `eval_horizon_m9_v2_stub.py`. Scan 10:00 / q75. Reopen M4R event search or cash Stage C.

## Artifacts

- `data/GOLDEN_PARQUET/s1_v2pc.log`, `s1_v2_zenodo.log`, `s2_c0.log`, `s2_c0_ladder.log`, `s6_multiday.log`
- `data/GOLDEN_IV/nifty_option_snapshots_zenodo.parquet` (report-only; not the quote store)
