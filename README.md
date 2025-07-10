# Universal Recycle

A polyglot, manifest-driven, hermetic build system for recycling and modernizing code across languages (Python, C++, and more). Designed for reproducibility, and extensibility.

## Design Goals

- **Polyglot**: Python, C++, and easily extensible to other languages
- **Manifest-driven**: Add repos via a single `repos.yaml` file
- **Hermetic builds**: Reproducible, cross-platform builds using Bazel
- **Remote-cache-friendly**: Fast CI/CD with remote caching
- **Pluggable adapters**: Lint, modernize, scan, and bind-gen as plugins

## High-Level Architecture

```
repos.yaml → Fetch Engine (libgit2) → Build Orchestrator (Bazel)
      │                │ plugins/*.so        │ bazel rules
      ▼                ▼                     ▼
CLI / gRPC API ← Adapt / Scan / Modernise pipeline → Artefact registry
```

## Repository Layout

```
universal-recycle/
├─ repos.yaml            # declarative source list
├─ recycle/              # CLI tool (to be implemented)
├─ plugins/              # compiled adapters
├─ rules/                # Bazel overlays
├─ tools/ci/             # CI scripts
├─ docs/                 # Documentation
└─ examples/             # Example manifests, configs, etc.
```

## Getting Started

1. Add a repo to `repos.yaml`
2. Run the CLI to fetch and update Bazel workspace
3. Build, lint, adapt, and publish artefacts

## Next Steps

- Scaffold the initial directory structure
- Add a minimal `repos.yaml`
- Implement the CLI skeleton
- Set up Bazel and basic build rules
