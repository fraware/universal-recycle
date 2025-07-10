"""
Interactive wizard for Universal Recycle onboarding.

This module provides an interactive CLI wizard to help new users
set up their Universal Recycle project with minimal friction.
"""

import os
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import re


class Colors:
    """ANSI color codes for rich CLI output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print("=" * len(text))


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")


def get_user_input(prompt: str, default: str = "", required: bool = True) -> str:
    """Get user input with optional default value."""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt}: ").strip()

        if not required or user_input:
            return user_input
        print_error("This field is required. Please enter a value.")


def get_yes_no(prompt: str, default: str = "Y") -> bool:
    """Get a yes/no response from the user."""
    while True:
        response = get_user_input(prompt, default, required=False).upper()
        if response in ["Y", "YES"]:
            return True
        elif response in ["N", "NO"]:
            return False
        print_error("Please enter 'Y' or 'N'.")


def detect_language_from_url(url: str) -> Optional[str]:
    """Attempt to detect language from repository URL or name."""
    url_lower = url.lower()

    # Check for language-specific patterns in URL
    if any(pattern in url_lower for pattern in ["python", "py-", "-py"]):
        return "python"
    elif any(pattern in url_lower for pattern in ["cpp", "c++", "cxx"]):
        return "cpp"
    elif any(pattern in url_lower for pattern in ["rust", "rs-", "-rs"]):
        return "rust"
    elif any(pattern in url_lower for pattern in ["go-", "-go", "golang"]):
        return "go"
    elif any(pattern in url_lower for pattern in ["wasm", "webassembly"]):
        return "wasm"

    # Check repository name
    repo_name = url.split("/")[-1].replace(".git", "").lower()
    if any(pattern in repo_name for pattern in ["python", "py-", "-py"]):
        return "python"
    elif any(pattern in repo_name for pattern in ["cpp", "c++", "cxx"]):
        return "cpp"
    elif any(pattern in repo_name for pattern in ["rust", "rs-", "-rs"]):
        return "rust"
    elif any(pattern in repo_name for pattern in ["go-", "-go", "golang"]):
        return "go"
    elif any(pattern in repo_name for pattern in ["wasm", "webassembly"]):
        return "wasm"

    return None


def get_language_choice() -> str:
    """Get language choice from user."""
    languages = ["python", "cpp", "rust", "go", "wasm"]

    print_info("Available languages:")
    for i, lang in enumerate(languages, 1):
        print(f"  {i}. {lang}")

    while True:
        try:
            choice = input("Select language (1-5): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= 5:
                return languages[int(choice) - 1]
            elif choice in languages:
                return choice
            else:
                print_error("Please enter a number 1-5 or the language name.")
        except (ValueError, IndexError):
            print_error("Invalid choice. Please try again.")


def get_adapters_for_language(language: str) -> List[str]:
    """Get suggested adapters for a language."""
    adapter_map = {
        "python": ["ruff", "mypy"],
        "cpp": ["clang-tidy", "vcpkg"],
        "rust": ["cargo-check", "cargo-fmt"],
        "go": ["go-fmt", "go-vet"],
        "wasm": ["wasm-pack", "wasm-bindgen"],
    }
    return adapter_map.get(language, [])


def get_bindings_for_language(language: str) -> List[str]:
    """Get suggested bindings for a language."""
    binding_map = {
        "python": ["grpc"],
        "cpp": ["pybind11", "grpc"],
        "rust": ["pyo3", "wasm", "grpc"],
        "go": ["cgo", "grpc"],
        "wasm": ["wasm"],
    }
    return binding_map.get(language, [])


def create_repos_yaml(repos: List[Dict[str, Any]]) -> str:
    """Create repos.yaml content."""
    content = {"repositories": repos}
    return yaml.dump(content, default_flow_style=False, sort_keys=False)


def create_cache_config(
    use_local: bool = True,
    use_redis: bool = False,
    use_s3: bool = False,
    use_gcs: bool = False,
) -> str:
    """Create cache_config.yaml content."""
    backends = []

    if use_local:
        backends.append(
            {
                "type": "local",
                "cache_dir": ".cache/universal_recycle",
                "default_ttl": 86400,
            }
        )

    if use_redis:
        backends.append(
            {
                "type": "redis",
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": None,
                "prefix": "universal_recycle:",
                "default_ttl": 3600,
            }
        )

    if use_s3:
        backends.append(
            {
                "type": "s3",
                "bucket_name": "your-universal-recycle-cache",
                "region_name": "us-east-1",
                "aws_access_key_id": "${AWS_ACCESS_KEY_ID}",
                "aws_secret_access_key": "${AWS_SECRET_ACCESS_KEY}",
                "prefix": "universal_recycle/",
                "default_ttl": 86400,
            }
        )

    if use_gcs:
        backends.append(
            {
                "type": "gcs",
                "bucket_name": "your-universal-recycle-cache",
                "project_id": "${GCP_PROJECT_ID}",
                "credentials_file": "${GOOGLE_APPLICATION_CREDENTIALS}",
                "prefix": "universal_recycle/",
                "default_ttl": 86400,
            }
        )

    content = {
        "backends": backends,
        "policies": {
            "build_artifacts": {"enabled": True, "ttl": 604800, "max_size_mb": 1024},
            "binding_generation": {"enabled": True, "ttl": 2592000, "max_size_mb": 512},
        },
    }

    return yaml.dump(content, default_flow_style=False, sort_keys=False)


def create_distribution_config(
    use_pypi: bool = False,
    use_npm: bool = False,
    use_vcpkg: bool = False,
    use_crates: bool = False,
    use_go_modules: bool = False,
) -> str:
    """Create distribution_config.yaml content."""
    endpoints = {}

    if use_pypi:
        endpoints["pypi"] = {
            "type": "pypi",
            "credentials": {
                "username": "${PYPI_USERNAME}",
                "password": "${PYPI_PASSWORD}",
            },
            "options": {
                "repository": "testpypi",
                "skip_existing": True,
                "verbose": True,
            },
        }

    if use_npm:
        endpoints["npm"] = {
            "type": "npm",
            "credentials": {
                "registry": "https://registry.npmjs.org/",
                "scope": "${NPM_SCOPE}",
            },
            "options": {"access": "public", "tag": "latest", "dry_run": False},
        }

    if use_vcpkg:
        endpoints["vcpkg"] = {
            "type": "vcpkg",
            "credentials": {
                "registry_url": "https://github.com/microsoft/vcpkg",
                "fork_url": "${VCPKG_FORK_URL}",
            },
            "options": {
                "registry_branch": "master",
                "auto_pr": False,
                "review_required": True,
            },
        }

    if use_crates:
        endpoints["crates_io"] = {
            "type": "crates.io",
            "credentials": {"api_token": "${CRATES_IO_TOKEN}"},
            "options": {"dry_run": False, "allow_dirty": False, "verify": True},
        }

    if use_go_modules:
        endpoints["go_modules"] = {
            "type": "go_modules",
            "credentials": {
                "git_remote": "origin",
                "git_user": "${GIT_USER}",
                "git_email": "${GIT_EMAIL}",
            },
            "options": {"auto_tag": True, "tag_prefix": "v", "push_tags": True},
        }

    content = {
        "endpoints": endpoints,
        "global": {
            "default_endpoints": {
                "python": ["pypi"] if use_pypi else [],
                "rust": ["crates_io"] if use_crates else [],
                "wasm": ["npm"] if use_npm else [],
                "cpp": ["vcpkg"] if use_vcpkg else [],
                "go": ["go_modules"] if use_go_modules else [],
            },
            "require_validation": True,
            "continue_on_failure": False,
            "timeout": 300,
        },
    }

    return yaml.dump(content, default_flow_style=False, sort_keys=False)


def run_wizard() -> bool:
    """Run the interactive setup wizard."""
    print_header("Welcome to Universal Recycle!")
    print_info("This wizard will help you set up your Universal Recycle project.")
    print_info(
        "Universal Recycle is a polyglot build system for recycling and modernizing code across languages."
    )

    # Get project name
    project_name = get_user_input(
        "What would you like to call your project?", "my-recycle-project"
    )

    # Collect repositories
    repos = []
    print_header("Repository Setup")
    print_info("Let's add the repositories you want to recycle and modernize.")

    while True:
        add_repo = get_yes_no("Add a repository?", "Y")
        if not add_repo:
            break

        repo_name = get_user_input("Repository name (e.g., my-cool-lib)")
        repo_url = get_user_input(
            "Repository URL (e.g., https://github.com/example/cool-lib.git)"
        )

        # Try to detect language
        detected_lang = detect_language_from_url(repo_url)
        if detected_lang:
            use_detected = get_yes_no(
                f"Detected language: {detected_lang}. Use this?", "Y"
            )
            if use_detected:
                language = detected_lang
            else:
                print_info("Select language manually:")
                language = get_language_choice()
        else:
            print_info("Could not detect language. Please select manually:")
            language = get_language_choice()

        # Get adapters
        suggested_adapters = get_adapters_for_language(language)
        print_info(
            f"Suggested adapters for {language}: {', '.join(suggested_adapters)}"
        )
        use_suggested = get_yes_no("Use suggested adapters?", "Y")

        if use_suggested:
            adapters = suggested_adapters
        else:
            print_info("Available adapters:")
            all_adapters = [
                "ruff",
                "mypy",
                "clang-tidy",
                "vcpkg",
                "cargo-check",
                "cargo-fmt",
                "go-fmt",
                "go-vet",
                "wasm-pack",
                "wasm-bindgen",
            ]
            for i, adapter in enumerate(all_adapters, 1):
                print(f"  {i}. {adapter}")

            adapter_choice = get_user_input(
                "Enter adapter numbers (comma-separated) or 'all' for suggested"
            )
            if adapter_choice.lower() == "all":
                adapters = suggested_adapters
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in adapter_choice.split(",")]
                    adapters = [
                        all_adapters[i] for i in indices if 0 <= i < len(all_adapters)
                    ]
                except (ValueError, IndexError):
                    print_warning("Invalid choice, using suggested adapters")
                    adapters = suggested_adapters

        # Get bindings
        suggested_bindings = get_bindings_for_language(language)
        print_info(
            f"Suggested bindings for {language}: {', '.join(suggested_bindings)}"
        )
        use_suggested_bindings = get_yes_no("Use suggested bindings?", "Y")

        if use_suggested_bindings:
            bindings = suggested_bindings
        else:
            print_info("Available bindings:")
            all_bindings = ["pybind11", "pyo3", "cgo", "wasm", "grpc"]
            for i, binding in enumerate(all_bindings, 1):
                print(f"  {i}. {binding}")

            binding_choice = get_user_input(
                "Enter binding numbers (comma-separated) or 'all' for suggested"
            )
            if binding_choice.lower() == "all":
                bindings = suggested_bindings
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in binding_choice.split(",")]
                    bindings = [
                        all_bindings[i] for i in indices if 0 <= i < len(all_bindings)
                    ]
                except (ValueError, IndexError):
                    print_warning("Invalid choice, using suggested bindings")
                    bindings = suggested_bindings

        repo_config = {
            "name": repo_name,
            "language": language,
            "git": repo_url,
            "commit": "main",
            "adapters": adapters,
            "bindings": bindings,
            "description": f"Recycled {language} library",
        }

        repos.append(repo_config)
        print_success(f"Added {repo_name} ({language})")

    if not repos:
        print_error("No repositories added. Setup cancelled.")
        return False

    # Cache configuration
    print_header("Cache Configuration")
    print_info("Universal Recycle can cache build artifacts for faster rebuilds.")

    use_local_cache = get_yes_no("Use local file cache?", "Y")
    use_redis_cache = get_yes_no("Use Redis cache (requires Redis server)?", "N")
    use_s3_cache = get_yes_no("Use AWS S3 cache?", "N")
    use_gcs_cache = get_yes_no("Use Google Cloud Storage cache?", "N")

    # Distribution configuration
    print_header("Distribution Configuration")
    print_info(
        "Universal Recycle can publish generated packages to various registries."
    )

    use_pypi = get_yes_no("Publish Python packages to PyPI?", "N")
    use_npm = get_yes_no("Publish WebAssembly packages to npm?", "N")
    use_vcpkg = get_yes_no("Publish C++ packages to vcpkg?", "N")
    use_crates = get_yes_no("Publish Rust packages to crates.io?", "N")
    use_go_modules = get_yes_no("Publish Go modules?", "N")

    # Generate configuration files
    print_header("Generating Configuration Files")

    # Create repos.yaml
    repos_content = create_repos_yaml(repos)
    with open("repos.yaml", "w") as f:
        f.write(repos_content)
    print_success("Created repos.yaml")

    # Create cache_config.yaml
    cache_content = create_cache_config(
        use_local_cache, use_redis_cache, use_s3_cache, use_gcs_cache
    )
    with open("cache_config.yaml", "w") as f:
        f.write(cache_content)
    print_success("Created cache_config.yaml")

    # Create distribution_config.yaml
    dist_content = create_distribution_config(
        use_pypi, use_npm, use_vcpkg, use_crates, use_go_modules
    )
    with open("distribution_config.yaml", "w") as f:
        f.write(dist_content)
    print_success("Created distribution_config.yaml")

    # Summary and next steps
    print_header("Setup Complete!")
    print_success(f"Your Universal Recycle project '{project_name}' is ready!")

    print_info("Generated files:")
    print("  - repos.yaml (repository manifest)")
    print("  - cache_config.yaml (caching configuration)")
    print("  - distribution_config.yaml (distribution configuration)")

    print_info("Next steps:")
    print("  1. Review the generated configuration files")
    print("  2. Run: python recycle/cli.py sync")
    print("  3. Run: python recycle/cli.py adapt")
    print("  4. Run: python recycle/cli.py bind")

    if any([use_pypi, use_npm, use_vcpkg, use_crates, use_go_modules]):
        print("  5. Configure your distribution credentials")
        print(
            "  6. Run: python recycle/cli.py distribute --distribution-command distribute"
        )

    print_info("For help, run: python recycle/cli.py --help")

    # Offer to run initial commands
    run_initial = get_yes_no("Would you like to run the initial sync now?", "Y")
    if run_initial:
        print_info("Running initial sync...")
        # This would be handled by the main CLI
        return True

    return True
