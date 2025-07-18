"""
Validation utilities for Universal Recycle.

This module provides validation for manifests and configuration files
with helpful error messages and suggestions.
"""

import os
import yaml
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        self.message = message
        self.field = field
        self.suggestion = suggestion
        super().__init__(self.message)


def validate_repos_manifest(manifest_path: str) -> Tuple[bool, List[str]]:
    """Validate a repos.yaml manifest file."""
    errors = []

    if not os.path.exists(manifest_path):
        errors.append(f"Manifest file not found: {manifest_path}")
        return False, errors

    try:
        with open(manifest_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML syntax: {e}")
        return False, errors

    # Handle both old and new manifest formats
    if isinstance(data, list):
        repos = data
    elif isinstance(data, dict) and "repositories" in data:
        repos = data["repositories"]
    else:
        errors.append(
            "Invalid manifest format. Expected list of repositories or {repositories: [...]}"
        )
        return False, errors

    if not repos:
        errors.append("No repositories defined in manifest")
        return False, errors

    # Validate each repository
    for i, repo in enumerate(repos):
        if not isinstance(repo, dict):
            errors.append(
                f"Repository {i+1}: Expected dictionary, got {type(repo).__name__}"
            )
            continue

        # Required fields
        required_fields = ["name", "language", "git"]
        for field in required_fields:
            if field not in repo:
                errors.append(f"Repository {i+1}: Missing required field '{field}'")
                continue

        # Validate name
        name = repo.get("name", "")
        if not name or not isinstance(name, str):
            errors.append(f"Repository {i+1}: Invalid name '{name}'")

        # Validate language
        language = repo.get("language", "")
        valid_languages = ["python", "cpp", "rust", "go", "wasm"]
        if language not in valid_languages:
            errors.append(
                f"Repository {i+1}: Invalid language '{language}'. Valid options: {', '.join(valid_languages)}"
            )

        # Validate git URL
        git_url = repo.get("git", "")
        if not git_url or not isinstance(git_url, str):
            errors.append(f"Repository {i+1}: Invalid git URL '{git_url}'")
        elif not (git_url.startswith("http") or git_url.startswith("git@")):
            errors.append(
                f"Repository {i+1}: Git URL should start with 'http' or 'git@': {git_url}"
            )

        # Validate commit (optional)
        commit = repo.get("commit", "")
        if commit and not isinstance(commit, str):
            errors.append(f"Repository {i+1}: Invalid commit '{commit}'")

        # Validate adapters (optional)
        adapters = repo.get("adapters", [])
        if adapters and not isinstance(adapters, list):
            errors.append(
                f"Repository {i+1}: Adapters should be a list, got {type(adapters).__name__}"
            )
        elif adapters:
            valid_adapters = [
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
            for adapter in adapters:
                if adapter not in valid_adapters:
                    errors.append(
                        f"Repository {i+1}: Unknown adapter '{adapter}'. Valid options: {', '.join(valid_adapters)}"
                    )

        # Validate bindings (optional)
        bindings = repo.get("bindings", [])
        if bindings and not isinstance(bindings, list):
            errors.append(
                f"Repository {i+1}: Bindings should be a list, got {type(bindings).__name__}"
            )
        elif bindings:
            valid_bindings = ["pybind11", "pyo3", "cgo", "wasm", "grpc"]
            for binding in bindings:
                if binding not in valid_bindings:
                    errors.append(
                        f"Repository {i+1}: Unknown binding '{binding}'. Valid options: {', '.join(valid_bindings)}"
                    )

    return len(errors) == 0, errors


def validate_cache_config(config_path: str) -> Tuple[bool, List[str]]:
    """Validate a cache_config.yaml file."""
    errors = []

    if not os.path.exists(config_path):
        errors.append(f"Cache config file not found: {config_path}")
        return False, errors

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML syntax: {e}")
        return False, errors

    if not isinstance(data, dict):
        errors.append("Cache config should be a dictionary")
        return False, errors

    # Validate backends
    backends = data.get("backends", [])
    if not isinstance(backends, list):
        errors.append("Backends should be a list")
        return False, errors

    if not backends:
        errors.append("No cache backends configured")
        return False, errors

    valid_backend_types = ["local", "redis", "s3", "gcs"]

    for i, backend in enumerate(backends):
        if not isinstance(backend, dict):
            errors.append(
                f"Backend {i+1}: Expected dictionary, got {type(backend).__name__}"
            )
            continue

        backend_type = backend.get("type")
        if not backend_type:
            errors.append(f"Backend {i+1}: Missing 'type' field")
            continue

        if backend_type not in valid_backend_types:
            errors.append(
                f"Backend {i+1}: Invalid type '{backend_type}'. Valid options: {', '.join(valid_backend_types)}"
            )
            continue

        # Validate backend-specific fields
        if backend_type == "local":
            cache_dir = backend.get("cache_dir")
            if not cache_dir:
                errors.append(
                    f"Backend {i+1}: Local backend requires 'cache_dir' field"
                )

        elif backend_type == "redis":
            required_fields = ["host", "port"]
            for field in required_fields:
                if field not in backend:
                    errors.append(
                        f"Backend {i+1}: Redis backend requires '{field}' field"
                    )

        elif backend_type == "s3":
            required_fields = ["bucket_name", "region_name"]
            for field in required_fields:
                if field not in backend:
                    errors.append(f"Backend {i+1}: S3 backend requires '{field}' field")

        elif backend_type == "gcs":
            required_fields = ["bucket_name", "project_id"]
            for field in required_fields:
                if field not in backend:
                    errors.append(
                        f"Backend {i+1}: GCS backend requires '{field}' field"
                    )

    return len(errors) == 0, errors


def validate_distribution_config(config_path: str) -> Tuple[bool, List[str]]:
    """Validate a distribution_config.yaml file."""
    errors = []

    if not os.path.exists(config_path):
        errors.append(f"Distribution config file not found: {config_path}")
        return False, errors

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML syntax: {e}")
        return False, errors

    if not isinstance(data, dict):
        errors.append("Distribution config should be a dictionary")
        return False, errors

    # Validate endpoints
    endpoints = data.get("endpoints", {})
    if not isinstance(endpoints, dict):
        errors.append("Endpoints should be a dictionary")
        return False, errors

    valid_endpoint_types = ["pypi", "npm", "vcpkg", "crates.io", "go_modules"]

    for endpoint_name, endpoint_config in endpoints.items():
        if not isinstance(endpoint_config, dict):
            errors.append(
                f"Endpoint '{endpoint_name}': Expected dictionary, got {type(endpoint_config).__name__}"
            )
            continue

        endpoint_type = endpoint_config.get("type")
        if not endpoint_type:
            errors.append(f"Endpoint '{endpoint_name}': Missing 'type' field")
            continue

        if endpoint_type not in valid_endpoint_types:
            errors.append(
                f"Endpoint '{endpoint_name}': Invalid type '{endpoint_type}'. Valid options: {', '.join(valid_endpoint_types)}"
            )
            continue

        # Validate endpoint-specific fields
        if endpoint_type == "pypi":
            # PyPI endpoints typically use environment variables for credentials
            pass

        elif endpoint_type == "npm":
            registry = endpoint_config.get("credentials", {}).get("registry")
            if not registry:
                errors.append(
                    f"Endpoint '{endpoint_name}': npm endpoint should specify registry in credentials"
                )

        elif endpoint_type == "vcpkg":
            registry_url = endpoint_config.get("credentials", {}).get("registry_url")
            if not registry_url:
                errors.append(
                    f"Endpoint '{endpoint_name}': vcpkg endpoint should specify registry_url in credentials"
                )

        elif endpoint_type == "crates.io":
            # crates.io typically uses cargo login or API tokens
            pass

        elif endpoint_type == "go_modules":
            # Go modules typically use git configuration
            pass

    return len(errors) == 0, errors


def validate_all_configs(
    manifest_path: str,
    cache_config_path: Optional[str] = None,
    distribution_config_path: Optional[str] = None,
) -> Tuple[bool, Dict[str, List[str]]]:
    """Validate all configuration files."""
    all_errors = {}

    # Validate manifest
    manifest_valid, manifest_errors = validate_repos_manifest(manifest_path)
    all_errors["manifest"] = manifest_errors

    # Validate cache config if provided
    if cache_config_path:
        cache_valid, cache_errors = validate_cache_config(cache_config_path)
        all_errors["cache"] = cache_errors
    else:
        all_errors["cache"] = []

    # Validate distribution config if provided
    if distribution_config_path:
        dist_valid, dist_errors = validate_distribution_config(distribution_config_path)
        all_errors["distribution"] = dist_errors
    else:
        all_errors["distribution"] = []

    # Check if all validations passed
    all_valid = all(len(errors) == 0 for errors in all_errors.values())

    return all_valid, all_errors


def print_validation_errors(errors: Dict[str, List[str]]):
    """Print validation errors in a user-friendly format."""
    from colors import print_error, print_warning, print_info

    total_errors = sum(len(error_list) for error_list in errors.values())

    if total_errors == 0:
        print_info("All configuration files are valid!")
        return

    print_error(f"Found {total_errors} validation error(s):")

    for config_type, error_list in errors.items():
        if error_list:
            print_warning(f"\n{config_type.upper()} Configuration:")
            for error in error_list:
                print_error(f"  • {error}")


def suggest_fixes(errors: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Generate suggestions for fixing validation errors."""
    suggestions = {}

    for config_type, error_list in errors.items():
        config_suggestions = []

        for error in error_list:
            if "Missing required field" in error:
                field = error.split("'")[1] if "'" in error else "field"
                config_suggestions.append(f"Add the missing '{field}' field")

            elif "Invalid language" in error:
                config_suggestions.append("Use one of: python, cpp, rust, go, wasm")

            elif "Unknown adapter" in error:
                config_suggestions.append(
                    "Use valid adapters: ruff, mypy, clang-tidy, vcpkg, cargo-check, cargo-fmt, go-fmt, go-vet, wasm-pack, wasm-bindgen"
                )

            elif "Unknown binding" in error:
                config_suggestions.append(
                    "Use valid bindings: pybind11, pyo3, cgo, wasm, grpc"
                )

            elif "Invalid git URL" in error:
                config_suggestions.append(
                    "Use a valid git URL starting with 'http' or 'git@'"
                )

            elif "Invalid YAML syntax" in error:
                config_suggestions.append(
                    "Check your YAML syntax, ensure proper indentation"
                )

            elif "No repositories defined" in error:
                config_suggestions.append(
                    "Add at least one repository to your manifest"
                )

            else:
                config_suggestions.append(
                    "Review the configuration format in the documentation"
                )

        if config_suggestions:
            suggestions[config_type] = config_suggestions

    return suggestions


def print_suggestions(suggestions: Dict[str, List[str]]):
    """Print suggestions for fixing validation errors."""
    from colors import print_info

    if not suggestions:
        return

    print_info("\nSuggestions to fix the errors:")

    for config_type, suggestion_list in suggestions.items():
        print_info(f"\n{config_type.upper()} Configuration:")
        for suggestion in suggestion_list:
            print(f"  • {suggestion}")
