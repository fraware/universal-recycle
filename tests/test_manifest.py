"""Tests for manifest loading helpers in recycle.cli."""

from pathlib import Path


from recycle.cli import load_manifest


def test_load_manifest_repositories_key(tmp_path: Path) -> None:
    p = tmp_path / "repos.yaml"
    p.write_text(
        """
repositories:
  - name: a
    language: python
    git: https://github.com/x/a.git
    commit: main
""",
        encoding="utf-8",
    )
    repos = load_manifest(str(p))
    assert len(repos) == 1
    assert repos[0]["name"] == "a"


def test_load_manifest_list_format(tmp_path: Path) -> None:
    p = tmp_path / "repos.yaml"
    p.write_text(
        """
- name: b
  language: go
  git: https://github.com/x/b.git
  commit: main
""",
        encoding="utf-8",
    )
    repos = load_manifest(str(p))
    assert len(repos) == 1
    assert repos[0]["language"] == "go"


def test_load_fixture_manifest() -> None:
    path = Path(__file__).resolve().parent / "fixtures" / "minimal-manifest.yaml"
    repos = load_manifest(str(path))
    assert len(repos) == 1
    assert repos[0]["name"] == "tiny-example"
