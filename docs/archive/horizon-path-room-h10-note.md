"""Pre-first-peek path-room circularity / H10 note (Horizon v2 step 4).

**Status:** LOCKED note — first build may include path-room features; first gated
A+B claim requires this note. Do **not** treat path-room as proven path skill.

**Depends on:** [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md),
[triple-barrier-verdict.md](../triple-barrier-verdict.md)

---

## What path-room encodes

| Feature | Definition | Geometry link |
|---|---|---|
| `tp_room_atr_long` | `TP_FLOOR_LONG (90bps) / rv_15_mean` | Same causal TOD `rv` as TB `atr_pct` |
| `tp_room_atr_short` | `TP_FLOOR_SHORT (75bps) / rv_15_mean` | Same |
| `sl_room_atr` | `SL_FLOOR (45bps) / rv_15_mean` | Same |
| `bars_to_mis_exit` | `min(bars to MIS_EXIT_BAR_END, H_BARS)` | Vertical budget |
| `range_compress_4` | `rv_15_mean / trailing_4bar_range%` | Coiling vs spent |
| `path_efficiency_4` | `\|net 4-bar ret\| / sum\|r\|` | Trend quality vs chop |
| `pullback_depth_atr` | `(4-bar high − close) / rv_15_mean` | Long continuation room |

`rv_15_mean` is **causal same-clock** absolute range baseline (prior sessions only) —
identical family to TB barrier denominator. No same-bar forward path, no daily ATR,
no label-window quantity.

---

## Circularity risk (why H10-style discipline)

`tp_room_*` is a **barrier-geometry transform**, not free alpha.

Long eligibility (`tb_eligible_long`) fires when `2.5 × rv ≥ 90bps` ⇒ `rv ≥ 36bps`.
At that boundary `tp_room_atr_long = 90/rv ≤ 2.5`. Quiet names have large
`tp_room_*` and fail eligibility; loud names have small `tp_room_*` and clear floors
via vol multiples.

So model scores that collapse to “prefer low `tp_room_*`” can reconstruct eligibility
/ horizontal-barrier geometry. That is **not** lookahead leakage, but it **is**
objective tautology risk under StockTB+1 labels.

---

## Audit rules (before first gated claim)

1. **Include** path-room in the first v2 build (charter allows).  
2. **Do not claim** path skill from path-room alone.  
3. Pre-registered ablation (counts as one peek lever when run): train/eval with
   path-room features dropped; if H5 / Top-K TB+1 lift vanishes vs the path-room
   model while H1/H2 stay similar, treat path-room as tautology and demote.  
4. Optional diagnostic: Spearman of `tp_room_atr_*` vs `tb_eligible_*` / `tb_label_*`
   on the holdout sleeve — report-only; high |ρ| with eligibility is expected.  
5. H10 null-score harness (`h10_null_leakage`) remains the score-shuffle
   precondition; path-room does not replace it.

### Free diagnostic results (2026-08-12) — report only, no peek

**Harness:** `python -m src.experiments.analyze_horizon_path_room --folds A,B`  
**Log:** `logs/horizon_path_room_h10_diag_ab.txt`

| Fold · side | ρ(tp_room, eligible) sleeve | ρ(tp_room, TB=+1) eligible | Read |
|---|---:|---:|---|
| A Long | **−0.83** | +0.023 | Geometry OK; label link weak |
| A Short | **−0.84** | +0.043 | Same |
| B Long | **−0.76** | +0.022 | Same |
| B Short | **−0.79** | +0.027 | Same |

**Also (baseline S2 free re-read):** Short morning H5 positive both folds; afternoon mixed/thin — **not** a clean PM-entry-cut case (do not pre-commit afternoon cut from this).

**Lock:** High |ρ| with eligibility is **expected** barrier geometry (quiet ⇒ large `tp_room` ⇒ ineligible). Weak eligible-label ρ does **not** clear path-room as alpha — gated claim still requires ablation peek (`--ablate-path-room`). Do not promote path-room to proven path skill from this table alone.

### Peek 2 ablation outcome (2026-08-12) — demote

Ablating path-room **raised** H5 / Top-K TB+1 vs the path-room-on baseline (see [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md) peek-2 table). That is the opposite of the tautology failure mode in rule #3 — path-room was **hurting** selection. **Demote** `PATH_ROOM_FEATURES` from default `LONG_FEATURES` / `SHORT_FEATURES`; keep the constant + `--ablate-path-room` / reverse flag only if a later charter re-tests inclusion.

---

## Code

- Features: `src/features/horizon.py`  
- Model lists: `PATH_ROOM_FEATURES` / `LONG_FEATURES` / `SHORT_FEATURES` /
  `features_for_direction(..., ablate_path_room=)` in `src/horizon/horizon_model.py`
- Free diagnostic: `src/experiments/analyze_horizon_path_room.py`
- Ablation peek: `python -m src.experiments.eval_horizon --ablate-path-room ...`
