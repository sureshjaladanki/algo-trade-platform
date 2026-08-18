# Horizon M9 — Range Monetization Charter

**Status:** OPEN — V1 PASS (2026-08-17); V2 blocked on option marks  
**Authority:** Follows [horizon-fresh-architecture-blueprint.md](horizon-fresh-architecture-blueprint.md) Rev 3 §15A–§15B after [M4R-b STOP](../archive/horizon-fresh-m4rb-stop-memo.md)  
**Parent programme:** Horizon Fresh (M0–M4R-b) — directional Nifty-100 MIS cash **§14 capability FAIL**  
**Product under test:** Monetize Stage B’s remaining-range forecast, not directional barrier races  
**Constraint inherited:** Round-trip realism still matters; option friction replaces cash `c*` for V2/V3  

This is a **new charter**, not a silent continuation of Stage C. Production Regime → Horizon → Precision stays frozen.

---

## One-line

Stage B predicts session range better than it predicts direction. M9 asks whether that forecast is
**incremental to implied** — and if so, whether it can be sold in options (primary) or used to time
a cheaper futures instrument (secondary).

---

## Inheritance (keep) vs discard

| Keep | Discard |
|---|---|
| Stage A tradability / `c_eff` discipline | Stage C directional meta-label on cash MIS |
| Stage B range head (K1/K2 PASS) | Barrier-race geometry search |
| Absolute admit + sparse book posture | Top-K as economic gate |
| K-gate hygiene, MDE publication, three-way / pooled reads | Remounting H=6 / 60–30 / production Top-K |
| Purged folds + dual/rolling holdouts | Claiming cascade-ready from M9 alone |

---

## Why this charter exists (locked facts)

| Fact | Source |
|---|---|
| Range Spearman **0.607–0.635** (within-clock **0.617**) | M3 K1 |
| Directional selector IC ≈ **0.022** vs need **0.054** | M4R-b F1 |
| Best unconditional Short reversion drift CI UB ≈ **+17 bps** < 20 | M4R |
| Median `c_eff` on liquid tail ≈ **7–8 bps** still insufficient | M4R-b F2 |
| §14 FAIL earned for directional cash MIS | M4R-b stop memo |

Spearman 0.6 vs *realized* range is **not** an edge by itself. Implied vol already prices a HAR-style
forecast plus a variance risk premium. The tradable object is **realized − implied**.

---

## Tracks

### Track A — Primary: sell range in options

| ID | Gate | Rule | If FAIL |
|---|---|---|---|
| **V0** | VIX bridge (report-only) | Name remaining range ~ India-VIX-implied remaining range + `range_q50`; publish incremental coef for `range_q50`. **Not authority** — index IV is a noisy proxy for single-name implied | Informs data urgency; cannot alone PASS Track A |
| **V1** | Incremental information | Realized remaining range ~ **single-name** (or ATM-straddle) implied range + `range_q50`; `range_q50` coef significant, correct sign, dual-fold (A+B) or 6/8 rolling | Stop Track A — head is redundant with the option market |
| **V2** | Sign economics | Gross straddle/strangle (or variance-swap proxy) PnL on V1-selected sessions; martingale-residual / session-block CI LB > 0, cost-free | No vol edge; stop Track A |
| **V3** | Net economics | V2 after option friction (premium spread, STT on premium, slippage; delta-hedge cost if hedged) | Edge below option friction; stop Track A |

**Instrument sketch (post-V1):** long premium when `range_q50` ≫ implied (underpriced vol); short premium / iron condor only if V1 sign and risk limits explicitly allow short-vol — default bias is **long premium on underpriced forecast** until V2 says otherwise.

**V1 recorded 2026-08-17:** dual-fold PASS (`m9_v1_full.log`). Next gate is V2, not a ship.

### Track B — Secondary: single-stock futures (cost cut)

Attack \(c\) rather than invent \(\delta\). Reuse M4R winning *event* definitions only as a research sleeve on F&O names with futures RT ≪ cash.

| ID | Gate | Rule | If FAIL |
|---|---|---|---|
| **S0** | Data + universe | Liquid SSF panel with survivorship-safe eligibility history | Block Track B |
| **S1** | Friction | Median futures round-trip (spread + fees) published; must be materially below cash `c_eff` | No instrument advantage; stop Track B |
| **S2** | Edge reprint | M4R-b-style K4 on vertical-only Short reject (or best sleeve) under S1 friction | Same as cash FAIL → stop Track B |

Track B does **not** reopen feature fishing on cash. It is an instrument change.

---

## Data prerequisites (critical path)

| Need | In repo today? | Action |
|---|---|---|
| India VIX 1m OHLCV (`^INDIAVIX.csv`) | **Yes** | Enables **V0** immediately |
| Single-name IV / ATM IV / option chain history | **Yes** (EOD ATM, 2015–2019) | Unblocks **V1** after pre-registration |
| Option trade marks / bid-ask for friction | **No** | Needed for **V3**; can stub V2 with mid marks |
| Single-stock futures OHLCV + lot sizes | **No** | Blocks Track B **S0** |

**Rule:** Do not run authority V1 without single-name implied **and** a written pre-registration.
V0 / V1-index are published; V1-index dual-fold **PASS** does not replace name-level V1.

### Implied-range definition (V0 / V1)

For decision time \(t\) with fraction \(f\) of the cash session remaining:

\[
\widehat{R}^{\mathrm{imp}}(t) \approx \kappa \cdot \sigma_{\mathrm{day}} \cdot \sqrt{f}
\]

where \(\sigma_{\mathrm{day}} = \mathrm{IV}/(100\sqrt{252})\) (IV in percent), and \(\kappa\) is a fixed Parkinson-style
range constant (default **1.6**, pre-registered; sensitivity at 1.4 / 1.8 report-only).

- **V0:** IV = India VIX (same for all names that day — known limitation).  
- **V1:** IV = name ATM IV (or straddle/spot) as of \(t\) or last mark before \(t\), no look-ahead.

---

## Build order

1. **M9-0** — DONE (EOD ATM IV parquet + coverage).  
2. **V0** — DONE (report-only).  
3. **V1** — DONE dual-fold PASS 2026-08-17.  
4. **V2 → V3** — only after V1 PASS (now unlocked; blocked on option marks).  
5. **Track B** — parallel workstream once SSF data exists; do not let it distract from V2.

Peek discipline: pre-register each V-gate; publish MDE; no geometry / Top-K remount language.

---

## Capability sentences

| Path | Sentence |
|---|---|
| **PASS (M9)** | Under inherited Stage A/B, a Horizon range head that is incremental to implied can select sessions where option (or SSF) economics clear friction dual-fold / pooled. |
| **FAIL (M9 Track A)** | `range_q50` is not incremental to implied (V1 FAIL) — then the range head is a filter, not a product; Track B or a different product definition is required. |
| **FAIL (programme)** | Both Track A and Track B fail — then Nifty-100 intraday under realistic friction has no Horizon product in this family; stop remounting cash directional Stage C. |

---

## Out of scope

- Silent cutover of production cascade  
- Precision bailout of failed V-gates  
- Directional cash Stage C peeks  
- Claiming “vol edge” from V0 alone  
- Cost shopping that redefines success after seeing the ledger  

---

## Related docs

| Doc | Role |
|---|---|
| [horizon-fresh-architecture-blueprint.md](horizon-fresh-architecture-blueprint.md) | Design parent (§15A/B) |
| [horizon-fresh-architecture-implementation-plan.md](horizon-fresh-architecture-implementation-plan.md) | Milestone map (M9) |
| [horizon-fresh-m4rb-stop-memo.md](../archive/horizon-fresh-m4rb-stop-memo.md) | Why directional closed |
| [horizon-m9-v1-preregistration.md](../archive/horizon-m9-v1-preregistration.md) | V1 locked before the peek |
| [horizon-m9-v1-memo.md](../archive/horizon-m9-v1-memo.md) | V1 dual-fold PASS |
| `src/horizon/m9/` | Code boundary for this charter |
