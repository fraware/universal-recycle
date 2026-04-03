"""Smoke tests for installed CLI (subprocess)."""

import shutil
import subprocess
import sys


def test_recycle_help_exits_zero() -> None:
    exe = shutil.which("recycle")
    assert exe is not None, "recycle console script should be on PATH when env is set up"
    r = subprocess.run([exe, "--help"], capture_output=True, text=True, check=False)
    assert r.returncode == 0
    assert "Universal Recycle" in r.stdout


def test_python_m_recycle_help() -> None:
    r = subprocess.run(
        [sys.executable, "-m", "recycle", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
    assert "Universal Recycle" in r.stdout


def test_python_m_recycle_cli_help() -> None:
    r = subprocess.run(
        [sys.executable, "-m", "recycle.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
    assert "Universal Recycle" in r.stdout
