"""Tests for recycle.validation."""

from pathlib import Path

import pytest

from recycle.validation import validate_repos_manifest


def test_validate_minimal_manifest_ok(tmp_path: Path) -> None:
    p = tmp_path / "repos.yaml"
    p.write_text(
        """
repositories:
  - name: demo
    language: python
    git: https://github.com/example/demo.git
    commit: main
""",
        encoding="utf-8",
    )
    ok, errors = validate_repos_manifest(str(p))
    assert ok is True
    assert errors == []


def test_validate_list_format_ok(tmp_path: Path) -> None:
    p = tmp_path / "repos.yaml"
    p.write_text(
        """
- name: demo
  language: rust
  git: https://github.com/example/demo.git
  commit: main
""",
        encoding="utf-8",
    )
    ok, errors = validate_repos_manifest(str(p))
    assert ok is True
    assert errors == []


def test_validate_missing_file(tmp_path: Path) -> None:
    ok, errors = validate_repos_manifest(str(tmp_path / "nope.yaml"))
    assert ok is False
    assert any("not found" in e.lower() for e in errors)


def test_validate_invalid_yaml(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("{ not: valid yaml [[[", encoding="utf-8")
    ok, errors = validate_repos_manifest(str(p))
    assert ok is False
    assert any("yaml" in e.lower() for e in errors)


def test_validate_bad_structure(tmp_path: Path) -> None:
    p = tmp_path / "repos.yaml"
    p.write_text("foo: bar\n", encoding="utf-8")
    ok, errors = validate_repos_manifest(str(p))
    assert ok is False
    assert any("format" in e.lower() for e in errors)


def test_validate_missing_required_fields(tmp_path: Path) -> None:
    p = tmp_path / "repos.yaml"
    p.write_text(
        """
repositories:
  - name: x
    language: python
""",
        encoding="utf-8",
    )
    ok, errors = validate_repos_manifest(str(p))
    assert ok is False
    assert any("git" in e.lower() for e in errors)


def test_validate_invalid_language(tmp_path: Path) -> None:
    p = tmp_path / "repos.yaml"
    p.write_text(
        """
repositories:
  - name: x
    language: cobol
    git: https://github.com/a/b.git
""",
        encoding="utf-8",
    )
    ok, errors = validate_repos_manifest(str(p))
    assert ok is False
    assert any("language" in e.lower() for e in errors)


@pytest.fixture()
def fixture_manifest() -> str:
    return str(Path(__file__).resolve().parent / "fixtures" / "minimal-manifest.yaml")


def test_validate_fixture_manifest(fixture_manifest: str) -> None:
    ok, errors = validate_repos_manifest(fixture_manifest)
    assert ok is True
    assert errors == []
