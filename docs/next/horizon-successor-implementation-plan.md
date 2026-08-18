# Horizon Successor — Implementation Plan

**Authority:** Implements [horizon-successor-architecture-blueprint.md](horizon-successor-architecture-blueprint.md) Rev 3  
**Status:** **STOPPED** — directional cash MIS **CLOSED**. P1 `residual>0` **CLOSED**. **V2p-c PASS** (range). Last-trade V2 **FAIL (report)**. **S4-P1 waived** (do not buy quotes). **S2 C0 PASS** at 3 bps; **S4-P2 SSF not earned**. **S6 T+3 INCONCLUSIVE**. Production cascade frozen. Memo: [horizon-successor-stop-memo.md](../archive/horizon-successor-stop-memo.md). This plan does not continue Fresh M6–M8.  
**Date:** 2026-08-18 (Rev 3)  
**Constraint:** Cash `c* = 20` is a stress / archive identity only. P1 uses index-option friction (V2/V3). P2 uses haircut; SSF is stopped at the forward schedule.

> **Where this plan stands.** V1-index and V1n **PASS**. V2p residual>0 is **CLOSED**. **V2p-c PASS** in range space. Last-trade V2 **FAIL (report)**; vendor quotes are **not** the next spend. C0 **PASS** at 3 bps does **not** earn SSF. S6 T+3 is **INCONCLUSIVE**. Do **not** acquire name-option marks, EOD bhavcopy as V2, SSF history, or a licensed 2018–19 Nifty chain for this V2.

---

## How to read this plan

This is a **milestone map**, not a peek charter. Each milestone has a why, what to build, cleanup that travels with it, exit criteria, and a stop.

- Production Regime → Horizon → Precision stays **frozen**. Fresh `src/horizon/fresh/` is infrastructure, not a ship path.
- Fresh M6–M8 remain **archived scaffolding**. Do not “unblock” `eval_horizon_fresh_m6_admit.py`.
- Peek budgets and dual-judge text belong in a **follow-on charter** derived from a PASS here — not in this document.
- Cleanup is scheduled inside milestones.
- Consume the **repaired** Fresh library from the 2026-08-17 implementation review (`apply_purge_date_filter`, disaster **clip**, `k5_pooled`). Do not reimplement those gates.

---

## The essence (why this plan exists)

Horizon Fresh earned a §14 FAIL for directional Nifty-100 MIS cash. Two assets survived: a range head (Spearman ~0.61) and a thin Short-fade drift (~+7 bps). Fresh M9 ranked those as “buy name IV, then sell name options.” That acquisition happened. Name V1 PASSed because lagged EOD ATM barely prices remaining-session range. Fresh’s next action is name-option V2, blocked on marks.

This plan does **not** follow that spend. It tests the **remaining in-repo** kill-switches:

1. **P1 — Index vol:** V1-index already shows `range_q50` incremental to VIX (`b_q50` ≈ 0.60 / 0.61). Does it still beat a **causal HAR**? If yes, does selected-session \((R - R^{\mathrm{imp}})\) have a positive CI LB (V2p)?  
2. **P2 — Fade vs cheaper \(c\):** does the frozen Short-reject pool clear pooled \(EV_{net}\) at 3 bps on the **8 folds** M5P paid for (R2017–R2022 still never run)?

Expected outcome prior (not a gate): P1 V1n is the more likely FAIL (VIX already embeds HAR; name V1 does not change that prior). P2 C0 is the more likely INCONCLUSIVE (power vs ~4 bps net). Either way, the programme learns in days, not after a marks project.

---

## Non-negotiables

| Lock | Rule |
|---|---|
| Do not remount | Top-K / H=6 / 60–30, cash Stage C peeks, geometry sweep, Precision-as-Horizon-bailout, Regime I1/I5 search, new event rules after M4R STOP (including N-bar exhaustion), name V2 stub |
| In-repo first | S1 remainder and S2 must complete (or STOP) before **index** option marks or SSF download. Name marks are not in this plan |
| Nested V1 | P1 V1 is **PASS**. Remaining P1 authority is **V1n** (HAR) then **V2p**. V0 and name V1 are not evidence |
| C0 pool | Unconditional frozen sleeve, not F1’s 70–96% admit set. First live caller of `k5_pooled` |
| MDE | Every gate prints MDE next to the point estimate |
| Production | No cutover in this plan. Ship is a later charter after P1 V2/V3 or P2 S2 |

### Global STOP language

If **V1n** FAIL dual-fold on a passable harness → stop P1; do **not** salvage with name V1 PASS.  
If **C0** FAIL at 3 bps (pooled + sign test) on a passable harness → stop P2; do not download SSF.  
If both stop → programme FAIL sentence in the blueprint; next is outside this family.

Before invoking FAIL, run the Fresh four-point harness checklist (gate passable, inputs can carry the effect, MDE, pipeline wired) plus: the statistic is the one the product named; the hurdle is the instrument’s, not flat cash 20.

---

## Milestone map (at a glance)

| ID | Name | Primary outcome | Hard stop if… |
|---|---|---|---|
| **S0** | Posture & freeze | Directional cash closed in the working set; P1/P2 package boundary; name V2 stub frozen | Cannot reprint M4R-b / M3 K1 / V1-index numbers from existing logs |
| **S1** | P1 V1n + V2p | Index-vol remaining kill-switch on `^NSEI` + `^INDIAVIX` | V1n FAIL. residual>0 **CLOSED** (empty set, two clocks) |
| **S2** | P2 C0 cost bound | 8-fold pooled fade \(EV_{net}\) at 3/5/8 bps | C0 FAIL at 3 bps (historical). **C0-ladder FAIL at 5** → SSF not earned |
| **S3** | Branch | P1 = one peek (V2p-c); P2 = STOP; S6 = new family | Programme FAIL only after V2p-c **and** S6 FAIL |
| **S4** | Earned data | **Index** option marks only after **V2p-c PASS**. SSF panel **unopened** | Acquisition without a cheap PASS; EOD bhavcopy as remaining-session V2 |
| **S5** | Product book | Instrument-specific admit/sizing — **not** Fresh M6 | Building S5 without a live product |
| **S6** | Multi-day fade | Same frozen rule, T+1…T+5 close-to-close, pooled K5 at c = 6 | LB ≤ 0 at c = 6 → programme family exhausted |

**S1 remainder and S2 run in parallel.** S0 is a short freeze, not a research peek. V1-index is already the S1 V1 exit.

---

## S0 — Posture, freeze, and package boundary

### Why

The working tree now presents Fresh **name V2 / `option_marks_daily.parquet`** as the natural “next,” with M6–M8 still listed as blocked cascade cutover. That ranking is what this programme is replacing. Make the workspace match the strategy before spending peeks.

### Build

1. Add `src/horizon/successor/` (or keep P1 under `src/horizon/m9/` and P2 under `src/horizon/fresh/` — **one** home per product, documented in a 20-line README). Prefer extending `src/horizon/m9/` for P1 (V1-index code already exists) and a thin `src/horizon/successor/fade_bound.py` for P2 rather than a speculative framework.  
2. Write a freeze note at the top of the successor README: production cascade frozen; Fresh M6 harness stays hard-exit; Precision bridge not on the path; **`eval_horizon_m9_v2_stub.py` is Fresh Track A ledger, not P1 V2**.  
3. Confirm reprint paths: M3 K1, M4R drift ledger, M4R-b F1/F2, V0, **V1-index** (`m9_v1_index.log`), name V1 memo (report-only). Do not re-run those as authority.

### Cleanup / refactor

| Action | Detail |
|---|---|
| Do not delete Fresh | `src/horizon/fresh/` is the range head + folds + gates + `c_eff` library |
| Do not “fix” M6 | Leave `eval_horizon_fresh_m6_admit.py` hard-exit |
| Do not populate name marks | `option_marks_daily.parquet` / V2 stub stay frozen. M9-0 ATM store is ledger-only |
| Quarantine language | Fresh implementation plan remains the **historical** M0–M9 map; this file is the active map |

### Exit criteria

- [x] Successor README states P1/P2, in-repo-first, V1-index PASS, name V1 report-only, and the freeze  
- [x] Pointers to authority logs (M3, M4R, M4R-b, V0, V1-index) without re-peeking  
- [x] Tests still green: `poetry run pytest tests/horizon/fresh tests/horizon/test_m9_range.py` (plus successor / HAR / V2p unit tests)

### Stop

Cannot locate the M4R-b / M3 / V1-index artifacts that this plan cites → fix infra, do not design a new Stage C.

---

## S1 — P1 index vol: V1n, V1κ, V2p

### Why

Fresh treated `eval_horizon_m9_v1_index.py` as a rehearsal. Rev 1 of this plan asked to publish it as P1 authority. That run is **done**: dual-fold **PASS**, `b_q50` ≈ 0.60 / 0.61, no `volume_z`, log `data/GOLDEN_PARQUET/m9_v1_index.log`.

Name V1 (`b_q50` ≈ 0.95, `b_imp` ≈ 0.14) does **not** close P1. It is the stale-control lesson: a weak implied makes the head look incremental. V1-index used same-session VIX and the coefficient dropped from ~1.0 (V0) to ~0.60. **V1n** asks whether HAR takes the rest.

Index volume is identically 0 — keep `INDEX_OPPORTUNITY_FEATURES` without `volume_z`. Do not invent participation.

### Already complete (do not re-peek as authority)

- [x] **V1** dual-fold (A+B) published — `b_q50` ≈ 0.60 / 0.61, p ≪ 0.05 (`m9_v1_index.log`)

### Build

1. **V1n nested HAR** — add a causal Nifty remaining-range baseline that a market-maker already has, for example:  
   - trailing 1d / 5d realized range (or Parkinson) scaled by \(\sqrt{f}\), computed only from information available at the decision bar;  
   - include it in the OLS: realized ~ implied + HAR + `range_q50`.  
   Authority: `range_q50` still > 0 and significant.  
   Extend `incremental_range_ols` to 3+ regressors rather than copy-paste (it is still hardcoded `[1, implied, q50]`).  
2. **V1κ** — reprint V1 at \(\kappa \in \{1.4, 1.6, 1.8\}\) report-only.  
3. **V2p** — only if **V1n** PASS. Pre-register a residual threshold (e.g. residual > 0, or residual > train-fold q75 — pick **one** before the peek). Session-block CI on mean\((R - R^{\mathrm{imp}})\) for selected Nifty sessions. Publish MDE and expected session count first (`declare_admit_power` analogue). Apply `apply_purge_date_filter` on train (review: this was display-only until 2026-08-17).  
4. Clock control: remaining range falls with `bars_to_mis`. Publish a **within-clock** residual check so V1n is not a TOD artefact (same lesson as Fresh K1).  
5. Do **not** call `eval_horizon_m9_v2_stub.py`. That harness is a name-level T→T+1 EOD hold, blocked on marks, clock-mismatched vs remaining-session.

### Cleanup / refactor

| Action | Detail |
|---|---|
| Reuse Stage B trainer | Do not bolt onto `GBMHorizonModel` |
| Reuse `incremental_range_ols` | Extend to 3+ regressors rather than copy-paste |
| V0 / name V1 stay report-only | Do not promote `b_q50 ≈ 1` or name `b_q50 ≈ 0.93` into a P1 PASS |
| Feature hygiene | Index path must not use `volume_z` |
| Purge | Real `apply_purge_date_filter`, not a printed `train_end_disp` |

### Exit criteria

- [x] V1 dual-fold (A+B) published with coef, SE, p, n, R² — **PASS** (`m9_v1_index.log`)  
- [x] V1n published on the same folds — **PASS** `b_q50`=+0.569 / +0.616 (`s1_v1n.log`)  
- [x] V1κ report-only table — all three κ PASS; `b_q50` unchanged  
- [x] If V1n PASS: V2p with pre-declared threshold, session count, MDE, three-way verdict — **INCONCLUSIVE** (3 sessions/fold, thin)  
- [x] V2p-b clock repair (09:45, residual>0) — **INCONCLUSIVE** (3 / 2 sessions). Log `s1_v2pb.log`. Do not scan other clocks.  
  — [horizon-successor-s1-v2pb-memo.md](../archive/horizon-successor-s1-v2pb-memo.md)  
- [x] V2p-c (09:45, bottom tercile, paired `R_imp − R`) — **PASS**. Log `s1_v2pc.log`.  
  — [horizon-successor-s1-v2pc-memo.md](../archive/horizon-successor-s1-v2pc-memo.md)  
- [x] Written memo: PASS / FAIL / INCONCLUSIVE against blueprint §8 — [horizon-successor-s1-memo.md](../archive/horizon-successor-s1-memo.md)  

### Stop

**V1n FAIL** → P1 STOP. Do not switch the story to single-name options. Do not treat name V1 PASS as salvage.  
**V1n PASS but V2p CI LB ≤ 0** → incremental information without sign economics; P1 STOP.  
**INCONCLUSIVE** (conversion isolated to \(\kappa\), or MDE > effect) → repair; do not record FAIL.

---

## S2 — P2 fade cost-bound: C0

### Why

M4R-b F2 used folds A+B and a Stage C admit set that was not sparse (69.8% / 96.2%). The question “does +7 bps clear *futures-like* friction?” was never asked on the 8-fold design M5P already paid for. The implementation review recorded the same gap: R2017–R2022 were pre-registered and **not run**.

This milestone does **not** need SSF files. Haircut the existing vertical-only Short-reject paths.

`k5_pooled` is correct and unit-tested but has **no live caller** (M6 was the intended consumer and is blocked). **S2 is that caller.** Do not reimplement pooled K5.

### Build

1. Freeze sleeve: `prior_day_high_reject` Short, transition events. Primary table = **unconditional pool** (A∩B optional as a companion column, not the gate).  
2. Geometry: MIS vertical-only + disaster **clip** to `−sl_floor` (implementation review: M4R-b originally **dropped** the left tail; FAIL still stands, but C0 must not repeat the bias).  
3. Folds: A+B + R2017–R2022 (same `ROLLING_FOLDS` / purge as M5P). Apply `apply_purge_date_filter` (review: this was display-only until 2026-08-17).  
4. Costs: **3, 5, 8** bps as scalars on path return (not `c_eff` — this is an instrument counterfactual). Also reprint row-level cash `c_eff` as a companion so F2 is not lost.  
5. Gate: Fresh `k5_pooled` + sign test at **c = 3**. Publish per-fold points and MDEs. Pre-declare expected event/session counts (`declare_admit_power`).  
6. Companions (report-only): `vwap_loss` Short, `gap_fill_short`. Do not pick a new winner after seeing the log. Do **not** add N-bar exhaustion.  
7. Do **not** fit Stage C.

### Cleanup / refactor

| Action | Detail |
|---|---|
| Reuse `path_ev_net(..., cost=)` | Array or scalar; already M5P-b |
| Reuse `k5_pooled` | First production caller; unit tests already in `tests/horizon/fresh/test_m5pb_gates.py` |
| Reuse event registry | Frozen M4R rules; no N-bar exhaustion |
| Keep `m4r_drift_ledger.log` | Authority for unconditional sign; C0 is the economics reprint |

### Exit criteria

- [x] Pre-registration note (sleeve, costs, folds, pooled-K5 rule) written **before** the run  
  — [horizon-successor-s2-c0-preregistration.md](../archive/horizon-successor-s2-c0-preregistration.md)  
- [x] C0 table: pooled mean, CI, sign count, MDE, n sessions, at 3/5/8 bps  
  — pooled c=3 CI **[+1.5, +8.9] bps**, sign **6/6**, MDE 3.7 (`s2_c0.log`)  
- [x] Disaster-stop **clip** confirmed (no dropped left tail) — 379 rows at floor  
- [x] Memo: PASS / FAIL / INCONCLUSIVE — [horizon-successor-s2-c0-memo.md](../archive/horizon-successor-s2-c0-memo.md)  

### Stop

**C0 FAIL at 3 bps** (pooled CI LB ≤ 0 **or** sign test fail, on a passable harness with MDE < 3 bps) → P2 STOP; no SSF download.  
If MDE at 3 bps still exceeds 3 bps even on 8 folds → **INCONCLUSIVE**; say so; do not acquire SSF to manufacture power on a ~4 bps effect.

---

## S3 — Branch (Rev 3)

S3 (2026-08-18) named SSF as earned. **Superseded** the same day by architect review: C0 PASS at 3 bps does not clear forward SSF friction.

| Product | Status | Next |
|---|---|---|
| P1 | V1/V1n PASS; residual>0 **CLOSED**; **V2p-c PASS**; last-trade V2 **FAIL (report)** | **STOP** — do not buy quotes |
| P2 | C0 PASS at 3; **SSF not earned** | STOP at forward friction. Do not open S4-P2 |
| New family | T+3 c=6 **INCONCLUSIVE** | Do not buy SSF to manufacture power |

Do not merge P1 and P2 into one Horizon. Production cascade stays frozen.

### Exit criteria

- [x] Written branch decision — [horizon-successor-s3-branch.md](../archive/horizon-successor-s3-branch.md) (S3-day; ranking superseded by Rev 3)  
- [x] C0-ladder memo — [horizon-successor-s2-cost-ladder-memo.md](../archive/horizon-successor-s2-cost-ladder-memo.md) (`s2_c0_ladder.log`: c=5 CI [−0.5, +6.9], **P2 STOP**)  
- [x] V2p-c prereg — [horizon-successor-s1-v2pc-preregistration.md](../archive/horizon-successor-s1-v2pc-preregistration.md)  
- [x] V2p-c memo — [horizon-successor-s1-v2pc-memo.md](../archive/horizon-successor-s1-v2pc-memo.md) (**PASS**; `s1_v2pc.log`)  
- [x] S6 charter — [horizon-successor-s6-multiday-fade-charter.md](horizon-successor-s6-multiday-fade-charter.md)  
- [x] S6 memo — [horizon-successor-s6-multiday-fade-memo.md](../archive/horizon-successor-s6-multiday-fade-memo.md) (T+3 c=6 **INCONCLUSIVE**)

---

## S4 — Earned data (not the door)

### S4-P1 — Index option marks (earned by **V2p-c PASS**; **waived** — do not acquire)

**Charter:** [horizon-successor-s4-p1-index-marks-charter.md](horizon-successor-s4-p1-index-marks-charter.md)  
**V2 prereg (locked before marks):** [horizon-successor-s1-v2-preregistration.md](../archive/horizon-successor-s1-v2-preregistration.md)

Need for **V2/V3**: **Nifty** option bid/ask around the **decision clock** (09:45 remaining-session) and MIS flatten (15:15), not EOD settle. Expiry DTE ∈ [1, 10]. Forward STT **0.15% of premium** (Finance Act 2026, from 2026-04-01).

| Option | Use |
|---|---|
| Vendor **intraday** Nifty chain | Was required for authority V2. **Earned** by V2p-c PASS; **waived** after last-trade V2 FAIL (report). Do not buy |
| NSE index-option bhavcopy / FO reports | **Not acceptable** as a remaining-session mark (clock mismatch; same failure class as name V1 `b_imp` ≈ 0.14) |
| India VIX futures | Optional companion; not a substitute for Nifty options |

### Build

1. Vendor 09:45 + 15:15 Nifty ATM quotes for folds A/B test windows (2018, 2019). Same strike/expiry held through flatten.  
2. Materialize `data/GOLDEN_IV/nifty_option_snapshots.parquet` via `src.horizon.m9.index_option_store`.  
3. Coverage vs frozen V2p-c selection (`eval_horizon_successor_s4_p1_coverage.py`). Gate ≥ 70%.  
4. Only then run `eval_horizon_successor_s1_v2.py`. Hard-exits if the store is missing.

### Cleanup / refactor

| Action | Detail |
|---|---|
| Do not unblock the name stub | `eval_horizon_m9_v2_stub.py` stays Fresh Track A ledger |
| Do not populate name marks | `option_marks_daily.parquet` / M9-0 ATM stay frozen |
| Do not DIY bhavcopy | Clock-mismatched; forbidden as V2 |

### Exit criteria

- [x] Charter + V2 prereg written before any premium peek  
  — [horizon-successor-s4-p1-index-marks-charter.md](horizon-successor-s4-p1-index-marks-charter.md)  
- [x] Store contract + remaining-session PnL helper + coverage/V2 harness (hard-exit without marks)  
- [ ] `nifty_option_snapshots.parquet` present with source ≠ `nse_bhavcopy_bs` — **waived**  
- [ ] Coverage ≥ 70% of V2p-c selected sessions, both clocks — **waived** (Zenodo last-trade coverage PASSed; quote store not filled)  
- [ ] V2 peek under the locked prereg — **waived**; last-trade V2 FAIL (report) is the premium-space read  

### Stop

Using EOD bhavcopy or the name V2 stub as a remaining-session proxy → stop; that is not V2.

Do **not** start (or extend) single-name marks here. M9-0 ATM IV is ledger-only. Name IV is Phase-2 after **index** V3, same-session only.

Do **not** unblock `eval_horizon_m9_v2_stub.py`.

### Report-only companion — Zenodo last-trade (done; not S4-P1)

**Prereg:** [horizon-successor-s1-v2-zenodo-preregistration.md](../archive/horizon-successor-s1-v2-zenodo-preregistration.md)  
**Memo:** [horizon-successor-s1-v2-zenodo-memo.md](../archive/horizon-successor-s1-v2-zenodo-memo.md)

Public 1m last-trade (Bhat 2024, CC0) on the locked 2018–19 V2p-c sessions. Coverage PASS (A 100%, B 94.4%). V2 **FAIL (report)** pooled CI [−1.9, +3.1] bps. Bid = ask = close. This does **not** fill `nifty_option_snapshots.parquet` and does **not** earn V3. The product hunt **STOP**s here: do not buy vendor bid/ask. See [horizon-successor-stop-memo.md](../archive/horizon-successor-stop-memo.md).

### S4-P2 — SSF panel — **UNOPENED**

C0 PASS at 3 bps does **not** earn this. Forward SSF RT (STT 0.02% sell-side + spread + MIS exit) sits at ≈ 5–10 bps vs `c_max` ≈ 4.5. Leave unopened. The F&O eligibility / lot panel is earned only if **S6** PASSes (multi-day product), not by the intraday fade.

---

## S5 — Product book (not Fresh Stage D)

**Not opened.** S3 named no live product. See [horizon-successor-stop-memo.md](../archive/horizon-successor-stop-memo.md).

### P1 book

- Vega / premium cap per session  
- **Short premium is the default** after V2p-c PASS; long-vol stays off  
- Hard daily premium-loss cap; no new entries into a defined flatten window  
- Pooled economics gate analogue of K5 on **option** PnL, not cash `EV_{net}`

### P2 book

- Lot granularity vs sparse fires  
- F&O eligibility as-of  
- Vertical-only + disaster **clip** (not drop)  
- Concurrency / daily loss (reuse `admit.py` helpers if they fit; do not remount M5 Stage C)

### Explicitly not S5

- `geometry_argmax`  
- Precision on production Top-K  
- Cutover of `predict_horizon_gbm`  
- Conformal cash \(EV_{net}\) as if the book were still MIS cash names  
- Name-option OMS

---

## S6 — Multi-day fade (new family)

**Charter:** [horizon-successor-s6-multiday-fade-charter.md](horizon-successor-s6-multiday-fade-charter.md)  
**Memo:** [horizon-successor-s6-multiday-fade-memo.md](../archive/horizon-successor-s6-multiday-fade-memo.md) — T+3 c=6 **INCONCLUSIVE** (`s6_multiday.log`).

Same frozen rule `prior_day_high_reject` Short. Horizon is **T+1…T+5 close-to-close** on in-repo daily bars, 6 disjoint years, pooled `k5_pooled` at **c = 6 bps**. No new event rules. No SSF download.

| Gate | Result |
|---|---|
| Pooled `EV_net` CI LB > 0 at c = 6 **and** sign ≥ 5/6 | **INCONCLUSIVE** — MDE 10.2 ≥ 6; CI [−20.5, −0.0]; sign 2/6. Do not buy SSF |

---

## Work not in this plan (and why)

| Work | Why it waits or dies |
|---|---|
| Fresh M6–M8 | No directional cash book. Review: M6 remount was dangerous; harness hard-exits 3 |
| Name V1 as P1 authority | Stale EOD control; wrong instrument. Memo stays report-only |
| `eval_horizon_m9_v2_stub.py` / `option_marks_daily.parquet` | Name book, overnight hold, blocked on marks. Not V2p-c, not index V2 |
| Extending M9-0 name IV | Store COMPLETE; not the door for P1 |
| Precision Execution Bridge | 2–4 bps prior vs 12–19 bps deficit; not a successor kill-switch |
| New event rules / N-bar exhaustion | Pool peek after M4R STOP (review: never coded; frozen) |
| Regime reopen | I1 failed on the index; A0 closed |
| **SSF / S4-P2 download** | C0-ladder `c_max` ≈ 4.5 < forward RT. Unopened |
| Live OMS options rewrite | After V2p-c/V2, as a live-architecture addendum, not a research peek |

---

## Human checkpoints

After S1 remainder and after S2, write a ½–1 page memo:

1. Modules touched  
2. Numbers (V1n/V2p or C0 3/5/8)  
3. Cleanup done vs deferred  
4. Go / Stop / Rework  

Do not wait for a dual-judge document to record a Stop — the blueprint already defines the language.

---

## What “done” looks like

**P1:** V1 ∧ V1n ∧ **V2p-c PASS** (range). Last-trade V2 **FAIL (report)**. Remaining-session option sleeve **STOPPED**. Vendor quotes not purchased.  
**P2:** *Intraday* SSF is not a PASS path at forward friction. C0 at 3 bps is a sleeve bound only.  
**S6:** T+3 c=6 **INCONCLUSIVE** (MDE ≥ 6). Not a product. Do not download SSF.  
**Programme FAIL:** V2p-c FAIL **and** S6 FAIL on passable harnesses — **does not fire** (V2p-c PASS). This STOP is the product hunt, not that sentence. Production cascade stays as-is. Do not return to Top-K + H=6 / 60/30. Do not salvage with name-option V2.  
**Stop memo:** [horizon-successor-stop-memo.md](../archive/horizon-successor-stop-memo.md)

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-successor-architecture-blueprint.md](horizon-successor-architecture-blueprint.md) | Design authority (Rev 3) |
| [horizon-fresh-architecture-blueprint.md](horizon-fresh-architecture-blueprint.md) | Closed cash-directional design; hygiene inherits |
| [horizon-fresh-architecture-implementation-plan.md](horizon-fresh-architecture-implementation-plan.md) | Historical M0–M9 map + 2026-08-17 implementation review |
| [horizon-m9-range-monetization-charter.md](horizon-m9-range-monetization-charter.md) | M9 text this plan re-ranks (next Fresh action ≠ this plan’s next action) |
| [horizon-m9-v1-memo.md](../archive/horizon-m9-v1-memo.md) | Name V1 PASS — report-only for P1 |
| [horizon-fresh-m4rb-stop-memo.md](../archive/horizon-fresh-m4rb-stop-memo.md) | Why cash directional is closed |
| [horizon-successor-s1-memo.md](../archive/horizon-successor-s1-memo.md) | V1n PASS, V2p-0 INCONCLUSIVE |
| [horizon-successor-s1-v2pb-memo.md](../archive/horizon-successor-s1-v2pb-memo.md) | residual>0 CLOSED (still thin at 09:45) |
| [horizon-successor-s1-v2pc-preregistration.md](../archive/horizon-successor-s1-v2pc-preregistration.md) | T-02 V2p-c locked before peek |
| [horizon-successor-s1-v2pc-memo.md](../archive/horizon-successor-s1-v2pc-memo.md) | V2p-c PASS (range); S4-P1 later waived |
| [horizon-successor-s2-c0-memo.md](../archive/horizon-successor-s2-c0-memo.md) | C0 PASS at 3 bps |
| [horizon-successor-s2-cost-ladder-memo.md](../archive/horizon-successor-s2-cost-ladder-memo.md) | T-01: `c_max` ≈ 4.5; P2 STOP at forward friction |
| [horizon-successor-s3-branch.md](../archive/horizon-successor-s3-branch.md) | S3-day ranking; superseded by Rev 3 |
| [horizon-successor-s6-multiday-fade-charter.md](horizon-successor-s6-multiday-fade-charter.md) | T-03 new family |
| [horizon-successor-s6-multiday-fade-memo.md](../archive/horizon-successor-s6-multiday-fade-memo.md) | S6 T+3 INCONCLUSIVE |
| [horizon-successor-s4-p1-index-marks-charter.md](horizon-successor-s4-p1-index-marks-charter.md) | S4-P1 acquisition spec; **waived** |
| [horizon-successor-s4-p1-checkpoint.md](../archive/horizon-successor-s4-p1-checkpoint.md) | Store missing; V2 did not peek |
| [horizon-successor-s1-v2-preregistration.md](../archive/horizon-successor-s1-v2-preregistration.md) | V2 locked before marks |
| [horizon-successor-s1-v2-zenodo-preregistration.md](../archive/horizon-successor-s1-v2-zenodo-preregistration.md) | Report-only last-trade V2, locked before ingest |
| [horizon-successor-s1-v2-zenodo-memo.md](../archive/horizon-successor-s1-v2-zenodo-memo.md) | Zenodo V2 FAIL (report) |
| [horizon-successor-stop-memo.md](../archive/horizon-successor-stop-memo.md) | Product hunt STOP; S4-P1 waived |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Production map until a new product ships |

---

## Appendix — Milestone → blueprint map

| Milestone | Blueprint sections |
|---|---|
| S0 | §1 closed products, freeze, §2.3–2.4 |
| S1 | §4 P1 gates V1 (done) / V1n (done) / V2p CLOSED / V2p-c PASS |
| S2 | §5 P2 C0 + C0-ladder; SSF STOP |
| S3 | §8 capability sentences (Rev 3) |
| S4 | §4.3 last-trade V2 FAIL (report); S4-P1 waived; S4-P2 unopened |
| S5 | §3.2 product-specific C/D |
| S6 | T+3 INCONCLUSIVE; not programme FAIL |
