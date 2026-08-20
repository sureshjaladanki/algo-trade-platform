# Algo Trade Platform

Retail US desk for listed equities and related retail-accessible products (ETFs, listed index options, micro index futures). Capital envelope $25k–$500k. Passive VTI core plus pre-registered active sleeves that must beat an after-tax VTI hold.

This is an **orphan** of the forced-flow tree. That programme's source and archive are not on this branch.

## Authority

- [Architecture blueprint](docs/next/us-equity-architecture-blueprint.md) (Rev 1)
- [Execution plan](docs/next/us-equity-execution-plan.md)

## Setup

Python 3.12 and Poetry. Conventions: [docs/repo-conventions.md](docs/repo-conventions.md), [docs/coding-conventions.md](docs/coding-conventions.md).

```powershell
poetry install --with dev
poetry run pre-commit install
poetry run pytest
```

## Layout

| Path | Role |
|---|---|
| `src/` | Python package. Modules (`costs`, `tax`, …) are added when a milestone needs them. |
| `tests/` | Pytest |
| `docs/next/` | Active blueprint and plan |
| `docs/archive/` | STOP memos, once a book closes |
| `data/` | Panels (gitignored except `.gitkeep`) |
| `logs/` | Run output (gitignored except `.gitkeep`) |

## Not in v1

No tick replay, event bus, Redis, Kubernetes, MLflow, HMM, LightGBM, short stock, naked short options, or live capital used as a research lab. A passing book needs a daily instruction list, an audit record, and broker reconciliation — after L0, not before. Runtime libraries (Polars, …) are added with Poetry when a milestone imports them.
