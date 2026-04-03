# Universal Recycle Documentation

Welcome to Universal Recycle: a polyglot, manifest-driven workflow for syncing repositories, running adapters, generating bindings, and automating builds.

## Quick start

```bash
git clone https://github.com/fraware/universal-recycle.git
cd universal-recycle
pip install -e ".[dev]"

recycle init
recycle sync
recycle build --target my-project
```

Use **`python -m recycle`** instead of **`recycle`** whenever the console script is not on your `PATH`. Dependencies and optional extras are defined in [`pyproject.toml`](../pyproject.toml) at the repository root.

## Documentation index

### Getting started

- [Installation Guide](installation.md) — Requirements, PyPI, source, Docker, pipx, verification
- [Quick Start Tutorial](quickstart.md) — Walkthrough from install to sync and build
- [Main README](../README.md) — Overview, features, and project status

### Reference and guides

- [CLI Reference](cli-reference.md) — Commands and options (`recycle` / `python -m recycle`)
- [Plugin Development](plugins.md) — Adapters, generators, and packaging (Python 3.9+)
- [Troubleshooting](troubleshooting.md) — Common errors and fixes

## Key features

### Polyglot support

- **Python** — Ruff, MyPy, and related adapters
- **C++** — Clang-tidy, vcpkg-oriented workflows
- **Rust**, **Go**, **WebAssembly** — Described in manifests and CLI; toolchains must be installed separately where used

### Build and distribution

- Manifest-driven **`repos.yaml`** (list or `repositories:` form)
- Local clone directory **`repos/`** (not committed in the default upstream layout)
- Build profiles, Bazel-oriented helpers, cache and distribution subsystems (see CLI reference)

### Extensibility

- Plugin discovery under `plugins/` and packaged entry points
- Templates under the `templates/` package

## Example workflow

```yaml
# repos.yaml
repositories:
  - name: my-python-lib
    language: python
    git: https://github.com/org/my-python-lib
    commit: main
    adapters: [ruff, mypy]

  - name: my-cpp-lib
    language: cpp
    git: https://github.com/org/my-cpp-lib
    commit: v1.0.0
    adapters: [clang_tidy, vcpkg_manifest]
```

```bash
recycle sync
recycle adapt
recycle bind --generators pybind11 grpc
recycle build --target my-cpp-lib --profile release --bazel
recycle distribute --target my-python-lib
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development setup (`pip install -e ".[dev]"`), tests, and pull requests. For security-sensitive issues, see [SECURITY.md](../SECURITY.md).

## License

Universal Recycle is licensed under the MIT License. See [LICENSE](../LICENSE).
