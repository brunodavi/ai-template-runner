# AGENTS.md

## Project

- Python CLI (`ait`) that runs Markdown+TOML templates through an LLM.
- Template syntax lives in README.md (source of truth) and in the live
  examples `examples/features/*` (each one executed by `test/test_cli.py`).
  This file holds work rules only — do not copy syntax here.
- Architecture decisions, device setup and benchmarks live in `docs/`
  (`architecture.md`, `termux.md`, `benchmarks.md`, `maintenance.md`) —
  point there, do not duplicate.

## Dev commands

- Run all tests: `uv run python -m unittest` (must run from repo root — tests import `src.ai_template_runner...` and `test.helpers`, which only resolve from the root).
- Run one test: `uv run python -m unittest test.test_process_prompt.TestProcessSystemPrompt.test_system_prompt_with_cmd`
- Setup after cloning: `uv sync && uv pip install -e .` (makes the `ait` CLI available).
- Runtime floor is 3.12 (CI matrix: 3.12/3.13/3.14). `.python-version` pins
  3.14 for dev; use `uv run` (never bare `python`) so the right interpreter
  and editable install are used.

## Work style

- TDD: for each change, write a failing test first, then implement until it passes.
  - Exception: utility scripts under `tmp/` (hand-run helpers, not part of
    the package) need no tests.
- Conventional Commits for every commit: `type: imperative subject` (e.g. `feat: add [out] engine`). Version bumps are `chore` commits.
- At the end of a change, commit in parts, in this order: `feat`, `test`, `docs`, `chore` (e.g. version bump) — each part gets its own commit.
- Before pushing a version tag: bump `version` in `pyproject.toml` AND refresh `uv.lock` (run `uv sync` so the lock reflects the new version).
- Every template feature added or changed in a release must land in `examples/features/` (as a new example or an update to an existing one) with its behavior pinned by a test in `test/test_cli.py`.
- A release needs a `## [X.Y.Z]` CHANGELOG.md section matching the tag —
  release.yml extracts it verbatim and hard-fails when tag ≠ pyproject version.
- tmp/ is fully local (gitignored, script included): never commit anything under it.
- Benchmark data (behavioral or `llama-bench` hardware curves) flows through
  `tmp/bench.sh` → `tmp/bench.txt` → `docs/benchmarks.md`; models are always
  named by the llama.cpp build identity, never by local file aliases.
- If the conversation defines or changes a work rule: the agent proposes the AGENTS.md diff at the end of the task and only commits after user approval.

## Gotchas

Only what blocks work every session, with a proven failure behind it.
Syntax belongs to README.md and `examples/features/`.

- Literal `{`/`}` in prompts must be doubled to `{{`/`}}` — every prompt goes through `str.format`.
- Every annotation in `models/` must be resolvable with eager annotation
  evaluation (Python 3.12/3.13): missing imports there fail only on those
  versions. Pinned by `TestTemplateAnnotations`.
- `Template(user_prompt, system_prompt='', ...)`: the first positional arg is `user_prompt`.
- Provider requires `base_url`/`model`; validation lives in `processor.py`, not the dataclass.
- `examples/features/*` are executed by the suite: editing an example (or its placeholders) can break tests.
