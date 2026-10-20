# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
