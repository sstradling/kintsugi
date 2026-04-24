"""Tests for :mod:`pipeline.generators.sphere_8_slices`."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from pipeline.generators import generate_sphere_8_slices
from pipeline.manifest import load_manifest
from pipeline.obj_io import read_obj


@pytest.fixture(scope="module")
def sphere_bundle(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("sphere_8_slices")
    generate_sphere_8_slices(out)
    return out


def test_generates_eight_slices(sphere_bundle: Path) -> None:
    m = load_manifest(sphere_bundle / "manifest.json")
    assert len(m.pieces) == 8
    assert {p.id for p in m.pieces} == {f"s_{i}" for i in range(8)}


def test_seven_seams_in_a_linear_stack(sphere_bundle: Path) -> None:
    m = load_manifest(sphere_bundle / "manifest.json")
    assert len(m.seams) == 7


def test_endpoint_slices_have_one_neighbour(sphere_bundle: Path) -> None:
    m = load_manifest(sphere_bundle / "manifest.json")
    pieces = {p.id: p for p in m.pieces}
    assert pieces["s_0"].neighbors == ("s_1",)
    assert pieces["s_7"].neighbors == ("s_6",)


def test_middle_slices_have_two_neighbours(sphere_bundle: Path) -> None:
    m = load_manifest(sphere_bundle / "manifest.json")
    for i in range(1, 7):
        p = next(pp for pp in m.pieces if pp.id == f"s_{i}")
        assert set(p.neighbors) == {f"s_{i - 1}", f"s_{i + 1}"}


def test_starter_is_one_of_the_middle_slices(sphere_bundle: Path) -> None:
    m = load_manifest(sphere_bundle / "manifest.json")
    assert m.starter_piece_id in {f"s_{i}" for i in range(2, 6)}


def test_seam_loops_are_circles_of_correct_radius(sphere_bundle: Path) -> None:
    m = load_manifest(sphere_bundle / "manifest.json")
    for seam in m.seams:
        ys = [v.y for v in seam.vertex_loop]
        assert max(ys) - min(ys) < 1e-9, "seam should be planar in Y"
        y = ys[0]
        expected_r = math.sqrt(max(0.0, 1.0 - y * y))
        for v in seam.vertex_loop:
            r = math.sqrt(v.x * v.x + v.z * v.z)
            assert r == pytest.approx(expected_r, abs=1e-6)


def test_slice_meshes_stay_within_unit_sphere(sphere_bundle: Path) -> None:
    m = load_manifest(sphere_bundle / "manifest.json")
    for piece in m.pieces:
        mesh = read_obj(sphere_bundle / piece.mesh_path)
        for x, y, z in mesh.vertices:
            r2 = x * x + y * y + z * z
            assert r2 <= 1.0 + 1e-5, f"{piece.id}: vertex outside unit sphere"


def test_slice_meshes_are_constrained_to_their_y_band(sphere_bundle: Path) -> None:
    m = load_manifest(sphere_bundle / "manifest.json")
    step = 2.0 / 8
    for i, piece in enumerate(m.pieces):
        mesh = read_obj(sphere_bundle / piece.mesh_path)
        y_low, y_high = -1.0 + i * step, -1.0 + (i + 1) * step
        for _, y, _ in mesh.vertices:
            assert y_low - 1e-6 <= y <= y_high + 1e-6


def test_bounding_radius_is_one(sphere_bundle: Path) -> None:
    m = load_manifest(sphere_bundle / "manifest.json")
    assert m.bounding_radius == pytest.approx(1.0)
