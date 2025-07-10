"""
Plugin system for Universal Recycle adapters.

This module defines the interface and base classes for plugins that can
process repositories (lint, modernize, scan, bind-gen, etc.).
"""

import os
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging
import yaml
import shutil

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Base exception for plugin-related errors."""

    pass


class AdapterPlugin(ABC):
    """Base class for all adapter plugins."""

    def __init__(self, repo_path: str, config: Dict[str, Any]):
        self.repo_path = repo_path
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    def can_handle(self, language: str) -> bool:
        """Check if this plugin can handle the given language."""
        pass

    @abstractmethod
    def run(self) -> bool:
        """Run the adapter on the repository. Returns True if successful."""
        pass

    def log(self, message: str, level: str = "info"):
        """Log a message with the plugin name prefix."""
        log_func = getattr(logger, level)
        log_func(f"[{self.name}] {message}")


class PythonAdapter(AdapterPlugin):
    """Base class for Python-specific adapters."""

    def can_handle(self, language: str) -> bool:
        return language.lower() in ["python", "py"]

    def _run_command(self, cmd: List[str], cwd: Optional[str] = None) -> bool:
        """Run a command and return success status."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            self.log(f"Command succeeded: {' '.join(cmd)}")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {' '.join(cmd)} - {e.stderr}", "error")
            return False


class CppAdapter(AdapterPlugin):
    """Base class for C++-specific adapters."""

    def can_handle(self, language: str) -> bool:
        return language.lower() in ["cpp", "c++", "cxx"]

    def _run_command(self, cmd: List[str], cwd: Optional[str] = None) -> bool:
        """Run a command and return success status."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            self.log(f"Command succeeded: {' '.join(cmd)}")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {' '.join(cmd)} - {e.stderr}", "error")
            return False


# Concrete adapter implementations
class RuffAdapter(PythonAdapter):
    """Ruff linter and formatter for Python."""

    def run(self) -> bool:
        self.log("Running ruff linter and formatter")

        # Check if ruff is available
        if not self._run_command(["ruff", "--version"]):
            self.log("Ruff not found, skipping", "warning")
            return True

        # Run ruff check
        check_success = self._run_command(["ruff", "check", "."])

        # Run ruff format
        format_success = self._run_command(["ruff", "format", "."])

        return check_success and format_success


class MyPyAdapter(PythonAdapter):
    """MyPy type checker for Python."""

    def run(self) -> bool:
        self.log("Running mypy type checker")

        # Check if mypy is available
        if not self._run_command(["mypy", "--version"]):
            self.log("MyPy not found, skipping", "warning")
            return True

        # Run mypy
        return self._run_command(["mypy", "."])


class ClangTidyAdapter(CppAdapter):
    """Clang-tidy linter for C++."""

    def run(self) -> bool:
        self.log("Running clang-tidy")

        # Check if clang-tidy is available
        if not self._run_command(["clang-tidy", "--version"]):
            self.log("Clang-tidy not found, skipping", "warning")
            return True

        # Find C++ source files
        cpp_files = []
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith((".cpp", ".cc", ".cxx", ".h", ".hpp")):
                    cpp_files.append(os.path.join(root, file))

        if not cpp_files:
            self.log("No C++ files found", "warning")
            return True

        # Run clang-tidy on each file
        success = True
        for cpp_file in cpp_files[:5]:  # Limit to first 5 files for demo
            if not self._run_command(["clang-tidy", cpp_file]):
                success = False

        return success


class VcpkgManifestAdapter(CppAdapter):
    """Generate vcpkg manifest for C++ projects."""

    def run(self) -> bool:
        self.log("Generating vcpkg manifest")

        manifest_path = os.path.join(self.repo_path, "vcpkg.json")

        # Check if manifest already exists
        if os.path.exists(manifest_path):
            self.log("vcpkg.json already exists, skipping", "info")
            return True

        # Create a basic vcpkg manifest
        manifest_content = {
            "name": os.path.basename(self.repo_path),
            "version": "0.1.0",
            "dependencies": [],
            "builtin-baseline": "2024-01-01",
        }

        try:
            import json

            with open(manifest_path, "w") as f:
                json.dump(manifest_content, f, indent=2)
            self.log(f"Created vcpkg.json at {manifest_path}")
            return True
        except Exception as e:
            self.log(f"Failed to create vcpkg.json: {e}", "error")
            return False


# Plugin registry
PLUGIN_REGISTRY = {
    "ruff": RuffAdapter,
    "mypy": MyPyAdapter,
    "clang_tidy": ClangTidyAdapter,
    "vcpkg_manifest": VcpkgManifestAdapter,
}


def get_plugin(
    plugin_name: str, repo_path: str, config: Dict[str, Any]
) -> Optional[AdapterPlugin]:
    """Get a plugin instance by name."""
    if plugin_name not in PLUGIN_REGISTRY:
        logger.warning(f"Plugin '{plugin_name}' not found in registry")
        return None

    plugin_class = PLUGIN_REGISTRY[plugin_name]
    return plugin_class(repo_path, config)


def run_adapters(
    repo: Dict[str, Any], repo_path: str, adapters: List[str]
) -> Dict[str, bool]:
    """Run specified adapters on a repository."""
    results = {}

    for adapter_name in adapters:
        plugin = get_plugin(adapter_name, repo_path, {"repo": repo})
        if plugin and plugin.can_handle(repo.get("language", "")):
            results[adapter_name] = plugin.run()
        else:
            logger.warning(
                f"Adapter '{adapter_name}' cannot handle language '{repo.get('language', '')}'"
            )
            results[adapter_name] = False

    return results


class PluginManifest:
    """Represents a plugin manifest (metadata)."""

    def __init__(self, manifest_path: str):
        self.path = manifest_path
        self.data = self._load_manifest(manifest_path)

    def _load_manifest(self, path: str) -> Dict[str, Any]:
        with open(path, "r") as f:
            return yaml.safe_load(f)

    @property
    def name(self) -> str:
        return self.data.get("name", "unknown")

    @property
    def version(self) -> str:
        return self.data.get("version", "0.1.0")

    @property
    def description(self) -> str:
        return self.data.get("description", "")

    @property
    def language(self) -> str:
        return self.data.get("language", "any")

    @property
    def entrypoint(self) -> str:
        return self.data.get("entrypoint", "")

    @property
    def author(self) -> str:
        return self.data.get("author", "")

    @property
    def tags(self) -> List[str]:
        return self.data.get("tags", [])


def discover_local_plugins(plugins_dir: str) -> List[PluginManifest]:
    """Discover plugin manifests in the local plugins directory."""
    manifests = []
    if not os.path.exists(plugins_dir):
        return manifests
    for entry in os.listdir(plugins_dir):
        entry_path = os.path.join(plugins_dir, entry)
        if os.path.isdir(entry_path):
            manifest_path = os.path.join(entry_path, "plugin.yaml")
            if os.path.exists(manifest_path):
                try:
                    manifests.append(PluginManifest(manifest_path))
                except Exception as e:
                    logger.warning(
                        f"Failed to load plugin manifest: {manifest_path}: {e}"
                    )
    return manifests


def list_plugins(plugins_dir: str) -> List[Dict[str, Any]]:
    """List all available plugins with metadata."""
    manifests = discover_local_plugins(plugins_dir)
    plugins = []
    for manifest in manifests:
        plugins.append(
            {
                "name": manifest.name,
                "version": manifest.version,
                "description": manifest.description,
                "language": manifest.language,
                "author": manifest.author,
                "tags": manifest.tags,
                "path": manifest.path,
            }
        )
    return plugins


def check_plugin_health(plugin_dir: str) -> dict:
    """Check the health of a plugin: manifest validity, entrypoint existence, etc."""
    manifest_path = os.path.join(plugin_dir, "plugin.yaml")
    status = {
        "manifest_found": False,
        "manifest_valid": False,
        "entrypoint_found": False,
        "errors": [],
    }
    if not os.path.exists(manifest_path):
        status["errors"].append("plugin.yaml not found")
        return status
    status["manifest_found"] = True
    try:
        manifest = PluginManifest(manifest_path)
        status["manifest_valid"] = True
        entrypoint = manifest.entrypoint
        if entrypoint:
            entrypoint_path = os.path.join(plugin_dir, entrypoint)
            if os.path.exists(entrypoint_path):
                status["entrypoint_found"] = True
            else:
                status["errors"].append(f"Entrypoint '{entrypoint}' not found")
        else:
            status["errors"].append("No entrypoint specified in manifest")
    except Exception as e:
        status["errors"].append(f"Manifest invalid: {e}")
    return status


def install_plugin(source_path: str, plugins_dir: str) -> dict:
    """Install a plugin from a local directory. Returns status dict."""
    status = {"success": False, "errors": [], "name": None}
    if not os.path.exists(source_path):
        status["errors"].append(f"Source path '{source_path}' does not exist.")
        return status
    manifest_path = os.path.join(source_path, "plugin.yaml")
    if not os.path.exists(manifest_path):
        status["errors"].append("plugin.yaml not found in source directory.")
        return status
    try:
        manifest = PluginManifest(manifest_path)
        plugin_name = manifest.name
        status["name"] = plugin_name
        dest_path = os.path.join(plugins_dir, plugin_name)
        if os.path.exists(dest_path):
            status["errors"].append(f"Plugin '{plugin_name}' already exists.")
            return status
        shutil.copytree(source_path, dest_path)
        # Validate after copy
        health = check_plugin_health(dest_path)
        if not (
            health["manifest_found"]
            and health["manifest_valid"]
            and health["entrypoint_found"]
        ):
            status["errors"].extend(health["errors"])
            shutil.rmtree(dest_path)
            return status
        status["success"] = True
        return status
    except Exception as e:
        status["errors"].append(str(e))
        return status


def remove_plugin(plugin_name: str, plugins_dir: str) -> dict:
    """Remove a plugin by name from the plugins directory. Returns status dict."""
    status = {"success": False, "errors": []}
    plugin_path = os.path.join(plugins_dir, plugin_name)
    if not os.path.exists(plugin_path):
        status["errors"].append(f"Plugin '{plugin_name}' not found.")
        return status
    try:
        shutil.rmtree(plugin_path)
        status["success"] = True
        return status
    except Exception as e:
        status["errors"].append(str(e))
        return status


def search_plugins(plugins_dir: str, query: str) -> list:
    """Search plugins by name, tag, language, or description (case-insensitive substring match)."""
    query = query.lower()
    results = []
    for plugin in list_plugins(plugins_dir):
        if (
            query in plugin["name"].lower()
            or query in plugin["language"].lower()
            or query in plugin["description"].lower()
            or any(query in tag.lower() for tag in plugin["tags"])
        ):
            results.append(plugin)
    return results
