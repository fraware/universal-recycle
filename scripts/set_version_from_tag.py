"""Set `version = \"...\"` in pyproject.toml from GITHUB_REF_NAME (e.g. v0.2.0 -> 0.2.0)."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def main() -> None:
    ref = os.environ.get("GITHUB_REF_NAME", "").strip()
    if not ref:
        print("GITHUB_REF_NAME is not set; skipping version bump", file=sys.stderr)
        return
    version = ref.removeprefix("v")
    if not version:
        print(f"Invalid tag name {ref!r}", file=sys.stderr)
        sys.exit(1)
    path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r'^version = "[^"]*"',
        f'version = "{version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if n != 1:
        print("Could not find project.version in pyproject.toml", file=sys.stderr)
        sys.exit(1)
    path.write_text(new_text, encoding="utf-8")
    print(f"Set package version to {version}")


if __name__ == "__main__":
    main()
