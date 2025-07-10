"""
Template management for Universal Recycle.

This module handles listing and copying predefined templates
for different project types and configurations.
"""

import os
import shutil
import yaml
from pathlib import Path
from typing import List, Dict, Any


def get_templates_dir() -> Path:
    """Get the templates directory path."""
    # Get the directory where this module is located
    current_dir = Path(__file__).parent
    return current_dir / "templates"


def list_templates() -> List[Dict[str, Any]]:
    """List all available templates."""
    templates_dir = get_templates_dir()
    templates = []

    if not templates_dir.exists():
        return templates

    for template_file in templates_dir.glob("*.yaml"):
        if template_file.name == "__init__.py":
            continue

        template_name = template_file.stem
        template_path = template_file

        # Read template to get description
        try:
            with open(template_path, "r") as f:
                content = yaml.safe_load(f)
                repos = content.get("repositories", [])

                # Extract languages used
                languages = list(set(repo.get("language", "unknown") for repo in repos))

                # Get first line comment as description
                with open(template_path, "r") as f:
                    first_line = f.readline().strip()
                    description = (
                        first_line.replace("# ", "")
                        if first_line.startswith("#")
                        else f"{len(repos)} repositories"
                    )

                templates.append(
                    {
                        "name": template_name,
                        "description": description,
                        "languages": languages,
                        "repo_count": len(repos),
                        "path": template_path,
                    }
                )
        except Exception as e:
            # Fallback if template can't be parsed
            templates.append(
                {
                    "name": template_name,
                    "description": f"Template with {template_name} configuration",
                    "languages": ["unknown"],
                    "repo_count": 0,
                    "path": template_path,
                }
            )

    return templates


def copy_template(template_name: str, output_path: str = "repos.yaml") -> bool:
    """Copy a template to the specified output path."""
    templates_dir = get_templates_dir()
    template_path = templates_dir / f"{template_name}.yaml"

    if not template_path.exists():
        print(f"Template '{template_name}' not found.")
        print("Available templates:")
        for template in list_templates():
            print(f"  - {template['name']}: {template['description']}")
        return False

    try:
        shutil.copy2(template_path, output_path)
        print(f"✓ Template '{template_name}' copied to {output_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to copy template: {e}")
        return False


def print_template_info(template_name: str) -> bool:
    """Print detailed information about a template."""
    templates_dir = get_templates_dir()
    template_path = templates_dir / f"{template_name}.yaml"

    if not template_path.exists():
        print(f"Template '{template_name}' not found.")
        return False

    try:
        with open(template_path, "r") as f:
            content = yaml.safe_load(f)
            repos = content.get("repositories", [])

            print(f"\nTemplate: {template_name}")
            print("=" * (len(template_name) + 9))

            # Print description from first line
            with open(template_path, "r") as f:
                first_line = f.readline().strip()
                if first_line.startswith("# "):
                    print(f"Description: {first_line[2:]}")

            print(f"Repositories: {len(repos)}")

            # Group by language
            by_language = {}
            for repo in repos:
                lang = repo.get("language", "unknown")
                if lang not in by_language:
                    by_language[lang] = []
                by_language[lang].append(repo)

            print("\nRepositories by language:")
            for lang, lang_repos in by_language.items():
                print(f"  {lang.upper()} ({len(lang_repos)}):")
                for repo in lang_repos:
                    adapters = ", ".join(repo.get("adapters", []))
                    bindings = ", ".join(repo.get("bindings", []))
                    print(
                        f"    - {repo['name']}: {repo.get('description', 'No description')}"
                    )
                    print(f"      Adapters: {adapters}")
                    print(f"      Bindings: {bindings}")

            return True

    except Exception as e:
        print(f"✗ Failed to read template: {e}")
        return False


def create_custom_template(repos: List[Dict[str, Any]], template_name: str) -> bool:
    """Create a custom template from a list of repositories."""
    templates_dir = get_templates_dir()
    templates_dir.mkdir(exist_ok=True)

    template_path = templates_dir / f"{template_name}.yaml"

    try:
        content = {"repositories": repos}

        with open(template_path, "w") as f:
            yaml.dump(content, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Custom template '{template_name}' created at {template_path}")
        return True

    except Exception as e:
        print(f"✗ Failed to create template: {e}")
        return False
