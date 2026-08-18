# Horizon Fresh — Quarantine Index

**Date:** 2026-08-16  
**Authority:** [horizon-fresh-architecture-implementation-plan.md](../next/horizon-fresh-architecture-implementation-plan.md) M0  
**Rule:** CLOSED Horizon peeks are **audit-only**. Do not grow them; do not run new peeks on the production Top-K book under “fresh” naming.

Live production Horizon eval remains `src/horizon/eval/__init__.py` gates (H1–H5) + `src/pipelines/horizon_pipeline.py`. Fresh work lives under `src/horizon/fresh/`.

---

## Audit-only — `src/horizon/eval/`

| Module | CLOSED ledger |
|---|---|
| `admission.py` | Tier-2 admission / rank-tier / veto-head |
| `path_quality_veto.py` | Path-quality veto |
| `tp_floor.py` | TP-floor recalibration |
| `mfe_decay.py` | Exit MFE decay |
| `ev_net_rebuild.py` | EV-net rebuild Step 0 (STOP) |
| `short_travel.py` | Short travel separation |
| `capacity.py` | Short capacity |
| `architecture.py` | Short architecture |
| `path_density.py` | Path-density |

**Still live (not quarantined):** `gates.py`, `bar_stats.py`, `panel.py`, `diagnostics.py`, `long_eval.py`, `short_eval.py`, `constants.py`, `nifty50_pit.py`, `__init__.py`.

---

## Audit-only — `src/experiments/`

| Script | Role |
|---|---|
| `analyze_horizon_admission.py` | Admission analyze |
| `analyze_horizon_path_quality_veto.py` | Veto analyze |
| `analyze_horizon_path_density.py` | Path density |
| `analyze_horizon_tp_floor.py` | TP floor |
| `analyze_horizon_mfe_decay.py` | MFE decay |
| `analyze_horizon_architecture.py` | Short architecture |
| `analyze_horizon_short_travel.py` | Short travel |
| `analyze_horizon_short_capacity.py` | Short capacity |
| `analyze_horizon_ev_net_step0.py` | EV-net Step 0 (**baseline reprint OK**) |
| `eval_horizon_admission_peek1.py` | Peek-1 |
| `eval_horizon_path_quality_veto_peek1.py` | Peek-1 |

**Still live:** `eval_horizon.py`, `test_horizon_pipeline.py`.

---

## Fresh (live build track)

| Path | Milestone |
|---|---|
| `src/horizon/fresh/` | M0+ package |
| `src/labels/fresh_barrier.py` | M1/M5 absolute / MIS labels |
| `src/experiments/materialize_golden_parquet.py` | M0 Parquet |
| `src/experiments/eval_horizon_fresh_*.py` | M1+ fresh harnesses |

---

## Archived docs (do not reopen as peeks)

See `docs/archive/horizon-*-{charter,stop-memo}.md` — especially `horizon-ev-net-rebuild-stop-memo.md`. Design authority for the replacement hypothesis: `docs/next/horizon-fresh-architecture-blueprint.md`.
