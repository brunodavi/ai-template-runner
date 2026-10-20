# Architecture

This document explains *why* the code is shaped the way it is, for contributors.
The template syntax itself is documented in the [README](../README.md) and pinned
by executable examples in [`examples/features/`](../examples/features/).

## Design principles

1. **Zero runtime dependencies.** The package runs with the standard library only
   (`urllib`, `tomllib`, `subprocess`, `json`, `argparse`). This matters for the
   primary target environment — constrained devices running Termux/llama.cpp —
   where every extra wheel is friction.
2. **Templates are data, not code.** Everything the user can change lives in the
   Markdown+TOML template: configuration, prompts, commands, validation and
   output rendering. The Python code never needs to change to create a new
   workflow; it only needs to change to add a new template *feature*.
3. **Every feature is pinned by an example.** `examples/` files double as
   documentation and as test fixtures — `test/test_cli.py` executes them, so an
   edit that breaks an example breaks the suite.

## Module map

```
src/ai_template_runner/
├── cli.py            # argparse entrypoint: run -q -t; ties the pipeline together
├── processor.py      # parse, extends inheritance, interpolation, validation guard
├── command.py        # lazy shell commands behind {cmd.*} placeholders
├── output.py         # the [out] engine: rendering, transforms, Smart wrapper
├── checks.py         # the [test] table: response validation
├── providers.py      # HTTP call to an OpenAI-compatible chat endpoint
└── models/
    ├── provider.py   # dataclass of generation parameters
    └── template.py   # dataclass holding the fully-promoted template state
```

The pipeline in `cli.py` is linear on purpose:

```
process_template(path)      → Template
process_prompt(template)    → interpolated user prompt
process_system_prompt(...)  → interpolated system prompt
llamacpp(provider, ...)     → response JSON
run_checks([test], text)    → PASS/FAIL, stderr, exit code
render_out([out], text)     → stdout
```

## Decisions worth knowing

### Parsing lives in `processor.py`, not in the dataclasses

`models/provider.py` and `models/template.py` are plain dataclasses/bags of
fields. Validation (e.g. "provider requires `base_url` and `model`", "template
must begin with a ` ```toml ` block", "unclosed block") is centralized in
`processor.py::process_template`/`load_template`, so every error message comes
from one place. The dataclasses do one thing: carry promoted state from parse
time into the render pipeline.

### `extends` resolves lazily with a cycle stack

`load_template` recurses through the `extends` chain before any config is
promoted, passing a `frozenset` of resolved parent paths — a visited-set that
turns circular inheritance into a clean `ValueError` instead of infinite
recursion. Paths resolve relative to the child template file, which is what
makes `examples/features/*.md` relocatable with `extends = '../base.md'`.

Config merge (`merge_configs`) is recursive per table level with child-wins
semantics; prompts fall back to the parent only when the child prompt is empty.
This asymmetry (values merge, empty strings fall back) is what makes "question
specializations" possible: one `base.md` prompt chain, many one-line children.

### `[[out.<method>]]` headers are numbered before parsing

`tomllib` groups array-of-tables by key and loses cross-key document order, but
`[out]` transform steps *must* run in the order they are written. `processor.py`
calls `output.py::number_out_headers` before `tomllib.loads`, giving each
`[[out.replace]]`-style header a unique `-1`, `-2`, ... suffix; `build_out`
strips the suffix and rebuilds an ordered steps list. The suffix pattern is
chosen so numbering is idempotent (never applied twice).

### `Smart` is the transform boundary

`output.py::Smart` subclasses `str` so that field transforms ride the existing
`str.format` machinery instead of a bespoke mini-language:

- `__getitem__` maps `'1:'`-style keys from `{field[1:]}` to a real `slice`.
- `__format__` maps `{field:replace:a:b}` to one `apply_op` step.

The `{cmd.*}` values are also `Smart`, but lazy: `command.py` builds the
subprocess result only when a field of the command is *actually used* in an
interpolation. This is also why `{question}`-style transforms work everywhere —
they are the same wrapper, not special cases.

### Transforms and checks never share a namespace

Attribute access on `Rec` (JSON fields) and on `Command` is data-only: a field
called `count` must not resolve to `str.count`. That is enforced by wrapping in
`Rec`/`Smart` rather than by name sanitization, and pinned by tests
(`test/test_output.py`, `test/test_command.py`).

### `[test]` fails, never raises

`checks.py::run_checks` converts every kind of bad input (invalid JSON, missing
fields, invalid regex) into a `FAIL CheckResult` with a detail string instead of
throwing. The exit-code contract lives in `cli.py`: stdout stays clean for
pipes, PASS/FAIL goes to stderr, exit `1` on any failure — so templates are
safe to use as build steps.

### One provider, one URL

`providers.py::llamacpp` posts an OpenAI-ish chat payload to any endpoint
llama.cpp/Ollama/LM Studio serve. llama.cpp-only sampling options travel in
`[provider.extras]`, which avoids a growing zoo of first-class fields while
keeping the common parameters explicit.

## Testing conventions

- `uv run python -m unittest` from the repository root (imports of
  `src.ai_template_runner.*` and `test.helpers` resolve only from there).
- Runtime floor is Python 3.12 and CI enforces it on 3.12/3.13/3.14.
- Template behavior goes into `examples/features/*` + `test/test_cli.py`;
  unit-level edge cases go into the matching `test/test_*.py`.
- Support for Python versions with eager annotation evaluation clarified an
  existing rule: every annotation in `models/` must be importable (see
  `TestTemplateAnnotations`), not just lazy-compatible.
