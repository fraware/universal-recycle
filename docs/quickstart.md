# Quick Start Tutorial

Get up and running with Universal Recycle in 5 minutes! This tutorial will guide you through creating your first multi-language project.

## Prerequisites

- Python 3.9 or higher
- Git
- Basic familiarity with command line tools

## Step 1: Installation

```bash
# Clone the repository
git clone https://github.com/fraware/universal-recycle.git
cd universal-recycle

# Install the package (editable install with dev extras for contributors)
pip install -e ".[dev]"
```

Dependencies are declared in `pyproject.toml`. Optional feature groups include `grpc`, `bindings`, `cache-redis`, `cache-s3`, `cache-gcs`, `rust`, and `all`.

## Step 2: Initialize Your Project

Universal Recycle provides an interactive wizard to set up your project:

```bash
recycle init
# or: python -m recycle init
```

The wizard will ask you several questions:

```
Universal Recycle Project Initialization
==========================================

What type of project would you like to create?
1. Multi-language library (Python + C++)
2. Web service (Python + TypeScript)
3. Data science (Python + R)
4. Custom configuration

Enter your choice (1-4): 1

Project name: my-awesome-lib
Description: A high-performance library with Python and C++ components

Which languages will you be using?
- Python (y/n): y
- C++ (y/n): y
- Rust (y/n): n
- Go (y/n): n

Creating project structure...
Project initialized successfully!
```

This creates:

- `repos.yaml` - Repository manifest
- `build_profiles.yaml` - Build configurations
- `.gitignore` - Git ignore rules
- `README.md` - Project documentation

## Step 3: Configure Your Repositories

Edit the generated `repos.yaml` file:

```yaml
repositories:
  - name: python-core
    language: python
    git: https://github.com/fraware/python-core
    commit: main
    adapters: [ruff, mypy, security]

  - name: cpp-engine
    language: cpp
    git: https://github.com/fraware/cpp-engine
    commit: v1.0.0
    adapters: [clang-tidy, vcpkg]
```

## Step 4: Sync Repositories

Download and sync your repositories. By default clones are written to **`repos/`** in your project root (that directory is gitignored in the upstream repository so only your machine keeps the checkouts).

```bash
recycle sync
```

Output:

```
Universal Recycle Repository Sync
====================================

Syncing repositories to ./repos...

[1/2] Cloning python-core...
  ✓ Successfully cloned python-core

[2/2] Cloning cpp-engine...
  ✓ Successfully cloned cpp-engine

Sync Summary: 2/2 repositories synced successfully
```

## Step 5: Run Adapters

Modernize and improve your code with adapters:

```bash
recycle adapt
```

Output:

```
🔧 Universal Recycle Adapter System
===================================

Running adapters on repositories...

Processing python-core...
  ✓ ruff (code formatting)
  ✓ mypy (type checking)
  ✓ security (vulnerability scan)

Processing cpp-engine...
  ✓ clang-tidy (static analysis)
  ✓ vcpkg (dependency management)

Adapter Summary: 5/5 adapters succeeded
```

## Step 6: Generate Language Bindings

Create cross-language interoperability:

```bash
recycle bind --generators pybind11 grpc
```

Output:

```
Universal Recycle Binding Generation
=======================================

Generating bindings for repositories...

Processing cpp-engine...
  ✓ pybind11 (Python bindings)
  ✓ grpc (service definitions)

Binding Generation Summary: 2/2 generators succeeded
```

## Step 7: Build Your Project

Build with advanced features:

```bash
# Build with debug profile
recycle build --target cpp-engine --profile debug

# Build with Bazel integration
recycle build --target cpp-engine --profile release --bazel

# Build with distributed system
recycle build --target cpp-engine --distributed
```

## Step 8: Distribute Packages

Publish your packages to registries:

```bash
recycle distribute --target python-core
```

## What You've Accomplished

In just a few minutes, you've:

1. ✅ **Set up a multi-language project** with Python and C++
2. ✅ **Synced repositories** from different sources
3. ✅ **Modernized code** with linting and security scanning
4. ✅ **Generated bindings** for cross-language interoperability
5. ✅ **Built with advanced features** like profiles and Bazel
6. ✅ **Distributed packages** to package registries

## Next Steps

### Explore Advanced Features

```bash
# Team collaboration
recycle team --team-command add-user --username alice --role member

# CI/CD integration
recycle cicd --cicd-command create-pipeline --pipeline-name production

# Performance monitoring
recycle performance --performance-command monitor
```

### Create Custom Plugins

```bash
# List available plugins
recycle plugin --plugin-command list

# Create your own plugin
mkdir -p plugins/my-custom-adapter
# Add plugin.yaml and implementation
```

### Use Templates

```bash
# List available templates
recycle template --template-command list

# Create project from template
recycle template --template-command create --template-name web-service
```

## Troubleshooting

### Common Issues

**Repository sync fails:**

```bash
# Check network connectivity
git clone https://github.com/fraware/python-core

# Verify repository URLs in repos.yaml
cat repos.yaml
```

**Adapters not found:**

```bash
# Install required tools
pip install ruff mypy bandit
# For C++: install clang-tidy and vcpkg
```

**Build fails:**

```bash
# Check build profiles
cat build_profiles.yaml

# Try different profile
recycle build --target cpp-engine --profile debug
```

## Congratulations!

You've successfully set up Universal Recycle and experienced its power for managing multi-language projects. The system is now ready to scale with your needs - from simple scripts to enterprise deployments.
