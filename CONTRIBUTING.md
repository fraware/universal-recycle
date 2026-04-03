# Contributing to Universal Recycle

Thank you for your interest in contributing. This document describes how to set up a development environment and what we expect in pull requests.

## Development setup

Requirements:

- Python 3.9 or newer
- Git

Clone the repository and install the project in editable mode with development dependencies:

```bash
git clone https://github.com/fraware/universal-recycle.git
cd universal-recycle
pip install -e ".[dev]"
```

Optional tooling:

```bash
pre-commit install
pre-commit run --all-files
```

Feature groups for optional runtime behavior are defined in `pyproject.toml` (for example `grpc`, `bindings`, `cache-redis`, `all`). Install as needed:

```bash
pip install -e ".[all]"
```

## Running the CLI

After an editable install:

```bash
recycle --help
python -m recycle --help
python -m recycle.cli --help
```

## Tests

```bash
pytest
```

Coverage settings live in `pyproject.toml` under `[tool.pytest.ini_options]` and `[tool.coverage.*]`.

## Lint and types

```bash
ruff check recycle tests
ruff format --check recycle tests
mypy recycle/
```

## Repository layout

- `recycle/` — application code.
- `tests/` — automated tests; `tests/fixtures/` includes small manifests for CI.
- `repos/` — **local only**: clones from `sync` are written here and are gitignored (see `repos/.gitkeep`).
- `templates/` — packaged YAML templates.
- `examples/` — example manifests (not used as the default `repos.yaml`).

## Pull requests

- Keep changes focused on a single concern when possible.
- Add or update tests for behavior changes.
- Ensure `pytest`, `ruff check`, and `ruff format --check` pass locally before opening a PR.

## Code of conduct

Be respectful and constructive in issues and pull requests. For security-sensitive reports, see [SECURITY.md](SECURITY.md).

## Releases and PyPI

Tag a release as `vX.Y.Z`. The [release workflow](.github/workflows/release.yml) builds from `pyproject.toml`, runs `scripts/set_version_from_tag.py` to align the declared version with the tag, uploads GitHub Release artifacts, and publishes to PyPI using [trusted publishing](https://docs.pypi.org/trusted-publishers/). Configure a `pypi` GitHub Environment (and the matching trusted publisher on PyPI) for your fork or organization; otherwise the `publish-pypi` job will not succeed until that is set up.
