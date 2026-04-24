"""Puzzle manifest schema.

The manifest is the contract between the authoring pipeline and the
runtime. It is deliberately small, JSON-serialisable, and engine-agnostic
so that:

- A Blender exporter, a procedural generator, and a hand-authored test
  fixture can all produce the same shape.
- The Unity runtime loader has a single code path regardless of source.
- Diffing two puzzles is a textual diff.

All coordinates are expressed in **assembly local space** (the assembly's
own coordinate frame, not world space). Quaternions are stored as
``(x, y, z, w)``.

Routing notes
-------------
A user opening a puzzle from the catalog triggers
``Catalog -> AssetLoader.load(puzzle_id)`` which fetches the bundle
directory, parses ``manifest.json`` via :func:`load_manifest`, and hands
the resulting :class:`PuzzleManifest` to the runtime ``AssemblyController``.
The controller uses each :class:`PieceSpec` to instantiate a piece prefab,
parents the starter piece to the assembly root, and keeps the rest in
the tray until snapped.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Iterable, Sequence
import json
import math
from pathlib import Path

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Vec3:
    """3D point or vector in assembly local space."""

    x: float
    y: float
    z: float

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.z]

    @staticmethod
    def from_list(values: Sequence[float]) -> "Vec3":
        if len(values) != 3:
            raise ValueError(f"Vec3 expects 3 components, got {len(values)}")
        return Vec3(float(values[0]), float(values[1]), float(values[2]))


@dataclass(frozen=True)
class Quat:
    """Unit quaternion stored as (x, y, z, w).

    The pipeline does not normalise on construction. Use :meth:`normalised`
    when you need to guarantee unit length.
    """

    x: float
    y: float
    z: float
    w: float

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.z, self.w]

    @staticmethod
    def identity() -> "Quat":
        return Quat(0.0, 0.0, 0.0, 1.0)

    @staticmethod
    def from_list(values: Sequence[float]) -> "Quat":
        if len(values) != 4:
            raise ValueError(f"Quat expects 4 components, got {len(values)}")
        return Quat(
            float(values[0]),
            float(values[1]),
            float(values[2]),
            float(values[3]),
        )

    def normalised(self) -> "Quat":
        n = math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w)
        if n == 0.0:
            return Quat.identity()
        return Quat(self.x / n, self.y / n, self.z / n, self.w / n)


@dataclass(frozen=True)
class Seam:
    """A shared edge loop between two adjacent shards.

    Used by the finisher to generate the strip of geometry that filler
    materials are rendered along. The vertex loop is stored as a list of
    points in assembly local space; the runtime is responsible for
    generating a ribbon mesh from it at finish time.

    ``piece_a`` and ``piece_b`` are piece IDs and are stored in
    lexicographic order so seams are canonicalised.
    """

    piece_a: str
    piece_b: str
    vertex_loop: tuple[Vec3, ...]

    def __post_init__(self) -> None:
        if self.piece_a >= self.piece_b:
            raise ValueError(
                f"Seam piece IDs must be lexicographically ordered "
                f"(got {self.piece_a!r}, {self.piece_b!r})"
            )

    @staticmethod
    def make(piece_a: str, piece_b: str, vertex_loop: Iterable[Vec3]) -> "Seam":
        a, b = sorted([piece_a, piece_b])
        return Seam(a, b, tuple(vertex_loop))


@dataclass
class PieceSpec:
    """Metadata for a single shard.

    ``mesh_path`` is relative to the bundle directory. ``target_pos`` and
    ``target_rot`` describe the piece's pose **inside the assembly local
    frame** (i.e. the pose at which it is considered "snapped"). The
    ``neighbors`` list is the adjacency graph used both for the seam
    generator and for runtime hint logic.
    """

    id: str
    mesh_path: str
    target_pos: Vec3
    target_rot: Quat = field(default_factory=Quat.identity)
    neighbors: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class PuzzleManifest:
    """Top-level puzzle bundle descriptor.

    ``starter_piece_id`` identifies the piece that is anchored to the
    assembly root at puzzle start (the player cannot move it; everything
    else snaps relative to it).

    ``bounding_radius`` is the radius of the assembly's bounding sphere
    in local-space units; it is used by the runtime to compute the
    snap-distance tolerance per decision D1 (default 1.5% of this value).
    """

    id: str
    display_name: str
    starter_piece_id: str
    pieces: list[PieceSpec]
    seams: list[Seam]
    bounding_radius: float
    schema_version: int = SCHEMA_VERSION

    def piece_ids(self) -> set[str]:
        return {p.id for p in self.pieces}

    def validate(self) -> None:
        """Raise :class:`ValueError` if the manifest is internally inconsistent.

        Checks performed:

        - Piece IDs are unique.
        - ``starter_piece_id`` references a real piece.
        - All ``neighbors`` and seam endpoints reference real pieces.
        - Adjacency is symmetric (if A lists B, B lists A).
        - ``bounding_radius`` is positive.
        - ``schema_version`` matches the version this loader understands.
        - Piece count is within the supported range (see decision D3,
          1..200 enforced as a hard upper bound here; the design target
          is 8-60).
        """
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"manifest schema_version {self.schema_version} does not "
                f"match loader version {SCHEMA_VERSION}"
            )
        if self.bounding_radius <= 0:
            raise ValueError(f"bounding_radius must be > 0, got {self.bounding_radius}")
        if not self.pieces:
            raise ValueError("manifest must contain at least one piece")
        if len(self.pieces) > 200:
            raise ValueError(
                f"manifest contains {len(self.pieces)} pieces; the runtime hard "
                f"limit is 200 (design target 8-60, see decision D3)"
            )
        ids = self.piece_ids()
        if len(ids) != len(self.pieces):
            raise ValueError("piece IDs must be unique")
        if self.starter_piece_id not in ids:
            raise ValueError(
                f"starter_piece_id {self.starter_piece_id!r} not present in pieces"
            )
        adjacency: dict[str, set[str]] = {p.id: set(p.neighbors) for p in self.pieces}
        for piece_id, neighbors in adjacency.items():
            for n in neighbors:
                if n not in ids:
                    raise ValueError(
                        f"piece {piece_id!r} lists unknown neighbor {n!r}"
                    )
                if piece_id not in adjacency[n]:
                    raise ValueError(
                        f"adjacency not symmetric: {piece_id!r} -> {n!r} but "
                        f"not {n!r} -> {piece_id!r}"
                    )
        for seam in self.seams:
            if seam.piece_a not in ids or seam.piece_b not in ids:
                raise ValueError(
                    f"seam references unknown piece(s): {seam.piece_a!r}, {seam.piece_b!r}"
                )
            if seam.piece_b not in adjacency[seam.piece_a]:
                raise ValueError(
                    f"seam {seam.piece_a!r}<->{seam.piece_b!r} present but pieces "
                    f"are not listed as neighbors"
                )

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "display_name": self.display_name,
            "starter_piece_id": self.starter_piece_id,
            "bounding_radius": self.bounding_radius,
            "pieces": [
                {
                    "id": p.id,
                    "mesh_path": p.mesh_path,
                    "target_pos": p.target_pos.to_list(),
                    "target_rot": p.target_rot.to_list(),
                    "neighbors": list(p.neighbors),
                }
                for p in self.pieces
            ],
            "seams": [
                {
                    "piece_a": s.piece_a,
                    "piece_b": s.piece_b,
                    "vertex_loop": [v.to_list() for v in s.vertex_loop],
                }
                for s in self.seams
            ],
        }

    @staticmethod
    def from_dict(data: dict) -> "PuzzleManifest":
        pieces = [
            PieceSpec(
                id=p["id"],
                mesh_path=p["mesh_path"],
                target_pos=Vec3.from_list(p["target_pos"]),
                target_rot=Quat.from_list(p.get("target_rot", [0.0, 0.0, 0.0, 1.0])),
                neighbors=tuple(p.get("neighbors", [])),
            )
            for p in data["pieces"]
        ]
        seams = [
            Seam(
                piece_a=s["piece_a"],
                piece_b=s["piece_b"],
                vertex_loop=tuple(Vec3.from_list(v) for v in s["vertex_loop"]),
            )
            for s in data.get("seams", [])
        ]
        return PuzzleManifest(
            id=data["id"],
            display_name=data["display_name"],
            starter_piece_id=data["starter_piece_id"],
            pieces=pieces,
            seams=seams,
            bounding_radius=float(data["bounding_radius"]),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
        )


def load_manifest(path: str | Path) -> PuzzleManifest:
    """Load a manifest from disk and validate it.

    Raises :class:`ValueError` for schema violations and the usual file
    errors for I/O problems.
    """
    text = Path(path).read_text(encoding="utf-8")
    manifest = PuzzleManifest.from_dict(json.loads(text))
    manifest.validate()
    return manifest


def write_manifest(manifest: PuzzleManifest, path: str | Path) -> None:
    """Serialise a manifest to disk as pretty-printed JSON.

    Validates first so we never write a broken bundle.
    """
    manifest.validate()
    Path(path).write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
