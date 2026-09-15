# Agent guidelines

How agents talk in this repo. Code style is in [coding-conventions.md](coding-conventions.md). Tooling is in [repo-conventions.md](repo-conventions.md).

## All models: readable replies

Write for a person who wants the answer, not a report.

- Use plain English. Prefer everyday words over domain jargon. If a term is required (sleeve, hurdle, MDE), define it once, then use it.
- Keep replies short. Say the outcome, then only the detail needed to act on it.
- Completeness still matters: include the decision, the files touched, and the next step. Cut the diary of how you got there.
- Do not recap the whole task, narrate tool calls, or write journal-style sections the user did not ask for.

```text
# ❌ BAD
I started by exploring the repository structure, then I reviewed the relevant
modules, after which I implemented a carefully considered change to the cost
path. In this write-up I will walk through the background, the options I
considered, and a detailed rationale for each edit.

# ✅ GOOD
Updated `src/costs.py` so round-trip cost uses the same bps as the hurdle
check. Tests: `poetry run pytest tests/test_costs.py`.
```

## Non-Cursor, non-Grok models: sub-agents only

Parent work stays on Cursor-included models (including Grok). Non-Cursor, non-Grok models (Claude, Gemini, and other billed models) run **only as sub-agents**, and only after the Cursor parent has packed the prompt.

Do not use a billed model as the parent agent. If this session is already a billed parent, do not launch more billed sub-agents; ask the user to switch the parent to a Cursor model.

### Cursor parent packs context first

Before starting a billed sub-agent, the Cursor parent does the cheap work:

1. Search, read, and decide the job on the parent.
2. Write a prompt with one job, a **complete fact picture**, and what to return. Pack means compact, not thin: include every constraint, decision, path, and quote the sub-agent needs. Do not omit facts to save tokens.
3. Do not forward chat history, these guidelines, whole files, or long logs. Point to paths and symbols; quote only the lines that matter.

```text
# ❌ BAD
Launch a billed model as the parent, or pass it five full modules plus the
last three chat turns. Or pass a one-liner that leaves out constraints.

# ✅ GOOD
Cursor parent finds the cost module, then launches a billed sub-agent with:
Job: check round-trip cost vs hurdle. Path: src/costs.py, function
round_trip_bps. Constraint: hurdle uses the same bps; do not change the
hurdle formula. Quote: `cost_bps = 2 * one_way_bps`. Return: file, function,
and whether they match. Do not paste the whole file.
```
