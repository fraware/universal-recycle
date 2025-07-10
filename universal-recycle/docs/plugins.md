# Plugin Development Guide

Learn how to create custom plugins for Universal Recycle to extend its functionality with your own adapters and generators.

## Overview

Universal Recycle's plugin system allows you to:

- **Create custom adapters** for linting, modernization, and security scanning
- **Build custom generators** for language bindings and interfaces
- **Extend the CLI** with new commands and functionality
- **Share plugins** with the community

## Plugin Architecture

```
plugins/
├── my-custom-adapter/
│   ├── plugin.yaml          # Plugin manifest
│   ├── __init__.py          # Plugin entry point
│   ├── adapter.py           # Adapter implementation
│   └── README.md            # Plugin documentation
└── my-custom-generator/
    ├── plugin.yaml          # Plugin manifest
    ├── __init__.py          # Plugin entry point
    ├── generator.py         # Generator implementation
    └── README.md            # Plugin documentation
```

## Plugin Manifest

Every plugin requires a `plugin.yaml` manifest file:

```yaml
name: my-custom-adapter
version: 1.0.0
description: A custom adapter for my specific needs
author: Your Name <your.email@example.com>
license: MIT

# Plugin type: adapter, generator, or cli
type: adapter

# Supported languages
languages: [python, cpp]

# Plugin entry point
entrypoint: my_custom_adapter.adapter:MyCustomAdapter

# Dependencies
dependencies:
  - requests>=2.25.0
  - click>=8.0.0

# Configuration schema
config_schema:
  timeout:
    type: integer
    default: 30
    description: Timeout in seconds
  output_format:
    type: string
    enum: [json, xml, text]
    default: json
    description: Output format

# CLI commands (for CLI plugins)
commands:
  - name: my-command
    description: My custom command
    entrypoint: my_custom_adapter.cli:my_command
```

## Creating an Adapter Plugin

### Step 1: Create Plugin Structure

```bash
mkdir -p plugins/my-custom-adapter
cd plugins/my-custom-adapter
```

### Step 2: Create Plugin Manifest

```yaml
# plugin.yaml
name: my-custom-adapter
version: 1.0.0
description: Custom code analysis adapter
author: Your Name <your.email@example.com>
license: MIT
type: adapter
languages: [python]
entrypoint: my_custom_adapter.adapter:MyCustomAdapter
dependencies:
  - requests>=2.25.0
config_schema:
  api_key:
    type: string
    required: true
    description: API key for the service
  severity:
    type: string
    enum: [low, medium, high]
    default: medium
    description: Minimum severity level
```

### Step 3: Implement the Adapter

```python
# adapter.py
import os
import json
import requests
from typing import Dict, List, Any
from pathlib import Path

class MyCustomAdapter:
    """Custom code analysis adapter."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key')
        self.severity = self.config.get('severity', 'medium')

    def can_handle(self, language: str) -> bool:
        """Check if this adapter can handle the given language."""
        return language.lower() == 'python'

    def run(self, repo_path: str, language: str) -> Dict[str, Any]:
        """Run the adapter on the repository."""
        if not self.can_handle(language):
            return {
                'success': False,
                'error': f'Cannot handle language: {language}'
            }

        try:
            # Find Python files
            python_files = list(Path(repo_path).rglob('*.py'))

            if not python_files:
                return {
                    'success': True,
                    'message': 'No Python files found',
                    'issues': []
                }

            # Analyze files
            issues = []
            for file_path in python_files:
                file_issues = self._analyze_file(file_path)
                issues.extend(file_issues)

            # Filter by severity
            filtered_issues = [
                issue for issue in issues
                if self._get_severity_level(issue['severity']) >= self._get_severity_level(self.severity)
            ]

            return {
                'success': True,
                'issues': filtered_issues,
                'summary': {
                    'total_files': len(python_files),
                    'total_issues': len(filtered_issues),
                    'severity_breakdown': self._count_by_severity(filtered_issues)
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _analyze_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze a single Python file."""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Your custom analysis logic here
            # This is just an example
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                if len(line) > 100:
                    issues.append({
                        'file': str(file_path),
                        'line': line_num,
                        'column': 1,
                        'severity': 'medium',
                        'message': 'Line too long (over 100 characters)',
                        'code': 'LINE_TOO_LONG'
                    })

                if 'TODO' in line:
                    issues.append({
                        'file': str(file_path),
                        'line': line_num,
                        'column': line.find('TODO') + 1,
                        'severity': 'low',
                        'message': 'TODO comment found',
                        'code': 'TODO_FOUND'
                    })

        except Exception as e:
            issues.append({
                'file': str(file_path),
                'line': 1,
                'column': 1,
                'severity': 'high',
                'message': f'Error reading file: {str(e)}',
                'code': 'FILE_READ_ERROR'
            })

        return issues

    def _get_severity_level(self, severity: str) -> int:
        """Convert severity string to numeric level."""
        levels = {'low': 1, 'medium': 2, 'high': 3}
        return levels.get(severity.lower(), 1)

    def _count_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by severity."""
        counts = {'low': 0, 'medium': 0, 'high': 0}
        for issue in issues:
            severity = issue.get('severity', 'low').lower()
            counts[severity] = counts.get(severity, 0) + 1
        return counts
```

### Step 4: Create Entry Point

```python
# __init__.py
from .adapter import MyCustomAdapter

__all__ = ['MyCustomAdapter']
```

### Step 5: Test Your Adapter

```bash
# Install your plugin
python recycle/cli.py plugin --plugin-command install --plugin-path ./plugins/my-custom-adapter

# Check plugin health
python recycle/cli.py plugin --plugin-command check --plugin-name my-custom-adapter

# Run your adapter
python recycle/cli.py adapt --adapter my-custom-adapter
```

## Creating a Generator Plugin

### Step 1: Create Plugin Structure

```bash
mkdir -p plugins/my-custom-generator
cd plugins/my-custom-generator
```

### Step 2: Create Plugin Manifest

```yaml
# plugin.yaml
name: my-custom-generator
version: 1.0.0
description: Custom binding generator
author: Your Name <your.email@example.com>
license: MIT
type: generator
languages: [cpp, rust]
entrypoint: my_custom_generator.generator:MyCustomGenerator
dependencies:
  - jinja2>=3.0.0
config_schema:
  output_format:
    type: string
    enum: [header, source, both]
    default: both
    description: Output format
  namespace:
    type: string
    default: my_bindings
    description: C++ namespace
```

### Step 3: Implement the Generator

```python
# generator.py
import os
import json
from typing import Dict, List, Any
from pathlib import Path
from jinja2 import Template

class MyCustomGenerator:
    """Custom binding generator."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.output_format = self.config.get('output_format', 'both')
        self.namespace = self.config.get('namespace', 'my_bindings')

    def can_handle(self, language: str) -> bool:
        """Check if this generator can handle the given language."""
        return language.lower() in ['cpp', 'rust']

    def generate(self, repo_path: str, language: str, output_dir: str = None) -> Dict[str, Any]:
        """Generate bindings for the repository."""
        if not self.can_handle(language):
            return {
                'success': False,
                'error': f'Cannot handle language: {language}'
            }

        try:
            # Create output directory
            if output_dir is None:
                output_dir = os.path.join(repo_path, 'generated_bindings')

            os.makedirs(output_dir, exist_ok=True)

            # Find source files
            if language.lower() == 'cpp':
                source_files = list(Path(repo_path).rglob('*.cpp')) + list(Path(repo_path).rglob('*.hpp'))
            else:  # rust
                source_files = list(Path(repo_path).rglob('*.rs'))

            if not source_files:
                return {
                    'success': True,
                    'message': f'No {language} source files found',
                    'generated_files': []
                }

            # Generate bindings
            generated_files = []

            if self.output_format in ['header', 'both']:
                header_file = self._generate_header(repo_path, language, source_files, output_dir)
                if header_file:
                    generated_files.append(header_file)

            if self.output_format in ['source', 'both']:
                source_file = self._generate_source(repo_path, language, source_files, output_dir)
                if source_file:
                    generated_files.append(source_file)

            return {
                'success': True,
                'generated_files': generated_files,
                'summary': {
                    'total_source_files': len(source_files),
                    'total_generated_files': len(generated_files)
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_header(self, repo_path: str, language: str, source_files: List[Path], output_dir: str) -> str:
        """Generate header file."""
        header_template = """
#ifndef {{ namespace.upper() }}_BINDINGS_H
#define {{ namespace.upper() }}_BINDINGS_H

#include <string>
#include <vector>

namespace {{ namespace }} {

{% for file in source_files %}
// Generated from {{ file.name }}
{% endfor %}

class Bindings {
public:
    static void initialize();
    static void cleanup();

    // Add your binding methods here
    static std::string getVersion();
    static std::vector<std::string> getFunctions();
};

} // namespace {{ namespace }}

#endif // {{ namespace.upper() }}_BINDINGS_H
"""

        template = Template(header_template)
        header_content = template.render(
            namespace=self.namespace,
            source_files=[f.name for f in source_files]
        )

        header_path = os.path.join(output_dir, f'{self.namespace}_bindings.h')
        with open(header_path, 'w') as f:
            f.write(header_content)

        return header_path

    def _generate_source(self, repo_path: str, language: str, source_files: List[Path], output_dir: str) -> str:
        """Generate source file."""
        source_template = """
#include "{{ namespace }}_bindings.h"
#include <iostream>

namespace {{ namespace }} {

void Bindings::initialize() {
    std::cout << "Initializing {{ namespace }} bindings" << std::endl;
}

void Bindings::cleanup() {
    std::cout << "Cleaning up {{ namespace }} bindings" << std::endl;
}

std::string Bindings::getVersion() {
    return "{{ version }}";
}

std::vector<std::string> Bindings::getFunctions() {
    return {
{% for file in source_files %}
        "{{ file.name }}",
{% endfor %}
    };
}

} // namespace {{ namespace }}
"""

        template = Template(source_template)
        source_content = template.render(
            namespace=self.namespace,
            version="1.0.0",
            source_files=[f.name for f in source_files]
        )

        source_path = os.path.join(output_dir, f'{self.namespace}_bindings.cpp')
        with open(source_path, 'w') as f:
            f.write(source_content)

        return source_path
```

### Step 4: Create Entry Point

```python
# __init__.py
from .generator import MyCustomGenerator

__all__ = ['MyCustomGenerator']
```

### Step 5: Test Your Generator

```bash
# Install your plugin
python recycle/cli.py plugin --plugin-command install --plugin-path ./plugins/my-custom-generator

# Generate bindings
python recycle/cli.py bind --generators my-custom-generator
```

## Creating a CLI Plugin

### Step 1: Create Plugin Structure

```bash
mkdir -p plugins/my-custom-cli
cd plugins/my-custom-cli
```

### Step 2: Create Plugin Manifest

```yaml
# plugin.yaml
name: my-custom-cli
version: 1.0.0
description: Custom CLI commands
author: Your Name <your.email@example.com>
license: MIT
type: cli
entrypoint: my_custom_cli.cli:MyCustomCLI
dependencies:
  - click>=8.0.0
commands:
  - name: my-command
    description: My custom command
    entrypoint: my_custom_cli.cli:my_command
  - name: analyze
    description: Analyze repositories
    entrypoint: my_custom_cli.cli:analyze_command
```

### Step 3: Implement CLI Commands

```python
# cli.py
import click
import json
from pathlib import Path
from typing import Dict, Any

class MyCustomCLI:
    """Custom CLI plugin."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

@click.command()
@click.option('--name', default='World', help='Name to greet')
def my_command(name):
    """My custom command."""
    click.echo(f"Hello, {name}!")
    click.echo("This is a custom CLI command from my plugin!")

@click.command()
@click.option('--repo', help='Repository to analyze')
@click.option('--output', '-o', help='Output file')
def analyze_command(repo, output):
    """Analyze repositories."""
    if repo:
        click.echo(f"Analyzing repository: {repo}")

        # Your analysis logic here
        analysis_result = {
            'repository': repo,
            'files_count': 0,
            'languages': [],
            'issues': []
        }

        repo_path = Path(repo)
        if repo_path.exists():
            # Count files
            analysis_result['files_count'] = len(list(repo_path.rglob('*')))

            # Detect languages
            extensions = set()
            for file_path in repo_path.rglob('*'):
                if file_path.is_file():
                    extensions.add(file_path.suffix)

            language_map = {
                '.py': 'Python',
                '.cpp': 'C++',
                '.hpp': 'C++',
                '.rs': 'Rust',
                '.go': 'Go',
                '.js': 'JavaScript',
                '.ts': 'TypeScript'
            }

            analysis_result['languages'] = [
                language_map.get(ext, ext[1:].upper())
                for ext in extensions
                if ext in language_map
            ]

        if output:
            with open(output, 'w') as f:
                json.dump(analysis_result, f, indent=2)
            click.echo(f"Analysis saved to {output}")
        else:
            click.echo(json.dumps(analysis_result, indent=2))
    else:
        click.echo("Please specify a repository with --repo")
```

### Step 4: Create Entry Point

```python
# __init__.py
from .cli import MyCustomCLI, my_command, analyze_command

__all__ = ['MyCustomCLI', 'my_command', 'analyze_command']
```

### Step 5: Test Your CLI Plugin

```bash
# Install your plugin
python recycle/cli.py plugin --plugin-command install --plugin-path ./plugins/my-custom-cli

# Run your command
python recycle/cli.py my-command --name "Universal Recycle"

# Run analysis
python recycle/cli.py analyze --repo ./repos/python-requests --output analysis.json
```

## Testing Your Plugin

### Unit Testing

```python
# test_my_custom_adapter.py
import unittest
from pathlib import Path
from my_custom_adapter.adapter import MyCustomAdapter

class TestMyCustomAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = MyCustomAdapter()

    def test_can_handle_python(self):
        self.assertTrue(self.adapter.can_handle('python'))
        self.assertFalse(self.adapter.can_handle('cpp'))

    def test_analyze_file(self):
        # Create a test file
        test_file = Path('test_file.py')
        test_file.write_text('print("Hello, World!")\n# TODO: Add more tests\n' + 'x' * 150)

        try:
            issues = self.adapter._analyze_file(test_file)

            # Should find TODO and long line
            self.assertGreater(len(issues), 0)

            # Check for TODO issue
            todo_issues = [i for i in issues if i['code'] == 'TODO_FOUND']
            self.assertEqual(len(todo_issues), 1)

            # Check for long line issue
            long_line_issues = [i for i in issues if i['code'] == 'LINE_TOO_LONG']
            self.assertEqual(len(long_line_issues), 1)

        finally:
            test_file.unlink()

    def test_run_success(self):
        # Create a test repository
        test_repo = Path('test_repo')
        test_repo.mkdir()
        (test_repo / 'test.py').write_text('print("test")')

        try:
            result = self.adapter.run(str(test_repo), 'python')

            self.assertTrue(result['success'])
            self.assertIn('issues', result)
            self.assertIn('summary', result)

        finally:
            import shutil
            shutil.rmtree(test_repo)

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

```bash
# Test plugin installation
python recycle/cli.py plugin --plugin-command install --plugin-path ./plugins/my-custom-adapter

# Test plugin health
python recycle/cli.py plugin --plugin-command check --plugin-name my-custom-adapter

# Test plugin functionality
python recycle/cli.py adapt --adapter my-custom-adapter --repo ./repos/python-requests
```

## Publishing Your Plugin

### 1. Prepare Your Plugin

```bash
# Create a proper package structure
my-custom-adapter/
├── setup.py
├── README.md
├── LICENSE
├── my_custom_adapter/
│   ├── __init__.py
│   ├── adapter.py
│   └── cli.py
└── tests/
    └── test_adapter.py
```

### 2. Create setup.py

```python
# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="universal-recycle-my-custom-adapter",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Custom adapter for Universal Recycle",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/universal-recycle-my-custom-adapter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "click>=8.0.0",
    ],
    entry_points={
        "universal_recycle.plugins": [
            "my-custom-adapter = my_custom_adapter.adapter:MyCustomAdapter",
        ],
    },
)
```

### 3. Publish to PyPI

```bash
# Build package
python setup.py sdist bdist_wheel

# Upload to PyPI
pip install twine
twine upload dist/*
```

### 4. Install from PyPI

```bash
# Install your plugin
pip install universal-recycle-my-custom-adapter

# Use your plugin
python recycle/cli.py adapt --adapter my-custom-adapter
```

## Best Practices

### Plugin Design

1. **Keep it focused** - Each plugin should do one thing well
2. **Follow conventions** - Use consistent naming and structure
3. **Handle errors gracefully** - Always return meaningful error messages
4. **Be configurable** - Allow customization through config schema
5. **Document everything** - Include README and docstrings

### Performance

1. **Cache results** - Avoid redundant computations
2. **Use async when possible** - For I/O operations
3. **Limit resource usage** - Don't consume too much memory or CPU
4. **Provide progress feedback** - For long-running operations

### Security

1. **Validate inputs** - Always validate configuration and inputs
2. **Sanitize outputs** - Don't expose sensitive information
3. **Use secure defaults** - Default to secure configurations
4. **Handle secrets properly** - Use environment variables for API keys

### Testing

1. **Write unit tests** - Test individual components
2. **Write integration tests** - Test with Universal Recycle
3. **Test error conditions** - Test failure scenarios
4. **Use test fixtures** - Create reusable test data

## Debugging Plugins

### Enable Debug Logging

```bash
# Enable debug logging
export UNIVERSAL_RECYCLE_LOG_LEVEL=DEBUG
python recycle/cli.py adapt --adapter my-custom-adapter
```

### Check Plugin Loading

```bash
# List installed plugins
python recycle/cli.py plugin --plugin-command list

# Check plugin health
python recycle/cli.py plugin --plugin-command check --plugin-name my-custom-adapter

# Show plugin info
python recycle/cli.py plugin --plugin-command info --plugin-name my-custom-adapter
```

### Common Issues

1. **Import errors** - Check your entry point and dependencies
2. **Configuration errors** - Validate your plugin.yaml
3. **Permission errors** - Check file permissions
4. **Version conflicts** - Ensure compatible dependency versions

## Contributing

We welcome plugin contributions! See our [Contributing Guide](../contributing.md) for details on:

- Code of Conduct
- Development Setup
- Pull Request Process
- Plugin Review Guidelines
