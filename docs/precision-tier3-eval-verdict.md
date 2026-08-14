# Tier 3 Precision — Evaluation Framework Verdict

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Tier-level **eval harness** for Precision timing / selectivity only (Long + Short) — rules / features locked elsewhere  
**Judges:** Gemini Flash, Claude Sonnet  
**Date:** 2026-08-13  
**Friction lock:** **0.20% (20 bps)** round-trip working (`c*`); archive stress **0.30%** companion — do not re-derive  
**Depends on:** [precision-tier3-verdict.md](precision-tier3-verdict.md), [horizon-tier2-eval-verdict.md](horizon-tier2-eval-verdict.md), [regime-tier1-eval-verdict.md](regime-tier1-eval-verdict.md), [triple-barrier-verdict.md](triple-barrier-verdict.md), [cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md)  
**Status:** **REVISE → build harness** (philosophy + primary metrics locked; formulas hardened before ship)

---

## Summary

| Decision | Locked choice |
|---|---|
| Role of eval | Measure Precision as a **monetizer / timing filter** (selectivity + fill timing vs naive 15m entry) — **not** a stock picker or regime detector |
| Confounding | **Never** score Precision with Regime I1/I5 or Horizon H1 IC; **never** claim Horizon rank skill from Precision fire PnL |
| Confirmatory / gated | **P1, P2** always; **P3 absolute** only after upstream H5 precondition; **P0** binary precondition |
| Long vs Short | **Shared metric taxonomy, separate gates** — not a different metric language |
| Sign / sizing | Gates on **unsized** per-unit returns; `size_mult` is diagnostic only (`P3_sized`) |
| P3 posture | **Option C** — report absolute net always; promote to absolute gate only when same-sleeve Horizon **H5 CI LB > 0** |
| Naive reference | **15m decision-bar close** + frozen TB geometry (mirrors Horizon H5 entry lock) |
| Gate rigor | **Session-block-bootstrap 95% CI LB > 0**; no invented absolute bps floors until A+B baselines |
| Folds | Reuse Regime calendar: **A+B gate**; **C informational** |
| Build posture | **REVISE → build** (both judges) |

**One-line:** Precision eval measures whether 1m rules skip worse paths and improve fills vs naive decision-close entry — never whether Regime/Horizon admitted an economically viable book.

---

## Why this eval exists

WS0/WS1 ([cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md)) showed Precision cannot clear friction while the admitted registry has `tb_tp_rate` only ~7–12% and rank 1–2 worse than 3–5. That correctly escalated to Horizon/Regime. It does **not** remove the need for a Tier-3 harness: once upstream path quality improves, and while iterating Precision knobs, we still need to answer at Precision alone: *does selectivity skip worse paths, and does 1m timing beat naive 15m entry on the trades we take?*

Sibling pattern: Regime I5 (admission quality) → Horizon H5 (Top-K TB quality) → Precision **P1/P2** (selectivity + timing lift on that registry).

---

## Judge scores

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Long eval design | 9/10 | 7/10 | **Strong P1/P2 bridge; harden formulas** |
| Short eval design | 8/10 | 6/10 | **Shared formulas + asymmetric min-N / MIS / afternoon slices** |
| Long ≠ Short separation | 9/10 | 8/10 | **Shared taxonomy, separate gates — lock** |
| Tier 1/2 anti-confounding | 10/10 | 8/10 | **Role division good; keep P6 diagnostic** |
| Gate rigor | 8/10 | **5/10** | **Formulas + P3 precondition were the weak link — harden** |
| NSE practicality | 7/10 | 6/10 | **Fill realism + circuit hygiene in P0** |
| Overall | **REVISE** (8.5) | **REVISE** (6.5) | **REVISE → build** |

---

## Locked philosophy

1. **Precision is a monetizer / timing filter**, not a stock picker and not a regime detector.  
2. Prefer **marginal value vs naive Horizon entry** (decision-bar close, frozen TB) over cascade end-to-end attribution alone.  
3. **Long ≠ Short** — every confirmatory metric is a *separate, separately-gated* number. Shared metric IDs and formulas; asymmetric K, min-N, MIS cutoffs, Short afternoon/cover slices.  
4. **Only P1 / P2 gate ship decisions unconditionally.** P3 absolute nets only after upstream H5 precondition. P4–P11 are diagnostic (P0 is a binary precondition).  
5. **Do not score with Regime index I1/I5** or **Horizon H1 IC**. Low registry `tb_tp_rate` is **context / upstream bridge**, not a Precision fail condition by itself.  
6. **Do not retune** wait / spread / conviction / rank knobs against gated metrics on the same fold used for ship without a fresh A+B check.  
7. **Inference:** session-block bootstrap CIs — no bar-level binomial “significance.”  
8. **Gates are unsized** — `size_mult` never enters P1/P2/P3 confirmatory numbers.

---

## Metric catalog

| ID | Metric | Role |
|---|---|---|
| **P0** | Causality / leakage / fill realism / MIS / circuit audit | **PRECONDITION** (binary) |
| **P1** | Selectivity lift (fired vs skipped naive TB path EV) | **PRIMARY / GATED** |
| **P2** | Timing lift (Precision fill net − naive decision-close net on same fires) | **PRIMARY / GATED / BRIDGE** |
| **P3** | Cost-netted fire expectancy (`mean(gross − c*)`) | **PRIMARY / CONDITIONAL GATE** |
| P4 | Exit-mix discipline (TP / SL / TIMEOUT / MIS + TO among `tb_label=0`) | Diagnostic |
| P5 | Setup vs fallback quality differential | Diagnostic (promote only if WS finds persistent fallback toxicity) |
| P6 | Rank-band fire PnL / fire-rate (1–2 vs 3–5) | Diagnostic — Horizon inversion bleed, **not** Precision skill |
| P7 | Edge-score quartile monotonicity (sleeve-separate) | Diagnostic |
| P8 | Coverage / fire_rate / episode scarcity | Diagnostic |
| P9 | Fill hygiene: wait mins, spread at fill, room-to-barrier, afternoon cover, circuit proximity | Diagnostic |
| P10 | Fold stability (A/B; C informational) | Diagnostic |
| P11 | Under/over-monetization vs `tb_label` (`prec_tp` vs `tb_tp`; overfire non-+1) | Diagnostic / upstream bridge |
| P1r | Skip-reason attribution (companion to P1) | Diagnostic |
| P2n | Drift-null control (random fill within wait window) | Diagnostic robustness |
| P3s | Stress-cost dual readout (`gross − 0.0030`) + sized companion | Diagnostic |

---

## Primary metric definitions (locked)

### Shared setup

For registry episode `e` (cascade-admitted, Horizon Top-K / bottom-K, session date `d`), `side = +1` Long / `−1` Short:

```
attemptable(e) = has causal 1m path
                 ∧ inside MIS entry cutoff for side
                 ∧ not structurally blocked before any Precision gate
                   (missing bars / halt at decision / past last-entry)

NaiveTBPathEV(e) =
  side · (exit_px_naive − decision_close) / decision_close − c*
  where exit is resolved by FROZEN TB geometry at the 15m decision bar
        (TP/SL widths from decision-bar atr_pct only; vertical = decision_bar + H)
        Entry = decision_bar CLOSE  — never Precision fill

PrecNet(e) = side · (exit_px_prec − entry_px_prec) / entry_px_prec − c*
             # identical to realized gross_ret − c* on fires
```

| Constraint | Lock |
|---|---|
| Auction bleed | Bar-end **09:30** excluded from gated metrics |
| Long last decision | ≤ **~14:15** bar-end |
| Short last decision | ≤ **~14:00** bar-end |
| Vertical H | **H = 6** bars (**90m**) working; H=4 diagnostic companion only |
| Cost in gated P1/P2/P3 | **`c* = 0.0020`**; also report archive **0.0030** as P3s |
| Bootstrap unit | **Trading session** (session-block); episode-block as robustness diagnostic |
| K (registry) | Match live Precision / Horizon emit: Long **K=5**; Short **K=3** (asymmetric). If pipeline still emits Short K=5, eval must flag universe-parity fail under P0 |
| Sizing | **Unsized** for P1/P2/P3 gates |

### P0 — Preconditions (binary, before research metrics)

| Check | Rule |
|---|---|
| Causality | No 1m bar beyond the wait window used for gate inputs; no future-bar “best fill” |
| Frozen geometry | TP/SL widths frozen at decision bar — never recomputed at fill from post-decision 1m vol |
| Fill policy | Eval fill = **same rule as production Precision** (selected 1m bar close under setup/fallback). Document; do not invent a second fill model in the harness |
| MIS / bleed | Attemptable mask matches Tier 2/3 session locks |
| Circuit / halt | Flag / exclude episodes where entry or SL/MIS exit is circuit-pinned / book-locked (Short UC traps especially) |
| Wiring | Rank↔edge polarity within `(bar, direction)` is a **P0 sanity check**, not a recurring gated metric |
| Universe parity | Eval registry == Precision live Top-K mask (PIT + ADV + sleeve + K) |

Fail any binary check → do not interpret P1–P3.

### P1 — Selectivity lift (PRIMARY)

```
# Denominator = attemptable episodes only (P0 owns structural unattemptables)
Fired(e)   = precision_fire == True          # includes setup AND fallback fills
Skipped(e) = attemptable ∧ ~precision_fire   # all gate rejects (conviction / spread /
                                             # room / afternoon / no-reentry / …)

P1_side = mean(NaiveTBPathEV | Fired) − mean(NaiveTBPathEV | Skipped)
```

**Gate (A+B):** session-block-bootstrap 95% CI LB on `P1_Long` and `P1_Short` each **> 0**.

**Companion (P1r, diagnostic):** for each skip reason `r`,
`mean(NaiveTBPathEV | skip_reason=r) − mean(NaiveTBPathEV | Fired)` — makes P1 actionable.

### P2 — Timing lift (PRIMARY / BRIDGE)

```
# Same fired episodes only
NaiveNet(e) = NaiveTBPathEV(e)   # decision-close entry, frozen geometry, full H from decision
PrecNet(e)  = realized Precision path net (fill px/time; TP/SL widths still decision-frozen;
              vertical remaining from decision_bar + H — matches live Precision clock)

P2_side = mean(PrecNet − NaiveNet | Fired)
```

**Gate (A+B):** CI LB on `P2_Long` and `P2_Short` each **> 0**.

**Why this stays Precision skill (not Horizon):** same names, same frozen widths; only entry time/price differs. If P2 used a different exit policy or recomputed ATR at fill, it smuggles geometry skill.

**Companion (P2n, diagnostic):** replace Precision fill with a **uniform-random 1m bar inside the wait window** (hard gates still applied). If random timing ≈ Precision timing, P2 may be post-signal drift, not selective setup skill.

### P3 — Cost-netted expectancy (CONDITIONAL PRIMARY)

```
P3_side = mean(gross_ret − c* | Fired)     # unsized
P3s_side = mean(gross_ret − 0.0030 | Fired)  # archive stress readout
P3_sized = size-weighted companion only      # diagnostic — never a ship gate
```

**Gate policy (locked Option C):**

| State | Rule |
|---|---|
| Upstream **blocked** | Same sleeve / fold / Top-K: Horizon **H5 CI LB ≤ 0** (or H5 not yet measured) → **P3 is report-only**; ship gates are **P1 + P2 only**; mark fold `UPSTREAM_BLOCKED` |
| Upstream **clears** | Same-sleeve Horizon **H5 CI LB > 0** → promote P3: require CI LB on `P3_side` **> 0** on Fold A **and** B |

Do **not** invent provisional absolute floors (e.g. NaiveNet ≥ −10 bps, `tb_tp ≥ 18%`) as P3 unlocks — that violates sibling CI discipline. Tie promotion to the existing Horizon bridge gate.

---

## Long vs Short — expert lock

| Item | Lock |
|---|---|
| Metric language | **Same IDs and formulas** (`side` folded in) |
| Acceptance | **Separate** CI gates, min-N — never pool |
| K | Long **5** / Short **3** (align with Horizon eval; flag if Precision pipeline drifts) |
| Min-N (provisional) | Long: ≥ **100** fires **and** ≥ **30** sessions; Short: ≥ **60** fires **and** ≥ **30** sessions |
| MIS cutoff | Long ~14:15 / Short ~14:00 (inherited) |
| Short-only slices | Afternoon cover, no-reentry-after-SL, circuit/UC traps — diagnostic under P9 / P1r |
| Verdict | Separate eval **runs** and **acceptance**, not a wholly different Short metric set |

**Expert judgment:** Shared taxonomy is correct (mirrors Regime + Horizon). NSE MIS asymmetry lives in cutoffs, K, min-N, and Short hygiene slices — not in forked metric IDs.

---

## Acceptance gates (hardened)

### Precondition (binary)

| Gate | Rule |
|---|---|
| P0 | Pass/fail checklist above before interpreting research metrics |

### Confirmatory (must pass Fold A **and** B)

| Gate | Rule |
|---|---|
| P1 | CI(P1) LB > 0, Long and Short separately |
| P2 | CI(P2) LB > 0, Long and Short separately |
| P3 | **Only if** same-sleeve Horizon H5 CI LB > 0; then CI(P3) LB > 0 Long and Short separately |

### Diagnostic (report; do not ship-lock alone)

| Check | Guidance |
|---|---|
| Absolute net / tb_tp floors | Gemini aspirational readouts OK as commentary — **not** gates until A+B baselines + upstream clear |
| P4 exit mix | TIMEOUT mass + share among `tb_label=0` (WS1 dead-zone diagnostic) |
| P5 setup vs fallback | Port existing `by_entry_reason` — promote only with WS evidence |
| P6 rank bands | Port existing 1–2 vs 3–5 — **Horizon bleed detector**; never Precision ship gate |
| P7 edge quartiles | Sleeve-separate only (pooled raw scores forbidden) |
| P8 / P9 / P10 | Coverage, fill hygiene, fold stability |
| P11 | `prec_tp` vs `tb_tp`; overfire non-+1 — upstream bridge (WS1 port) |
| P1r / P2n / P3s | Skip reasons; drift-null; stress-cost + sized companions |
| Fold C | Informational only — never a lock input |

### Minimum-N floor

Below Long/Short min-N → **insufficient data**, never gated (report `thin`; do not silently pass).

---

## Existing informal metrics — port map

| Existing (`src/precision/`) | Disposition |
|---|---|
| `fire_rate`, `mean_gross_ret`, `mean_net_ret` | **PORT** → P3 / P8 |
| `tp_rate` / `sl_rate` / `timeout_rate` / `mis_flatten_rate` | **PORT** → P4 |
| `tb_tp_rate` / `prec_tp_rate` | **PORT** → P11 |
| `by_entry_reason` (setup / fallback) | **PORT** → P5 |
| `by_rank` (1–2 / 3–5 / 6–8) | **PORT** → P6 (diagnostic) |
| Sleeve edge-score quartiles | **PORT** → P7; **drop pooled** as a gate input |
| `gate_pass_rate`, `wait_minutes`, entry composition | **PORT** → P8 / P9 |
| `fresh_flip` / `bars_since_regime_flip` | **PORT** → P9 diagnostic (Precision no-chase context) — not a Horizon metric |
| `check_rank_edge_polarity` | **DEMOTE** → P0 wiring sanity |
| Phase-2 experiment arms as acceptance | **DROP** — CLI/NO-LOCK; eval harness is Phase-1-default rules unless explicitly ablated |

---

## Top 5 to implement first (80% diagnostic value)

| Rank | Metric | Why |
|---|---|---|
| 1 | **P0** | Preconditions — cheapest binary fail-fast (causality, freeze, MIS, circuit, K parity) |
| 2 | **P1** | Does Precision skip worse naive paths? |
| 3 | **P2** | Core 1m value-add vs decision-close on fires |
| 4 | **P3** report + H5 precondition wiring | Absolute economics without false-failing on toxic books |
| 5 | **P5 + P11** | Setup/fallback + label monetization (WS0/WS1 ports) |

Second wave: P4, P6–P10, P1r, P2n, P3s, episode-block robustness, expiry/circuit/F&O Short slices.

*(Gemini preferred P2 before P1; locked order matches sibling fail-fast → skill → bridge pattern: P0 → P1 → P2 → P3.)*

---

## Anti-patterns (locked)

1. Scoring Precision with Regime index I1/I5  
2. Scoring Precision with Horizon H1 IC, or claiming rank skill from Precision fire PnL  
3. Pooling Long + Short into one acceptance number  
4. Locking wait / spread / conviction / K on Fold C  
5. Retuning Precision knobs against P1–P3 on the same selection fold without fresh A+B  
6. Bar-level binomial tests ignoring within-session autocorrelation  
7. Gating Precision **solely** on absolute net ≥ 0 while upstream H5 fails (category error — escalate Horizon/Regime)  
8. Recomputing TB widths from post-decision 1m data (lookahead)  
9. Assuming perfect passive limit fills that production does not model  
10. Putting `size_mult` inside confirmatory P1/P2/P3  
11. Promoting P6 rank-band inversion to a Precision gate (that is Horizon’s H3 job)  
12. Inventing new absolute bps / `tb_tp` floors as P3 unlocks instead of tying to Horizon H5  
13. Claiming cascade net ≥ 0 from Precision eval alone  

---

## Where judges disagreed

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| Overall | REVISE (8.5) | REVISE (6.5) | **REVISE → build** |
| P3 unlock | Numeric floors (NaiveNet ≥ −10 bps / `tb_tp ≥ 18%`) | Tie to Horizon H5 CI LB > 0 | **H5 CI LB > 0** (CI discipline) |
| P6 rank bands | Promote to Precision gate | Keep diagnostic (Horizon bleed) | **Diagnostic only** |
| P1/P2 formulas | Accept sketch | Must harden EV / denominator / exit clock / sizing | **Claude hardenings locked** |
| Implement #2/#3 | P2 then P1 | P1 then P2 | **P1 → P2** (sibling pattern) |
| Fill realism | Separate P12 metric | Fold into P0 checklist | **P0 + P9**; same fill rule as production |
| Capital velocity | Add P14 | Not prioritized | **Out of v1 harness** (optional later) |
| fresh_flip | Drop (Tier-2 state) | Port as hygiene | **Port under P9** (Precision no-chase context) |
| Absolute floors | Enthusiastic provisional | Reject until baselines | **CI LB > 0**; floors provisional commentary only |
| Min-N | Not specified | Long 100/30; Short 60/30 | **Claude floors locked** |

---

## NSE / India pitfalls (eval harness)

1. **Auction bleed** — exclude 09:30 from gated metrics.  
2. **MIS cutoffs** — Long ~14:15 / Short ~14:00 / live flat ~15:00 — no unrealizable windows.  
3. **Upper-circuit short traps** — cash short stuck in UC is catastrophic; circuit-hit windows → P0 exclude or max-adverse diagnostic.  
4. **Fill realism** — harness must match production Precision fill rule; do not silently assume better passive fills in eval than live.  
5. **Fallback mass** — WS1 showed Long fallback toxic and Short often 100% fallback; P5 is mandatory diagnostic even if not gated.  
6. **TIMEOUT dead zone** — large TO share with `tb_label=0` is upstream path geometry, not only Precision exit skill (P4 + P11).  
7. **Expiry days** — Thursday pinning; report expiry vs non-expiry; do not pollute pooled gates.  
8. **F&O / Short depth** — align with Horizon H7 Short eligibility staging.  
9. **Fold C** — COVID / circuit-halt quarantine — informational only.  
10. **Cost dual readout** — always print `c*=20` and archive `30` companions so old WS0/WS1 numbers remain comparable.

---

## Implementation sequence

1. Episode panel: attemptable registry + fired/skipped + skip_reason + NaiveTBPathEV + PrecNet (unsized), MIS/auction/circuit masks, frozen StockTB geometry.  
2. Preconditions: **P0** checklist + K/universe parity.  
3. Primaries: **P1 → P2 → P3(report)** on Folds A and B (Long/Short split, session-block bootstrap); wire H5 precondition for P3 promotion.  
4. Diagnostics: P4, P5, P6, P11 (WS ports), then P7–P10, P1r, P2n, P3s.  
5. Promote absolute commentary floors only after A+B baselines + upstream H5 clear — not before.

**Harness (planned):** `src/precision/eval/` + CLI  
`python -m src.experiments.eval_precision --train-period … --test-period … --direction both`  
(`--n-boot` default 500; Long/Short gated separately; Phase-1 rules default).

---

## Out of scope

- Redesigning Precision rules / features ([precision-tier3-verdict.md](precision-tier3-verdict.md))  
- Regime index evals / Horizon IC evals (separate tier harnesses)  
- Meta-label LightGBM take/skip ship gates (stage after rules P1/P2 clear on a non-blocked book)  
- Trailing stops / L2 fills as eval targets in v1  
- Using this harness to claim cascade net ≥ 0 while upstream H5 fails  

---

## Related docs

| Doc | Role |
|---|---|
| [precision-tier3-verdict.md](precision-tier3-verdict.md) | Locked rules / features this eval judges |
| [horizon-tier2-eval-verdict.md](horizon-tier2-eval-verdict.md) | Sibling harness; H5 is P3 unlock |
| [regime-tier1-eval-verdict.md](regime-tier1-eval-verdict.md) | Sibling filter-eval pattern |
| [triple-barrier-verdict.md](triple-barrier-verdict.md) | Frozen TB geometry, `c*`, H=6 |
| [cascade-tier3-ws01-verdict.md](archive/cascade-tier3-ws01-verdict.md) | Why absolute net alone is a category error on toxic books |
| [cascade-strategy-overview.md](cascade-strategy-overview.md) | Cascade contracts |
