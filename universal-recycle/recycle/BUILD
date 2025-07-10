load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_binary(
    name="cli",
    srcs=["cli.py"],
    data=["//:repos.yaml"],
    visibility=["//visibility:public"],
)

py_library(
    name="recycle_lib",
    srcs=["cli.py"],
    data=["//:repos.yaml"],
    visibility=["//visibility:public"],
)
 