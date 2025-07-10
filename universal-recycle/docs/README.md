# Universal Recycle Documentation

Welcome to Universal Recycle - the polyglot, manifest-driven, hermetic build system for recycling and modernizing code across languages.

## Quick Start

```bash
# Install Universal Recycle
git clone https://github.com/your-org/universal-recycle.git
cd universal-recycle

# Initialize a new project
python recycle/cli.py init

# Sync repositories and start building
python recycle/cli.py sync
python recycle/cli.py build --target my-project
```

## Documentation Sections

### **Getting Started**

- [Installation Guide](installation.md) - Setup and requirements
- [Quick Start Tutorial](quickstart.md) - Your first project in 5 minutes
- [Basic Concepts](concepts.md) - Understanding manifests, adapters, and bindings

### **Core Features**

- [Repository Management](repositories.md) - Syncing and managing code repositories
- [Adapter System](adapters.md) - Linting, modernization, and security scanning
- [Binding Generation](bindings.md) - Cross-language interoperability
- [Build System](builds.md) - Advanced builds with profiles and Bazel integration

### **Enterprise Features**

- [Team Collaboration](team.md) - User management and shared workspaces
- [CI/CD Integration](cicd.md) - Pipeline automation and webhooks
- [Performance Optimization](performance.md) - Distributed builds and caching

### **Advanced Topics**

- [Plugin Development](plugins.md) - Creating custom adapters and generators
- [Cache Management](caching.md) - Local and remote caching strategies
- [Distribution](distribution.md) - Publishing to package registries
- [Templates](templates.md) - Project templates and scaffolding

### **Reference**

- [CLI Reference](cli-reference.md) - Complete command documentation
- [Configuration Files](config-reference.md) - Manifest and config file formats
- [API Reference](api-reference.md) - Python API documentation
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## Key Features

### **Polyglot Support**

- **Python** - Ruff, MyPy, Black, Security scanning
- **C++** - Clang-tidy, vcpkg, Static analysis
- **Rust** - Cargo, Clippy, Security audits
- **Go** - Go modules, Linting, Testing
- **WebAssembly** - wasm-pack, Optimization

### **Advanced Build System**

- **Selective Builds** - Build only what you need
- **Build Profiles** - Debug, release, custom configurations
- **Bazel Integration** - Hermetic, reproducible builds
- **Distributed Builds** - Multi-node build distribution

### **Enterprise Ready**

- **Team Management** - User roles and permissions
- **CI/CD Integration** - Automated pipelines and webhooks
- **Performance Monitoring** - Metrics and optimization
- **Remote Caching** - Redis, S3, Google Cloud Storage

### **Extensible Architecture**

- **Plugin System** - Custom adapters and generators
- **Template Engine** - Project scaffolding
- **Binding Generation** - Cross-language interoperability
- **Distribution** - Multi-registry publishing

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Manifest      │    │   Adapters      │    │   Bindings      │
│   (repos.yaml)  │───▶│   (Lint/Modern) │───▶│   (pybind11/    │
│                 │    │                 │    │    gRPC/etc)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Build System  │    │   Cache System  │    │   Distribution  │
│   (Bazel/Prof)  │    │   (Local/Remote)│    │   (PyPI/npm/etc)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Example Workflow

```yaml
# repos.yaml - Define your repositories
repositories:
  - name: my-python-lib
    language: python
    git: https://github.com/org/my-python-lib
    commit: main
    adapters: [ruff, mypy, security]

  - name: my-cpp-lib
    language: cpp
    git: https://github.com/org/my-cpp-lib
    commit: v1.0.0
    adapters: [clang-tidy, vcpkg]
```

```bash
# Sync repositories
python recycle/cli.py sync

# Run adapters for modernization
python recycle/cli.py adapt

# Generate language bindings
python recycle/cli.py bind --generators pybind11 grpc

# Build with specific profile
python recycle/cli.py build --target my-cpp-lib --profile release --bazel

# Distribute packages
python recycle/cli.py distribute --target my-python-lib
```

## Contributing

We welcome contributions! See our [Contributing Guide](contributing.md) for details on:

- Code of Conduct
- Development Setup
- Pull Request Process
- Plugin Development

## License

Universal Recycle is licensed under the MIT License. See [LICENSE](../LICENSE) for details.
