# CLI Reference

Complete reference for the Universal Recycle command-line interface.

## Overview

```bash
python recycle/cli.py [COMMAND] [OPTIONS]
```

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
python recycle/cli.py init [OPTIONS]
```

**Options:**

- `--template NAME` - Use specific template
- `--non-interactive` - Skip interactive prompts
- `--output-dir PATH` - Output directory

**Examples:**

```bash
# Interactive initialization
python recycle/cli.py init

# Use specific template
python recycle/cli.py init --template web-service

# Non-interactive with defaults
python recycle/cli.py init --non-interactive --output-dir my-project
```

### `sync` - Repository Synchronization

Sync repositories defined in the manifest.

```bash
python recycle/cli.py sync [OPTIONS]
```

**Options:**

- `--repo NAME` - Sync specific repository
- `--force` - Force re-clone repositories
- `--shallow` - Use shallow clones
- `--jobs N` - Number of parallel jobs

**Examples:**

```bash
# Sync all repositories
python recycle/cli.py sync

# Sync specific repository
python recycle/cli.py sync --repo python-core

# Force re-clone
python recycle/cli.py sync --force

# Parallel sync
python recycle/cli.py sync --jobs 4
```

### `adapt` - Adapter System

Run adapters for linting, modernization, and security scanning.

```bash
python recycle/cli.py adapt [OPTIONS]
```

**Options:**

- `--repo NAME` - Run on specific repository
- `--adapter NAME` - Run specific adapter
- `--fix` - Apply automatic fixes
- `--parallel` - Run adapters in parallel

**Examples:**

```bash
# Run all adapters
python recycle/cli.py adapt

# Run specific adapter
python recycle/cli.py adapt --adapter ruff

# Run on specific repo with fixes
python recycle/cli.py adapt --repo python-core --fix

# Parallel execution
python recycle/cli.py adapt --parallel
```

### `bind` - Binding Generation

Generate cross-language bindings and interfaces.

```bash
python recycle/cli.py bind [OPTIONS]
```

**Options:**

- `--repo NAME` - Generate for specific repository
- `--generators NAMES` - Specific generators to use
- `--output-dir PATH` - Output directory for bindings
- `--force` - Regenerate existing bindings

**Examples:**

```bash
# Generate all bindings
python recycle/cli.py bind

# Generate specific bindings
python recycle/cli.py bind --generators pybind11 grpc

# Generate for specific repo
python recycle/cli.py bind --repo cpp-engine --generators pybind11

# Force regeneration
python recycle/cli.py bind --force
```

### `build` - Build System

Advanced build system with profiles and Bazel integration.

```bash
python recycle/cli.py build [OPTIONS]
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
python recycle/cli.py build

# Build with profile
python recycle/cli.py build --target cpp-engine --profile release

# Use Bazel
python recycle/cli.py build --target cpp-engine --bazel

# Distributed build
python recycle/cli.py build --distributed --jobs 8
```

#### Build Subcommands

##### `build graph` - Build Dependency Graph

```bash
python recycle/cli.py build --build-command graph [OPTIONS]
```

**Options:**

- `--output FORMAT` - Output format (text, json, dot)
- `--show-deps` - Show dependencies

**Examples:**

```bash
# Show build graph
python recycle/cli.py build --build-command graph

# Export as DOT format
python recycle/cli.py build --build-command graph --output dot
```

##### `build status` - Build Status

```bash
python recycle/cli.py build --build-command status [OPTIONS]
```

**Examples:**

```bash
# Show build status
python recycle/cli.py build --build-command status
```

##### `build logs` - Build Logs

```bash
python recycle/cli.py build --build-command logs [OPTIONS]
```

**Options:**

- `--target NAME` - Show logs for specific target
- `--lines N` - Number of log lines

**Examples:**

```bash
# Show recent logs
python recycle/cli.py build --build-command logs

# Show logs for target
python recycle/cli.py build --build-command logs --target cpp-engine
```

### `distribute` - Package Distribution

Distribute packages to various registries.

```bash
python recycle/cli.py distribute [OPTIONS]
```

**Options:**

- `--target NAME` - Distribute specific target
- `--registry NAME` - Target registry
- `--version VERSION` - Package version
- `--dry-run` - Preview distribution

**Examples:**

```bash
# Distribute all packages
python recycle/cli.py distribute

# Distribute to specific registry
python recycle/cli.py distribute --target python-core --registry pypi

# Dry run
python recycle/cli.py distribute --dry-run
```

#### Distribution Subcommands

##### `distribute status` - Distribution Status

```bash
python recycle/cli.py distribute --distribution-command status [OPTIONS]
```

**Examples:**

```bash
# Show distribution status
python recycle/cli.py distribute --distribution-command status
```

### `cache` - Cache Management

Manage local and remote caching.

```bash
python recycle/cli.py cache --cache-command COMMAND [OPTIONS]
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
python recycle/cli.py cache --cache-command status

# Clear cache
python recycle/cli.py cache --cache-command clear

# Show statistics
python recycle/cli.py cache --cache-command stats
```

### `plugin` - Plugin Management

Manage Universal Recycle plugins.

```bash
python recycle/cli.py plugin --plugin-command COMMAND [OPTIONS]
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
python recycle/cli.py plugin --plugin-command list

# Show plugin info
python recycle/cli.py plugin --plugin-command info --plugin-name example-plugin

# Check plugin health
python recycle/cli.py plugin --plugin-command check --plugin-name example-plugin

# Install plugin
python recycle/cli.py plugin --plugin-command install --plugin-path ./my-plugin

# Search plugins
python recycle/cli.py plugin --plugin-command search --query "python"
```

## `template` - Template Management

Manage project templates.

```bash
python recycle/cli.py template --template-command COMMAND [OPTIONS]
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
python recycle/cli.py template --template-command list

# Create from template
python recycle/cli.py template --template-command create --template-name web-service

# Add custom template
python recycle/cli.py template --template-command add --template-name my-template
```

### `validate` - Validation

Validate manifests and configurations.

```bash
python recycle/cli.py validate [OPTIONS]
```

**Options:**

- `--manifest PATH` - Path to manifest file
- `--config PATH` - Path to config file
- `--strict` - Enable strict validation

**Examples:**

```bash
# Validate current manifest
python recycle/cli.py validate

# Validate specific files
python recycle/cli.py validate --manifest custom-repos.yaml --config build-config.yaml

# Strict validation
python recycle/cli.py validate --strict
```

### `team` - Team Collaboration

Manage team collaboration features.

```bash
python recycle/cli.py team --team-command COMMAND [OPTIONS]
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
python recycle/cli.py team --team-command add-user --username alice --role member

# List users
python recycle/cli.py team --team-command list-users

# Create workspace
python recycle/cli.py team --team-command create-workspace --workspace-name production
```

### `cicd` - CI/CD Integration

Manage CI/CD pipelines and automation.

```bash
python recycle/cli.py cicd --cicd-command COMMAND [OPTIONS]
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
python recycle/cli.py cicd --cicd-command create-pipeline --pipeline-name production

# List pipelines
python recycle/cli.py cicd --cicd-command list-pipelines

# Run pipeline
python recycle/cli.py cicd --cicd-command run-pipeline --pipeline-name production
```

### `performance` - Performance Management

Monitor and optimize performance.

```bash
python recycle/cli.py performance --performance-command COMMAND [OPTIONS]
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
python recycle/cli.py performance --performance-command monitor

# Show stats
python recycle/cli.py performance --performance-command stats

# Generate report
python recycle/cli.py performance --performance-command report --output html
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
python recycle/cli.py init

# Sync repositories
python recycle/cli.py sync

# Run adapters
python recycle/cli.py adapt

# Generate bindings
python recycle/cli.py bind --generators pybind11 grpc

# Build with Bazel
python recycle/cli.py build --target cpp-engine --bazel --profile release

# Distribute packages
python recycle/cli.py distribute --target python-core
```

### Advanced Usage

```bash
# Parallel processing
python recycle/cli.py sync --jobs 8
python recycle/cli.py adapt --parallel

# Selective operations
python recycle/cli.py sync --repo python-core
python recycle/cli.py adapt --repo python-core --adapter ruff

# Build with profiles
python recycle/cli.py build --target cpp-engine --profile debug
python recycle/cli.py build --target cpp-engine --profile release --bazel

# Team collaboration
python recycle/cli.py team --team-command add-user --username bob --role admin
python recycle/cli.py cicd --cicd-command create-pipeline --pipeline-name staging
```

## Help and Support

```bash
# Show help
python recycle/cli.py --help

# Show command help
python recycle/cli.py sync --help

# Show version
python recycle/cli.py --version
```

For more information, see the [main documentation](../README.md) or visit our [GitHub repository](https://github.com/fraware/universal-recycle).
