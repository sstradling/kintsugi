"""Tests for :mod:`pipeline.validator`."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.generators import generate_cube_8, generate_sphere_8_slices
from pipeline.manifest import (
    PieceSpec,
    PuzzleManifest,
    Quat,
    Seam,
    Vec3,
    write_manifest,
)
from pipeline.validator import (
    validate_bundle,
    validate_manifest,
)


def _linear_chain(n: int) -> PuzzleManifest:
    """Build a small synthetic manifest of ``n`` pieces in a chain."""
    pieces: list[PieceSpec] = []
    for i in range(n):
        neighbours: list[str] = []
        if i > 0:
            neighbours.append(f"p_{i - 1}")
        if i < n - 1:
            neighbours.append(f"p_{i + 1}")
        pieces.append(
            PieceSpec(
                id=f"p_{i}",
                mesh_path=f"pieces/p_{i}.obj",
                target_pos=Vec3(float(i), 0.0, 0.0),
                target_rot=Quat.identity(),
                neighbors=tuple(neighbours),
            )
        )
    seams: list[Seam] = []
    for i in range(n - 1):
        seams.append(
            Seam.make(
                f"p_{i}",
                f"p_{i + 1}",
                [Vec3(i + 0.5, -0.5, 0), Vec3(i + 0.5, 0.5, 0), Vec3(i + 0.5, 0.5, 1)],
            )
        )
    return PuzzleManifest(
        id="chain",
        display_name="chain",
        starter_piece_id="p_0",
        pieces=pieces,
        seams=seams,
        bounding_radius=float(n),
    )


@pytest.fixture
def cube_bundle(tmp_path: Path) -> Path:
    generate_cube_8(tmp_path)
    return tmp_path


@pytest.fixture
def sphere_bundle(tmp_path: Path) -> Path:
    generate_sphere_8_slices(tmp_path)
    return tmp_path


def test_cube_8_validates_clean(cube_bundle: Path) -> None:
    report = validate_bundle(cube_bundle)
    assert report.ok, report.errors
    assert not report.warnings


def test_sphere_8_validates_clean(sphere_bundle: Path) -> None:
    report = validate_bundle(sphere_bundle)
    assert report.ok, report.errors
    assert not report.warnings


def test_disconnected_piece_fails_d5_reassemblability() -> None:
    m = _linear_chain(3)
    m.pieces.append(
        PieceSpec(
            id="orphan",
            mesh_path="pieces/orphan.obj",
            target_pos=Vec3(99, 0, 0),
            target_rot=Quat.identity(),
            neighbors=(),
        )
    )
    report = validate_manifest(m)
    assert not report.ok
    assert any("unreachable" in e for e in report.errors)
    assert any("orphan" in e for e in report.errors)


def test_seam_loop_with_two_vertices_fails() -> None:
    m = _linear_chain(2)
    m.seams[0] = Seam("p_0", "p_1", (Vec3(0, 0, 0), Vec3(1, 0, 0)))
    report = validate_manifest(m)
    assert not report.ok
    assert any("vertex/vertices" in e for e in report.errors)


def test_missing_seam_between_neighbours_warns_only() -> None:
    m = _linear_chain(3)
    m.seams = []
    report = validate_manifest(m)
    assert report.ok
    assert len(report.warnings) == 2


def test_missing_mesh_file_fails_when_bundle_dir_given(tmp_path: Path) -> None:
    m = _linear_chain(2)
    write_manifest(m, tmp_path / "manifest.json")
    report = validate_bundle(tmp_path)
    assert not report.ok
    assert any("missing mesh" in e for e in report.errors)


def test_schema_error_short_circuits_higher_level_checks() -> None:
    m = _linear_chain(2)
    m.bounding_radius = -1.0
    report = validate_manifest(m)
    assert not report.ok
    assert len(report.errors) == 1
    assert "schema validation failed" in report.errors[0]


def test_validation_report_raise_if_errors() -> None:
    m = _linear_chain(2)
    m.pieces.append(
        PieceSpec("orphan", "pieces/orphan.obj", Vec3(99, 0, 0), Quat.identity(), ())
    )
    report = validate_manifest(m)
    with pytest.raises(ValueError, match="unreachable"):
        report.raise_if_errors()


def test_cli_build_runs_validation_automatically(tmp_path: Path) -> None:
    import subprocess
    import sys

    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pipeline.cli",
            "build",
            "cube_8",
            "--out",
            str(tmp_path / "cube"),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_cli_validate_subcommand(cube_bundle: Path) -> None:
    import subprocess
    import sys

    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "pipeline.cli", "validate", str(cube_bundle)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "OK" in result.stdout
