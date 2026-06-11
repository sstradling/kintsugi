"""Tests for :mod:`pipeline.generators.cube_8`."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.generators import generate_cube_8
from pipeline.manifest import load_manifest
from pipeline.obj_io import read_obj


@pytest.fixture(scope="module")
def cube_bundle(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("cube_8")
    generate_cube_8(out)
    return out


def test_generates_eight_pieces(cube_bundle: Path) -> None:
    m = load_manifest(cube_bundle / "manifest.json")
    assert len(m.pieces) == 8


def test_each_piece_has_three_neighbours(cube_bundle: Path) -> None:
    m = load_manifest(cube_bundle / "manifest.json")
    for p in m.pieces:
        assert len(p.neighbors) == 3, f"{p.id} has {len(p.neighbors)} neighbours"


def test_twelve_seams_in_a_2x2x2_grid(cube_bundle: Path) -> None:
    m = load_manifest(cube_bundle / "manifest.json")
    assert len(m.seams) == 12


def test_starter_piece_present(cube_bundle: Path) -> None:
    m = load_manifest(cube_bundle / "manifest.json")
    assert m.starter_piece_id in {p.id for p in m.pieces}


def test_target_positions_form_2x2x2_grid(cube_bundle: Path) -> None:
    m = load_manifest(cube_bundle / "manifest.json")
    coords = sorted({round(p.target_pos.x, 6) for p in m.pieces})
    assert coords == [-0.25, 0.25]
    coords_y = sorted({round(p.target_pos.y, 6) for p in m.pieces})
    coords_z = sorted({round(p.target_pos.z, 6) for p in m.pieces})
    assert coords_y == [-0.25, 0.25]
    assert coords_z == [-0.25, 0.25]


def test_pieces_are_unit_cubes_of_side_half(cube_bundle: Path) -> None:
    mesh = read_obj(cube_bundle / "pieces" / "c_000.obj")
    assert len(mesh.vertices) == 8
    assert len(mesh.triangles) == 12
    xs = [v[0] for v in mesh.vertices]
    ys = [v[1] for v in mesh.vertices]
    zs = [v[2] for v in mesh.vertices]
    assert max(xs) - min(xs) == pytest.approx(0.5)
    assert max(ys) - min(ys) == pytest.approx(0.5)
    assert max(zs) - min(zs) == pytest.approx(0.5)


def test_bounding_radius_is_cube_diagonal(cube_bundle: Path) -> None:
    m = load_manifest(cube_bundle / "manifest.json")
    assert m.bounding_radius == pytest.approx(0.8660254, abs=1e-6)


def test_seam_loops_are_squares_of_side_half(cube_bundle: Path) -> None:
    m = load_manifest(cube_bundle / "manifest.json")
    for seam in m.seams:
        assert len(seam.vertex_loop) == 4
        ax, ay, az = seam.vertex_loop[0].x, seam.vertex_loop[0].y, seam.vertex_loop[0].z
        bx, by, bz = seam.vertex_loop[2].x, seam.vertex_loop[2].y, seam.vertex_loop[2].z
        diag_sq = (ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2
        assert diag_sq == pytest.approx(0.5, abs=1e-6)
