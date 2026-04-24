"""Tests for :mod:`pipeline.manifest`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.manifest import (
    PieceSpec,
    PuzzleManifest,
    Quat,
    Seam,
    Vec3,
    load_manifest,
    write_manifest,
)


def _two_piece_manifest() -> PuzzleManifest:
    return PuzzleManifest(
        id="t",
        display_name="t",
        starter_piece_id="a",
        pieces=[
            PieceSpec("a", "pieces/a.obj", Vec3(0, 0, 0), Quat.identity(), ("b",)),
            PieceSpec("b", "pieces/b.obj", Vec3(1, 0, 0), Quat.identity(), ("a",)),
        ],
        seams=[
            Seam.make("a", "b", [Vec3(0.5, 0, 0), Vec3(0.5, 1, 0), Vec3(0.5, 1, 1)]),
        ],
        bounding_radius=1.0,
    )


def test_round_trip_json(tmp_path: Path) -> None:
    m = _two_piece_manifest()
    path = tmp_path / "manifest.json"
    write_manifest(m, path)
    loaded = load_manifest(path)
    assert loaded.to_dict() == m.to_dict()


def test_validate_rejects_unknown_starter() -> None:
    m = _two_piece_manifest()
    m.starter_piece_id = "missing"
    with pytest.raises(ValueError, match="starter_piece_id"):
        m.validate()


def test_validate_rejects_duplicate_piece_ids() -> None:
    m = _two_piece_manifest()
    m.pieces.append(PieceSpec("a", "pieces/a2.obj", Vec3(2, 0, 0)))
    with pytest.raises(ValueError, match="unique"):
        m.validate()


def test_validate_rejects_asymmetric_adjacency() -> None:
    m = _two_piece_manifest()
    m.pieces[1] = PieceSpec(
        m.pieces[1].id,
        m.pieces[1].mesh_path,
        m.pieces[1].target_pos,
        m.pieces[1].target_rot,
        neighbors=(),
    )
    with pytest.raises(ValueError, match="symmetric"):
        m.validate()


def test_validate_rejects_seam_for_non_neighbours() -> None:
    m = PuzzleManifest(
        id="t",
        display_name="t",
        starter_piece_id="a",
        pieces=[
            PieceSpec("a", "a.obj", Vec3(0, 0, 0), Quat.identity(), ()),
            PieceSpec("b", "b.obj", Vec3(1, 0, 0), Quat.identity(), ()),
        ],
        seams=[Seam.make("a", "b", [Vec3(0, 0, 0)])],
        bounding_radius=1.0,
    )
    with pytest.raises(ValueError, match="not listed as neighbors"):
        m.validate()


def test_validate_rejects_negative_radius() -> None:
    m = _two_piece_manifest()
    m.bounding_radius = -1.0
    with pytest.raises(ValueError, match="bounding_radius"):
        m.validate()


def test_validate_rejects_wrong_schema_version() -> None:
    m = _two_piece_manifest()
    m.schema_version = 999
    with pytest.raises(ValueError, match="schema_version"):
        m.validate()


def test_seam_canonicalises_piece_order() -> None:
    s = Seam.make("z", "a", [Vec3(0, 0, 0)])
    assert (s.piece_a, s.piece_b) == ("a", "z")


def test_seam_rejects_non_canonical_construction() -> None:
    with pytest.raises(ValueError):
        Seam("z", "a", (Vec3(0, 0, 0),))


def test_load_manifest_validates(tmp_path: Path) -> None:
    bad = {
        "schema_version": 1,
        "id": "t",
        "display_name": "t",
        "starter_piece_id": "missing",
        "bounding_radius": 1.0,
        "pieces": [
            {
                "id": "a",
                "mesh_path": "a.obj",
                "target_pos": [0, 0, 0],
                "target_rot": [0, 0, 0, 1],
                "neighbors": [],
            }
        ],
        "seams": [],
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        load_manifest(p)
