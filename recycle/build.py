"""
Advanced build features for Universal Recycle.

This module provides build graph visualization, status tracking,
logs management, and build hooks for the Universal Recycle system.
"""

import os
import json
import time
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import yaml

logger = logging.getLogger(__name__)


class BuildGraph:
    """Represents a build dependency graph."""

    def __init__(self):
        self.nodes = {}  # target_name -> node_info
        self.edges = []  # list of (from, to) tuples

    def add_target(
        self, name: str, language: str = "unknown", dependencies: List[str] = None
    ):
        """Add a build target to the graph."""
        self.nodes[name] = {
            "name": name,
            "language": language,
            "dependencies": dependencies or [],
            "status": "pending",
        }

        if dependencies:
            for dep in dependencies:
                self.edges.append((dep, name))

    def get_dot_format(self) -> str:
        """Generate DOT format for graph visualization."""
        lines = ["digraph BuildGraph {"]
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box, style=filled];")

        # Add nodes with colors by language
        colors = {
            "python": "lightblue",
            "cpp": "lightgreen",
            "rust": "orange",
            "go": "lightcoral",
            "javascript": "lightyellow",
            "unknown": "lightgray",
        }

        for name, node in self.nodes.items():
            color = colors.get(node["language"], colors["unknown"])
            lines.append(
                f'  "{name}" [fillcolor="{color}", label="{name}\\n{node["language"]}"];'
            )

        # Add edges
        for from_node, to_node in self.edges:
            lines.append(f'  "{from_node}" -> "{to_node}";')

        lines.append("}")
        return "\n".join(lines)

    def save_dot_file(self, output_path: str):
        """Save the graph in DOT format to a file."""
        with open(output_path, "w") as f:
            f.write(self.get_dot_format())


class BuildStatus:
    """Tracks build status and diagnostics."""

    def __init__(self, build_dir: str = ".build"):
        self.build_dir = Path(build_dir)
        self.build_dir.mkdir(exist_ok=True)
        self.status_file = self.build_dir / "status.json"
        self.logs_dir = self.build_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def get_status(self) -> Dict[str, Any]:
        """Get current build status."""
        if self.status_file.exists():
            with open(self.status_file, "r") as f:
                return json.load(f)
        return {
            "last_build": None,
            "status": "never_built",
            "targets": {},
            "errors": [],
            "warnings": [],
        }

    def update_status(self, status_data: Dict[str, Any]):
        """Update build status."""
        with open(self.status_file, "w") as f:
            json.dump(status_data, f, indent=2)

    def add_log_entry(self, target: str, message: str, level: str = "info"):
        """Add a log entry for a target."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_file = self.logs_dir / f"{target}.log"

        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] [{level.upper()}] {message}\n")

    def get_recent_logs(self, target: str = None, lines: int = 50) -> List[str]:
        """Get recent build logs."""
        logs = []

        if target:
            log_files = [self.logs_dir / f"{target}.log"]
        else:
            log_files = list(self.logs_dir.glob("*.log"))

        for log_file in log_files:
            if log_file.exists():
                with open(log_file, "r") as f:
                    file_logs = f.readlines()
                    logs.extend(file_logs[-lines:])

        return sorted(logs, key=lambda x: x.split("]")[0] if "]" in x else x)


class BuildHooks:
    """Manages pre/post build hooks."""

    def __init__(self, hooks_dir: str = ".hooks"):
        self.hooks_dir = Path(hooks_dir)
        self.hooks_dir.mkdir(exist_ok=True)

    def list_hooks(self) -> Dict[str, List[str]]:
        """List available hooks."""
        hooks = {"pre": [], "post": []}

        for hook_type in ["pre", "post"]:
            hook_dir = self.hooks_dir / hook_type
            if hook_dir.exists():
                hooks[hook_type] = [f.name for f in hook_dir.iterdir() if f.is_file()]

        return hooks

    def add_hook(self, hook_type: str, name: str, script_content: str):
        """Add a new hook script."""
        hook_dir = self.hooks_dir / hook_type
        hook_dir.mkdir(exist_ok=True)

        hook_file = hook_dir / name
        with open(hook_file, "w") as f:
            f.write(script_content)

        # Make executable on Unix systems
        try:
            os.chmod(hook_file, 0o755)
        except:
            pass  # Windows doesn't have chmod

    def run_hooks(self, hook_type: str, context: Dict[str, Any] = None) -> bool:
        """Run hooks of a specific type."""
        hook_dir = self.hooks_dir / hook_type
        if not hook_dir.exists():
            return True

        success = True
        for hook_file in hook_dir.iterdir():
            if hook_file.is_file():
                try:
                    # Set environment variables for the hook
                    env = os.environ.copy()
                    if context:
                        for key, value in context.items():
                            env[f"BUILD_{key.upper()}"] = str(value)

                    result = subprocess.run(
                        [str(hook_file)],
                        env=env,
                        capture_output=True,
                        text=True,
                        cwd=self.hooks_dir,
                    )

                    if result.returncode != 0:
                        logger.error(f"Hook {hook_file.name} failed: {result.stderr}")
                        success = False
                    else:
                        logger.info(f"Hook {hook_file.name} completed successfully")

                except Exception as e:
                    logger.error(f"Failed to run hook {hook_file.name}: {e}")
                    success = False

        return success


def generate_build_graph_from_repos(repos: List[Dict[str, Any]]) -> BuildGraph:
    """Generate a build graph from repository information."""
    graph = BuildGraph()

    for repo in repos:
        repo_name = repo["name"]
        language = repo.get("language", "unknown")

        # Add the repository as a target
        graph.add_target(repo_name, language)

        # Add dependencies based on language-specific rules
        if language == "python":
            # Python repos might depend on other Python repos
            pass
        elif language == "cpp":
            # C++ repos might depend on other C++ repos
            pass

    return graph


def get_build_status() -> Dict[str, Any]:
    """Get the current build status."""
    status = BuildStatus()
    return status.get_status()


def get_build_logs(target: str = None, lines: int = 50) -> List[str]:
    """Get recent build logs."""
    status = BuildStatus()
    return status.get_recent_logs(target, lines)


def list_build_hooks() -> Dict[str, List[str]]:
    """List available build hooks."""
    hooks = BuildHooks()
    return hooks.list_hooks()


def get_subgraph_for_target(graph: BuildGraph, target: str) -> BuildGraph:
    """Return a subgraph containing the target and all its dependencies."""
    subgraph = BuildGraph()
    visited = set()

    def visit(node):
        if node in visited or node not in graph.nodes:
            return
        visited.add(node)
        node_info = graph.nodes[node]
        subgraph.add_target(node, node_info["language"], node_info["dependencies"])
        for dep in node_info["dependencies"]:
            visit(dep)

    visit(target)
    return subgraph


def simulate_build_targets(graph: BuildGraph, targets: list) -> dict:
    """Simulate building the given targets in the graph. Returns build status per target."""
    status = {}
    for target in targets:
        # Simulate build (in real system, invoke Bazel or build tool)
        status[target] = "built"
    return status


# Example build_profiles.yaml structure:
# profiles:
#   debug:
#     cflags: "-g -O0"
#     env:
#       DEBUG: "1"
#   release:
#     cflags: "-O3"
#     env:
#       DEBUG: "0"


def load_build_profiles(profiles_path: str = "build_profiles.yaml") -> dict:
    """Load build profiles from a YAML config file."""
    if not os.path.exists(profiles_path):
        # Provide default profiles if file is missing
        return {
            "debug": {"cflags": "-g -O0", "env": {"DEBUG": "1"}},
            "release": {"cflags": "-O3", "env": {"DEBUG": "0"}},
        }
    with open(profiles_path, "r") as f:
        data = yaml.safe_load(f)
    return data.get("profiles", {})


def get_profile_settings(profile_name: str, profiles: dict) -> dict:
    """Get settings for a given profile name."""
    if profile_name in profiles:
        return profiles[profile_name]
    # Fallback to debug if not found
    return profiles.get("debug", {})


def simulate_build_targets_with_profile(
    graph: BuildGraph, targets: list, profile_settings: dict
) -> dict:
    """Simulate building targets with profile settings (flags/env)."""
    status = {}
    for target in targets:
        # Simulate build (in real system, pass flags/env to Bazel or build tool)
        status[target] = {
            "result": "built",
            "cflags": profile_settings.get("cflags", ""),
            "env": profile_settings.get("env", {}),
        }
    return status
