"""Minimal Wavefront OBJ writer.

We deliberately ship a tiny in-tree writer instead of pulling in
``trimesh`` or similar. The pipeline only needs to emit triangle meshes
with no materials, and OBJ is the simplest format that every DCC tool
and game engine on the planet imports without ceremony.

Each piece's mesh is written into its own OBJ file inside the bundle
so the runtime can stream them independently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence


@dataclass
class TriMesh:
    """A simple indexed triangle mesh.

    Vertices are 1-indexed when written to OBJ (per spec) but stored
    here 0-indexed for ergonomics.
    """

    vertices: list[tuple[float, float, float]] = field(default_factory=list)
    triangles: list[tuple[int, int, int]] = field(default_factory=list)

    def add_vertex(self, x: float, y: float, z: float) -> int:
        """Append a vertex and return its 0-based index."""
        self.vertices.append((float(x), float(y), float(z)))
        return len(self.vertices) - 1

    def add_triangle(self, a: int, b: int, c: int) -> None:
        """Append a triangle by 0-based vertex indices."""
        n = len(self.vertices)
        for i in (a, b, c):
            if not 0 <= i < n:
                raise IndexError(f"triangle index {i} out of range (vertices={n})")
        self.triangles.append((a, b, c))

    def add_quad(self, a: int, b: int, c: int, d: int) -> None:
        """Append a quad as two triangles, preserving winding order."""
        self.add_triangle(a, b, c)
        self.add_triangle(a, c, d)

    def extend(self, other: "TriMesh") -> None:
        """Concatenate another mesh into this one."""
        offset = len(self.vertices)
        self.vertices.extend(other.vertices)
        self.triangles.extend(
            (a + offset, b + offset, c + offset) for a, b, c in other.triangles
        )


def write_obj(mesh: TriMesh, path: str | Path, *, name: str | None = None) -> None:
    """Write a triangle mesh to a Wavefront OBJ file.

    Includes a single ``o`` group named after the file stem (or
    ``name`` if supplied). No normals or UVs are emitted; those are
    expected to be authored downstream in the engine for puzzle pieces,
    where the seam direction matters for the finisher shader.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    obj_name = name or out.stem
    with out.open("w", encoding="utf-8") as fh:
        fh.write(f"# kintsugi pipeline - {obj_name}\n")
        fh.write(f"o {obj_name}\n")
        for x, y, z in mesh.vertices:
            fh.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
        for a, b, c in mesh.triangles:
            fh.write(f"f {a + 1} {b + 1} {c + 1}\n")


def read_obj(path: str | Path) -> TriMesh:
    """Read a Wavefront OBJ file produced by :func:`write_obj`.

    Tolerates only the subset we emit (``v`` and ``f`` lines, triangle
    faces with no slashes). Used by the unit tests to round-trip.
    """
    mesh = TriMesh()
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("o "):
            continue
        if line.startswith("v "):
            _, sx, sy, sz = line.split()
            mesh.vertices.append((float(sx), float(sy), float(sz)))
        elif line.startswith("f "):
            tokens = line.split()[1:]
            if len(tokens) != 3:
                raise ValueError(f"only triangle faces supported, got {len(tokens)}")
            indices = tuple(int(t.split("/")[0]) - 1 for t in tokens)
            mesh.triangles.append(indices)  # type: ignore[arg-type]
    return mesh
