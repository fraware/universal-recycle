"""
Color utilities for Universal Recycle CLI.

This module provides cross-platform color support for rich CLI output.
"""

import os
import sys
from typing import Optional


class Colors:
    """ANSI color codes for rich CLI output."""

    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Formatting
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"

    # Reset
    RESET = "\033[0m"

    # Semantic colors
    SUCCESS = GREEN
    ERROR = RED
    WARNING = YELLOW
    INFO = BLUE
    HEADER = BRIGHT_MAGENTA


def supports_color() -> bool:
    """Check if the terminal supports color output."""
    # Check if we're in a terminal
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    # Check for NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        return False

    # Check for Windows
    if os.name == "nt":
        # Windows 10+ supports ANSI colors
        return os.environ.get("TERM") == "xterm-256color" or "ANSICON" in os.environ

    return True


def colorize(text: str, color: str, bold: bool = False) -> str:
    """Add color to text if supported."""
    if not supports_color():
        return text

    result = color
    if bold:
        result += Colors.BOLD
    result += text + Colors.RESET

    return result


def print_success(text: str):
    """Print a success message in green."""
    print(colorize(f"✓ {text}", Colors.SUCCESS))


def print_error(text: str):
    """Print an error message in red."""
    print(colorize(f"✗ {text}", Colors.ERROR))


def print_warning(text: str):
    """Print a warning message in yellow."""
    print(colorize(f"⚠ {text}", Colors.WARNING))


def print_info(text: str):
    """Print an info message in blue."""
    print(colorize(f"ℹ {text}", Colors.INFO))


def print_header(text: str):
    """Print a header message in bright magenta."""
    print()
    print(colorize(text, Colors.HEADER, bold=True))
    print("=" * len(text))


def print_step(step: int, total: int, text: str):
    """Print a step message with progress indicator."""
    progress = f"[{step}/{total}]"
    print(colorize(f"{progress} {text}", Colors.BRIGHT_BLUE))


def print_summary(title: str, items: dict):
    """Print a summary with colored status indicators."""
    print_header(title)
    for name, status in items.items():
        if isinstance(status, bool):
            icon = "✓" if status else "✗"
            color = Colors.SUCCESS if status else Colors.ERROR
            print(f"  {colorize(icon, color)} {name}")
        else:
            print(f"  {name}: {status}")


def print_progress(current: int, total: int, description: str = ""):
    """Print a progress bar."""
    if not supports_color():
        percentage = int((current / total) * 100)
        print(f"Progress: {percentage}% {description}")
        return

    bar_length = 30
    filled_length = int(bar_length * current // total)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)
    percentage = int((current / total) * 100)

    progress_text = f"Progress: [{bar}] {percentage}% {description}"
    print(f"\r{colorize(progress_text, Colors.BRIGHT_BLUE)}", end="", flush=True)

    if current == total:
        print()  # New line when complete


def print_command_suggestion(command: str, description: str = ""):
    """Print a suggested next command."""
    if description:
        print_info(f"Next: {description}")
    print(colorize(f"  $ {command}", Colors.BRIGHT_CYAN))


def print_help_section(title: str, commands: list):
    """Print a help section with commands."""
    print_header(title)
    for cmd, desc in commands:
        print(f"  {colorize(cmd, Colors.BRIGHT_CYAN)} - {desc}")


# Convenience functions for common patterns
def print_sync_summary(success_count: int, total_count: int):
    """Print a sync operation summary."""
    if success_count == total_count:
        print_success(f"All {total_count} repositories synced successfully!")
    else:
        print_warning(f"{success_count}/{total_count} repositories synced successfully")
        print_error(f"{total_count - success_count} repositories failed to sync")


def print_adapter_summary(results: dict):
    """Print an adapter operation summary."""
    print_header("Adapter Summary")
    for repo_name, repo_results in results.items():
        success_count = sum(1 for success in repo_results.values() if success)
        total_count = len(repo_results)

        if success_count == total_count:
            print_success(
                f"{repo_name}: {success_count}/{total_count} adapters succeeded"
            )
        else:
            print_warning(
                f"{repo_name}: {success_count}/{total_count} adapters succeeded"
            )

            # Show which adapters failed
            for adapter, success in repo_results.items():
                if not success:
                    print_error(f"    {adapter} failed")


def print_binding_summary(results: dict):
    """Print a binding generation summary."""
    print_header("Binding Generation Summary")
    for repo_name, repo_results in results.items():
        success_count = sum(1 for success in repo_results.values() if success)
        total_count = len(repo_results)

        if success_count == total_count:
            print_success(
                f"{repo_name}: {success_count}/{total_count} generators succeeded"
            )
        else:
            print_warning(
                f"{repo_name}: {success_count}/{total_count} generators succeeded"
            )

            # Show which generators failed
            for generator, success in repo_results.items():
                if not success:
                    print_error(f"    {generator} failed")

        # Show generated bindings
        if success_count > 0:
            print_info(f"    Generated bindings available in:")
            # This would be populated based on actual generated files
            print(f"      - {repo_name}/python_bindings/ (pybind11)")
            print(f"      - {repo_name}/grpc/ (gRPC)")


def print_cache_summary(stats: dict):
    """Print a cache operation summary."""
    print_header("Cache Summary")
    for backend_name, backend_stats in stats.items():
        print(f"  {colorize(backend_name.upper(), Colors.BRIGHT_BLUE)} Backend:")
        print(f"    Total files: {backend_stats.get('total_files', 0)}")
        print(f"    Total size: {backend_stats.get('total_size_mb', 0):.2f} MB")
        if "cache_dir" in backend_stats:
            print(f"    Cache directory: {backend_stats['cache_dir']}")


def print_validation_summary(valid: bool, errors: dict):
    """Print a validation summary."""
    if valid:
        print_success("All configuration files are valid!")
    else:
        print_error("Configuration validation failed!")
        print_header("Validation Errors")
        for file_path, file_errors in errors.items():
            print(f"  {colorize(file_path, Colors.BRIGHT_RED)}:")
            for error in file_errors:
                print(f"    {colorize('✗', Colors.ERROR)} {error}")


def print_next_steps(steps: list):
    """Print suggested next steps."""
    print_header("Next Steps")
    for i, step in enumerate(steps, 1):
        print(f"  {colorize(f'{i}.', Colors.BRIGHT_BLUE)} {step}")


def print_command_help(command: str, description: str, examples: list | None = None):
    """Print help for a specific command."""
    print_header(f"Command: {command}")
    print(f"  {description}")
    if examples:
        print()
        print("  Examples:")
        for example in examples:
            print(f"    {colorize(f'$ {example}', Colors.BRIGHT_CYAN)}")


def print_plugin_status(plugin_name: str, status: bool, details: str = ""):
    """Print plugin status with details."""
    icon = "✓" if status else "✗"
    color = Colors.SUCCESS if status else Colors.ERROR
    status_text = "Available" if status else "Not available"

    print(f"  {colorize(icon, color)} {plugin_name}: {status_text}")
    if details:
        print(f"    {colorize(details, Colors.DIM)}")


def print_repository_info(repo: dict):
    """Print detailed repository information."""
    print(f"  {colorize(repo['name'], Colors.BRIGHT_BLUE)} ({repo['language']})")
    print(f"    Repository: {repo['git']}")
    print(f"    Commit: {repo['commit']}")
    if "adapters" in repo:
        print(f"    Adapters: {', '.join(repo['adapters'])}")
    if "bindings" in repo:
        print(f"    Bindings: {', '.join(repo['bindings'])}")


def print_manifest_summary(repos: list):
    """Print a manifest summary."""
    print_header("Manifest Summary")
    print(f"  Total repositories: {len(repos)}")

    # Group by language
    languages = {}
    for repo in repos:
        lang = repo["language"]
        if lang not in languages:
            languages[lang] = []
        languages[lang].append(repo["name"])

    print("  By language:")
    for lang, repos_list in languages.items():
        print(f"    {colorize(lang, Colors.BRIGHT_GREEN)}: {len(repos_list)} repos")
        for repo_name in repos_list:
            print(f"      - {repo_name}")


def print_workspace_info(workspace_path: str, repo_count: int):
    """Print workspace generation information."""
    print_success(f"Generated Bazel workspace at {workspace_path}")
    print(f"  Contains {repo_count} repositories")
    print_next_steps(
        [
            "Review the generated workspace file",
            "Add it to your main WORKSPACE file",
            f"Build with: bazel build @{repo_count > 0 and 'repo_name' or 'target'}//...",
        ]
    )


def print_distribution_summary(results: dict):
    """Print a distribution operation summary."""
    print_header("Distribution Summary")
    for repo_name, repo_results in results.items():
        print(f"  {colorize(repo_name, Colors.BRIGHT_BLUE)}:")

        for package_type, endpoint_results in repo_results.items():
            if isinstance(endpoint_results, dict):
                success_count = sum(
                    1 for success in endpoint_results.values() if success
                )
                total_count = len(endpoint_results)

                if success_count == total_count:
                    print_success(
                        f"    {package_type}: {success_count}/{total_count} endpoints succeeded"
                    )
                else:
                    print_warning(
                        f"    {package_type}: {success_count}/{total_count} endpoints succeeded"
                    )

                # Show individual endpoint results
                for endpoint_name, success in endpoint_results.items():
                    icon = "✓" if success else "✗"
                    color = Colors.SUCCESS if success else Colors.ERROR
                    print(f"      {colorize(icon, color)} {endpoint_name}")
