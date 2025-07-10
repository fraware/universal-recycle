"""
Distribution endpoints for Universal Recycle.

This module handles publishing generated packages to various package registries
including PyPI, npm, vcpkg, crates.io, and Go modules.
"""

import os
import json
import yaml
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import tempfile
import shutil

logger = logging.getLogger(__name__)


@dataclass
class DistributionConfig:
    """Configuration for distribution endpoints."""

    endpoint_type: str
    credentials: Dict[str, Any]
    options: Dict[str, Any]


class DistributionEndpoint:
    """Base class for distribution endpoints."""

    def __init__(self, config: DistributionConfig):
        self.config = config
        self.name = self.__class__.__name__

    def log(self, message: str, level: str = "info"):
        """Log a message with the endpoint name prefix."""
        log_func = getattr(logger, level)
        log_func(f"[{self.name}] {message}")

    def can_distribute(self, package_type: str) -> bool:
        """Check if this endpoint can distribute the given package type."""
        return False

    def prepare_package(self, source_path: str, package_config: Dict[str, Any]) -> str:
        """Prepare a package for distribution. Returns the path to the prepared package."""
        raise NotImplementedError

    def publish(self, package_path: str, package_config: Dict[str, Any]) -> bool:
        """Publish a package to the distribution endpoint."""
        raise NotImplementedError

    def validate_credentials(self) -> bool:
        """Validate that credentials are properly configured."""
        raise NotImplementedError


class PyPIDistributionEndpoint(DistributionEndpoint):
    """PyPI distribution endpoint for Python packages."""

    def can_distribute(self, package_type: str) -> bool:
        return package_type.lower() in ["python", "pybind11", "pyo3"]

    def validate_credentials(self) -> bool:
        """Validate PyPI credentials."""
        try:
            # Check if twine is available
            result = subprocess.run(
                ["twine", "--version"], capture_output=True, text=True, check=True
            )
            self.log("Twine is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("Twine not found. Install with: pip install twine", "warning")
            return False

    def prepare_package(self, source_path: str, package_config: Dict[str, Any]) -> str:
        """Prepare a Python package for PyPI distribution."""
        self.log(f"Preparing Python package from {source_path}")

        # Check if setup.py exists
        setup_py_path = os.path.join(source_path, "setup.py")
        if not os.path.exists(setup_py_path):
            self.log(f"setup.py not found at {setup_py_path}", "error")
            return ""

        # Build the package
        try:
            subprocess.run(
                ["python", "setup.py", "sdist", "bdist_wheel"],
                cwd=source_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Find the built packages
            dist_dir = os.path.join(source_path, "dist")
            if os.path.exists(dist_dir):
                packages = [
                    f for f in os.listdir(dist_dir) if f.endswith((".tar.gz", ".whl"))
                ]
                if packages:
                    self.log(f"Built packages: {packages}")
                    return dist_dir

            self.log("No packages found in dist/ directory", "error")
            return ""

        except subprocess.CalledProcessError as e:
            self.log(f"Failed to build package: {e.stderr}", "error")
            return ""

    def publish(self, package_path: str, package_config: Dict[str, Any]) -> bool:
        """Publish a Python package to PyPI."""
        self.log(f"Publishing to PyPI from {package_path}")

        try:
            # Use test PyPI if specified
            repository = self.config.options.get("repository", "pypi")
            if repository == "testpypi":
                cmd = [
                    "twine",
                    "upload",
                    "--repository",
                    "testpypi",
                    f"{package_path}/*",
                ]
            else:
                cmd = ["twine", "upload", f"{package_path}/*"]

            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.log("Successfully published to PyPI")
            return True

        except subprocess.CalledProcessError as e:
            self.log(f"Failed to publish to PyPI: {e.stderr}", "error")
            return False


class NpmDistributionEndpoint(DistributionEndpoint):
    """npm distribution endpoint for WebAssembly packages."""

    def can_distribute(self, package_type: str) -> bool:
        return package_type.lower() in ["wasm", "webassembly", "javascript"]

    def validate_credentials(self) -> bool:
        """Validate npm credentials."""
        try:
            # Check if npm is available
            result = subprocess.run(
                ["npm", "--version"], capture_output=True, text=True, check=True
            )
            self.log("npm is available")

            # Check if logged in
            result = subprocess.run(["npm", "whoami"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"Logged in as: {result.stdout.strip()}")
                return True
            else:
                self.log("Not logged in to npm. Run: npm login", "warning")
                return False

        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("npm not found", "error")
            return False

    def prepare_package(self, source_path: str, package_config: Dict[str, Any]) -> str:
        """Prepare a WebAssembly package for npm distribution."""
        self.log(f"Preparing npm package from {source_path}")

        # Check if package.json exists
        package_json_path = os.path.join(source_path, "package.json")
        if not os.path.exists(package_json_path):
            self.log(f"package.json not found at {package_json_path}", "error")
            return ""

        # Build the package if needed
        try:
            # Check if build script exists
            with open(package_json_path, "r") as f:
                pkg_data = json.load(f)

            if "scripts" in pkg_data and "build" in pkg_data["scripts"]:
                self.log("Building npm package...")
                subprocess.run(
                    ["npm", "run", "build"],
                    cwd=source_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            return source_path

        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            self.log(f"Failed to prepare npm package: {e}", "error")
            return ""

    def publish(self, package_path: str, package_config: Dict[str, Any]) -> bool:
        """Publish a WebAssembly package to npm."""
        self.log(f"Publishing to npm from {package_path}")

        try:
            # Check if package is scoped
            with open(os.path.join(package_path, "package.json"), "r") as f:
                pkg_data = json.load(f)

            package_name = pkg_data.get("name", "")
            is_scoped = package_name.startswith("@")

            # Publish to npm
            cmd = ["npm", "publish"]
            if is_scoped:
                cmd.append("--access", "public")

            subprocess.run(
                cmd, cwd=package_path, check=True, capture_output=True, text=True
            )
            self.log("Successfully published to npm")
            return True

        except subprocess.CalledProcessError as e:
            self.log(f"Failed to publish to npm: {e.stderr}", "error")
            return False


class VcpkgDistributionEndpoint(DistributionEndpoint):
    """vcpkg distribution endpoint for C++ packages."""

    def can_distribute(self, package_type: str) -> bool:
        return package_type.lower() in ["cpp", "c++", "cxx"]

    def validate_credentials(self) -> bool:
        """Validate vcpkg credentials."""
        try:
            # Check if git is available
            result = subprocess.run(
                ["git", "--version"], capture_output=True, text=True, check=True
            )
            self.log("Git is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("Git not found", "error")
            return False

    def prepare_package(self, source_path: str, package_config: Dict[str, Any]) -> str:
        """Prepare a C++ package for vcpkg distribution."""
        self.log(f"Preparing vcpkg package from {source_path}")

        # Check if vcpkg.json exists
        vcpkg_json_path = os.path.join(source_path, "vcpkg.json")
        if not os.path.exists(vcpkg_json_path):
            self.log(f"vcpkg.json not found at {vcpkg_json_path}", "error")
            return ""

        # Create a temporary directory for the vcpkg port
        temp_dir = tempfile.mkdtemp(prefix="vcpkg_port_")

        try:
            # Read vcpkg.json
            with open(vcpkg_json_path, "r") as f:
                vcpkg_data = json.load(f)

            package_name = vcpkg_data.get("name", "unknown")

            # Create port directory structure
            port_dir = os.path.join(temp_dir, package_name)
            os.makedirs(port_dir, exist_ok=True)

            # Copy vcpkg.json to port
            shutil.copy2(vcpkg_json_path, os.path.join(port_dir, "vcpkg.json"))

            # Create portfile.cmake if it doesn't exist
            portfile_path = os.path.join(port_dir, "portfile.cmake")
            if not os.path.exists(portfile_path):
                self._create_portfile_cmake(portfile_path, package_name, source_path)

            self.log(f"Prepared vcpkg port at {port_dir}")
            return port_dir

        except Exception as e:
            self.log(f"Failed to prepare vcpkg package: {e}", "error")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return ""

    def _create_portfile_cmake(
        self, portfile_path: str, package_name: str, source_path: str
    ):
        """Create a basic portfile.cmake for the package."""
        portfile_content = f"""# Auto-generated portfile.cmake for {package_name}
vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO {package_name}
    REF v1.0.0
    SHA512 0000000000000000000000000000000000000000000000000000000000000000
    HEAD_REF main
)

vcpkg_configure_cmake(
    SOURCE_PATH ${{SOURCE_PATH}}
    PREFER_NINJA
)

vcpkg_install_cmake()
vcpkg_fixup_cmake_targets()

file(REMOVE_RECURSE ${{CURRENT_PACKAGES_DIR}}/debug/include)

file(INSTALL ${{SOURCE_PATH}}/LICENSE DESTINATION ${{CURRENT_PACKAGES_DIR}}/share/${{PORT}} RENAME copyright)
"""

        with open(portfile_path, "w") as f:
            f.write(portfile_content)

    def publish(self, package_path: str, package_config: Dict[str, Any]) -> bool:
        """Publish a C++ package to vcpkg registry."""
        self.log(f"Publishing to vcpkg registry from {package_path}")

        try:
            # This would typically involve creating a PR to the vcpkg registry
            # For now, we'll just log the package details
            package_name = os.path.basename(package_path)

            self.log(f"Package {package_name} prepared for vcpkg registry")
            self.log("To publish, create a PR to the vcpkg registry with:")
            self.log(f"  - Port directory: {package_path}")
            self.log(f"  - Package name: {package_name}")

            return True

        except Exception as e:
            self.log(f"Failed to prepare for vcpkg registry: {e}", "error")
            return False


class CratesIoDistributionEndpoint(DistributionEndpoint):
    """crates.io distribution endpoint for Rust packages."""

    def can_distribute(self, package_type: str) -> bool:
        return package_type.lower() in ["rust", "rs"]

    def validate_credentials(self) -> bool:
        """Validate crates.io credentials."""
        try:
            # Check if cargo is available
            result = subprocess.run(
                ["cargo", "--version"], capture_output=True, text=True, check=True
            )
            self.log("Cargo is available")

            # Check if logged in
            result = subprocess.run(["cargo", "whoami"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"Logged in as: {result.stdout.strip()}")
                return True
            else:
                self.log("Not logged in to crates.io. Run: cargo login", "warning")
                return False

        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("Cargo not found", "error")
            return False

    def prepare_package(self, source_path: str, package_config: Dict[str, Any]) -> str:
        """Prepare a Rust package for crates.io distribution."""
        self.log(f"Preparing Rust package from {source_path}")

        # Check if Cargo.toml exists
        cargo_toml_path = os.path.join(source_path, "Cargo.toml")
        if not os.path.exists(cargo_toml_path):
            self.log(f"Cargo.toml not found at {cargo_toml_path}", "error")
            return ""

        # Build the package
        try:
            subprocess.run(
                ["cargo", "build", "--release"],
                cwd=source_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Check if package is ready for publishing
            subprocess.run(
                ["cargo", "package", "--allow-dirty"],
                cwd=source_path,
                check=True,
                capture_output=True,
                text=True,
            )

            self.log("Rust package prepared successfully")
            return source_path

        except subprocess.CalledProcessError as e:
            self.log(f"Failed to prepare Rust package: {e.stderr}", "error")
            return ""

    def publish(self, package_path: str, package_config: Dict[str, Any]) -> bool:
        """Publish a Rust package to crates.io."""
        self.log(f"Publishing to crates.io from {package_path}")

        try:
            # Publish to crates.io
            subprocess.run(
                ["cargo", "publish"],
                cwd=package_path,
                check=True,
                capture_output=True,
                text=True,
            )

            self.log("Successfully published to crates.io")
            return True

        except subprocess.CalledProcessError as e:
            self.log(f"Failed to publish to crates.io: {e.stderr}", "error")
            return False


class GoModulesDistributionEndpoint(DistributionEndpoint):
    """Go modules distribution endpoint for Go packages."""

    def can_distribute(self, package_type: str) -> bool:
        return package_type.lower() in ["go", "golang"]

    def validate_credentials(self) -> bool:
        """Validate Go modules credentials."""
        try:
            # Check if go is available
            result = subprocess.run(
                ["go", "version"], capture_output=True, text=True, check=True
            )
            self.log("Go is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("Go not found", "error")
            return False

    def prepare_package(self, source_path: str, package_config: Dict[str, Any]) -> str:
        """Prepare a Go package for module distribution."""
        self.log(f"Preparing Go package from {source_path}")

        # Check if go.mod exists
        go_mod_path = os.path.join(source_path, "go.mod")
        if not os.path.exists(go_mod_path):
            self.log(f"go.mod not found at {go_mod_path}", "error")
            return ""

        # Build the package
        try:
            subprocess.run(
                ["go", "build", "./..."],
                cwd=source_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Run tests
            subprocess.run(
                ["go", "test", "./..."],
                cwd=source_path,
                check=True,
                capture_output=True,
                text=True,
            )

            self.log("Go package prepared successfully")
            return source_path

        except subprocess.CalledProcessError as e:
            self.log(f"Failed to prepare Go package: {e.stderr}", "error")
            return ""

    def publish(self, package_path: str, package_config: Dict[str, Any]) -> bool:
        """Publish a Go package to module registry."""
        self.log(f"Publishing Go module from {package_path}")

        try:
            # For Go modules, publishing typically involves creating a git tag
            # and pushing to the repository
            module_name = self._get_module_name(package_path)

            self.log(f"Go module {module_name} prepared for distribution")
            self.log("To publish, create a git tag and push to the repository:")
            self.log(f"  git tag v1.0.0")
            self.log(f"  git push origin v1.0.0")

            return True

        except Exception as e:
            self.log(f"Failed to prepare Go module: {e}", "error")
            return False

    def _get_module_name(self, package_path: str) -> str:
        """Get the module name from go.mod."""
        try:
            with open(os.path.join(package_path, "go.mod"), "r") as f:
                for line in f:
                    if line.startswith("module "):
                        return line.split()[1].strip()
        except Exception:
            pass
        return "unknown"


# Distribution endpoint registry
DISTRIBUTION_REGISTRY = {
    "pypi": PyPIDistributionEndpoint,
    "npm": NpmDistributionEndpoint,
    "vcpkg": VcpkgDistributionEndpoint,
    "crates.io": CratesIoDistributionEndpoint,
    "go_modules": GoModulesDistributionEndpoint,
}


class DistributionManager:
    """Manages multiple distribution endpoints."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.endpoints: Dict[str, DistributionEndpoint] = {}
        self._setup_endpoints()

    def _setup_endpoints(self):
        """Set up distribution endpoints based on configuration."""
        endpoints_config = self.config.get("endpoints", {})

        for endpoint_name, endpoint_config in endpoints_config.items():
            endpoint_type = endpoint_config.get("type")

            if endpoint_type not in DISTRIBUTION_REGISTRY:
                logger.warning(f"Unknown distribution endpoint type: {endpoint_type}")
                continue

            try:
                config = DistributionConfig(
                    endpoint_type=endpoint_type,
                    credentials=endpoint_config.get("credentials", {}),
                    options=endpoint_config.get("options", {}),
                )

                endpoint_class = DISTRIBUTION_REGISTRY[endpoint_type]
                endpoint = endpoint_class(config)

                if endpoint.validate_credentials():
                    self.endpoints[endpoint_name] = endpoint
                    logger.info(f"Initialized {endpoint_type} distribution endpoint")
                else:
                    logger.warning(
                        f"Failed to validate credentials for {endpoint_type}"
                    )

            except Exception as e:
                logger.error(f"Failed to initialize {endpoint_type} endpoint: {e}")

    def get_endpoint(self, endpoint_name: str) -> Optional[DistributionEndpoint]:
        """Get a distribution endpoint by name."""
        return self.endpoints.get(endpoint_name)

    def get_endpoints_for_package_type(
        self, package_type: str
    ) -> List[DistributionEndpoint]:
        """Get all endpoints that can distribute the given package type."""
        return [
            endpoint
            for endpoint in self.endpoints.values()
            if endpoint.can_distribute(package_type)
        ]

    def distribute_package(
        self,
        source_path: str,
        package_type: str,
        package_config: Dict[str, Any],
        target_endpoints: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """Distribute a package to all applicable endpoints."""
        results = {}

        # Get applicable endpoints
        if target_endpoints:
            endpoints = [
                self.endpoints[name]
                for name in target_endpoints
                if name in self.endpoints
            ]
        else:
            endpoints = self.get_endpoints_for_package_type(package_type)

        for endpoint in endpoints:
            endpoint_name = endpoint.name
            self.log(f"Distributing to {endpoint_name}...")

            try:
                # Prepare package
                prepared_path = endpoint.prepare_package(source_path, package_config)
                if not prepared_path:
                    results[endpoint_name] = False
                    continue

                # Publish package
                success = endpoint.publish(prepared_path, package_config)
                results[endpoint_name] = success

                if success:
                    self.log(f"Successfully distributed to {endpoint_name}")
                else:
                    self.log(f"Failed to distribute to {endpoint_name}")

            except Exception as e:
                self.log(f"Error distributing to {endpoint_name}: {e}", "error")
                results[endpoint_name] = False

        return results

    def log(self, message: str, level: str = "info"):
        """Log a message with the manager name prefix."""
        log_func = getattr(logger, level)
        log_func(f"[DistributionManager] {message}")

    def get_status(self) -> Dict[str, Any]:
        """Get status of all distribution endpoints."""
        status = {"endpoints": {}, "total_endpoints": len(self.endpoints)}

        for name, endpoint in self.endpoints.items():
            status["endpoints"][name] = {
                "type": endpoint.config.endpoint_type,
                "validated": endpoint.validate_credentials(),
            }

        return status


def load_distribution_config(config_path: str) -> Dict[str, Any]:
    """Load distribution configuration from file."""
    if not os.path.exists(config_path):
        logger.warning(
            f"Distribution config not found at {config_path}, using defaults"
        )
        return {"endpoints": {}}

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def distribute_packages(
    repos: List[Dict[str, Any]],
    repos_dir: str,
    distribution_config: Dict[str, Any],
    target_repos: Optional[List[str]] = None,
) -> Dict[str, Dict[str, bool]]:
    """Distribute packages for all repositories."""
    manager = DistributionManager(distribution_config)
    all_results = {}

    for repo in repos:
        repo_name = repo["name"]

        # Skip if not in target repos
        if target_repos and repo_name not in target_repos:
            continue

        repo_path = os.path.join(repos_dir, repo_name)
        if not os.path.exists(repo_path):
            logger.warning(f"Repository {repo_name} not found at {repo_path}")
            continue

        logger.info(f"Distributing packages for {repo_name}")

        # Determine package types based on generated bindings
        package_types = []
        if os.path.exists(os.path.join(repo_path, "python_bindings")):
            if repo.get("language") == "rust":
                package_types.append("rust")  # PyO3
            else:
                package_types.append("python")  # pybind11

        if os.path.exists(os.path.join(repo_path, "wasm_bindings")):
            package_types.append("wasm")

        if not package_types:
            logger.info(f"No distributable packages found for {repo_name}")
            continue

        # Distribute each package type
        repo_results = {}
        for package_type in package_types:
            package_config = {
                "name": repo_name,
                "version": "0.1.0",
                "language": repo.get("language", "unknown"),
                "source_repo": repo.get("git", ""),
                "commit": repo.get("commit", ""),
            }

            # Determine source path based on package type
            if package_type == "python":
                source_path = os.path.join(repo_path, "python_bindings")
            elif package_type == "rust":
                source_path = os.path.join(repo_path, "python_bindings")
            elif package_type == "wasm":
                source_path = os.path.join(repo_path, "wasm_bindings")
            else:
                source_path = repo_path

            if os.path.exists(source_path):
                results = manager.distribute_package(
                    source_path, package_type, package_config
                )
                repo_results[package_type] = results

        all_results[repo_name] = repo_results

    return all_results
