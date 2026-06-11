"""Static validation of puzzle bundles.

Goes beyond :meth:`pipeline.manifest.PuzzleManifest.validate` (which only
checks schema-level consistency) and enforces the higher-level invariants
that make a manifest *playable* under decision D5 (see
``docs/GAME_PLAN.md``):

- **Reassemblability.** Because pieces snap strictly tray ↔ assembly,
  the only pieces a player can ever place are those reachable from the
  starter via the neighbour graph. An orphaned piece is unplaceable and
  the puzzle is unwinnable. The validator does a BFS from the starter
  and rejects manifests where any piece is unreached.
- **Seam loop sanity.** Every seam must have a vertex loop with at
  least 3 points (the finisher needs a polyline to build a ribbon
  along, and 2 collinear points define no shape).
- **Mesh existence.** Each piece's referenced mesh file is present on
  disk relative to the bundle directory.

Routing
-------
Operators invoke the validator either as a standalone CLI
(``python3 -m pipeline.cli validate <bundle>``) or implicitly via
``build``, which runs validation immediately after generation so a
broken bundle is never written without an error.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .manifest import PuzzleManifest, load_manifest


@dataclass
class ValidationReport:
    """Outcome of a validation pass.

    ``errors`` block release (the bundle is broken in a way that would
    make the puzzle unplayable). ``warnings`` are advisory.
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True iff no errors were reported."""
        return not self.errors

    def raise_if_errors(self) -> None:
        """Raise :class:`ValueError` aggregating all errors if any exist."""
        if self.errors:
            joined = "\n  - ".join(self.errors)
            raise ValueError(f"manifest failed validation:\n  - {joined}")


def _reachable_from_starter(manifest: PuzzleManifest) -> set[str]:
    """Return the set of piece IDs reachable from the starter via neighbours."""
    adjacency: dict[str, tuple[str, ...]] = {
        p.id: p.neighbors for p in manifest.pieces
    }
    visited: set[str] = set()
    queue: deque[str] = deque([manifest.starter_piece_id])
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        for neighbour in adjacency.get(current, ()):
            if neighbour not in visited:
                queue.append(neighbour)
    return visited


def _check_reassemblable(manifest: PuzzleManifest, report: ValidationReport) -> None:
    """Per D5: every piece must be reachable from the starter."""
    reached = _reachable_from_starter(manifest)
    unreached = sorted(p.id for p in manifest.pieces if p.id not in reached)
    if unreached:
        report.errors.append(
            f"{len(unreached)} piece(s) unreachable from starter "
            f"{manifest.starter_piece_id!r} via the neighbour graph "
            f"(per decision D5, the assembly must be a single connected "
            f"component anchored on the starter): {unreached}"
        )


def _check_seam_loops(manifest: PuzzleManifest, report: ValidationReport) -> None:
    """Every seam must have a usable vertex loop (>= 3 points)."""
    for seam in manifest.seams:
        if len(seam.vertex_loop) < 3:
            report.errors.append(
                f"seam {seam.piece_a!r}<->{seam.piece_b!r} has only "
                f"{len(seam.vertex_loop)} vertex/vertices; the finisher "
                f"needs at least 3 to build a ribbon"
            )


def _check_seam_coverage(manifest: PuzzleManifest, report: ValidationReport) -> None:
    """Every pair of adjacent pieces should have a corresponding seam.

    Demoted to a warning because some authoring tools may emit pieces
    that touch only at an edge or vertex and have no meaningful seam
    geometry, but for v1 puzzles we expect coverage to be complete.
    """
    seam_pairs = {(s.piece_a, s.piece_b) for s in manifest.seams}
    reported: set[tuple[str, str]] = set()
    for piece in manifest.pieces:
        for neighbour in piece.neighbors:
            key = tuple(sorted([piece.id, neighbour]))
            if key in seam_pairs or key in reported:
                continue
            reported.add(key)
            report.warnings.append(
                f"adjacent pieces {key[0]!r} and {key[1]!r} have no seam "
                f"in the manifest; the finisher will not draw a filler "
                f"ribbon between them"
            )


def _check_mesh_files(
    manifest: PuzzleManifest,
    bundle_dir: Path | None,
    report: ValidationReport,
) -> None:
    """If a bundle directory is supplied, verify each piece's mesh exists."""
    if bundle_dir is None:
        return
    for piece in manifest.pieces:
        mesh_path = bundle_dir / piece.mesh_path
        if not mesh_path.is_file():
            report.errors.append(
                f"piece {piece.id!r} references missing mesh file "
                f"{piece.mesh_path!r} (looked at {mesh_path})"
            )


def validate_manifest(
    manifest: PuzzleManifest,
    *,
    bundle_dir: Path | None = None,
) -> ValidationReport:
    """Run all higher-level checks against a manifest.

    ``bundle_dir`` is optional; if provided, mesh files referenced by the
    manifest are checked for existence relative to it. Schema-level
    validation (:meth:`PuzzleManifest.validate`) is run first; if it
    fails, that error is surfaced and no further checks are run because
    they would either be redundant or operate on an inconsistent
    manifest.
    """
    report = ValidationReport()
    try:
        manifest.validate()
    except ValueError as exc:
        report.errors.append(f"schema validation failed: {exc}")
        return report
    _check_reassemblable(manifest, report)
    _check_seam_loops(manifest, report)
    _check_seam_coverage(manifest, report)
    _check_mesh_files(manifest, bundle_dir, report)
    return report


def validate_bundle(bundle_dir: str | Path) -> ValidationReport:
    """Convenience: load + validate a bundle directory.

    Loads ``manifest.json`` from ``bundle_dir`` and runs
    :func:`validate_manifest` with mesh-file checks enabled.
    """
    bundle_path = Path(bundle_dir)
    manifest = load_manifest(bundle_path / "manifest.json")
    return validate_manifest(manifest, bundle_dir=bundle_path)


def format_report(report: ValidationReport) -> str:
    """Human-readable summary of a report (used by the CLI)."""
    lines: list[str] = []
    if report.errors:
        lines.append(f"{len(report.errors)} error(s):")
        for err in report.errors:
            lines.append(f"  - {err}")
    if report.warnings:
        lines.append(f"{len(report.warnings)} warning(s):")
        for warn in report.warnings:
            lines.append(f"  - {warn}")
    if not lines:
        lines.append("OK")
    return "\n".join(lines)


__all__ = [
    "ValidationReport",
    "format_report",
    "validate_bundle",
    "validate_manifest",
]
