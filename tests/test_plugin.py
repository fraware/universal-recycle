"""Tests for recycle.plugin."""

from recycle.plugin import PLUGIN_REGISTRY, RuffAdapter, get_plugin, run_adapters


def test_plugin_registry_contains_ruff() -> None:
    assert "ruff" in PLUGIN_REGISTRY


def test_ruff_adapter_language() -> None:
    adapter = RuffAdapter("/tmp/unused", {})
    assert adapter.can_handle("python") is True
    assert adapter.can_handle("cpp") is False


def test_get_plugin_returns_instance() -> None:
    p = get_plugin("ruff", "/tmp/unused-ruff", {})
    assert p is not None
    assert isinstance(p, RuffAdapter)


def test_run_adapters_empty_list(tmp_path) -> None:
    repo = {"name": "t", "language": "python"}
    results = run_adapters(repo, str(tmp_path), [])
    assert results == {}
