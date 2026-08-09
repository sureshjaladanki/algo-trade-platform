# Tier 3 WS0/WS1 Verdict — Path Audit & Upstream Escalation

**Market:** NSE India, Nifty 100, intraday MIS cash  
**Date:** 2026-08-09  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Depends on:** [cascade-selectivity-tweak-plan.md](cascade-selectivity-tweak-plan.md), [cascade-strategy-overview.md](cascade-strategy-overview.md), [precision-tier3-verdict.md](precision-tier3-verdict.md)  
**Frozen rules baseline:** Phase 1 only — `TOP_K=5` + shared median conviction gate. No-chase / #10 stay **NO-LOCK** / CLI-only.  
**Status:** **WS0 / WS1 CLOSED as interpreted (Fold A).** Diagnostic code removed from Precision pipeline after one-shot measurement. Next focus = **Horizon / Regime** (not more Precision knobs).

**Evidence runs (Fold A, train 2015–2017 → test 2018):**

| Arm | Run | Flags |
|---|---|---|
| Phase 1 base | `9466a013` | `no_chase=False`, `top_k=5`, conviction gate ON |
| No-chase pooled | `d595a237` | `--no-chase --no-chase-rank-max 5` |

---

## Locked verdict

| Question | Answer |
|---|---|
| Is no-chase a real lift on Fold A? | **Yes** — blended net −16.2 → −13.0 bps (+3.1); A-Short −5.5 → ~0 (+5.5) |
| Promote no-chase / #10? | **No** — absolute ≥0 unmet; gross ~17 bps ≪ 30; stays CLI-only |
| Is A-Short ~0 a top-decile artifact? | **Not on Fold A alone** — top-decile positive-gross share ~34%; morning-skewed; still need Fold B |
| Is Precision under-monetizing good TB labels? | **No (main mass)** — `prec_tp` ≥ `tb_tp`; under-monetize on rare +1 labels only ~14–25% |
| Are we over-firing bad paths? | **Yes** — ~88–93% of fires have `tb_label ≠ +1` |
| Are Regime + Horizon filtering well enough? | **No** — `tb_tp_rate` only ~7–12% in admitted fires; ranks 1–2 worse than 3–5 |
| Next Precision rules arm (WS2)? | **Skip** — label gap says escalate upstream, not another runway/fallback knob |
| Meta as next headline? | **Demote** until Horizon/Regime path quality improves; offline scaffolding optional only |
| Keep WS0/WS1 audit code in repo? | **No** — one-shot investigation done; removed from pipeline (this doc is the record) |

**One-line:** Tier 3 selectivity cannot clear 30 bps while the Horizon registry rarely supplies `tb_label=+1` paths; escalate Regime + Horizon diagnostics / model quality.

---

## Fold A headline (bps)

| Metric | Phase 1 | No-chase pooled | Δ |
|---|---:|---:|---:|
| Fires | 2265 | 1765 | −500 |
| Fire % | 69.5% | 54.2% | −15.3 pp |
| Mean gross | +13.8 | +17.0 | +3.2 |
| Mean net | **−16.2** | **−13.0** | +3.1 |
| Long n / net | 1353 / **−23.3** | 1070 / **−21.7** | +1.6 |
| Short n / net | 912 / **−5.5** | 695 / **~0** | +5.5 |

Absolute gates still fail. Matches prior selectivity-plan no-chase pooled read.

---

## WS0 — A-Short decompose (no-chase pooled, n=695)

| Check | Result |
|---|---|
| Mean / median net | ~**0** / **−0.9** bps |
| Top-decile positive-gross share | **34%** (below 45% artifact flag) |
| Exit mix | TP 18.7% / SL 13.1% / **TO 67.9%** |
| Entry | **100% fallback** |
| TOD net | morning **+16** (n=294) · midday **−10** (n=379) · afternoon **−32** (n=22 thin) |
| Rank net | 1–2 **−12** · 3–5 **+6** |
| Cross-fold | **Not done** — Fold B required before any durable Short claim |

**WS0b non-promotion (locked text):** Phase 1 base remains sole production default; `--no-chase` / `--skip-rank-1-2` stay NO-LOCK / off-by-default; cite relative lifts only; never claim absolute net ≥0 from these arms; #10 closed as production experiment.

---

## WS1a — Path quality (no-chase)

| Finding | Observation |
|---|---|
| Primary drag | **`long/fallback`** (n=893, net **−26** bps) |
| TIMEOUT | Still **~59%** of exits (1048/1765) |
| Fresh flips | Removed by construction (Long fresh was −30 bps / SL 40%; Short fresh −27 bps / TP 6%) |
| Rank inversion | 1–2 **−20** vs 3–5 **−9** — persists after no-chase |
| Runway split | All fills in 41–60m band — no short-runway lever on this sample |

No-chase helps by deleting flip-chase toxicity. It does **not** fix TIMEOUT mass or Long fallback.

---

## WS1b — Rules vs `tb_label_*`

| Sleeve (no-chase) | `tb_tp_rate` | `prec_tp_rate` | Over-fire non-+1 | Under-monetize |
|---|---:|---:|---:|---:|
| Long | **7.4%** | 9.5% | **93%** | 25% |
| Short | **12.2%** | 18.7% | **88%** | 14% |

~86% of TIMEOUTs are `tb_label=0` (dead zone).

**Decision tree call:** `escalate_horizon_regime` — `tb_label=+1` rare in the admitted book. Not a Precision under-monetization story.

---

## WS1 upstream smoke

| Flag | Phase 1 | No-chase |
|---|---|---|
| `rank_1_2_worse_than_3_5` | True | True |
| `low_tb_tp_rate_flag` (<20%) | True | True |

Regime + Horizon are structurally gating sleeves/names but **not** delivering economically selectable top-K paths under 30 bps friction.

---

## What this changes in the plan

| Prior step | Post–Fold-A WS0/WS1 |
|---|---|
| Optional WS2 fallback/runway rules | **Defer / skip** unless Horizon lifts `tb_tp_rate` |
| Meta offline as next eng headline | **Behind** Horizon/Regime path-quality work |
| Fold C Regime/Horizon audit | **Elevate** as peer to A/B Horizon IC / rank monotone / sleeve purity — still never a Precision lock input |
| Precision Phase 1 default | **Unchanged** |

---

## Explicit non-goals (unchanged)

- Promote no-chase / #10  
- Widen TP/SL, trail, wait 5→8m  
- Lock thresholds from Fold C  
- Put portfolio kill-switches inside Precision fire logic  
- Claim rules selectivity exhausted *as a research statement* without upstream work — **path selection** at Tier 3 is near-exhausted relative to label rarity  

---

## Code posture

WS0/WS1 audit module was a **one-shot measurement harness**. After Fold A interpretation it is **removed** from `precision_pipeline` / experiment runners so every run does not pay for nested MLflow spam. Existing Phase 2 diagnostics (`diagnose_rank_root_cause`, `audit_entry_composition`) and summary slices remain. Fill-time geometry columns on trade rows (`bars_to_vertical`, `dist_to_tp_bps`, `dist_to_sl_bps`, `spread_proxy_bps`) are **kept** for future meta / research joins.

Re-run Fold B Phase 1 vs no-chase pooled only if needed to close WS0 cross-fold; do not rebuild the audit suite into the default pipeline unless a new measurement cycle opens.

---

## Related

| Doc | Role |
|---|---|
| [cascade-selectivity-tweak-plan.md](cascade-selectivity-tweak-plan.md) | Phase 0–2 evidence + locks |
| [precision-tier3-verdict.md](precision-tier3-verdict.md) | Rules + staged meta contract |
| [cascade-strategy-overview.md](cascade-strategy-overview.md) | Narrow-downward cascade |
| [horizon-tier2-verdict.md](horizon-tier2-verdict.md) | Next escalation owner (ranking / IC) |
| [regime-tier1-verdict.md](regime-tier1-verdict.md) | Next escalation owner (sleeve purity) |
