# AGENTS.md

## Dev commands

- Run all tests: `uv run python -m unittest` (must run from repo root — tests import `src.ai_template_runner...` and `test.helpers`, which only resolve from the root).
- Run one test: `uv run python -m unittest test.test_process_prompt.TestProcessSystemPrompt.test_system_prompt_with_cmd`
- Setup after cloning: `uv sync && uv pip install -e .` (makes the `ait` CLI available).
- Python 3.14 pinned in `.python-version`; use `uv run` (never bare `python`) so the right interpreter and editable install are used.

## Work style

- TDD: for each change, write a failing test first, then implement until it passes.

## Template format (v1.0.0)

- Templates must start with a ` ```toml ` config block; two `---` lines delimit an optional system prompt; the rest is the user prompt.
- No legacy `+++` support — don't reintroduce it; tests in `test/test_process_template.py` deliberately assert old-format templates are rejected.

## Gotchas

- `examples/features/*.md` are not just docs: `test/test_cli.py` runs them. **Rule: every template feature added or changed in a release must land in `examples/features/` as a new example or an update to an existing one** (so the feature is exercisable and its behavior is pinned by a test). Current mapping: `output.md` = `[out]` render from JSON fields, `transforms.md` = `[[out.<method>]]` steps in document order + inline `:spec` and `[slice]`. Editing an example (or its placeholders) can break tests. `examples/features/system.md` is the only one with a system prompt. The examples echo the template body (prompt text) before the AI output, so `assertNotIn` on the whole stdout must target raw JSON tokens (e.g. `'"type": "feat"'`), not words that legitimately appear in the prompt body. Task templates live directly in `examples/` (e.g. `email-subject.md`, `conventional-commits.md`) and are not used by tests.
- Templates may declare `extends = '<path>'` as the first TOML key; the path is resolved relative to the template file (e.g. `../base.md` from `examples/features/`). Parent provider/cmd configs merge per key and empty child prompts inherit parent prompts — so a child can override just the user prompt. Literal `{`/`}` in prompts (JSON examples) must be doubled to `{{`/`}}` because both prompts go through `str.format`.
- `src/ai_template_runner/models/template.py`: `Template(user_prompt, system_prompt='', ...)` — first positional arg is `user_prompt`.
- Provider config is validated in `processor.py`, not the dataclass: missing `base_url`/`model` raises `ValueError` there.
- `examples/simulation/` contains live simulations of task templates (e.g. `conventional-commits/*.md` extends the task with pre-filled git fixtures; only the user prompt is local). Each one carries its own `[test]` table (`type = '<expected commit type>'`) and is validated live with `ait run <file> --test` (exit code 1 on failure, requires the llama.cpp server up) — keep fixtures brace-escaped (`{` → `{{`).
- `[test]` table has reserved keys `text`, `text_contains`, `text_regex`; every other key is a dotted path into the parsed JSON output. `--test` prints PASS/FAIL to stderr and exits 1 on failure. `run_checks` lives in `checks.py`.
- `[out]` table renders the display output: `text` is a render template over parsed JSON fields (`{out.field}`, missing → `''`); `[[out.<method>]]` tables are steps in real document order (empty table = no args, populated = named args mapped positionally by the real `str` signature; `slice` is the only helper). Inline single step `{out.field:method:arg1:arg2}` and pythonic `{out.field[1:]}` come from the `Smart` wrapper in `output.py` — transforms exist ONLY in the `:spec`/`[[out.x]]` channels, never as attribute names (a JSON field named `count` stays data). `--test` still validates the raw response; engine tests in `test/test_output.py`. The same `Smart` also powers `{question}` (None stays raw → 'None') and `{cmd.*}` (`Command.__getattr__` returns `Smart`, commands still run lazily per attribute access) — tests in `test/test_process_prompt.py::TestSmartPromptInterpolation`.
