# Algo Trade Platform

Retail India desk for listed NSE/BSE equities.

This is an **orphan** of the US-equity tree. That programme's source and archive are not on this branch.

## Setup

Python 3.12 and Poetry. Conventions: [docs/repo-conventions.md](docs/repo-conventions.md), [docs/coding-conventions.md](docs/coding-conventions.md).

Copy `.env.example` to `.env`. `.env` is gitignored.

```powershell
poetry install --with dev
poetry run pre-commit install
poetry run pytest
```

## Layout

| Path | Role |
|---|---|
| `src/` | Python package. Modules are added when a milestone needs them. `harness` is H0; `books/ledger` is L1; `portfolio` is L2; `execute` / `ops` are L0 (paper). |
| `tests/` | Pytest |
| `docs/next/` | Active charter: [architecture blueprint](docs/next/india-equity-architecture-blueprint.md), [execution plan](docs/next/india-equity-execution-plan.md) |
| `docs/archive/` | STOP memos, once a book closes |
| `data/` | Panels (gitignored except `.gitkeep`) |
| `logs/` | Run output (gitignored except `.gitkeep`) |

## Not in v1

Runtime libraries (Polars, Kaggle client, …) are added with Poetry when a milestone imports them.
