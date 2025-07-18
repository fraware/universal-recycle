workspace(name = "universal_recycle")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:utils.bzl", "maybe")

# Python rules
maybe(
    http_archive,
    name = "rules_python",
    sha256 = "94750828b18044533e98a1293b9a8cee845f61e4d5e0c0e2b8c2c7b8c8c8c8c8c",
    strip_prefix = "rules_python-0.21.0",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.21.0/rules_python-0.21.0.tar.gz",
)

load("@rules_python//python:repositories.bzl", "python_register_toolchains")

python_register_toolchains(
    name = "python3_9",
    python_version = "3.9",
)

# C++ rules (built into Bazel)
load("@rules_cc//cc:repositories.bzl", "rules_cc_dependencies")
load("@rules_cc//cc:defs.bzl", "cc_binary", "cc_library")

rules_cc_dependencies()

# Additional dependencies for the project
maybe(
    http_archive,
    name = "com_google_googletest",
    sha256 = "8ad598c73ad796e0d8280b082cebd82a630d73e73cd3c70057938a6501bba5d7",
    strip_prefix = "googletest-1.14.0",
    urls = ["https://github.com/google/googletest/archive/refs/tags/v1.14.0.tar.gz"],
)

# For future: vcpkg integration
# maybe(
#     http_archive,
#     name = "vcpkg",
#     sha256 = "...",
#     strip_prefix = "vcpkg-...",
#     url = "https://github.com/microsoft/vcpkg/archive/refs/tags/...tar.gz",
# ) 