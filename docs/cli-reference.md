# CLI Reference

Complete reference for the Universal Recycle command-line interface.

## Overview

After installing the package (`pip install -e .` or from PyPI):

```bash
recycle [COMMAND] [OPTIONS]
# or: python -m recycle [COMMAND] [OPTIONS]
```

Every command shown as `recycle …` can also be run as `python -m recycle …` (same arguments). From a checkout without installing, use `python -m recycle.cli …`.

## Global Options

| Option              | Description                | Default      |
| ------------------- | -------------------------- | ------------ |
| `--config PATH`     | Path to configuration file | `repos.yaml` |
| `--verbose, -v`     | Enable verbose output      | `False`      |
| `--quiet, -q`       | Suppress output            | `False`      |
| `--log-level LEVEL` | Set logging level          | `INFO`       |

## Commands

### `init` - Initialize Project

Interactive wizard to set up a new Universal Recycle project.

```bash
recycle init [OPTIONS]
```

**Options:**

- `--template NAME` - Use specific template
- `--non-interactive` - Skip interactive prompts
- `--output-dir PATH` - Output directory

**Examples:**

```bash
# Interactive initialization
recycle init

# Use specific template
recycle init --template web-service

# Non-interactive with defaults
recycle init --non-interactive --output-dir my-project
```

### `sync` - Repository Synchronization

Sync repositories defined in the manifest.

```bash
recycle sync [OPTIONS]
```

**Options:**

- `--repo NAME` - Sync specific repository
- `--force` - Force re-clone repositories
- `--shallow` - Use shallow clones
- `--jobs N` - Number of parallel jobs

**Examples:**

```bash
# Sync all repositories
recycle sync

# Sync specific repository
recycle sync --repo python-core

# Force re-clone
recycle sync --force

# Parallel sync
recycle sync --jobs 4
```

### `adapt` - Adapter System

Run adapters for linting, modernization, and security scanning.

```bash
recycle adapt [OPTIONS]
```

**Options:**

- `--repo NAME` - Run on specific repository
- `--adapter NAME` - Run specific adapter
- `--fix` - Apply automatic fixes
- `--parallel` - Run adapters in parallel

**Examples:**

```bash
# Run all adapters
recycle adapt

# Run specific adapter
recycle adapt --adapter ruff

# Run on specific repo with fixes
recycle adapt --repo python-core --fix

# Parallel execution
recycle adapt --parallel
```

### `bind` - Binding Generation

Generate cross-language bindings and interfaces.

```bash
recycle bind [OPTIONS]
```

**Options:**

- `--repo NAME` - Generate for specific repository
- `--generators NAMES` - Specific generators to use
- `--output-dir PATH` - Output directory for bindings
- `--force` - Regenerate existing bindings

**Examples:**

```bash
# Generate all bindings
recycle bind

# Generate specific bindings
recycle bind --generators pybind11 grpc

# Generate for specific repo
recycle bind --repo cpp-engine --generators pybind11

# Force regeneration
recycle bind --force
```

### `build` - Build System

Advanced build system with profiles and Bazel integration.

```bash
recycle build [OPTIONS]
```

**Options:**

- `--target NAME` - Build specific target
- `--profile NAME` - Use build profile
- `--bazel` - Use Bazel for builds
- `--distributed` - Enable distributed builds
- `--jobs N` - Number of parallel jobs

**Examples:**

```bash
# Build all targets
recycle build

# Build with profile
recycle build --target cpp-engine --profile release

# Use Bazel
recycle build --target cpp-engine --bazel

# Distributed build
recycle build --distributed --jobs 8
```

#### Build Subcommands

##### `build graph` - Build Dependency Graph

```bash
recycle build --build-command graph [OPTIONS]
```

**Options:**

- `--output FORMAT` - Output format (text, json, dot)
- `--show-deps` - Show dependencies

**Examples:**

```bash
# Show build graph
recycle build --build-command graph

# Export as DOT format
recycle build --build-command graph --output dot
```

##### `build status` - Build Status

```bash
recycle build --build-command status [OPTIONS]
```

**Examples:**

```bash
# Show build status
recycle build --build-command status
```

##### `build logs` - Build Logs

```bash
recycle build --build-command logs [OPTIONS]
```

**Options:**

- `--target NAME` - Show logs for specific target
- `--lines N` - Number of log lines

**Examples:**

```bash
# Show recent logs
recycle build --build-command logs

# Show logs for target
recycle build --build-command logs --target cpp-engine
```

### `distribute` - Package Distribution

Distribute packages to various registries.

```bash
recycle distribute [OPTIONS]
```

**Options:**

- `--target NAME` - Distribute specific target
- `--registry NAME` - Target registry
- `--version VERSION` - Package version
- `--dry-run` - Preview distribution

**Examples:**

```bash
# Distribute all packages
recycle distribute

# Distribute to specific registry
recycle distribute --target python-core --registry pypi

# Dry run
recycle distribute --dry-run
```

#### Distribution Subcommands

##### `distribute status` - Distribution Status

```bash
recycle distribute --distribution-command status [OPTIONS]
```

**Examples:**

```bash
# Show distribution status
recycle distribute --distribution-command status
```

### `cache` - Cache Management

Manage local and remote caching.

```bash
recycle cache --cache-command COMMAND [OPTIONS]
```

**Commands:**

- `status` - Show cache status
- `clear` - Clear cache
- `stats` - Show cache statistics

**Options:**

- `--backend NAME` - Target cache backend
- `--all` - Apply to all backends

**Examples:**

```bash
# Show cache status
recycle cache --cache-command status

# Clear cache
recycle cache --cache-command clear

# Show statistics
recycle cache --cache-command stats
```

### `plugin` - Plugin Management

Manage Universal Recycle plugins.

```bash
recycle plugin --plugin-command COMMAND [OPTIONS]
```

**Commands:**

- `list` - List available plugins
- `info` - Show plugin information
- `check` - Validate plugin health
- `install` - Install plugin
- `remove` - Remove plugin
- `search` - Search plugins

**Options:**

- `--plugin-name NAME` - Target plugin name
- `--plugin-path PATH` - Plugin path for install

**Examples:**

```bash
# List plugins
recycle plugin --plugin-command list

# Show plugin info
recycle plugin --plugin-command info --plugin-name example-plugin

# Check plugin health
recycle plugin --plugin-command check --plugin-name example-plugin

# Install plugin
recycle plugin --plugin-command install --plugin-path ./my-plugin

# Search plugins
recycle plugin --plugin-command search --query "python"
```

## `template` - Template Management

Manage project templates.

```bash
recycle template --template-command COMMAND [OPTIONS]
```

**Commands:**

- `list` - List available templates
- `create` - Create project from template
- `add` - Add custom template
- `remove` - Remove template

**Options:**

- `--template-name NAME` - Template name
- `--output-dir PATH` - Output directory

**Examples:**

```bash
# List templates
recycle template --template-command list

# Create from template
recycle template --template-command create --template-name web-service

# Add custom template
recycle template --template-command add --template-name my-template
```

### `validate` - Validation

Validate manifests and configurations.

```bash
recycle validate [OPTIONS]
```

**Options:**

- `--manifest PATH` - Path to manifest file
- `--config PATH` - Path to config file
- `--strict` - Enable strict validation

**Examples:**

```bash
# Validate current manifest
recycle validate

# Validate specific files
recycle validate --manifest custom-repos.yaml --config build-config.yaml

# Strict validation
recycle validate --strict
```

### `team` - Team Collaboration

Manage team collaboration features.

```bash
recycle team --team-command COMMAND [OPTIONS]
```

**Commands:**

- `add-user` - Add team member
- `remove-user` - Remove team member
- `list-users` - List team members
- `set-role` - Set user role
- `create-workspace` - Create shared workspace
- `list-workspaces` - List workspaces

**Options:**

- `--username NAME` - Username
- `--role ROLE` - User role (admin, member, viewer)
- `--workspace-name NAME` - Workspace name

**Examples:**

```bash
# Add team member
recycle team --team-command add-user --username alice --role member

# List users
recycle team --team-command list-users

# Create workspace
recycle team --team-command create-workspace --workspace-name production
```

### `cicd` - CI/CD Integration

Manage CI/CD pipelines and automation.

```bash
recycle cicd --cicd-command COMMAND [OPTIONS]
```

**Commands:**

- `create-pipeline` - Create CI/CD pipeline
- `list-pipelines` - List pipelines
- `run-pipeline` - Execute pipeline
- `add-webhook` - Add webhook
- `list-webhooks` - List webhooks

**Options:**

- `--pipeline-name NAME` - Pipeline name
- `--trigger TRIGGER` - Pipeline trigger (push, pr, manual)
- `--webhook-url URL` - Webhook URL

**Examples:**

```bash
# Create pipeline
recycle cicd --cicd-command create-pipeline --pipeline-name production

# List pipelines
recycle cicd --cicd-command list-pipelines

# Run pipeline
recycle cicd --cicd-command run-pipeline --pipeline-name production
```

### `performance` - Performance Management

Monitor and optimize performance.

```bash
recycle performance --performance-command COMMAND [OPTIONS]
```

**Commands:**

- `monitor` - Start performance monitoring
- `stats` - Show performance statistics
- `report` - Generate performance report
- `optimize` - Run optimizations

**Options:**

- `--duration SECONDS` - Monitoring duration
- `--output FORMAT` - Report format (text, json, html)

**Examples:**

```bash
# Start monitoring
recycle performance --performance-command monitor

# Show stats
recycle performance --performance-command stats

# Generate report
recycle performance --performance-command report --output html
```

## Environment Variables

| Variable                       | Description              | Default                    |
| ------------------------------ | ------------------------ | -------------------------- |
| `UNIVERSAL_RECYCLE_CONFIG`     | Default config file path | `repos.yaml`               |
| `UNIVERSAL_RECYCLE_CACHE_DIR`  | Cache directory          | `.cache/universal_recycle` |
| `UNIVERSAL_RECYCLE_LOG_LEVEL`  | Logging level            | `INFO`                     |
| `UNIVERSAL_RECYCLE_PLUGIN_DIR` | Plugin directory         | `./plugins`                |

## Configuration Files

### `repos.yaml` - Repository Manifest

```yaml
repositories:
  - name: python-core
    language: python
    git: https://github.com/org/python-core
    commit: main
    adapters: [ruff, mypy, security]

  - name: cpp-engine
    language: cpp
    git: https://github.com/org/cpp-engine
    commit: v1.0.0
    adapters: [clang-tidy, vcpkg]
```

### `build_profiles.yaml` - Build Profiles

```yaml
profiles:
  debug:
    flags: ["-g", "-O0"]
    env:
      BUILD_TYPE: debug

  release:
    flags: ["-O3", "-DNDEBUG"]
    env:
      BUILD_TYPE: release
```

## Exit Codes

| Code | Description         |
| ---- | ------------------- |
| `0`  | Success             |
| `1`  | General error       |
| `2`  | Configuration error |
| `3`  | Repository error    |
| `4`  | Build error         |
| `5`  | Adapter error       |
| `6`  | Binding error       |
| `7`  | Distribution error  |

## Examples

### Complete Workflow

```bash
# Initialize project
recycle init

# Sync repositories
recycle sync

# Run adapters
recycle adapt

# Generate bindings
recycle bind --generators pybind11 grpc

# Build with Bazel
recycle build --target cpp-engine --bazel --profile release

# Distribute packages
recycle distribute --target python-core
```

### Advanced Usage

```bash
# Parallel processing
recycle sync --jobs 8
recycle adapt --parallel

# Selective operations
recycle sync --repo python-core
recycle adapt --repo python-core --adapter ruff

# Build with profiles
recycle build --target cpp-engine --profile debug
recycle build --target cpp-engine --profile release --bazel

# Team collaboration
recycle team --team-command add-user --username bob --role admin
recycle cicd --cicd-command create-pipeline --pipeline-name staging
```

## Help and Support

```bash
# Show help
recycle --help

# Show command help
recycle sync --help

# Show version
recycle --version
```

For more information, see the [main documentation](../README.md) or visit our [GitHub repository](https://github.com/fraware/universal-recycle).
