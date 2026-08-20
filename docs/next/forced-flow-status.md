# Book F — milestone status pack

**Date:** 2026-08-19. **Branch:** `forced-flow`.  
**Authority:** [forced-flow-architecture-blueprint.md](forced-flow-architecture-blueprint.md) Rev 3, [forced-flow-execution-plan.md](forced-flow-execution-plan.md).  
**Question for review:** answered. C2 STOP. G0 **PASS**. G1 **PASS** (+33.5 bps). G2 **INCONCLUSIVE / economic FAIL** (gross 33.5 < 45). G3 not opened. Next spend: none. Desk is a passive core plus an audit log. See [g1-earnings-drift.md](../archive/g1-earnings-drift.md), [g2-net.md](../archive/g2-net.md).

This is a status pack, not a peek charter. Numbers below are already measured. Windows are not to be moved after seeing them.

---

## Programme posture

Retail India desk, cash delivery only. Passive core is the after-tax benchmark. Book G is **closed** (G1 PASS, G2 economic FAIL). Book F ranking skill is retained; C1 public residual and C2 predicted-basket residual are both closed. Production cascade and Horizon Successor stay frozen.

| Lock | Value |
|---|---|
| Delivery round trip | 45 bps |
| STCG | 20.8% |
| LTCG (passive hold) | 12.5% |
| Prior event σ | 600 bps |
| Disaster clip | −500 bps, keep the row |
| Instrument | Cash delivery vs Nifty close. No futures, no options |
| T | First NSE session where PIT Nifty 50 membership flips |

---

## Milestone map

| ID | Plan name | Status | Verdict |
|---|---|---|---|
| **P0** | Posture, cost lock, panel | Done | Exit met |
| **F0** | Event pool | Done | 68 events, 43 tradable on GOLDEN |
| **F1** | Effect exists (T−20→T) | Done | **INCONCLUSIVE** both sleeves |
| **F1a** | Announcement → effective | Done | **INCONCLUSIVE** both sleeves |
| **F1b / F3 skill** | Rank Next 50 by 6-month FF mcap | Done | **PASS** top-k hit rate |
| **F1c** | T→T+20 fade (additions authority) | Done | **INCONCLUSIVE** additions |
| **F2-NET** | 45 bps then 20.8% tax | Closed-N/A | C1 and C2 both closed |
| **F3-RESIDUAL** | Hold predicted top-3 to PR | Done | **STOP** +205 vs 300 hurdle |
| **F4** | Decay | Folded into C2 eras | No standalone peek |
| **F5** | Tradability | Not opened | C2 was STOP |
| **G0–G3** | Earnings drift | **Closed** | G0 PASS; G1 PASS +33.5; G2 INCONCLUSIVE / economic FAIL; G3 not opened |
| **L0** | Operating loop | Not opened | No passing book remains |

---

## P0 — panel and benchmark

Daily panel from `data/GOLDEN` 1-minute bars → `data/derived/daily_panel.parquet`.

- ~251,686 rows, 100 equity symbols, 2015-02-02 to 2026-04-08
- Zero placeholder ticks dropped; unadjusted splits fail loud
- Nifty from `^NSEI.csv`
- After-tax passive Nifty hold terminal wealth ≈ **2.6309**

---

## F0 — event pool

Nifty 50 PIT membership from the in-repo replacement ledger. Events = first-session difference.

| | Count |
|---|---|
| Additions | 34 |
| Deletions | 34 |
| Tradable on GOLDEN at T | 43 |
| F1 addition n (complete window) | 27 |
| F1 deletion n | 16 |
| Semi-annual additions (F1b labels) | 29 |
| Ad-hoc (excluded from F1b) | 5 |

Announcement dates later recovered from free IISL/NSE Indices PRs and contemporaneous press (`src/events/announcements.py`). Sector GOLDEN files are price only — no membership.

---

## F1 residual peeks (cost-free)

Statistic: mean trade residual vs Nifty, disaster-clipped, session-block 95% CI, fold sign. Prior MDE uses σ = 600 bps. INCONCLUSIVE if MDE ≥ |point|.

### Authority and F1a / F1c

| Sleeve | Window | n | Prior MDE | Point | 95% CI | Sample σ | Verdict |
|---|---|---|---|---|---|---|---|
| Additions | T−20→T (F1-effective) | 27 | 323.5 | +26.3 | [−162.5, +247.0] | 511.7 | **INCONCLUSIVE** |
| Deletions | T−20→T | 16 | 420.2 | −119.6 | [−283.3, +86.3] | 400.3 | **INCONCLUSIVE** |
| Additions | Announce→T (F1a) | 27 | 323.5 | +51.8 | [−172.7, +318.8] | 591.1 | **INCONCLUSIVE** |
| Deletions | Announce→T (F1a) | 16 | 420.2 | −145.4 | [−340.6, +91.2] | 392.2 | **INCONCLUSIVE** |
| Additions | T→T+20 fade (F1c authority) | 27 | 323.5 | +128.9 | [−86.3, +363.7] | 538.7 | **INCONCLUSIVE** |
| Deletions | T→T+20 fade (companion) | 16 | 420.2 | +527.7 | [+252.6, +788.0] | 776.4 | prior-σ PASS; sample MDE 543.8 ≥ 527.7 — **do not promote** |

### Companions (locked, not authority)

| Sleeve | Window | n | Point | CI | Note |
|---|---|---|---|---|---|
| Additions | T−40→T−20 | 27 | +538.1 | [244.6, 850.8] | prior-σ PASS; sample σ 982, sample MDE 529 vs 538 — do not move authority |
| Deletions | T−40→T−20 | 15 | +150.7 | [−145.2, 417.8] | INCONCLUSIVE |

**Repair written into the F1 charter:** more event history from this panel. Never a different window after seeing the print. Never a data purchase. C1 F2-NET is closed-not-applicable.

**Power fact:** MDE scales as 1/√n. Filling the 25 GOLDEN-missing names lifts additions toward 34 and barely moves MDE (~288 bps). Detecting a 50 bps effect at σ 600 needs on the order of a thousand events. Nifty 50 semi-annual reconstitutions will not provide that.

Year prints (additions F1-effective, bps): 2015 −163, 2016 −500, 2017 +172, 2018 +576, 2019 −7, 2020 +90, 2021 +213, 2022 +1, 2023 −425, 2024 −68, 2025 −304. Fold sign 4/8 among years with ≥2 events.

---

## F1b / F3 ranking (not a residual)

Source: NSE Indices monthly MCWB zips (Nifty 50 **and** Next 50), free-float mcap + avg impact cost, 2014–2025. HuggingFace Nifty 50 weights were not used (wrong universe). Nov 2024 zip missing; Jan 2025 window still had 5 of 6 months. F&O eligibility not applied (no PIT F&O field).

Rule: 6-month average FF mcap to 31 Jan / 31 Jul; rank Next 50; hit if actual semi-annual addition ranks ≤ k (k = additions that cycle). Naive = k/50.

| | Value |
|---|---|
| Charter n | 29 semi-annual additions |
| Charter naive | 4.07% |
| Charter MDE | 10.28 hit-rate points |
| Scored n | 24 (5 universe misses dropped) |
| Hit rate | **66.7%** CI [47.8%, 85.5%] |
| Naive (scored) | 4.1% |
| Mean Next 50 rank | 2.67 |
| 1.5× buffer recall | 100% |
| 1.5× buffer precision | 15.5% |
| 2015–2019 | 76.9% vs 4.8% naive, PASS |
| 2020–2025 | 54.5% vs 3.3% naive, PASS |
| **Verdict** | **PASS** |

Universe misses: IBULHSGFIN and IOC already in the Nifty 50 MCWB file at Jan-2017 cut-off; GRASIM, NESTLEIND, MAXHEALTH absent from both files at their cut-offs.

The F1b memo's residual-block sentence is **superseded** by Rev 3. C2 is measured in [f3-residual.md](../archive/f3-residual.md). F1a remains closed.

---

## F3-RESIDUAL / C2 (cost-free)

Charter: [f3-residual-charter.md](f3-residual-charter.md). Memo: [f3-residual.md](../archive/f3-residual.md). Module `src/events/f3r.py`. Rank lag: cut-off month MCWB file (no roll-forward shares/float fields).

Fixed k=3, equal weight, first session of Feb/Aug → first session strictly after the periodic-review PR. Missing GOLDEN bars = 0 bps (cash). Clip −500 bps on the basket. Prior σ 750 bps. n=22 cycles 2015–2025 including 5 with zero semi-annual Nifty 50 additions.

| Sleeve | n | Prior MDE | Point | 95% CI | Sample σ | Eras | Verdict |
|---|---|---|---|---|---|---|---|
| Authority: top-3 − ranks 21–50 | 22 | 448.0 | **+204.8** | [+54.6, +353.1] | 374.8 | +154 / +247 | **STOP** |
| Companion: top-3 vs Nifty | 22 | 448.0 | +236.4 | [+52.0, +417.0] | 451.1 | +164 / +297 | STOP |
| Sensitivity: treat coverage ≥ 2/3 | 19 | 482.0 | +175.8 | [+12.6, +338.8] | 388.5 | +53 / +247 | STOP |

Mean coverage: treat 78.8%, control 46.0% (ranks 21–50 sit partly outside the 100-name panel; cash fill as chartered). Fold sign 8/11. Both era halves positive. CI lower bound > 0. Point 205 < 300 hurdle → **STOP**. GO required ≥ 450 and CI low > 0 and both eras positive.

Year prints (authority bps): 2015 +183, 2016 +266, 2017 +201, 2018 +437, 2019 −319, 2020 +72, 2021 +219, 2022 +589, 2023 −62, 2024 +720, 2025 −55.

**Book F capital is closed.** Ranking remains an asset. Do not open F2-NET, F5, or a model. Do not re-peek.

---

## G0 — Results calendar (closed PASS)

Free NSE `corporates-financial-results` JSON, GOLDEN 100-name panel, quarterly only. First broadcast per `(symbol, period_end)`. Charter: [g0-charter.md](g0-charter.md). Memo: [g0-calendar.md](../archive/g0-calendar.md). Not a residual peek.

| | |
|---|---|
| Names with ≥1 filing | **95 / 100** |
| Events after first-broadcast dedup | **3,586** |
| Span | 2015-01-15 17:12:03 .. 2025-02-17 22:32:13 |
| G1 MDE at this n, σ=600 | **28.1 bps** |
| Missing | ENRIN.NS, HDFCLIFE.NS, SBILIFE.NS, TATACAP.NS, TMCV.NS |
| 2025 events | 95 (thin — Integrated Filing) |

Working sample for G1 is 2015 through early 2025. Do not buy a vendor to fill 2025.

---

## G1 — Earnings drift, gross (closed PASS)

Charter: [g1-charter.md](g1-charter.md). Memo: [g1-earnings-drift.md](../archive/g1-earnings-drift.md). Module `src/events/g1.py`.

T = first session close that contains the NSE timestamp (15:30 cutoff). Side = sign of T−1 close → T close residual vs Nifty. Authority = T close → T+3 close. Cost-free. Disaster clip −500. Overnight skip is G3, not this gate.

| Sleeve | n | Prior MDE | Point | 95% CI | Sample σ | Eras | Verdict |
|---|---|---|---|---|---|---|---|
| Authority T+3 | 3543 | 28.2 | **+33.5** | [+22.6, +45.8] | 321.2 | +27.5 / +38.7 | **PASS** |
| Companion T+1 | 3543 | 28.2 | +10.0 | [+3.1, +17.6] | 202.7 | +4.8 / +14.4 | INCONCLUSIVE |
| Companion T+5 | 3543 | 28.2 | +47.2 | [+34.1, +59.7] | 384.8 | +42.5 / +51.1 | PASS — **do not promote** |

Fold sign 11/11. Both era halves positive. CI lower bound > 0. Point 33.5 > MDE 28.2. Sessions clustered: 1033 unique T dates.

Year prints (authority bps): 2015 +62, 2016 +32, 2017 +4, 2018 +5, 2019 +40, 2020 +57, 2021 +63, 2022 +36, 2023 +20, 2024 +26, 2025 +12.

**Do not** move authority to T+5 after seeing it.

---

## G2 — Net of delivery and STCG (closed)

Charter: [g2-charter.md](g2-charter.md). Memo: [g2-net.md](../archive/g2-net.md). Module `src/events/g2.py`.

net = 0.792 × (gross − 45) on the clipped G1 T+3 residual.

| Sleeve | n | Prior MDE | Point | 95% CI | Sample σ | Eras | Verdict |
|---|---|---|---|---|---|---|---|
| T+3 net | 3543 | 28.2 | **−9.1** | [−17.8, +0.6] | 254.4 | −13.9 / −5.0 | **INCONCLUSIVE** |

G1 gross 33.5 < 45 delivery → **economic FAIL**. Fold sign 3/11. Sample MDE 12.0 ≥ 9.1. G3 not opened.

---

## G3 — Gap already in (not opened)

Charter: [g3-charter.md](g3-charter.md) was written before the G1 peek. G2 did not PASS. Do not open G3.

---

## Naming (Rev 3)

Gates keep F-numbers. Constructions are C1–C4.

| Label | Meaning |
|---|---|
| **F2-NET** | 45 bps then 20.8% tax on a passing residual |
| **C4** | F&O list entry/exit (deferred; was colliding with F2) |
| **F3-SKILL** | Ranking hit rate — **PASS** |
| **F3-RESIDUAL** | C2 predicted basket, cut-off → session after PR — **STOP** (+205 vs 300) |
| **G0** | Free NSE quarterly results calendar — **PASS** (3,586 events, 95 names) |
| **G1** | T+3 residual vs Nifty — **PASS** (+33.5 bps, n=3543) |
| **G2** | 45 bps then 20.8% — **INCONCLUSIVE / economic FAIL** (net −9.1; gross 33.5 < 45) |
| **G3** | Small overnight-gap sleeve — **not opened** |

---

## What is not allowed without a plan change

- Re-run any peeked C1 window (T−20→T, announce→T, T→T+20 additions)
- Re-window F1 to T−40→T−20 after seeing the companion
- Promote F1c deletion companion
- Treat F1 INCONCLUSIVE as PASS or open F2-NET on C1
- Fit a GBDT / probability-weighted sizing on Book F
- Buy a vendor event or fundamental panel
- Widen to foreign index families for sample size
- Build a PIT F&O list or a full-NSE panel to rescue C2
- A standalone F4 peek
- Start L0 before F2-NET on a passing book
- Treat F3-RESIDUAL STOP (or INCONCLUSIVE) as anything other than closed Book F capital
- Re-run C2 with a new control, coverage rule, or estimator
- Run G1 without a written-before-peek charter
- Buy a vendor to fill 2025 Integrated Filing, or expand the GOLDEN panel for Book G
- Re-run G1 or G2 with a new estimator, clip, or window
- Promote G1 T+5 (or T+1) after seeing the companion
- Open G3 or L0

---

## Next spend (Rev 3)

None. Global STOP is invoked: F3-RESIDUAL STOPPED and Book G failed on a passable harness. The desk is a **passive core plus an audit log**.

C1 and C2 are closed. Ranking is retained. G0 and G1 are closed PASS. G2 closed the earnings book. G3 was not opened.
