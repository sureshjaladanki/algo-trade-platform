# Horizon Fresh — M4R STOP memo (no sleeve with a route past friction)

**Date:** 2026-08-16
**Authority:** blueprint Revision 3 §10.3 (three-way K4), §15A; implementation plan M4R
**Decision:** **STOP the unconditional rule-pool search.** Escalation to a product change is gated on
**M4R-b** — two pre-registered falsifications.

## What was tested

- Decision set: transition events ∩ Stage A ∩ Stage B (`opportunity_ok`), one row per (symbol, bar)
- Measure: barrier-free drift from the event bar to MIS flatten, session-block CI
- Universe: 82 trade names; 8 folds (A/B + rolling R2017–R2022), 5-day purge
- Pre-registered sleeve-selection rule: fold-consistent sign **and** CI UB ≥ \(c^*\) on ≥ 1 fold

## Results (authority — `data/GOLDEN_PARQUET/m4r_drift_ledger.log`)

| Rule | Side | Drift | CI UB | Sign consistent |
|---|---|---|---|---|
| `prior_day_high_reject` | Short | **+6.2 / +7.8 bps** | ≈ +16.3 / +16.8 | yes |
| `gap_fill_short` | Short | +6.8 / +4.4 bps | — | yes |
| `vwap_loss` | Short | +3.2 / +5.2 bps | — | yes |

Several reversion rules are fold-consistent in sign. **No** rule's CI upper bound reaches
\(c^*=20\) bps. Best UB ≈ +16.8.

Validation power is not the issue: M5P established K4 MDE of **9.0–12.6 bps on 8/8 folds**
(`m5p_full_run.log`), so this is a real bound rather than noise. The reversion hypothesis is directionally
**right** — Indian intraday single names fade rather than continue, and every continuation rule tested
negative — but the effect is roughly a third of the friction it must pay.

## Interpretation

> Directional event drift on Nifty-100 intraday is **real, fold-consistent, and bounded at CI UB ≈ +17 bps**
> against a 20 bps round-trip. The signal is smaller than the friction, not absent.

### Required-IC arithmetic (blueprint §15A)

Per-trade gross dispersion at 200/100 is σ ≈ 137 bps. Top-decile selection lifts the mean by
ρ·σ·E[z | top 10%] ≈ 240ρ bps. Carrying the best sleeve from +7 bps to:

| Target | Required selector IC |
|---|---|
| Breakeven at 20 bps | **0.054** |
| 30 bps gross (with margin) | **0.10** |

Measured achievable intraday single-name directional IC ≈ **0.07** (§4.1, R² ~0.005). Breakeven sits
*below* the ceiling; margin sits *above* it. The directional product has no headroom — which is a
defensible basis for stopping, but not the same claim as "no route exists."

## Why the stop is narrowed rather than final

Two gaps in what the ledger is entitled to conclude:

1. **It bounds the pool, not the product.** Blueprint §10.2 is explicit that a pre-selection mean is not
   the gate, because *selection is the job*. Gating on unconditional per-rule drift is the EV-net Step 0
   error one level up. The statistic that can refute the architecture is K4 on the **admitted** set after
   Stage C, which was never run on the winning sleeve.
2. **The hurdle used was the flat `c*`.** Stage A computes row-level `c_eff` and the pipeline keeps only
   the boolean `c_eff ≤ 20` (blueprint §3.1). Statutory cost is ~4 of the 20 bps; the rest is spread, tick
   and impact, which vary by an order of magnitude across the universe. A 1–4 fire/day book confined to
   the liquid tail faces a materially lower hurdle.

Both are closable with existing code and one peek each. Both are pre-registered as **expected FAIL**.

## Two findings that change the design regardless of outcome

**Barriers are destroying edge at these signal strengths.** On identical rows M5R read barrier-race gross
return of −10.6 / −5.3 bps against barrier-free drift of −5.3 / +4.7 bps. With session σ ≈ 125 bps a
100 bps stop is inside noise, so it is triggered by randomness rather than information. The §1.1 \(\Delta p\)
requirement is a property of *barrier races* — drop the barriers and \(EV_{net} = \delta - c\) with no
probability-edge requirement at all. Blueprint §1.6 now makes **vertical-only** the default for thin-drift
sleeves, with risk managed by Stage D sizing.

**K5 was unpassable by the intended book.** A 95% lower bound above zero on a true \(EV_{net}\) of +10 bps
needs SE < 5.1 bps → ~1,150 clustered trades ≈ 4.6 fires per session, against a design target of 1–4 per
day across ~88 names. Blueprint §10.3 now makes K5 a pooled read with a fold sign test.

## Forbidden next steps (unchanged)

- Geometry grid search to find a PASS
- Precision peeks to bail out Horizon
- Remounting production Top-K / H=6 / 60–30
- More directional feature engineering — 8 folds across multiple sleeves have bounded the effect

## Next steps

**M5P-b** (gate repairs: pooled K5, `c_eff` hurdle, admit-count pre-declaration, vertical-only geometry)
→ **M4R-b**:

- **F1** Stage C selector on `prior_day_high_reject` Short, vertical-only, K4 on the admitted set, realized vs required IC published, admit count declared in advance.
- **F2** Row-level `c_eff` threaded into the EV arithmetic; liquid-tail reprint with a capacity statement.

**Both fail → blueprint §14 capability FAIL is earned**, and **M9** opens the successor charter. Primary
hypothesis: monetize the range head (Spearman 0.607–0.635) in options rather than using it to filter a
directional bet (IC ~0.07) that cannot pay its own friction — gated first on **V1**, whether the head
carries information incremental to *implied* range. Secondary: same signal on single-stock futures to cut
\(c\) rather than raise \(\delta\). Rejected with reasons: hedged cash book, wider universe, multi-day cash
delivery (blueprint §15B).

## Artifacts

- `data/GOLDEN_PARQUET/m4r_drift_ledger.log` — authority
- `data/GOLDEN_PARQUET/m5p_full_run.log` — power (MDE 9.0–12.6 bps, 8/8 folds)
- `data/GOLDEN_PARQUET/m5r_full_run.log` — Long continuation FAIL, barrier vs drift comparison
- Prior: [horizon-fresh-m5-stop-memo.md](horizon-fresh-m5-stop-memo.md) + addendum
