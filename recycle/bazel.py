"""
Bazel integration for Universal Recycle.

This module provides deep integration with Bazel as the build orchestrator,
including BUILD file generation, command invocation, and result parsing.
"""

import os
import subprocess
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def check_bazel_available() -> bool:
    """Check if Bazel is available in the system PATH."""
    try:
        result = subprocess.run(
            ["bazel", "--version"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_bazel_version() -> Optional[str]:
    """Get the Bazel version if available."""
    try:
        result = subprocess.run(
            ["bazel", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def generate_bazel_build_file(
    repo_info: Dict[str, Any], repo_path: str, profile_settings: Dict[str, Any]
) -> str:
    """Generate a Bazel BUILD file for a repository based on its language and profile settings."""
    language = repo_info.get("language", "unknown")
    repo_name = repo_info["name"]

    build_content = []
    build_content.append(f"# Generated BUILD file for {repo_name}")
    build_content.append(f"# Language: {language}")
    build_content.append("")

    if language == "python":
        build_content.extend(
            _generate_python_build(repo_name, repo_path, profile_settings)
        )
    elif language == "cpp":
        build_content.extend(
            _generate_cpp_build(repo_name, repo_path, profile_settings)
        )
    elif language == "rust":
        build_content.extend(
            _generate_rust_build(repo_name, repo_path, profile_settings)
        )
    elif language == "go":
        build_content.extend(_generate_go_build(repo_name, repo_path, profile_settings))
    else:
        build_content.extend(
            _generate_generic_build(repo_name, repo_path, profile_settings)
        )

    return "\n".join(build_content)


def _generate_python_build(
    repo_name: str, repo_path: str, profile_settings: Dict[str, Any]
) -> List[str]:
    """Generate Python-specific Bazel BUILD rules."""
    lines = []
    lines.append('load("@rules_python//python:defs.bzl", "py_library", "py_binary")')
    lines.append("")
    lines.append(f"py_library(")
    lines.append(f'    name = "{repo_name}",')
    lines.append(f'    srcs = glob(["**/*.py"]),')
    lines.append(f'    visibility = ["//visibility:public"],')
    lines.append(f")")
    lines.append("")
    lines.append(f"py_binary(")
    lines.append(f'    name = "{repo_name}_bin",')
    lines.append(f'    srcs = ["__main__.py"],')
    lines.append(f'    deps = [":{repo_name}"],')
    lines.append(f")")
    return lines


def _generate_cpp_build(
    repo_name: str, repo_path: str, profile_settings: Dict[str, Any]
) -> List[str]:
    """Generate C++-specific Bazel BUILD rules."""
    lines = []
    lines.append('load("@rules_cc//cc:defs.bzl", "cc_library", "cc_binary")')
    lines.append("")

    # Apply profile settings
    cflags = profile_settings.get("cflags", "")
    if cflags:
        lines.append(f"cc_library(")
        lines.append(f'    name = "{repo_name}",')
        lines.append(f'    srcs = glob(["**/*.cpp", "**/*.cc"]),')
        lines.append(f'    hdrs = glob(["**/*.h", "**/*.hpp"]),')
        lines.append(f'    copts = ["{cflags}"],')
        lines.append(f'    visibility = ["//visibility:public"],')
        lines.append(f")")
    else:
        lines.append(f"cc_library(")
        lines.append(f'    name = "{repo_name}",')
        lines.append(f'    srcs = glob(["**/*.cpp", "**/*.cc"]),')
        lines.append(f'    hdrs = glob(["**/*.h", "**/*.hpp"]),')
        lines.append(f'    visibility = ["//visibility:public"],')
        lines.append(f")")

    return lines


def _generate_rust_build(
    repo_name: str, repo_path: str, profile_settings: Dict[str, Any]
) -> List[str]:
    """Generate Rust-specific Bazel BUILD rules."""
    lines = []
    lines.append('load("@rules_rust//rust:defs.bzl", "rust_library", "rust_binary")')
    lines.append("")
    lines.append(f"rust_library(")
    lines.append(f'    name = "{repo_name}",')
    lines.append(f'    srcs = glob(["src/**/*.rs"]),')
    lines.append(f'    visibility = ["//visibility:public"],')
    lines.append(f")")
    return lines


def _generate_go_build(
    repo_name: str, repo_path: str, profile_settings: Dict[str, Any]
) -> List[str]:
    """Generate Go-specific Bazel BUILD rules."""
    lines = []
    lines.append('load("@io_bazel_rules_go//go:def.bzl", "go_library", "go_binary")')
    lines.append("")
    lines.append(f"go_library(")
    lines.append(f'    name = "{repo_name}",')
    lines.append(f'    srcs = glob(["**/*.go"]),')
    lines.append(f'    importpath = "github.com/example/{repo_name}",')
    lines.append(f'    visibility = ["//visibility:public"],')
    lines.append(f")")
    return lines


def _generate_generic_build(
    repo_name: str, repo_path: str, profile_settings: Dict[str, Any]
) -> List[str]:
    """Generate generic BUILD rules for unknown languages."""
    lines = []
    lines.append(f"# Generic BUILD file for {repo_name}")
    lines.append(f"# Language not recognized, using basic filegroup")
    lines.append("")
    lines.append(f"filegroup(")
    lines.append(f'    name = "{repo_name}",')
    lines.append(f'    srcs = glob(["**/*"]),')
    lines.append(f'    visibility = ["//visibility:public"],')
    lines.append(f")")
    return lines


def invoke_bazel_command(
    command: List[str], workspace_path: str, profile_settings: Dict[str, Any]
) -> Tuple[bool, str, str]:
    """Invoke a Bazel command with profile settings applied."""
    # Set environment variables from profile
    env = os.environ.copy()
    for key, value in profile_settings.get("env", {}).items():
        env[key] = str(value)

    # Add profile-specific flags to Bazel command
    cflags = profile_settings.get("cflags", "")
    if cflags:
        command.extend(["--copt", cflags])

    try:
        result = subprocess.run(
            command,
            cwd=workspace_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        success = result.returncode == 0
        return success, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return False, "", "Bazel command timed out"
    except Exception as e:
        return False, "", f"Failed to invoke Bazel: {e}"


def build_target_with_bazel(
    target: str, workspace_path: str, profile_settings: Dict[str, Any]
) -> Dict[str, Any]:
    """Build a specific target using Bazel with profile settings."""
    if not check_bazel_available():
        return {
            "success": False,
            "error": "Bazel not available",
            "output": "",
            "stderr": "",
        }

    command = ["bazel", "build", f"//{target}"]
    success, stdout, stderr = invoke_bazel_command(
        command, workspace_path, profile_settings
    )

    return {
        "success": success,
        "output": stdout,
        "stderr": stderr,
        "target": target,
        "profile": profile_settings,
    }


def query_bazel_dependencies(target: str, workspace_path: str) -> List[str]:
    """Query Bazel for target dependencies."""
    if not check_bazel_available():
        return []

    try:
        result = subprocess.run(
            ["bazel", "query", f"deps(//{target})"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return [line.strip() for line in result.stdout.split("\n") if line.strip()]
    except Exception as e:
        logger.error(f"Failed to query Bazel dependencies: {e}")

    return []


def generate_bazel_workspace_with_profiles(
    repos: List[Dict[str, Any]], repos_dir: str, profile_settings: Dict[str, Any]
) -> str:
    """Generate a Bazel WORKSPACE file with profile-specific settings."""
    workspace_content = []
    workspace_content.append('workspace(name = "universal_recycle")')
    workspace_content.append("")

    # Add profile-specific workspace settings
    if profile_settings.get("env"):
        workspace_content.append("# Profile environment variables:")
        for key, value in profile_settings["env"].items():
            workspace_content.append(f"# {key}={value}")
        workspace_content.append("")

    # Add repository references
    for repo in repos:
        repo_name = repo["name"]
        repo_path = os.path.join(repos_dir, repo_name)

        if os.path.exists(repo_path):
            workspace_content.append(f"local_repository(")
            workspace_content.append(f'    name = "{repo_name}",')
            workspace_content.append(f'    path = "{repo_path}",')
            workspace_content.append(f")")
            workspace_content.append("")

    return "\n".join(workspace_content)
