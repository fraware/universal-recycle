# Universal Recycle

**The polyglot, manifest-driven, hermetic build system for recycling and modernizing code across languages.**

Universal Recycle revolutionizes how you manage multi-language projects by providing a unified, extensible platform for code modernization, cross-language interoperability, and enterprise-grade build automation.

[![GitHub stars](https://img.shields.io/github/stars/fraware/universal-recycle?style=social)](https://github.com/fraware/universal-recycle)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

## Overview

Universal Recycle is a comprehensive build system designed for modern software development workflows. It provides:

- **Multi-language support** across Python, C++, Rust, Go, and WebAssembly
- **Hermetic builds** with Bazel integration for reproducible results
- **Enterprise features** including team collaboration and CI/CD integration
- **Extensible architecture** with a plugin system for custom workflows
- **Performance optimization** with distributed builds and smart caching

## Key Features

### Multi-Language Support

- **Python** - Ruff, MyPy, Black, Security scanning
- **C++** - Clang-tidy, vcpkg, Static analysis
- **Rust** - Cargo, Clippy, Security audits
- **Go** - Go modules, Linting, Testing
- **WebAssembly** - wasm-pack, Optimization

### Advanced Build System

- **Selective Builds** - Build only what you need
- **Build Profiles** - Debug, release, custom configurations
- **Bazel Integration** - Hermetic, reproducible builds
- **Distributed Builds** - Multi-node build distribution

### Enterprise Ready

- **Team Management** - User roles and permissions
- **CI/CD Integration** - Automated pipelines and webhooks
- **Performance Monitoring** - Metrics and optimization
- **Remote Caching** - Redis, S3, Google Cloud Storage

### Extensible Architecture

- **Plugin System** - Custom adapters and generators
- **Template Engine** - Project scaffolding
- **Binding Generation** - Cross-language interoperability
- **Distribution** - Multi-registry publishing

## Quick Start

```bash
# Clone the repository
git clone https://github.com/fraware/universal-recycle.git
cd universal-recycle

# Initialize your first project
python recycle/cli.py init

# Sync repositories and start building
python recycle/cli.py sync
python recycle/cli.py build --target my-project
```

**Get started in 5 minutes with our [Quick Start Tutorial](docs/quickstart.md)!**

## Documentation

### Getting Started

- [Installation Guide](docs/installation.md) - Setup and requirements
- [Quick Start Tutorial](docs/quickstart.md) - Your first project in 5 minutes
- [CLI Reference](docs/cli-reference.md) - Complete command reference
- [Plugin Development](docs/plugins.md) - Creating custom extensions
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

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

## Use Cases

### Multi-Language Libraries

Build high-performance libraries with Python interfaces and C++/Rust backends.

### Microservices

Modernize legacy codebases with automated linting, security scanning, and cross-language bindings.

### Data Science Pipelines

Create reproducible data science workflows with Python, R, and C++ components.

### Web Applications

Build modern web apps with TypeScript frontends and Python/Go backends.

### Enterprise Systems

Scale development teams with role-based access, CI/CD automation, and performance monitoring.

## Plugin Ecosystem

Universal Recycle's extensible plugin system allows you to:

- **Create custom adapters** for your specific tools and workflows
- **Build custom generators** for new language bindings
- **Extend the CLI** with new commands and functionality
- **Share plugins** with the community

```bash
# List available plugins
python recycle/cli.py plugin --plugin-command list

# Create your own plugin
mkdir -p plugins/my-custom-adapter
# Add plugin.yaml and implementation

# Install and use your plugin
python recycle/cli.py plugin --plugin-command install --plugin-path ./plugins/my-custom-adapter
python recycle/cli.py adapt --adapter my-custom-adapter
```

See our [Plugin Development Guide](docs/plugins.md) to create your first plugin!

## Enterprise Features

### Team Collaboration

```bash
# Add team members
python recycle/cli.py team --team-command add-user --username alice --role member

# Create shared workspaces
python recycle/cli.py team --team-command create-workspace --workspace-name production
```

### CI/CD Integration

```bash
# Create automated pipelines
python recycle/cli.py cicd --cicd-command create-pipeline --pipeline-name production

# Add webhooks
python recycle/cli.py cicd --cicd-command add-webhook --webhook-url https://hooks.slack.com/...
```

### Performance Optimization

```bash
# Monitor performance
python recycle/cli.py performance --performance-command monitor

# Generate reports
python recycle/cli.py performance --performance-command report --output html
```

## Performance

Universal Recycle is designed for scale:

- **Parallel Processing** - Multi-core repository syncing and adapter execution
- **Distributed Builds** - Multi-node build distribution
- **Smart Caching** - Local and remote caching with intelligent invalidation
- **Incremental Updates** - Only process changed files and dependencies

## Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details on:

- **Code of Conduct** - Our community standards
- **Development Setup** - Getting started with development
- **Pull Request Process** - How to submit changes
- **Plugin Development** - Creating custom extensions

### Quick Contribution

```bash
# Fork and clone
git clone https://github.com/your-username/universal-recycle.git
cd universal-recycle

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Submit a pull request
```

## License

Universal Recycle is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

### Documentation

- [Main Documentation](docs/README.md)
- [Quick Start](docs/quickstart.md)
- [Troubleshooting](docs/troubleshooting.md)

### Community

- [GitHub Issues](https://github.com/fraware/universal-recycle/issues)
- [GitHub Discussions](https://github.com/fraware/universal-recycle/discussions)
- [Email Support](mailto:support@universal-recycle.org)

## What's Included

This repository contains the complete Universal Recycle ecosystem:

### Core System

- **Complete CLI tool** with interactive wizard and rich output
- **Plugin system** with example plugin and development guide
- **Advanced build system** with Bazel integration and profiles
- **Enterprise features** for team collaboration and CI/CD
- **Comprehensive documentation** for all user types

### Key Components

- **160+ files** with 37,000+ lines of production-ready code
- **Multi-language support** (Python, C++, Rust, Go, WebAssembly)
- **Plugin ecosystem** for extensibility
- **Enterprise features** for team collaboration
- **Performance optimization** with distributed builds
- **Complete documentation** with examples and guides

## Roadmap

- **Enhanced Language Support** - Additional language adapters and bindings
- **Cloud Integration** - Native cloud platform support
- **Advanced Analytics** - Build performance insights and recommendations
- **Community Plugins** - Curated plugin marketplace
- **Enterprise Features** - Advanced team management and security features
