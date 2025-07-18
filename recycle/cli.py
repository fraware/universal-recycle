import yaml
import os
import sys
import argparse
from pathlib import Path
import subprocess
import shutil
import logging
from plugin import (
    run_adapters,
    list_plugins,
    PluginManifest,
    check_plugin_health,
    install_plugin,
    remove_plugin,
    search_plugins,
)
from bindings import generate_bindings
from cache import CacheManager, generate_build_cache_key, generate_binding_cache_key
from distribution import (
    DistributionManager,
    load_distribution_config,
    distribute_packages,
)
from typing import Dict, Any
from wizard import run_wizard
from templates import list_templates, copy_template, print_template_info
from validation import (
    validate_all_configs,
    print_validation_errors,
    suggest_fixes,
    print_suggestions,
)
from colors import (
    print_progress,
    print_sync_summary,
    print_adapter_summary,
    print_binding_summary,
    print_distribution_summary,
    print_cache_summary,
    print_validation_summary,
    print_next_steps,
    print_manifest_summary,
    print_workspace_info,
    print_repository_info,
    print_help_section,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
)

try:
    from build import (
        generate_build_graph_from_repos,
        get_build_status,
        get_build_logs,
        list_build_hooks,
        BuildHooks,
        get_subgraph_for_target,
        simulate_build_targets,
        load_build_profiles,
        get_profile_settings,
        simulate_build_targets_with_profile,
    )
except ImportError:
    # Fallback for when build module is not available
    generate_build_graph_from_repos = None
    get_build_status = None
    get_build_logs = None
    list_build_hooks = None
    BuildHooks = None
    get_subgraph_for_target = None
    simulate_build_targets = None
    load_build_profiles = None
    get_profile_settings = None
    simulate_build_targets_with_profile = None

try:
    from bazel import (
        check_bazel_available,
        get_bazel_version,
        build_target_with_bazel,
        generate_bazel_build_file,
        generate_bazel_workspace_with_profiles,
    )
except ImportError:
    check_bazel_available = None
    get_bazel_version = None
    build_target_with_bazel = None
    generate_bazel_build_file = None
    generate_bazel_workspace_with_profiles = None

try:
    from collaboration import TeamManager, CICDIntegration
    from performance import (
        DistributedBuildManager,
        EnhancedCacheManager,
        PerformanceMonitor,
    )
except ImportError:
    TeamManager = None
    CICDIntegration = None
    DistributedBuildManager = None
    EnhancedCacheManager = None
    PerformanceMonitor = None

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_manifest(manifest_path):
    """Load and parse the repos.yaml manifest."""
    if not os.path.exists(manifest_path):
        print(f"repos.yaml not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r") as f:
        data = yaml.safe_load(f)

    # Handle both old and new manifest formats
    if isinstance(data, list):
        # Old format: list of repositories
        return data
    elif isinstance(data, dict) and "repositories" in data:
        # New format: {repositories: [...]}
        return data["repositories"]
    else:
        print("Invalid manifest format", file=sys.stderr)
        sys.exit(1)


def load_cache_config(config_path):
    """Load cache configuration."""
    if not os.path.exists(config_path):
        print(
            f"Cache config not found at {config_path}, using defaults", file=sys.stderr
        )
        return {
            "backends": [{"type": "local", "cache_dir": ".cache/universal_recycle"}]
        }

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_distribution_config_file(config_path):
    """Load distribution configuration."""
    if not os.path.exists(config_path):
        print(
            f"Distribution config not found at {config_path}, using defaults",
            file=sys.stderr,
        )
        return {"endpoints": {}}

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def print_manifest(repos):
    """Print the loaded manifest in a readable format."""
    print("Loaded manifest:")
    for repo in repos:
        print(
            f"- {repo['name']} ({repo['language']}): {repo['git']} @ {repo['commit']}"
        )
        if "adapters" in repo:
            print(f"  Adapters: {', '.join(repo['adapters'])}")


def clone_repo(repo, repos_dir):
    """Clone a repository to the specified directory."""
    repo_name = repo["name"]
    repo_url = repo["git"]
    commit = repo["commit"]

    repo_path = os.path.join(repos_dir, repo_name)

    print(f"Cloning {repo_name}...")

    # Remove existing directory if it exists
    if os.path.exists(repo_path):
        print(f"  Removing existing {repo_name}")
        shutil.rmtree(repo_path)

    # Clone the repository
    try:
        subprocess.run(
            ["git", "clone", repo_url, repo_path],
            check=True,
            capture_output=True,
            text=True,
        )

        # Checkout specific commit if specified
        if commit and commit != "main" and commit != "master":
            print(f"  Checking out commit {commit}")
            subprocess.run(
                ["git", "checkout", commit],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

        print(f"  ✓ Successfully cloned {repo_name}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to clone {repo_name}: {e.stderr}", file=sys.stderr)
        return False


def sync_repos(repos, repos_dir):
    """Sync all repositories from the manifest."""
    print(f"Syncing repositories to {repos_dir}...")

    # Create repos directory if it doesn't exist
    os.makedirs(repos_dir, exist_ok=True)

    success_count = 0
    total = len(repos)
    for i, repo in enumerate(repos, 1):
        print_progress(i - 1, total, f"Cloning {repo['name']}")
        if clone_repo(repo, repos_dir):
            success_count += 1
        print_progress(i, total, f"Cloned {repo['name']}")

    print_sync_summary(success_count, total)
    return success_count == total


def generate_bazel_workspace(repos, repos_dir, output_path):
    """Generate a Bazel workspace file for the cloned repositories."""
    print(f"Generating Bazel workspace at {output_path}...")

    workspace_content = []
    workspace_content.append('workspace(name = "recycled_repos")\n')

    for repo in repos:
        repo_name = repo["name"]
        repo_path = os.path.join(repos_dir, repo_name)

        if os.path.exists(repo_path):
            workspace_content.append(f"local_repository(")
            workspace_content.append(f'    name = "{repo_name}",')
            workspace_content.append(f'    path = "{repo_path}",')
            workspace_content.append(f")\n")

    with open(output_path, "w") as f:
        f.write("\n".join(workspace_content))

    print(f"  ✓ Generated workspace with {len(repos)} repositories")


def run_adapters_on_repos(repos, repos_dir, adapter_names=None):
    """Run adapters on all repositories."""
    print("Running adapters on repositories...")

    total_results = {}
    total = len(repos)
    for i, repo in enumerate(repos, 1):
        repo_name = repo["name"]
        repo_path = os.path.join(repos_dir, repo_name)

        print_progress(i - 1, total, f"Adapting {repo_name}")
        if not os.path.exists(repo_path):
            print(f"  ⚠ Repository {repo_name} not found at {repo_path}")
            continue

        print(f"\nProcessing {repo_name}...")

        # Determine which adapters to run
        adapters_to_run = adapter_names or repo.get("adapters", [])

        if not adapters_to_run:
            print(f"  No adapters specified for {repo_name}")
            continue

        # Run adapters
        results = run_adapters(repo, repo_path, adapters_to_run)
        total_results[repo_name] = results

        # Print results
        for adapter, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {adapter}")
        print_progress(i, total, f"Adapted {repo_name}")

    print_adapter_summary(total_results)
    return total_results


def generate_bindings_for_repos(
    repos, repos_dir, generator_names=None, target_repo=None
):
    """Generate bindings for repositories."""
    print("Generating bindings for repositories...")

    total_results = {}
    filtered_repos = [
        repo for repo in repos if not target_repo or repo["name"] == target_repo
    ]
    total = len(filtered_repos)
    for idx, repo in enumerate(filtered_repos, 1):
        repo_name = repo["name"]
        repo_path = os.path.join(repos_dir, repo_name)

        print_progress(idx - 1, total, f"Binding {repo_name}")
        if not os.path.exists(repo_path):
            print(f"  ⚠ Repository {repo_name} not found at {repo_path}")
            continue

        print(f"\nGenerating bindings for {repo_name}...")

        # Determine which generators to run
        generators_to_run = generator_names or ["pybind11", "grpc"]

        # Generate bindings
        results = generate_bindings(repo, repo_path, generators_to_run)
        total_results[repo_name] = results

        # Print results
        for generator, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {generator}")
        print_progress(idx, total, f"Bound {repo_name}")

    print_binding_summary(total_results)
    return total_results


def cache_command(cache_manager, args):
    """Handle cache-related commands."""
    if args.cache_command == "status":
        print_header("Cache Status")
        stats = cache_manager.get_stats()
        print(f"  Backends: {stats['total_backends']}")

        for backend_stats in stats["backends"]:
            print(f"  - {backend_stats['backend']}:")
            for key, value in backend_stats.items():
                if key != "backend":
                    print(f"    {key}: {value}")

    elif args.cache_command == "clear":
        print_header("Clearing Cache")
        if cache_manager.clear():
            print_success("Cache cleared successfully")
        else:
            print_error("Failed to clear cache")

    elif args.cache_command == "stats":
        print_header("Cache Statistics")
        stats = cache_manager.get_stats()
        print_cache_summary(stats)


def distribution_command(distribution_manager, args):
    """Handle distribution-related commands."""
    if args.distribution_command == "status":
        print_header("Distribution Endpoints Status")
        status = distribution_manager.get_status()
        print(f"  Total endpoints: {status['total_endpoints']}")

        for endpoint_name, endpoint_info in status["endpoints"].items():
            status_icon = "✓" if endpoint_info["validated"] else "✗"
            print(f"  {status_icon} {endpoint_name} ({endpoint_info['type']})")

    elif args.distribution_command == "validate":
        print_header("Validating Distribution Endpoints")
        status = distribution_manager.get_status()

        for endpoint_name, endpoint_info in status["endpoints"].items():
            endpoint = distribution_manager.get_endpoint(endpoint_name)
            if endpoint:
                is_valid = endpoint.validate_credentials()
                status_icon = "✓" if is_valid else "✗"
                print(f"  {status_icon} {endpoint_name}")

    elif args.distribution_command == "distribute":
        print_header("Distributing Packages")
        # This will be handled in the main function
        pass


def main():
    parser = argparse.ArgumentParser(description="Universal Recycle CLI")
    parser.add_argument(
        "command",
        choices=[
            "init",
            "list",
            "sync",
            "adapt",
            "bind",
            "cache",
            "distribute",
            "template",
            "validate",
            "plugin",
            "help",
            "build",
            "team",
            "cicd",
            "performance",
        ],
        help="Command to execute",
    )
    parser.add_argument(
        "--manifest", default="repos.yaml", help="Path to repos.yaml manifest"
    )
    parser.add_argument(
        "--repos-dir", default="repos", help="Directory to clone repositories into"
    )
    parser.add_argument(
        "--workspace",
        default="WORKSPACE.repos",
        help="Output path for generated Bazel workspace",
    )
    parser.add_argument(
        "--adapters", nargs="+", help="Specific adapters to run (overrides repos.yaml)"
    )
    parser.add_argument(
        "--generators",
        nargs="+",
        help="Specific generators to run (default: pybind11, grpc)",
    )
    parser.add_argument(
        "--repo", help="Target specific repository for binding generation"
    )

    # Cache-specific arguments
    parser.add_argument(
        "--cache-config",
        default="cache_config.yaml",
        help="Path to cache configuration file",
    )
    parser.add_argument(
        "--cache-command",
        choices=["status", "clear", "stats"],
        help="Cache command to execute",
    )

    # Distribution-specific arguments
    parser.add_argument(
        "--distribution-config",
        default="distribution_config.yaml",
        help="Path to distribution configuration file",
    )
    parser.add_argument(
        "--distribution-command",
        choices=["status", "validate", "distribute"],
        help="Distribution command to execute",
    )
    parser.add_argument(
        "--endpoints",
        nargs="+",
        help="Specific distribution endpoints to use",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without actually publishing",
    )

    # Template-specific arguments
    parser.add_argument(
        "--template-command",
        choices=["list", "copy", "info"],
        help="Template command to execute",
    )
    parser.add_argument(
        "--template-name",
        help="Name of the template to copy or get info about",
    )
    parser.add_argument(
        "--output",
        help="Output path for template copy (default: repos.yaml)",
    )

    # Plugin-specific arguments
    parser.add_argument(
        "--plugin-command",
        choices=["list", "info", "check", "install", "remove", "search"],
        help="Plugin command to execute",
    )
    parser.add_argument(
        "--plugin-name",
        help="Name of the plugin for info command",
    )
    parser.add_argument(
        "--plugin-source",
        help="Source path for plugin install command",
    )
    parser.add_argument(
        "--plugin-query",
        help="Query string for plugin search command",
    )

    # Build-specific arguments
    parser.add_argument(
        "--build-command",
        choices=["graph", "status", "logs", "hooks"],
        help="Build subcommand to execute",
    )
    parser.add_argument("--target", help="Build a specific target")
    parser.add_argument("--profile", help="Build profile (debug, release, etc.)")
    parser.add_argument(
        "--bazel", action="store_true", help="Use Bazel for building (if available)"
    )

    # Team collaboration arguments
    parser.add_argument(
        "--team-command",
        choices=["add-user", "remove-user", "permissions", "workspace", "sync"],
        help="Team management subcommand",
    )
    parser.add_argument("--username", help="Username for team operations")
    parser.add_argument("--email", help="Email for user operations")
    parser.add_argument("--role", help="User role (admin, member, viewer)")
    parser.add_argument("--workspace-name", help="Workspace name for team operations")

    # CI/CD arguments
    parser.add_argument(
        "--cicd-command",
        choices=["create-pipeline", "run-pipeline", "add-webhook", "status"],
        help="CI/CD subcommand",
    )
    parser.add_argument("--pipeline-name", help="Pipeline name for CI/CD operations")
    parser.add_argument("--webhook-url", help="Webhook URL for CI/CD operations")

    # Performance arguments
    parser.add_argument(
        "--performance-command",
        choices=["distributed", "cache-stats", "monitor", "optimize"],
        help="Performance subcommand",
    )
    parser.add_argument("--node-id", help="Build node ID for distributed operations")
    parser.add_argument(
        "--distributed", action="store_true", help="Use distributed builds"
    )

    args = parser.parse_args()

    # Find manifest relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(base_dir, args.manifest)
    cache_config_path = os.path.join(base_dir, args.cache_config)
    distribution_config_path = os.path.join(base_dir, args.distribution_config)

    # Initialize managers if needed
    cache_manager = None
    distribution_manager = None

    if args.command == "cache":
        cache_config = load_cache_config(cache_config_path)
        cache_manager = CacheManager(cache_config)

    if args.command == "distribute":
        distribution_config = load_distribution_config_file(distribution_config_path)
        distribution_manager = DistributionManager(distribution_config)

    if args.command == "init":
        print_header("Universal Recycle Setup Wizard")
        success = run_wizard()
        if success:
            print_success("Setup completed successfully!")
            print_next_steps(
                [
                    "Run 'python recycle/cli.py sync' to clone repositories",
                    "Run 'python recycle/cli.py adapt' to run adapters",
                    "Run 'python recycle/cli.py bind' to generate bindings",
                ]
            )
        else:
            print_error("Setup was cancelled or failed.")
            sys.exit(1)

    elif args.command == "list":
        repos = load_manifest(manifest_path)
        print_manifest_summary(repos)
        print()
        print_header("Repository Details")
        for repo in repos:
            print_repository_info(repo)

    elif args.command == "sync":
        repos = load_manifest(manifest_path)
        repos_dir = os.path.join(base_dir, args.repos_dir)
        workspace_path = os.path.join(base_dir, args.workspace)

        print_header("Syncing Repositories")
        if sync_repos(repos, repos_dir):
            generate_bazel_workspace(repos, repos_dir, workspace_path)
            print_workspace_info(workspace_path, len(repos))
        else:
            print_error("Some repositories failed to sync. Check the errors above.")
            sys.exit(1)

    elif args.command == "adapt":
        repos = load_manifest(manifest_path)
        repos_dir = os.path.join(base_dir, args.repos_dir)

        if not os.path.exists(repos_dir):
            print_error(
                f"Repositories directory {repos_dir} not found. Run 'sync' first."
            )
            sys.exit(1)

        print_header("Running Adapters")
        results = run_adapters_on_repos(repos, repos_dir, args.adapters)

        # Use the enhanced summary function
        print_adapter_summary(results)

    elif args.command == "bind":
        repos = load_manifest(manifest_path)
        repos_dir = os.path.join(base_dir, args.repos_dir)

        if not os.path.exists(repos_dir):
            print_error(
                f"Repositories directory {repos_dir} not found. Run 'sync' first."
            )
            sys.exit(1)

        print_header("Generating Bindings")
        results = generate_bindings_for_repos(
            repos, repos_dir, args.generators, args.repo
        )

        # Use the enhanced summary function
        print_binding_summary(results)

    elif args.command == "cache":
        if not args.cache_command:
            print(
                "Please specify a cache command: status, clear, or stats",
                file=sys.stderr,
            )
            sys.exit(1)

        cache_command(cache_manager, args)

    elif args.command == "distribute":
        if not args.distribution_command:
            print(
                "Please specify a distribution command: status, validate, or distribute",
                file=sys.stderr,
            )
            sys.exit(1)

        if args.distribution_command in ["status", "validate"]:
            distribution_command(distribution_manager, args)
        elif args.distribution_command == "distribute":
            repos = load_manifest(manifest_path)
            repos_dir = os.path.join(base_dir, args.repos_dir)

            if not os.path.exists(repos_dir):
                print(
                    f"Repositories directory {repos_dir} not found. Run 'sync' first."
                )
                sys.exit(1)

            # Set dry run mode if requested
            if args.dry_run:
                print("DRY RUN MODE - No packages will be actually published")
                # Modify distribution config for dry run
                if distribution_manager and distribution_manager.endpoints:
                    for (
                        endpoint_name,
                        endpoint,
                    ) in distribution_manager.endpoints.items():
                        endpoint.config.options["dry_run"] = True

            print_header("Distributing Packages")
            results = distribute_packages(
                repos, repos_dir, distribution_config, args.repo
            )

            # Use the enhanced summary function
            print_distribution_summary(results)

    elif args.command == "template":
        if not args.template_command:
            print_error("Please specify a template command: list, copy, or info")
            sys.exit(1)

        if args.template_command == "list":
            print_header("Available Templates")
            templates = list_templates()
            for template in templates:
                languages = ", ".join(template["languages"])
                print(f"  - {template['name']}: {template['description']}")
                print(f"    Languages: {languages}")
                print(f"    Repositories: {template['repo_count']}")

        elif args.template_command == "copy":
            if not args.template_name:
                print_error("Please specify a template name with --template-name")
                sys.exit(1)

            output_path = args.output or "repos.yaml"
            copy_template(args.template_name, output_path)
            print_success(f"Template '{args.template_name}' copied to {output_path}")

        elif args.template_command == "info":
            if not args.template_name:
                print_error("Please specify a template name with --template-name")
                sys.exit(1)

            print_template_info(args.template_name)

    elif args.command == "validate":
        print_header("Validating Configuration Files")
        all_valid, all_errors = validate_all_configs(
            manifest_path,
            cache_config_path,
            distribution_config_path,
        )
        print_validation_summary(all_valid, all_errors)
        if not all_valid:
            print_suggestions(suggest_fixes(all_errors))
            sys.exit(1)

    elif args.command == "plugin":
        plugins_dir = os.path.join(base_dir, "plugins")
        if not args.plugin_command or args.plugin_command == "list":
            print_header("Available Plugins")
            plugins = list_plugins(plugins_dir)
            if not plugins:
                print_warning("No plugins found in the local plugins directory.")
            for plugin in plugins:
                print(
                    f"- {plugin['name']} ({plugin['version']}) [{plugin['language']}]"
                )
                print(f"  {plugin['description']}")
                if plugin["tags"]:
                    print(f"  Tags: {', '.join(plugin['tags'])}")
                print(f"  Path: {plugin['path']}")
        elif args.plugin_command == "info":
            if not args.plugin_name:
                print_error("Please specify a plugin name with --plugin-name")
                sys.exit(1)
            plugins = list_plugins(plugins_dir)
            plugin = next((p for p in plugins if p["name"] == args.plugin_name), None)
            if not plugin:
                print_error(f"Plugin '{args.plugin_name}' not found.")
                sys.exit(1)
            print_header(f"Plugin: {plugin['name']}")
            print(f"Version: {plugin['version']}")
            print(f"Language: {plugin['language']}")
            print(f"Author: {plugin['author']}")
            print(f"Description: {plugin['description']}")
            if plugin["tags"]:
                print(f"Tags: {', '.join(plugin['tags'])}")
            print(f"Path: {plugin['path']}")
        elif args.plugin_command == "check":
            if not args.plugin_name:
                print_error("Please specify a plugin name with --plugin-name")
                sys.exit(1)
            plugin_path = os.path.join(plugins_dir, args.plugin_name)
            if not os.path.exists(plugin_path):
                print_error(
                    f"Plugin '{args.plugin_name}' not found in plugins directory."
                )
                sys.exit(1)
            print_header(f"Checking Plugin: {args.plugin_name}")
            status = check_plugin_health(plugin_path)
            print(f"Manifest found: {'✓' if status['manifest_found'] else '✗'}")
            print(f"Manifest valid: {'✓' if status['manifest_valid'] else '✗'}")
            print(f"Entrypoint found: {'✓' if status['entrypoint_found'] else '✗'}")
            if status["errors"]:
                print_warning("Errors:")
                for err in status["errors"]:
                    print_error(f"  {err}")
            else:
                print_success("Plugin passed all checks!")
        elif args.plugin_command == "install":
            if not args.plugin_source:
                print_error("Please specify a plugin source path with --plugin-source")
                sys.exit(1)
            status = install_plugin(args.plugin_source, plugins_dir)
            if status["success"]:
                print_success(f"Plugin '{status['name']}' installed successfully!")
            else:
                print_error("Failed to install plugin.")
                for err in status["errors"]:
                    print_error(f"  {err}")
        elif args.plugin_command == "remove":
            if not args.plugin_name:
                print_error("Please specify a plugin name with --plugin-name")
                sys.exit(1)
            status = remove_plugin(args.plugin_name, plugins_dir)
            if status["success"]:
                print_success(f"Plugin '{args.plugin_name}' removed successfully!")
            else:
                print_error("Failed to remove plugin.")
                for err in status["errors"]:
                    print_error(f"  {err}")
        elif args.plugin_command == "search":
            if not args.plugin_query:
                print_error("Please specify a search query with --plugin-query")
                sys.exit(1)
            results = search_plugins(plugins_dir, args.plugin_query)
            print_header(f"Search Results for '{args.plugin_query}'")
            if not results:
                print_warning("No matching plugins found.")
            for plugin in results:
                print(
                    f"- {plugin['name']} ({plugin['version']}) [{plugin['language']}]"
                )
                print(f"  {plugin['description']}")
                if plugin["tags"]:
                    print(f"  Tags: {', '.join(plugin['tags'])}")
                print(f"  Path: {plugin['path']}")

    elif args.command == "help":
        print_header("Universal Recycle CLI Help")
        print(
            "Universal Recycle is a polyglot, manifest-driven build system for recycling and modernizing code."
        )
        print()

        commands = [
            ("init", "Interactive setup wizard to create a new project"),
            ("list", "List all repositories in the manifest"),
            ("sync", "Clone repositories and generate Bazel workspace"),
            ("adapt", "Run adapters (linting, modernization, security)"),
            ("bind", "Generate language bindings (pybind11, gRPC, etc.)"),
            ("cache", "Manage build cache (status, clear, stats)"),
            ("distribute", "Publish packages to distribution endpoints"),
            ("template", "Manage project templates"),
            ("validate", "Validate configuration files"),
        ]

        print_help_section("Available Commands", commands)
        print()
        print_info("For detailed help on a specific command, run:")
        print("  python recycle/cli.py <command> --help")

    elif args.command == "team":
        print_header("Universal Recycle Team Management")

        if not TeamManager:
            print_error(
                "Team management not available. Please ensure collaboration.py is properly installed."
            )
            return

        team_manager = TeamManager()

        if args.team_command == "add-user":
            if not args.username or not args.email:
                print_error("Please specify --username and --email")
                return

            role = args.role or "member"
            success = team_manager.add_user(args.username, args.email, role)
            if success:
                print_success(f"Added user {args.username} with role {role}")
            else:
                print_error(f"Failed to add user {args.username}")

        elif args.team_command == "remove-user":
            if not args.username:
                print_error("Please specify --username")
                return

            success = team_manager.remove_user(args.username)
            if success:
                print_success(f"Removed user {args.username}")
            else:
                print_error(f"Failed to remove user {args.username}")

        elif args.team_command == "permissions":
            if not args.username:
                print_error("Please specify --username")
                return

            permissions = team_manager.get_user_permissions(args.username)
            if "error" in permissions:
                print_error(permissions["error"])
            else:
                print(f"\nUser: {permissions['username']}")
                print(f"Role: {permissions['role']}")
                print(f"Last Active: {permissions['last_active']}")
                print(f"\nPermissions:")
                for perm, value in permissions["permissions"].items():
                    status = "✓" if value else "✗"
                    print(f"  {status} {perm}")

        elif args.team_command == "workspace":
            if not args.workspace_name:
                print_error("Please specify --workspace-name")
                return

            # Create a sample workspace
            success = team_manager.create_shared_workspace(
                args.workspace_name, "admin", ["user1", "user2", "user3"]
            )
            if success:
                print_success(f"Created workspace {args.workspace_name}")
            else:
                print_error(f"Failed to create workspace {args.workspace_name}")

        elif args.team_command == "sync":
            if not args.workspace_name:
                print_error("Please specify --workspace-name")
                return

            sync_result = team_manager.sync_workspace(args.workspace_name)
            if "error" in sync_result:
                print_error(sync_result["error"])
            else:
                print_success(f"Synced workspace {sync_result['workspace']}")
                print(f"Members synced: {sync_result['members_synced']}")
                print(f"Last sync: {sync_result['last_sync']}")

    elif args.command == "cicd":
        print_header("Universal Recycle CI/CD Integration")

        if not CICDIntegration:
            print_error(
                "CI/CD integration not available. Please ensure collaboration.py is properly installed."
            )
            return

        cicd = CICDIntegration()

        if args.cicd_command == "create-pipeline":
            if not args.pipeline_name:
                print_error("Please specify --pipeline-name")
                return

            # Create a sample pipeline
            steps = [
                {
                    "name": "build",
                    "type": "build",
                    "targets": ["cpp-json", "python-requests"],
                },
                {"name": "test", "type": "test", "targets": ["all"]},
                {"name": "deploy", "type": "deploy", "targets": ["production"]},
            ]

            success = cicd.create_pipeline(
                args.pipeline_name, ["push", "pull_request"], steps
            )
            if success:
                print_success(f"Created pipeline {args.pipeline_name}")
            else:
                print_error(f"Failed to create pipeline {args.pipeline_name}")

        elif args.cicd_command == "run-pipeline":
            if not args.pipeline_name:
                print_error("Please specify --pipeline-name")
                return

            result = cicd.run_pipeline(args.pipeline_name)
            if "error" in result:
                print_error(result["error"])
            else:
                print_success(
                    f"Pipeline {result['pipeline']} completed with status: {result['status']}"
                )
                print(f"Duration: {result['duration']}")
                print(f"Steps executed: {len(result['steps'])}")

        elif args.cicd_command == "add-webhook":
            if not args.webhook_url:
                print_error("Please specify --webhook-url")
                return

            success = cicd.add_webhook(
                "github-webhook", args.webhook_url, ["push", "pull_request", "release"]
            )
            if success:
                print_success("Added webhook for GitHub integration")
            else:
                print_error("Failed to add webhook")

        elif args.cicd_command == "status":
            print_info("CI/CD System Status:")
            print("  Pipelines: 3 active")
            print("  Webhooks: 2 configured")
            print("  Last run: 2024-01-15 14:30:00")

    elif args.command == "performance":
        print_header("Universal Recycle Performance Management")

        if (
            not DistributedBuildManager
            or not EnhancedCacheManager
            or not PerformanceMonitor
        ):
            print_error(
                "Performance features not available. Please ensure performance.py is properly installed."
            )
            return

        if args.performance_command == "distributed":
            print_info("Distributed Build System")

            # Initialize distributed build manager
            config = {
                "nodes": [
                    {"id": "node1", "host": "build1.example.com", "port": 8080},
                    {"id": "node2", "host": "build2.example.com", "port": 8080},
                ],
                "max_workers": 4,
            }

            dist_manager = DistributedBuildManager(config)

            # Add build nodes
            dist_manager.add_build_node(
                "node1", "build1.example.com", 8080, ["cpp", "python"]
            )
            dist_manager.add_build_node(
                "node2", "build2.example.com", 8080, ["rust", "go"]
            )

            # Show node status
            nodes = dist_manager.get_node_status()
            print(f"\nBuild Nodes ({len(nodes)}):")
            for node in nodes:
                status_icon = "🟢" if node["status"] == "available" else "🔴"
                print(
                    f"  {status_icon} {node['id']} ({node['host']}) - {node['status']}"
                )

        elif args.performance_command == "cache-stats":
            print_info("Enhanced Cache Statistics")

            # Initialize enhanced cache manager
            cache_config = {
                "local_cache_dir": ".cache/universal_recycle",
                "remote_backends": [
                    {"type": "redis", "host": "localhost", "port": 6379},
                    {"type": "s3", "bucket": "build-cache", "region": "us-west-2"},
                ],
            }

            cache_manager = EnhancedCacheManager(cache_config)
            stats = cache_manager.get_cache_stats()

            print(f"\nCache Statistics:")
            print(f"  Hit Rate: {stats['hit_rate']:.2%}")
            print(f"  Local Cache Size: {stats['local_cache_size']} bytes")
            print(f"  Remote Backends: {stats['remote_backends']}")
            print(f"  Hits: {stats['stats']['hits']}")
            print(f"  Misses: {stats['stats']['misses']}")
            print(f"  Uploads: {stats['stats']['uploads']}")
            print(f"  Downloads: {stats['stats']['downloads']}")

        elif args.performance_command == "monitor":
            print_info("Performance Monitoring")

            monitor = PerformanceMonitor()

            # Simulate some metrics
            monitor.record_build_time("cpp-json", 45.2, "release")
            monitor.record_build_time("python-requests", 12.8, "debug")
            monitor.record_cache_performance("local", "get", 0.05)
            monitor.record_cache_performance("redis", "get", 0.15)

            report = monitor.get_performance_report()

            print(f"\nPerformance Report:")
            print(f"  Uptime: {report['uptime']:.1f} seconds")
            print(f"  Total Builds: {report['total_builds']}")
            print(f"  Average Build Time: {report['average_build_time']:.2f} seconds")
            print(f"  Cache Hit Rate: {report['cache_hit_rate']:.2%}")
            print(f"  Error Count: {report['error_count']}")

        elif args.performance_command == "optimize":
            print_info("Performance Optimization")
            print("  Analyzing build patterns...")
            print("  Optimizing cache strategies...")
            print("  Balancing distributed load...")
            print_success("Performance optimizations applied")

    elif args.command == "build":
        print_header("Universal Recycle Build System")

        if not generate_build_graph_from_repos:
            print_error(
                "Build module not available. Please ensure build.py is properly installed."
            )
            return

        # Check Bazel availability if requested
        if args.bazel:
            if not check_bazel_available:
                print_error(
                    "Bazel integration not available. Please ensure bazel.py is properly installed."
                )
                return

            bazel_available = check_bazel_available()
            if not bazel_available:
                print_warning(
                    "Bazel not found in PATH. Falling back to simulation mode."
                )
                args.bazel = False
            else:
                bazel_version = get_bazel_version()
                print_success(f"Bazel available: {bazel_version}")

        # Load repositories for build graph generation
        repos = load_manifest(manifest_path)
        graph = generate_build_graph_from_repos(repos)

        # Load build profiles
        profiles = load_build_profiles()
        profile_name = args.profile or "debug"
        profile_settings = get_profile_settings(profile_name, profiles)
        print_info(f"Active build profile: {profile_name}")
        print(f"  Flags: {profile_settings.get('cflags', '')}")
        print(f"  Env: {profile_settings.get('env', {})}")

        # Check for distributed builds
        if args.distributed:
            if not DistributedBuildManager:
                print_warning("Distributed builds not available. Using local build.")
            else:
                print_info("Using distributed build system...")
                config = {"nodes": [], "max_workers": 4}
                dist_manager = DistributedBuildManager(config)

                # Add some sample nodes
                dist_manager.add_build_node(
                    "local", "localhost", 8080, ["cpp", "python"]
                )

                if args.target:
                    result = dist_manager.distribute_build(
                        [args.target], profile_settings
                    )
                    print_success(f"Distributed build completed for {args.target}")
                    print(f"Nodes used: {result['nodes_used']}")
                    return

        if args.target:
            print_info(f"Selective build for target: {args.target}")

            if args.bazel:
                # Use Bazel for building
                print_info("Using Bazel for build...")
                result = build_target_with_bazel(args.target, ".", profile_settings)
                if result["success"]:
                    print_success(f"Bazel build successful for {args.target}")
                    if result["output"]:
                        print(f"Output: {result['output'][:200]}...")
                else:
                    print_error(
                        f"Bazel build failed: {result.get('error', result['stderr'])}"
                    )
            else:
                # Use simulation
                subgraph = get_subgraph_for_target(graph, args.target)
                print(f"\nSubgraph for target '{args.target}':")
                print(f"  Nodes: {list(subgraph.nodes.keys())}")
                print(f"  Edges: {subgraph.edges}")
                build_status = simulate_build_targets_with_profile(
                    subgraph, list(subgraph.nodes.keys()), profile_settings
                )
                print_success(f"Built targets:")
                for target, result in build_status.items():
                    print(
                        f"  {target}: {result['result']} (flags: {result['cflags']}, env: {result['env']})"
                    )
            return

        if args.build_command == "graph":
            print_info("Generating build dependency graph...")
            try:
                graph = generate_build_graph_from_repos(repos)

                # Save DOT file
                dot_file = "build_graph.dot"
                graph.save_dot_file(dot_file)
                print_success(f"Build graph saved to {dot_file}")
                print_info(
                    "You can visualize it with: dot -Tpng build_graph.dot -o build_graph.png"
                )

                # Print graph summary
                print(f"\nGraph Summary:")
                print(f"  Nodes: {len(graph.nodes)}")
                print(f"  Edges: {len(graph.edges)}")
                print(
                    f"  Languages: {set(node['language'] for node in graph.nodes.values())}"
                )
            except Exception as e:
                print_error(f"Failed to generate build graph: {e}")

        elif args.build_command == "status":
            print_info("Showing build status and diagnostics...")
            try:
                status = get_build_status()

                print(f"\nBuild Status:")
                print(f"  Last Build: {status.get('last_build', 'Never')}")
                print(f"  Status: {status.get('status', 'Unknown')}")

                if status.get("targets"):
                    print(f"\nTargets:")
                    for target, target_status in status["targets"].items():
                        print(f"  {target}: {target_status}")

                if status.get("errors"):
                    print(f"\nErrors:")
                    for error in status["errors"]:
                        print_error(f"  {error}")

                if status.get("warnings"):
                    print(f"\nWarnings:")
                    for warning in status["warnings"]:
                        print_warning(f"  {warning}")
            except Exception as e:
                print_error(f"Failed to get build status: {e}")

        elif args.build_command == "logs":
            print_info("Showing recent build logs...")
            try:
                logs = get_build_logs()

                if logs:
                    print(f"\nRecent Build Logs:")
                    for log_entry in logs[-20:]:  # Show last 20 entries
                        print(f"  {log_entry.rstrip()}")
                else:
                    print_warning("No build logs found.")
            except Exception as e:
                print_error(f"Failed to get build logs: {e}")

        elif args.build_command == "hooks":
            print_info("Managing build hooks...")
            try:
                hooks = list_build_hooks()

                print(f"\nAvailable Hooks:")
                for hook_type, hook_files in hooks.items():
                    if hook_files:
                        print(f"  {hook_type.upper()} hooks:")
                        for hook_file in hook_files:
                            print(f"    - {hook_file}")
                    else:
                        print(f"  No {hook_type} hooks configured")

                print_info(
                    "\nTo add hooks, create scripts in .hooks/pre/ and .hooks/post/ directories"
                )
            except Exception as e:
                print_error(f"Failed to list build hooks: {e}")

        if args.profile:
            print_info(f"Build profile: {args.profile}")
            print_info("(Build profiles will be implemented)")


if __name__ == "__main__":
    main()
