"""Integration test: the CLI builds both starter puzzles end-to-end."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from pipeline.manifest import load_manifest


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pipeline.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def test_cli_builds_all(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out = tmp_path / "build"
    _run_cli("build", "all", "--out", str(out), cwd=repo_root)
    cube = load_manifest(out / "cube_8" / "manifest.json")
    sphere = load_manifest(out / "sphere_8_slices" / "manifest.json")
    assert len(cube.pieces) == 8
    assert len(sphere.pieces) == 8


def test_cli_rejects_unknown_puzzle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            [sys.executable, "-m", "pipeline.cli", "build", "nonsense", "--out", str(tmp_path)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
