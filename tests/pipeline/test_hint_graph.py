"""Tests for :mod:`pipeline.hint_graph`."""

from __future__ import annotations

import pytest

from pipeline.generators import generate_cube_8, generate_sphere_8_slices
from pipeline.hint_graph import compute_hint_order
from pipeline.manifest import PieceSpec, PuzzleManifest, Quat, Seam, Vec3


def _linear_chain(n: int, starter_index: int = 0) -> PuzzleManifest:
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
                target_pos=Vec3(float(i), 0, 0),
                target_rot=Quat.identity(),
                neighbors=tuple(neighbours),
            )
        )
    return PuzzleManifest(
        id="chain",
        display_name="chain",
        starter_piece_id=f"p_{starter_index}",
        pieces=pieces,
        seams=[],
        bounding_radius=float(n),
    )


def test_linear_chain_from_end_walks_in_order() -> None:
    m = _linear_chain(5, starter_index=0)
    assert compute_hint_order(m) == ("p_1", "p_2", "p_3", "p_4")


def test_linear_chain_from_middle_walks_outward() -> None:
    m = _linear_chain(5, starter_index=2)
    order = compute_hint_order(m)
    assert order[:2] in (("p_1", "p_3"), ("p_3", "p_1"))
    assert set(order) == {"p_0", "p_1", "p_3", "p_4"}


def test_starter_is_never_in_order() -> None:
    m = _linear_chain(5, starter_index=2)
    assert m.starter_piece_id not in compute_hint_order(m)


def test_order_is_deterministic_across_calls() -> None:
    m = _linear_chain(5, starter_index=0)
    assert compute_hint_order(m) == compute_hint_order(m)


def test_cube_8_hint_order_prefers_most_constrained() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        m = generate_cube_8(td)
    order = m.hint_order
    assert m.starter_piece_id not in order
    assert len(order) == 7
    assert set(order) | {m.starter_piece_id} == {p.id for p in m.pieces}
    placed = {m.starter_piece_id}
    adjacency = {p.id: set(p.neighbors) for p in m.pieces}
    for pid in order:
        assert adjacency[pid] & placed, (
            f"{pid} placed before any of its neighbours: violates BFS frontier"
        )
        placed.add(pid)
    by_id = {p.id: p for p in m.pieces}
    last_pid = order[-1]
    last_placed_neighbour_count = len(
        adjacency[last_pid] & (placed - {last_pid})
    )
    assert last_placed_neighbour_count == len(adjacency[last_pid])


def test_sphere_8_slices_hint_order_walks_outward_from_starter() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        m = generate_sphere_8_slices(td)
    order = m.hint_order
    assert len(order) == 7
    starter_index = int(m.starter_piece_id.split("_")[1])
    indices = [int(pid.split("_")[1]) for pid in order]
    max_distance_seen = 0
    for idx in indices:
        distance = abs(idx - starter_index)
        assert distance >= max_distance_seen or distance == max_distance_seen
        max_distance_seen = max(max_distance_seen, distance)


def test_disconnected_piece_falls_back_to_lex_order() -> None:
    m = _linear_chain(3, starter_index=0)
    m.pieces.append(
        PieceSpec("z_orphan", "pieces/z.obj", Vec3(99, 0, 0), Quat.identity(), ())
    )
    m.pieces.append(
        PieceSpec("a_orphan", "pieces/a.obj", Vec3(99, 0, 0), Quat.identity(), ())
    )
    order = compute_hint_order(m)
    assert order[:2] == ("p_1", "p_2")
    assert order[2:] == ("a_orphan", "z_orphan")


def test_unknown_starter_raises() -> None:
    m = _linear_chain(3, starter_index=0)
    m.starter_piece_id = "missing"
    with pytest.raises(ValueError, match="not present"):
        compute_hint_order(m)
