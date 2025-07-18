"""
Binding generation for Universal Recycle.

This module handles generating Python bindings for C++ libraries using pybind11
and gRPC service definitions for cross-language communication.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import logging

logger = logging.getLogger(__name__)


class BindingGenerator:
    """Base class for generating language bindings."""

    def __init__(self, repo_path: str, config: Dict[str, Any]):
        self.repo_path = repo_path
        self.config = config
        self.name = self.__class__.__name__

    def log(self, message: str, level: str = "info"):
        """Log a message with the generator name prefix."""
        log_func = getattr(logger, level)
        log_func(f"[{self.name}] {message}")

    def can_generate(self, language: str) -> bool:
        """Check if this generator can handle the given language."""
        return False

    def generate(self) -> bool:
        """Generate bindings. Returns True if successful."""
        return False


class Pybind11Generator(BindingGenerator):
    """Generate pybind11 bindings for C++ libraries."""

    def can_generate(self, language: str) -> bool:
        return language.lower() in ["cpp", "c++", "cxx"]

    def _find_header_files(self) -> List[str]:
        """Find C++ header files in the repository."""
        headers = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common directories that shouldn't contain public headers
            dirs[:] = [
                d
                for d in dirs
                if d
                not in [".git", "build", "cmake-build", "test", "tests", "examples"]
            ]

            for file in files:
                if file.endswith((".h", ".hpp", ".hxx")):
                    headers.append(os.path.join(root, file))
        return headers

    def _extract_class_names(self, header_path: str) -> List[str]:
        """Extract class names from a C++ header file."""
        try:
            with open(header_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple regex to find class definitions
            class_pattern = r"class\s+(\w+)(?:\s*[:{])"
            classes = re.findall(class_pattern, content)

            # Filter out common non-user classes
            filtered_classes = []
            for cls in classes:
                if not cls.startswith("_") and cls not in [
                    "private",
                    "public",
                    "protected",
                ]:
                    filtered_classes.append(cls)

            return filtered_classes
        except Exception as e:
            self.log(f"Error parsing {header_path}: {e}", "warning")
            return []

    def _generate_pybind11_module(self, classes: List[str], module_name: str) -> str:
        """Generate pybind11 module code."""
        module_code = f'''# Auto-generated pybind11 bindings for {module_name}
import pybind11
from pybind11 import pybind11 as py

def register_module(m):
    """Register the {module_name} module with pybind11."""
'''

        for cls in classes:
            module_code += f"""
    # Bind class {cls}
    py::class_<{cls}>(m, "{cls}")
        .def(py::init<>())
        .def("__repr__", [](const {cls}& self) {{
            return "<{cls} object>";
        }});
"""

        return module_code

    def generate(self) -> bool:
        """Generate pybind11 bindings for the C++ library."""
        self.log(f"Generating pybind11 bindings for {self.repo_path}")

        # Find header files
        headers = self._find_header_files()
        if not headers:
            self.log("No header files found", "warning")
            return True

        self.log(f"Found {len(headers)} header files")

        # Extract class names from headers
        all_classes = []
        for header in headers[:10]:  # Limit to first 10 headers for demo
            classes = self._extract_class_names(header)
            all_classes.extend(classes)

        if not all_classes:
            self.log("No classes found in headers", "warning")
            return True

        # Remove duplicates
        unique_classes = list(set(all_classes))
        self.log(f"Found {len(unique_classes)} unique classes: {unique_classes[:5]}...")

        # Generate pybind11 module
        module_name = os.path.basename(self.repo_path)
        module_code = self._generate_pybind11_module(unique_classes, module_name)

        # Write the generated bindings
        bindings_dir = os.path.join(self.repo_path, "python_bindings")
        os.makedirs(bindings_dir, exist_ok=True)

        bindings_file = os.path.join(bindings_dir, f"{module_name}_bindings.cpp")
        with open(bindings_file, "w") as f:
            f.write(module_code)

        # Generate setup.py for the Python package
        setup_py = self._generate_setup_py(module_name, bindings_file)
        setup_file = os.path.join(bindings_dir, "setup.py")
        with open(setup_file, "w") as f:
            f.write(setup_py)

        self.log(f"Generated pybind11 bindings in {bindings_dir}")
        return True

    def _generate_setup_py(self, module_name: str, bindings_file: str) -> str:
        """Generate setup.py for the Python package."""
        return f"""from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "{module_name}",
        [r"{bindings_file}"],
        include_dirs=["../include", "../single_include"],
        language="c++",
    ),
]

setup(
    name="{module_name}-py",
    version="0.1.0",
    author="Universal Recycle",
    description="Python bindings for {module_name}",
    ext_modules=ext_modules,
    cmdclass={{'build_ext': build_ext}},
    zip_safe=False,
    python_requires=">=3.9",
)
"""


class PyO3Generator(BindingGenerator):
    """Generate PyO3 bindings for Rust libraries."""

    def can_generate(self, language: str) -> bool:
        return language.lower() in ["rust", "rs"]

    def _find_rust_files(self) -> List[str]:
        """Find Rust source files in the repository."""
        rust_files = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common directories
            dirs[:] = [
                d for d in dirs if d not in [".git", "target", "tests", "examples"]
            ]

            for file in files:
                if file.endswith(".rs"):
                    rust_files.append(os.path.join(root, file))
        return rust_files

    def _extract_struct_names(self, rust_file: str) -> List[str]:
        """Extract struct names from a Rust file."""
        try:
            with open(rust_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find struct definitions
            struct_pattern = r"struct\s+(\w+)"
            structs = re.findall(struct_pattern, content)

            # Find function definitions
            fn_pattern = r"fn\s+(\w+)\s*\("
            functions = re.findall(fn_pattern, content)

            return structs + functions
        except Exception as e:
            self.log(f"Error parsing {rust_file}: {e}", "warning")
            return []

    def _generate_pyo3_lib(self, items: List[str], module_name: str) -> str:
        """Generate PyO3 library code."""
        lib_code = f"""use pyo3::prelude::*;

/// Python bindings for {module_name}
#[pymodule]
fn {module_name}(_py: Python, m: &PyModule) -> PyResult<()> {{
"""

        for item in items:
            lib_code += f"""
    // Bind {item}
    m.add_class::<{item}>()?;
"""

        lib_code += """
    Ok(())
}
"""
        return lib_code

    def _generate_cargo_toml(self, module_name: str) -> str:
        """Generate Cargo.toml for the PyO3 package."""
        return f"""[package]
name = "{module_name}-py"
version = "0.1.0"
edition = "2021"

[lib]
name = "{module_name}"
crate-type = ["cdylib"]

[dependencies]
pyo3 = {{ version = "0.19", features = ["extension-module"] }}

[build-dependencies]
pyo3 = {{ version = "0.19", features = ["extension-module"] }}
"""

    def generate(self) -> bool:
        """Generate PyO3 bindings for the Rust library."""
        self.log(f"Generating PyO3 bindings for {self.repo_path}")

        # Find Rust files
        rust_files = self._find_rust_files()
        if not rust_files:
            self.log("No Rust files found", "warning")
            return True

        self.log(f"Found {len(rust_files)} Rust files")

        # Extract struct and function names
        all_items = []
        for rust_file in rust_files[:5]:  # Limit to first 5 files for demo
            items = self._extract_struct_names(rust_file)
            all_items.extend(items)

        if not all_items:
            self.log("No structs or functions found", "warning")
            return True

        # Remove duplicates
        unique_items = list(set(all_items))
        self.log(f"Found {len(unique_items)} unique items: {unique_items[:5]}...")

        # Generate PyO3 bindings
        module_name = os.path.basename(self.repo_path).replace("-", "_")
        lib_code = self._generate_pyo3_lib(unique_items, module_name)

        # Write the generated bindings
        bindings_dir = os.path.join(self.repo_path, "python_bindings")
        os.makedirs(bindings_dir, exist_ok=True)

        lib_file = os.path.join(bindings_dir, "src", "lib.rs")
        os.makedirs(os.path.dirname(lib_file), exist_ok=True)
        with open(lib_file, "w") as f:
            f.write(lib_code)

        # Generate Cargo.toml
        cargo_toml = self._generate_cargo_toml(module_name)
        cargo_file = os.path.join(bindings_dir, "Cargo.toml")
        with open(cargo_file, "w") as f:
            f.write(cargo_toml)

        # Generate build script
        build_rs = self._generate_build_rs(module_name)
        build_file = os.path.join(bindings_dir, "build.rs")
        with open(build_file, "w") as f:
            f.write(build_rs)

        self.log(f"Generated PyO3 bindings in {bindings_dir}")
        return True

    def _generate_build_rs(self, module_name: str) -> str:
        """Generate build.rs for PyO3."""
        return f"""use pyo3_build_config;

fn main() {{
    pyo3_build_config::add_extension_module_link_args();
}}
"""


class CGoGenerator(BindingGenerator):
    """Generate cgo bindings for Go libraries."""

    def can_generate(self, language: str) -> bool:
        return language.lower() in ["go", "golang"]

    def _find_go_files(self) -> List[str]:
        """Find Go source files in the repository."""
        go_files = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in [".git", "vendor", "test", "tests"]]

            for file in files:
                if file.endswith(".go"):
                    go_files.append(os.path.join(root, file))
        return go_files

    def _extract_go_types(self, go_file: str) -> List[str]:
        """Extract type names from a Go file."""
        try:
            with open(go_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find type definitions
            type_pattern = r"type\s+(\w+)\s+"
            types = re.findall(type_pattern, content)

            # Find function definitions
            func_pattern = r"func\s+(\w+)\s*\("
            functions = re.findall(func_pattern, content)

            return types + functions
        except Exception as e:
            self.log(f"Error parsing {go_file}: {e}", "warning")
            return []

    def _generate_cgo_bindings(self, items: List[str], module_name: str) -> str:
        """Generate cgo bindings code."""
        bindings_code = f"""package main

/*
#cgo CFLAGS: -I.
#cgo LDFLAGS: -L. -l{module_name}
#include <stdlib.h>
*/
import "C"
import (
    "unsafe"
    "github.com/golang/protobuf/proto"
)

// Python bindings for {module_name}
"""

        for item in items:
            bindings_code += f"""
//export {item}
func {item}() {{
    // Implementation for {item}
}}
"""

        return bindings_code

    def _generate_go_mod(self, module_name: str) -> str:
        """Generate go.mod for the cgo package."""
        return f"""module {module_name}-py

go 1.21

require (
    github.com/golang/protobuf v1.5.3
)
"""

    def generate(self) -> bool:
        """Generate cgo bindings for the Go library."""
        self.log(f"Generating cgo bindings for {self.repo_path}")

        # Find Go files
        go_files = self._find_go_files()
        if not go_files:
            self.log("No Go files found", "warning")
            return True

        self.log(f"Found {len(go_files)} Go files")

        # Extract types and functions
        all_items = []
        for go_file in go_files[:5]:  # Limit to first 5 files for demo
            items = self._extract_go_types(go_file)
            all_items.extend(items)

        if not all_items:
            self.log("No types or functions found", "warning")
            return True

        # Remove duplicates
        unique_items = list(set(all_items))
        self.log(f"Found {len(unique_items)} unique items: {unique_items[:5]}...")

        # Generate cgo bindings
        module_name = os.path.basename(self.repo_path).replace("-", "_")
        bindings_code = self._generate_cgo_bindings(unique_items, module_name)

        # Write the generated bindings
        bindings_dir = os.path.join(self.repo_path, "python_bindings")
        os.makedirs(bindings_dir, exist_ok=True)

        bindings_file = os.path.join(bindings_dir, f"{module_name}_bindings.go")
        with open(bindings_file, "w") as f:
            f.write(bindings_code)

        # Generate go.mod
        go_mod = self._generate_go_mod(module_name)
        go_mod_file = os.path.join(bindings_dir, "go.mod")
        with open(go_mod_file, "w") as f:
            f.write(go_mod)

        # Generate Makefile for building
        makefile = self._generate_makefile(module_name)
        makefile_path = os.path.join(bindings_dir, "Makefile")
        with open(makefile_path, "w") as f:
            f.write(makefile)

        self.log(f"Generated cgo bindings in {bindings_dir}")
        return True

    def _generate_makefile(self, module_name: str) -> str:
        """Generate Makefile for building cgo bindings."""
        return f"""# Makefile for {module_name} Python bindings
.PHONY: build clean

build:
	go build -buildmode=c-shared -o lib{module_name}.so {module_name}_bindings.go

clean:
	rm -f lib{module_name}.so
"""


class WasmBindgenGenerator(BindingGenerator):
    """Generate WebAssembly bindings using wasm-bindgen."""

    def can_generate(self, language: str) -> bool:
        return language.lower() in ["rust", "rs", "wasm", "webassembly"]

    def _generate_wasm_bindings(self, module_name: str) -> str:
        """Generate wasm-bindgen bindings."""
        return f"""use wasm_bindgen::prelude::*;

/// WebAssembly bindings for {module_name}
#[wasm_bindgen]
pub struct {module_name} {{
    // Implementation
}}

#[wasm_bindgen]
impl {module_name} {{
    #[wasm_bindgen(constructor)]
    pub fn new() -> {module_name} {{
        {module_name} {{}}
    }}
    
    pub fn process(&self, input: &str) -> String {{
        format!("Processed: {{}}", input)
    }}
}}

#[wasm_bindgen]
pub fn greet(name: &str) -> String {{
    format!("Hello, {{}}!", name)
}}
"""

    def _generate_cargo_toml(self, module_name: str) -> str:
        """Generate Cargo.toml for wasm-bindgen."""
        return f"""[package]
name = "{module_name}-wasm"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
wasm-bindgen = "0.2"

[dev-dependencies]
wasm-bindgen-test = "0.3"

[profile.release]
opt-level = "s"
"""

    def _generate_package_json(self, module_name: str) -> str:
        """Generate package.json for npm package."""
        return f"""{{
  "name": "{module_name}-wasm",
  "version": "0.1.0",
  "description": "WebAssembly bindings for {module_name}",
  "main": "index.js",
  "scripts": {{
    "build": "wasm-pack build --target web",
    "build-node": "wasm-pack build --target nodejs",
    "test": "wasm-pack test --headless --firefox"
  }},
  "devDependencies": {{
    "wasm-pack": "^0.12.0"
  }}
}}
"""

    def generate(self) -> bool:
        """Generate WebAssembly bindings."""
        self.log(f"Generating WebAssembly bindings for {self.repo_path}")

        # Generate wasm-bindgen bindings
        module_name = os.path.basename(self.repo_path).replace("-", "_")
        bindings_code = self._generate_wasm_bindings(module_name)

        # Write the generated bindings
        bindings_dir = os.path.join(self.repo_path, "wasm_bindings")
        os.makedirs(bindings_dir, exist_ok=True)

        # Create src directory and lib.rs
        src_dir = os.path.join(bindings_dir, "src")
        os.makedirs(src_dir, exist_ok=True)

        lib_file = os.path.join(src_dir, "lib.rs")
        with open(lib_file, "w") as f:
            f.write(bindings_code)

        # Generate Cargo.toml
        cargo_toml = self._generate_cargo_toml(module_name)
        cargo_file = os.path.join(bindings_dir, "Cargo.toml")
        with open(cargo_file, "w") as f:
            f.write(cargo_toml)

        # Generate package.json
        package_json = self._generate_package_json(module_name)
        package_file = os.path.join(bindings_dir, "package.json")
        with open(package_file, "w") as f:
            f.write(package_json)

        # Generate README
        readme = self._generate_wasm_readme(module_name)
        readme_file = os.path.join(bindings_dir, "README.md")
        with open(readme_file, "w") as f:
            f.write(readme)

        self.log(f"Generated WebAssembly bindings in {bindings_dir}")
        return True

    def _generate_wasm_readme(self, module_name: str) -> str:
        """Generate README for WebAssembly package."""
        return f"""# {module_name} WebAssembly Bindings

This package provides WebAssembly bindings for {module_name}.

## Installation

```bash
npm install {module_name}-wasm
```

## Usage

### In the browser

```html
<script type="module">
  import init, {{ {module_name} }} from './pkg/{module_name}_wasm.js';
  
  async function run() {{
    await init();
    const instance = new {module_name}();
    console.log(instance.process("Hello, WASM!"));
  }}
  
  run();
</script>
```

### In Node.js

```javascript
const {{ {module_name} }} = require('{module_name}-wasm');
const instance = new {module_name}();
console.log(instance.process("Hello, WASM!"));
```

## Building

```bash
npm run build        # For web
npm run build-node   # For Node.js
```
"""


class GrpcGenerator(BindingGenerator):
    """Generate gRPC service definitions."""

    def can_generate(self, language: str) -> bool:
        return language.lower() in ["cpp", "c++", "cxx", "python", "rust", "go"]

    def _find_service_candidates(self) -> List[str]:
        """Find potential service classes in the codebase."""
        service_candidates = []

        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith((".cpp", ".cc", ".h", ".hpp", ".py", ".rs", ".go")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Look for service-like patterns
                        if "class" in content and (
                            "Service" in content or "API" in content
                        ):
                            service_candidates.append(file_path)
                    except Exception:
                        continue

        return service_candidates

    def _generate_proto_file(self, service_name: str) -> str:
        """Generate a .proto file for gRPC service definition."""
        return f"""syntax = "proto3";

package {service_name.lower()};

// Auto-generated gRPC service definition
service {service_name}Service {{
    // Example RPC method
    rpc GetInfo(GetInfoRequest) returns (GetInfoResponse);
    
    // Add more RPC methods based on the actual service
}}

message GetInfoRequest {{
    string query = 1;
}}

message GetInfoResponse {{
    string info = 1;
    bool success = 2;
}}
"""

    def _generate_grpc_client(self, service_name: str) -> str:
        """Generate a Python gRPC client."""
        return f"""# Auto-generated gRPC client for {service_name}
import grpc
import {service_name.lower()}_pb2
import {service_name.lower()}_pb2_grpc

class {service_name}Client:
    def __init__(self, host='localhost', port=50051):
        self.channel = grpc.insecure_channel(f'{{host}}:{{port}}')
        self.stub = {service_name.lower()}_pb2_grpc.{service_name}ServiceStub(self.channel)
    
    def get_info(self, query: str) -> str:
        request = {service_name.lower()}_pb2.GetInfoRequest(query=query)
        response = self.stub.GetInfo(request)
        return response.info if response.success else "Error"
    
    def close(self):
        self.channel.close()
"""

    def generate(self) -> bool:
        """Generate gRPC service definitions."""
        self.log(f"Generating gRPC definitions for {self.repo_path}")

        # Find service candidates
        service_candidates = self._find_service_candidates()
        if not service_candidates:
            self.log("No service candidates found", "warning")
            return True

        self.log(f"Found {len(service_candidates)} service candidates")

        # Generate gRPC definitions
        grpc_dir = os.path.join(self.repo_path, "grpc")
        os.makedirs(grpc_dir, exist_ok=True)

        service_name = (
            os.path.basename(self.repo_path).replace("-", "_").replace(" ", "_")
        )

        # Generate .proto file
        proto_content = self._generate_proto_file(service_name)
        proto_file = os.path.join(grpc_dir, f"{service_name.lower()}.proto")
        with open(proto_file, "w") as f:
            f.write(proto_content)

        # Generate Python client
        client_content = self._generate_grpc_client(service_name)
        client_file = os.path.join(grpc_dir, f"{service_name.lower()}_client.py")
        with open(client_file, "w") as f:
            f.write(client_content)

        # Generate CMakeLists.txt for building gRPC
        cmake_content = self._generate_cmake_lists(service_name)
        cmake_file = os.path.join(grpc_dir, "CMakeLists.txt")
        with open(cmake_file, "w") as f:
            f.write(cmake_content)

        self.log(f"Generated gRPC definitions in {grpc_dir}")
        return True

    def _generate_cmake_lists(self, service_name: str) -> str:
        """Generate CMakeLists.txt for building gRPC services."""
        return f"""cmake_minimum_required(VERSION 3.16)
project({service_name}_grpc)

find_package(Protobuf REQUIRED)
find_package(gRPC REQUIRED)

# Generate protobuf and gRPC files
protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS {service_name.lower()}.proto)
protobuf_generate_grpc_cpp(GRPC_SRCS GRPC_HDRS {service_name.lower()}.proto)

# Create gRPC server library
add_library({service_name}_grpc_server
    ${{PROTO_SRCS}}
    ${{PROTO_HDRS}}
    ${{GRPC_SRCS}}
    ${{GRPC_HDRS}}
    server.cpp
)

target_link_libraries({service_name}_grpc_server
    protobuf::libprotobuf
    gRPC::grpc++
)

# Create gRPC client library
add_library({service_name}_grpc_client
    ${{PROTO_SRCS}}
    ${{PROTO_HDRS}}
    ${{GRPC_SRCS}}
    ${{GRPC_HDRS}}
    client.cpp
)

target_link_libraries({service_name}_grpc_client
    protobuf::libprotobuf
    gRPC::grpc++
)
"""


# Generator registry
GENERATOR_REGISTRY = {
    "pybind11": Pybind11Generator,
    "pyo3": PyO3Generator,
    "cgo": CGoGenerator,
    "wasm": WasmBindgenGenerator,
    "grpc": GrpcGenerator,
}


def get_generator(
    generator_name: str, repo_path: str, config: Dict[str, Any]
) -> Optional[BindingGenerator]:
    """Get a generator instance by name."""
    if generator_name not in GENERATOR_REGISTRY:
        logger.warning(f"Generator '{generator_name}' not found in registry")
        return None

    generator_class = GENERATOR_REGISTRY[generator_name]
    return generator_class(repo_path, config)


def generate_bindings(
    repo: Dict[str, Any], repo_path: str, generators: List[str]
) -> Dict[str, bool]:
    """Generate bindings for a repository."""
    results = {}

    for generator_name in generators:
        generator = get_generator(generator_name, repo_path, {"repo": repo})
        if generator and generator.can_generate(repo.get("language", "")):
            results[generator_name] = generator.generate()
        else:
            logger.warning(
                f"Generator '{generator_name}' cannot handle language '{repo.get('language', '')}'"
            )
            results[generator_name] = False

    return results
