# Repo conventions

How this repository is set up and how to work in it. Style and code-shape rules live in [coding-conventions.md](coding-conventions.md).

## Package manager: Poetry, not pip

Dependencies are declared in `pyproject.toml` and locked in `poetry.lock`. There is no `requirements.txt`.

| Do | Do not |
|----|--------|
| `poetry add <pkg>` | `pip install <pkg>` into `.venv` |
| `poetry add --group dev <pkg>` | `pip install -r …` |
| `poetry install --with dev` | create a second venv with `python -m venv` |
| `poetry run python …` / `poetry run pytest` | `python` / `pip` on the system interpreter |

Poetry keeps the env in-project at `.venv/` (`virtualenvs.in-project`). That folder is gitignored. `pip` still exists *inside* the venv; do not use it to add project packages.

### Everyday commands

```powershell
poetry install --with dev          # clone / refresh env from the lockfile
poetry add polars                  # runtime dependency, when a milestone imports it
poetry add --group dev pytest      # test / lint / hook dependency
poetry lock                        # refresh lockfile after a manual pyproject edit
poetry run python -m src
poetry run pytest
poetry run ruff check src tests
```

If a module is missing, add it with Poetry and commit both `pyproject.toml` and `poetry.lock`. Do not `pip install` to “just make it work.”

Add a runtime package only when a milestone needs it. v1 does not include HMM, LightGBM, MLflow, or Kaggle clients. Polars is not a seed dependency; add it when a panel milestone imports it.

## Running Python

Always go through Poetry so the interpreter matches the lockfile:

```powershell
poetry run python -m src
poetry run pytest
```

Prefer `python -m package.module` over calling a `.py` file by path.

## Tests and lint

- Tests live under `tests/`. Run with `poetry run pytest`.
- Lint is Ruff via pre-commit. After clone: `poetry run pre-commit install`.
- Do not add a second linter or formatter unless the repo already uses it.

## Layout

| Path | Role |
|------|------|
| `src/` | Python package. First milestones add `costs` and `tax`; later ones add `universe`, `panel`, `harness`, `books`, `portfolio`, `execute`, `ops`. |
| `tests/` | Pytest |
| `docs/` | Verdicts, charters, conventions (kebab-case filenames) |
| `data/` | Downloaded / generated data (gitignored except `.gitkeep`) |
| `logs/` | Experiment output (gitignored except `.gitkeep`) |

New docs go under `docs/` with kebab-case names. STOP memos and closed-programme summaries belong in `docs/archive/`; active next work in `docs/next/`.

## Cursor / agents

Agents must follow this file and [coding-conventions.md](coding-conventions.md). In particular: install and run through Poetry; never `pip install` a project dependency.
