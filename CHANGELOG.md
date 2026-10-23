# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.9.0] - 2026-10-23

### Added

- `[cmd]` values interpolate the run slots: `message = 'grep "{question}" notes.txt'` fills `{question}`, `{0}` (the template path) and every positional slot right before the subprocess runs, when the `{cmd.<name>}` placeholder is evaluated. Positional slots, slices and `:spec` transforms work exactly like in prompts — lazy like the `[memory]` collection query, and the usage errors name the site (`unknown placeholder ... in [cmd] message`, `not enough args in [cmd] message: slot {1} requested, got 0 arg(s)`). Interpolation is raw by design (no automatic quoting, documented in the README), and literal shell braces stay escaped (`awk '{{print $2}}'`).
- One shared slot interpolator: `slots.py::interpolate_slots` extracts the machine that was inline in the `[memory]` collection query — `[memory] query` and `[cmd]` values now run the same code path. `command.py::CommandView` receives the run context from the format call itself, so `Template` keeps no per-run state.
- `examples/features/command-path.md` and `examples/features/command-context.txt` demonstrating and pinning directory derivation from the `{0}` template path (`$(dirname "{0}")` to reach sibling data files).
- Repo process: every example now requires a signed-off live `llama-server` run before publishing — syntax bar for `examples/features/*.md`, quality bar for the `examples/*.md` task templates, with the human review made explicit (AGENTS.md).

## [1.8.0] - 2026-10-23

### Added

- `[memory]` template table: template-local retrieval (RAG) with zero new dependencies. The template declares an embeddings endpoint (`base_url` is the full `/v1/embeddings` URL and `model` is required, like `[provider]`; extra payload rides `[memory.extras]`) and one named collection per `[memory.<name>]` table. Each collection fills the `{memory.<name>}` placeholders — lazy like `{cmd.*}` and cached once per run — with the chunks closest to the query, which interpolates the same slots as the prompts (`{question}`, `{0}`, `{1}`, ...) and accepts Smart transforms on the result.
- Notes chunking preserves paragraphs (those that fit share one chunk, joined by a newline); oversized paragraphs fall back to a sliding window with stride `chunk_size - chunk_overlap`. Retrieval returns up to `top_k` chunks (default 4) past the `min_score` filter (default 0.0), capped by the `max_chars` context budget (2048).
- Self-refreshing sqlite index: the `db` file (or one next to the first source when omitted) stores chunk texts and float32 embeddings gated by a sha256 fingerprint of the sources plus the embeddings-relevant parameters (`model`, `chunk_size`, `chunk_overlap`, `extras`). `ait run` itself rebuilds the index when the notes or the setup change — no separate update command — while retrieval-only knobs (`top_k`, `min_score`, `max_chars`) never trigger a re-embed.
- Load-time validation before tokens are spent: embedder `base_url`/`model` are required, unknown `[memory]`/collection keys are rejected, and every collection source must resolve (literal file or glob) at template load.
- `examples/features/memory.md` and `examples/features/memory-notes.txt` demonstrating and pinning the behavior in `test/test_cli.py` (embeddings mocked two-stage in tests), plus the chunk-behavior evidence measured on real notes in the README.

## [1.7.0] - 2026-10-21

### Added

- `run` accepts multiple templates through a glob pattern: matches run in sorted order, files that do not start with the ` ```toml ` configuration block are skipped with a stderr warning inside a batch (a single non-template candidate is a usage error), and `--fail-fast` stops the batch at the first template with a FAIL; the exit code is 1 when any template fails.
- Positional placeholders: `{0}` is the absolute path of the running template and `{1}`, `{2}`, ... are the values passed after it (`{question}` remains the alias of `{1}`). All slots are `Smart` values, so pythonic slices (`{0[1:]}`, `{0[:3]}`) and inline transforms work on the path and on every arg.
- `--` escape in `run`: everything after `--` is verbatim arg data, so values starting with `-` reach the template unchanged.
- `examples/features/args.md` demonstrating the positional placeholders.

### Changed

- `run` flags may now appear before, between and after the positional args (intermixed argument parsing).

### Fixed

- Interpolation problems fail with friendly usage errors instead of raw tracebacks: unknown placeholders, too few args, and `{}` mixed with numbered slots get dedicated messages.

## [1.6.0] - 2026-10-20

### Added

- Contributor documentation: Termux guide overhauled (direct `pip install`, packaged `llama-cpp` via `pkg`, the phone-safe `llama-server` profile with capped threads/context, `llama-bench` recipe), architecture decisions doc and maintainer release routine doc.
- Reference benchmark documentation in `docs/benchmarks.md`: the behavioral capacity ranking of small models plus the hardware curve measured with `llama-bench` on the reference phone, standardized on llama.cpp model identities.
- Runtime floor lowered support matrix: tests now run on Python 3.12, 3.13 and 3.14 in CI (requires-python `>=3.12` shipped in 1.5.0 was already validated).

### Fixed

- CI: the `pip-audit` action failed to bootstrap because uv-managed venvs do not ship `pip`; CI now installs `pip` into the environment before the security audit step.

### Changed

- `AGENTS.md` synced with the new distribution and benchmark workflow rules (TDD exception for `tmp/` utilities, CHANGELOG/tag contract, benchmark data flow).

## [1.5.0] - 2026-10-20

### Added

- MIT license, PyPI metadata and install surface (`uvx`, `pipx`, `pip`, `uv tool install`).
- CI workflow (tests on Python 3.12, 3.13 and 3.14, build check, security audit) and tag-driven release workflow (PyPI publish + GitHub Release with changelog notes).
- Contributor documentation in `docs/`: architecture decisions, Termux guide and release routine.

### Changed

- `requires-python` lowered from `>=3.14` to `>=3.12`.

### Fixed

- `Template.cmd` annotation referenced an undefined `Command` name (only latent on Python 3.14; hard failure on 3.12/3.13).

## [1.4.1] - 2026-10-20

### Added

- New feature examples `output.md` and `transforms.md`, pinned by CLI tests.

## [1.4.0] - 2026-10-20

### Added

- Inline transforms rolled out to `{question}` and `{cmd.field}` interpolation (phase 2).

## [1.3.0] - 2026-10-20

### Added

- Documented the `[out]` engine and added render steps to the conventional-commits simulations.

## [1.2.0] - 2026-10-19

### Added

- Template self-validation with the `[test]` table and the `--test` flag.
- Template inheritance with the `extends` key, plus simulations covering it.

## [1.1.1] - 2026-10-19

### Fixed

- Duplicated field name dropped from check details.

### Changed

- Examples refactored and documented.

## [1.1.0] - 2026-10-18

### Added

- System prompt shown in the run display.

## [1.0.0] - 2026-10-18

### Added

- The TOML configuration block is parsed and removed from the template.
- Optional system prompt delimited by `---` separators, sent to the provider.

## [0.4.0] - 2026-10-18

### Added

- Full provider sampling parameter set (`top_k`, `min_p`, `repeat_penalty`, ...) and `[provider.extras]` for any other fields.

## [0.3.0] - 2026-10-17

### Added

- `-q` / `--quiet` flag to display only the AI response.

### Fixed

- Prompt processing without a `cmd` table.

## [0.2.0] - 2026-10-17

### Added

- `[cmd]` table: templates run shell commands and inject their output into prompts through `{cmd.*}` placeholders.

## [0.1.0] - 2026-10-17

### Added

- First working release: the `ait run` subcommand, prompt interpolation (`{question}`) and the `llamacpp` provider.
