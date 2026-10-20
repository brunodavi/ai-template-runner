# AGENTS.md

## Project

- Python CLI (`ait`) that runs Markdown+TOML templates through an LLM.
- Template syntax lives in README.md (source of truth) and in the live
  examples `examples/features/*` (each one executed by `test/test_cli.py`).
  This file holds work rules only — do not copy syntax here.

## Dev commands

- Run all tests: `uv run python -m unittest` (must run from repo root — tests import `src.ai_template_runner...` and `test.helpers`, which only resolve from the root).
- Run one test: `uv run python -m unittest test.test_process_prompt.TestProcessSystemPrompt.test_system_prompt_with_cmd`
- Setup after cloning: `uv sync && uv pip install -e .` (makes the `ait` CLI available).
- Python 3.14 pinned in `.python-version`; use `uv run` (never bare `python`) so the right interpreter and editable install are used.

## Work style

- TDD: for each change, write a failing test first, then implement until it passes.
- Conventional Commits for every commit: `type: imperative subject` (e.g. `feat: add [out] engine`). Version bumps are `chore` commits.
- At the end of a change, commit in parts, in this order: `feat`, `test`, `docs`, `chore` (e.g. version bump) — each part gets its own commit.
- Before pushing a version tag: bump `version` in `pyproject.toml` AND refresh `uv.lock` (run `uv sync` so the lock reflects the new version).
- Every template feature added or changed in a release must land in `examples/features/` (as a new example or an update to an existing one) with its behavior pinned by a test in `test/test_cli.py`.
- If the conversation defines or changes a work rule: the agent proposes the AGENTS.md diff at the end of the task and only commits after user approval.

## Gotchas

Only what blocks work every session, with a proven failure behind it.
Syntax belongs to README.md and `examples/features/`.

- Literal `{`/`}` in prompts must be doubled to `{{`/`}}` — every prompt goes through `str.format`.
- `Template(user_prompt, system_prompt='', ...)`: the first positional arg is `user_prompt`.
- Provider requires `base_url`/`model`; validation lives in `processor.py`, not the dataclass.
- `examples/features/*` are executed by the suite: editing an example (or its placeholders) can break tests.
