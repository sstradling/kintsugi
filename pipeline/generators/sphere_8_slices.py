"""``sphere_8_slices`` puzzle generator.

A unit-radius sphere centred at the origin, sliced into 8 parallel
sheets of equal thickness along the Y axis. Slices are bounded by the
9 planes ``y = -1, -0.75, -0.5, ..., 1.0``.

This puzzle exercises:

- Curved boundary surfaces (each shard's "rim" is a tessellated
  circle).
- A strictly linear adjacency graph (each slice has 1-2 neighbours).
- Non-trivial seam loops (the seams are circles of varying radius,
  not squares).

Slices are named ``s_0`` (bottom) through ``s_7`` (top).
"""

from __future__ import annotations

import math
from pathlib import Path

from ..hint_graph import compute_hint_order
from ..manifest import PieceSpec, PuzzleManifest, Quat, Seam, Vec3, write_manifest
from ..obj_io import TriMesh, write_obj

PUZZLE_ID = "sphere_8_slices"
DISPLAY_NAME = "Sphere of Eight Slices"

NUM_SLICES = 8
RADIAL_SEGMENTS = 32


def _slice_y_bounds(i: int) -> tuple[float, float]:
    """Return (y_low, y_high) for slice ``i`` in the unit sphere."""
    step = 2.0 / NUM_SLICES
    y_low = -1.0 + i * step
    y_high = y_low + step
    return y_low, y_high


def _ring_radius(y: float) -> float:
    """Cross-section radius of the unit sphere at height ``y``."""
    return math.sqrt(max(0.0, 1.0 - y * y))


def _ring_vertices(
    mesh: TriMesh, y: float, segments: int
) -> list[int]:
    """Append a ring of ``segments`` vertices at height ``y`` and return their indices.

    Returns an empty list if the ring degenerates to a single point
    (the top and bottom poles); in that case caller should add a single
    pole vertex instead.
    """
    r = _ring_radius(y)
    if r < 1e-9:
        return []
    indices: list[int] = []
    for k in range(segments):
        theta = 2.0 * math.pi * k / segments
        x = r * math.cos(theta)
        z = r * math.sin(theta)
        indices.append(mesh.add_vertex(x, y, z))
    return indices


def _stitch_rings(
    mesh: TriMesh, lower: list[int], upper: list[int]
) -> None:
    """Triangulate the side wall between two equal-length rings.

    Winding is chosen so the outward normal points away from the Y axis.
    """
    n = len(lower)
    assert len(upper) == n
    for k in range(n):
        a = lower[k]
        b = lower[(k + 1) % n]
        c = upper[(k + 1) % n]
        d = upper[k]
        mesh.add_quad(a, b, c, d)


def _cap_with_pole(
    mesh: TriMesh, ring: list[int], pole_index: int, *, ring_above_pole: bool
) -> None:
    """Triangulate a ring against a single pole vertex (top or bottom cap).

    ``ring_above_pole`` controls winding: True for a bottom cap (pole
    below ring, normal points down), False for a top cap.
    """
    n = len(ring)
    for k in range(n):
        a = ring[k]
        b = ring[(k + 1) % n]
        if ring_above_pole:
            mesh.add_triangle(pole_index, b, a)
        else:
            mesh.add_triangle(pole_index, a, b)


def _cap_flat_disc(
    mesh: TriMesh, ring: list[int], y: float, *, normal_up: bool
) -> None:
    """Triangulate a flat circular disc filling the seam at height ``y``.

    A central vertex is added at ``(0, y, 0)`` and the ring is fanned
    around it. ``normal_up`` controls winding: the disc's outward
    normal should point away from the slice's interior.
    """
    centre = mesh.add_vertex(0.0, y, 0.0)
    n = len(ring)
    for k in range(n):
        a = ring[k]
        b = ring[(k + 1) % n]
        if normal_up:
            mesh.add_triangle(centre, b, a)
        else:
            mesh.add_triangle(centre, a, b)


def _build_slice_mesh(slice_index: int) -> TriMesh:
    """Build the mesh for a single sphere slice in **assembly local space**.

    Slices are kept in their final position rather than centred on the
    origin: the curved surface depends on the absolute Y, so re-centring
    would require also storing the per-piece offset and reapplying it at
    render time. Easier and equivalent is to set ``target_pos = (0,0,0)``
    for every slice and bake the position into the mesh.
    """
    y_low, y_high = _slice_y_bounds(slice_index)
    mesh = TriMesh()
    is_bottom_pole = math.isclose(y_low, -1.0)
    is_top_pole = math.isclose(y_high, 1.0)
    inner_step = 2.0 / NUM_SLICES / 4.0
    inner_ys: list[float] = []
    y = y_low
    while y < y_high - 1e-9:
        inner_ys.append(y)
        y += inner_step
    inner_ys.append(y_high)
    rings: list[list[int]] = []
    pole_bottom: int | None = None
    pole_top: int | None = None
    for idx, yy in enumerate(inner_ys):
        if idx == 0 and is_bottom_pole:
            pole_bottom = mesh.add_vertex(0.0, yy, 0.0)
            rings.append([])
            continue
        if idx == len(inner_ys) - 1 and is_top_pole:
            pole_top = mesh.add_vertex(0.0, yy, 0.0)
            rings.append([])
            continue
        rings.append(_ring_vertices(mesh, yy, RADIAL_SEGMENTS))
    for i in range(len(rings) - 1):
        lower, upper = rings[i], rings[i + 1]
        if not lower and pole_bottom is not None and i == 0:
            _cap_with_pole(mesh, upper, pole_bottom, ring_above_pole=True)
        elif not upper and pole_top is not None and i == len(rings) - 2:
            _cap_with_pole(mesh, lower, pole_top, ring_above_pole=False)
        else:
            _stitch_rings(mesh, lower, upper)
    if not is_bottom_pole:
        _cap_flat_disc(mesh, rings[0], y_low, normal_up=False)
    if not is_top_pole:
        _cap_flat_disc(mesh, rings[-1], y_high, normal_up=True)
    return mesh


def _seam_loop_at_y(y: float) -> tuple[Vec3, ...]:
    """Return the circular seam loop at height ``y`` as a vertex ring."""
    r = _ring_radius(y)
    loop: list[Vec3] = []
    for k in range(RADIAL_SEGMENTS):
        theta = 2.0 * math.pi * k / RADIAL_SEGMENTS
        loop.append(Vec3(r * math.cos(theta), y, r * math.sin(theta)))
    return tuple(loop)


def generate_sphere_8_slices(out_dir: str | Path) -> PuzzleManifest:
    """Write the sphere_8_slices bundle to ``out_dir`` and return the manifest."""
    out = Path(out_dir)
    pieces_dir = out / "pieces"
    pieces_dir.mkdir(parents=True, exist_ok=True)
    pieces: list[PieceSpec] = []
    for i in range(NUM_SLICES):
        pid = f"s_{i}"
        mesh = _build_slice_mesh(i)
        write_obj(mesh, pieces_dir / f"{pid}.obj", name=pid)
        neighbours: list[str] = []
        if i > 0:
            neighbours.append(f"s_{i - 1}")
        if i < NUM_SLICES - 1:
            neighbours.append(f"s_{i + 1}")
        pieces.append(
            PieceSpec(
                id=pid,
                mesh_path=f"pieces/{pid}.obj",
                target_pos=Vec3(0.0, 0.0, 0.0),
                target_rot=Quat.identity(),
                neighbors=tuple(neighbours),
            )
        )
    seams: list[Seam] = []
    for i in range(NUM_SLICES - 1):
        _, y_seam = _slice_y_bounds(i)
        seams.append(Seam.make(f"s_{i}", f"s_{i + 1}", _seam_loop_at_y(y_seam)))
    starter_index = NUM_SLICES // 2 - 1
    starter = f"s_{starter_index}"
    manifest = PuzzleManifest(
        id=PUZZLE_ID,
        display_name=DISPLAY_NAME,
        starter_piece_id=starter,
        pieces=pieces,
        seams=seams,
        bounding_radius=1.0,
    )
    manifest.hint_order = compute_hint_order(manifest)
    write_manifest(manifest, out / "manifest.json")
    return manifest
