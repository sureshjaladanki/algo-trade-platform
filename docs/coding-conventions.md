# Coding Conventions

Principles for writing and reviewing code in this repository.

## Clean, simple, readable

Prefer clarity over cleverness. A reader should understand intent without reconstructing hidden control flow.

- Keep functions focused on one job.
- Prefer straight-line logic and small helpers over nested conditionals.
- Comment *why* when the reason is not obvious; do not narrate *what* the code already says.

## Idempotent by language and context

Write operations so repeating them does not change the result beyond the first successful run, when that is natural for the language and domain.

- Prefer pure transforms where practical (`df in → df out`).
- File and pipeline steps should be safe to re-run (overwrite or skip completed work deliberately, not accidentally append/duplicate).
- Avoid hidden mutable globals; make side effects explicit.

## Minimal branching

Keep control flow shallow.

- Avoid unnecessary `if` / `else` and defensive nesting.
- Do **not** add null/None-safe checks “just in case.” Trust typed contracts and fail fast at the boundary when invariants break.
- Prefer early returns only when they flatten real complexity—not as a habit.

## Modular

Split by responsibility so modules stay small and composable.

- One module ≈ one concern (costs, tax, harness).
- Public functions accept and return clear data structures; keep private helpers prefixed with `_` when they are implementation detail.
- Share utilities instead of copy-pasting near-identical logic.

## Do not over-engineer

Solve the problem in front of you.

- No abstractions, frameworks, or config layers until a second concrete use demands them.
- No speculative generality (“might need later”).
- Prefer the simplest correct implementation that matches existing patterns in the repo.

## Clear nomenclature

Names should encode role and meaning.

| Kind | Convention | Examples |
|------|------------|----------|
| Modules / files | `snake_case` | `costs.py`, `daily_panel.py` |
| Functions | verb + object, `snake_case` | `round_trip_bps`, `load_daily_panel` |
| Variables | `snake_case`, domain terms | `trade_date`, `credit_retained`, `event_df` |
| Constants | `SCREAMING_SNAKE_CASE` | `STCG_RATE`, `SECTION_1256_BLEND`, `PDT_MIN_EQUITY` |
| Classes | `PascalCase` | when used |
| Private helpers | leading `_` | `_resolve_run`, `_load_dotenv` |
| DataFrame columns | stable, descriptive `snake_case` | `vti_close`, `knowledge_date`, `round_trip_bps` |

Prefer domain vocabulary already used in the blueprint (cost, tax, hurdle, sleeve, MDE) over inventing parallel synonyms.

## Respect repository conventions

Tooling, Poetry vs pip, and how to run Python: [repo-conventions.md](repo-conventions.md).

Match the surrounding code before introducing a new style.

- Follow existing package layout under `src/` (modules appear when a milestone needs them).
- Prefer established libraries and patterns already in use (typed function signatures; Polars pipelines once a panel milestone adds Polars).
- When editing a file, mirror its naming, import style, and structure rather than reformatting unrelated code.
- New docs under `docs/` use kebab-case filenames.

When in doubt: **read a nearby module and do the same thing, only simpler.**
