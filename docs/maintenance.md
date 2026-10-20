# Maintainer guide

Everything a maintainer (or an AI agent you trust with the repo) needs to
release, in one place. The workflows live in `.github/workflows/`:

- `ci.yml` — on every push to `master`, every PR, and manual dispatch: the test
  suite on Python 3.12/3.13/3.14, a distribution build, and a security audit of
  the built wheel.
- `release.yml` — only on tags matching `v*.*.*` (or manual dispatch): runs the
  suite, builds, publishes to PyPI and opens a GitHub Release from the
  changelog.

## Release routine

```sh
# 1. Bump the version in pyproject.toml, then refresh uv.lock so it matches
uv sync

# 2. Update CHANGELOG.md with a new '## [X.Y.Z]' section (Keep a Changelog)

# 3. Commit in the established order, then tag
git commit -m "chore: bump version to X.Y.Z"
git tag vX.Y.Z
git push origin master vX.Y.Z
```

The tag push triggers `release.yml`. It hard-fails when the tag does not match
the version in `pyproject.toml`, so a wrong version string cannot publish.

The publish step uses **PyPI trusted publishing** (`id-token: write`): no
PyPI token is stored in the repository. One-time setup on the PyPI side:

1. Log in to [pypi.org](https://pypi.org) and open *Your projects → Manage →
   Publishing* for `ai-template-runner`.
2. Add a "pending publisher" with:
   - owner `brunodavi`, repository `ai-template-runner`
   - workflow name `release.yml`
   - environment `pypi`
3. On GitHub, create the repository **environment** `pypi` (Settings →
   Environments). Restricting it to the `master` branch is fine.

If trusted publishing is not an option, fall back to a token: create an
`API_TOKEN` secret on PyPI, add it to the repo secrets, and replace the publish
step with `pypa/gh-action-pypi-publish@release/v1` plus
`password: ${{ secrets.API_TOKEN }}` (and drop `id-token: write`).

## What a release produces

- **PyPI**: build (`ai_template_runner-X.Y.Z.tar.gz` + wheel) published, which
  makes `uvx`, `pipx`, `pip` and `uv tool` installs all work immediately.
- **GitHub Release**: created with the changelog section for that version
  extracted with `awk` plus the standard install block — so a release page
  explains what changed *and* how to install it.

## First release on a fresh setup

The very first publish must attach the trusted publisher correctly; if PyPI
shows `401`/`permission denied`, re-check the pending publisher fields
(workflow name *exactly* `release.yml`, environment `pypi`) and rerun the job
from Actions. Publishing the same version twice fails on PyPI — bump the
version instead of retrying.

## Release checks before tagging

- [ ] `uv run python -m unittest` green locally from the repo root
- [ ] `uv sync` run after the version bump (uv.lock refreshed)
- [ ] `CHANGELOG.md` has a `## [X.Y.Z]` section whose content matches the tag
- [ ] Every new template feature has an `examples/features/*` example and a
      pinning CLI test (project rule in `AGENTS.md`)
- [ ] `uv build` succeeds (the release job does it, but catching it locally is
      faster)
