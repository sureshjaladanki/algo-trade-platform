# Algo Trade Platform

Retail India desk for **forced-flow corporate events** on NSE: index reconstitution and F&O universe changes, cash delivery, low frequency.

This is an **orphan** of the cascade tree. Closed programmes (cash MIS, remaining-session vol, same-session fade) are summarized under `docs/archive/` and are not in source.

## Authority

- [Architecture blueprint](docs/next/forced-flow-architecture-blueprint.md) (Rev 2)
- [Execution plan](docs/next/forced-flow-execution-plan.md)
- [Freeze note](docs/archive/forced-flow-freeze-note.md)

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
| `src/events/` | Event pool, ranking, cost and tax constants |
| `tests/` | Pytest |
| `docs/next/` | Active blueprint and plan |
| `docs/archive/` | Closed-programme summaries and later gate memos |
| `data/` | Panels (gitignored except `.gitkeep`) |
| `logs/` | Fold output (gitignored except `.gitkeep`) |

## Not in v1

No tick feed, event bus, Redis, options chain, HMM, ranker, or paper-MIS stack. A passing book needs a daily instruction list, an audit record, and broker reconciliation — after F2, not before.
