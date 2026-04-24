"""``cube_8`` puzzle generator.

A unit cube centered at the origin (extent [-0.5, 0.5] on each axis)
fractured into 8 equal sub-cubes (a 2x2x2 grid). Each sub-cube has 3
neighbours (one across each face it shares with another sub-cube).

This is the simplest non-trivial 3D adjacency graph and is used as the
runtime bring-up puzzle: if cube_8 doesn't load and snap, nothing will.

Coordinate system convention: right-handed, Y-up. Sub-cubes are named
``c_<x><y><z>`` where each axis index is 0 or 1.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path

from ..manifest import PieceSpec, PuzzleManifest, Quat, Seam, Vec3
from ..obj_io import TriMesh, write_obj

PUZZLE_ID = "cube_8"
DISPLAY_NAME = "Cube of Eight"

SUBCUBE_SIZE = 0.5
HALF = SUBCUBE_SIZE / 2


def _piece_id(ix: int, iy: int, iz: int) -> str:
    return f"c_{ix}{iy}{iz}"


def _build_subcube_mesh() -> TriMesh:
    """Return a single sub-cube mesh centred on its own origin.

    The mesh is reused per-piece by re-emitting the same OBJ; the piece's
    target position positions it within the assembly.
    """
    mesh = TriMesh()
    s = HALF
    corners = [
        (-s, -s, -s),
        (s, -s, -s),
        (s, s, -s),
        (-s, s, -s),
        (-s, -s, s),
        (s, -s, s),
        (s, s, s),
        (-s, s, s),
    ]
    for x, y, z in corners:
        mesh.add_vertex(x, y, z)
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (1, 2, 6, 5),
        (0, 4, 7, 3),
    ]
    for a, b, c, d in faces:
        mesh.add_quad(a, b, c, d)
    return mesh


def _seam_loop_between(
    a_index: tuple[int, int, int], b_index: tuple[int, int, int]
) -> tuple[Vec3, ...]:
    """Return the 4 corners of the square seam between two adjacent sub-cubes.

    The seam lies on the midplane orthogonal to the axis on which the two
    sub-cubes differ. Vertices are returned in CCW order when viewed from
    sub-cube ``a`` toward sub-cube ``b``.
    """
    diff = tuple(b - a for a, b in zip(a_index, b_index))
    nonzero = [i for i, d in enumerate(diff) if d != 0]
    if len(nonzero) != 1:
        raise ValueError(f"seam pieces must differ on exactly one axis, got {diff}")
    axis = nonzero[0]
    centre = [
        (-0.5 + (a + 0.5) * SUBCUBE_SIZE) for a in a_index
    ]
    centre[axis] += diff[axis] * HALF
    other_axes = [i for i in range(3) if i != axis]
    u, v = other_axes
    loop: list[Vec3] = []
    for du, dv in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        p = list(centre)
        p[u] += du * HALF
        p[v] += dv * HALF
        loop.append(Vec3(p[0], p[1], p[2]))
    return tuple(loop)


def generate_cube_8(out_dir: str | Path) -> PuzzleManifest:
    """Write the cube_8 bundle to ``out_dir`` and return the manifest.

    Bundle layout::

        out_dir/
            manifest.json
            pieces/
                c_000.obj
                c_001.obj
                ...
    """
    out = Path(out_dir)
    pieces_dir = out / "pieces"
    pieces_dir.mkdir(parents=True, exist_ok=True)
    subcube = _build_subcube_mesh()
    indices = list(product([0, 1], repeat=3))
    pieces: list[PieceSpec] = []
    for ix, iy, iz in indices:
        pid = _piece_id(ix, iy, iz)
        write_obj(subcube, pieces_dir / f"{pid}.obj", name=pid)
        cx = -0.5 + (ix + 0.5) * SUBCUBE_SIZE
        cy = -0.5 + (iy + 0.5) * SUBCUBE_SIZE
        cz = -0.5 + (iz + 0.5) * SUBCUBE_SIZE
        neighbour_axes: list[str] = []
        for axis, current in enumerate((ix, iy, iz)):
            other = 1 - current
            n_index = list((ix, iy, iz))
            n_index[axis] = other
            neighbour_axes.append(_piece_id(*n_index))
        pieces.append(
            PieceSpec(
                id=pid,
                mesh_path=f"pieces/{pid}.obj",
                target_pos=Vec3(cx, cy, cz),
                target_rot=Quat.identity(),
                neighbors=tuple(sorted(neighbour_axes)),
            )
        )
    seams: list[Seam] = []
    seen: set[tuple[str, str]] = set()
    for ix, iy, iz in indices:
        for axis in range(3):
            current = (ix, iy, iz)[axis]
            if current != 0:
                continue
            other_index = list((ix, iy, iz))
            other_index[axis] = 1
            a_id = _piece_id(ix, iy, iz)
            b_id = _piece_id(*other_index)
            key = tuple(sorted([a_id, b_id]))
            if key in seen:
                continue
            seen.add(key)
            loop = _seam_loop_between((ix, iy, iz), tuple(other_index))  # type: ignore[arg-type]
            seams.append(Seam.make(a_id, b_id, loop))
    starter = _piece_id(0, 0, 0)
    bounding_radius = (3 ** 0.5) * 0.5
    manifest = PuzzleManifest(
        id=PUZZLE_ID,
        display_name=DISPLAY_NAME,
        starter_piece_id=starter,
        pieces=pieces,
        seams=seams,
        bounding_radius=bounding_radius,
    )
    from ..manifest import write_manifest
    write_manifest(manifest, out / "manifest.json")
    return manifest
