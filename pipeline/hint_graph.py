"""Build-time hint-order generator.

Per decision D6 (see ``docs/GAME_PLAN.md``) the runtime only ever gives
the player a *limited* number of hints, with additional hints gated
behind monetization (cosmetic IAP and rewarded interstitials). This
module owns the **what** of hinting — given a manifest, in what order
should pieces be revealed? — and is independent of the **when** (the
metering layer, owned by `Kintsugi.Monetization` on the runtime side).

Algorithm
---------
:func:`compute_hint_order` performs a constraint-aware BFS from the
starter piece. The sort key for each candidate is, in order:

1. **BFS depth from the starter** (smaller is better). This gives a
   visually fair, symmetric expansion outward and avoids "jumping" to
   distant well-constrained pieces while close pieces remain unplaced.
2. **Negative count of already-placed neighbours** (more is better).
   Among candidates at the same BFS depth, the most-constrained piece
   is the most informative hint because the player has the largest
   visual context to snap it into.
3. **Piece-id lexicographic order** for determinism across runs.

If the frontier ever empties before all pieces are placed (which should
be impossible for a manifest that passes the D5 reassemblability check
in :mod:`pipeline.validator`), the remaining pieces are appended in
lexicographic order so this function never crashes on a malformed
manifest. The validator is the one responsible for flagging that case.

The returned order **excludes the starter piece** because it is
pre-placed at puzzle start.

Why bake into the manifest
--------------------------
- Deterministic across devices.
- Zero runtime CPU cost.
- Reviewable in a JSON diff (an artist can hand-tune the order for a
  specific puzzle by editing the manifest).
"""

from __future__ import annotations

from collections import deque

from .manifest import PuzzleManifest


def _bfs_depths(
    adjacency: dict[str, set[str]], start: str
) -> dict[str, int]:
    """Return depth (in neighbour-hops) from ``start`` to each reachable piece.

    Unreachable pieces are not present in the returned dict.
    """
    depths: dict[str, int] = {start: 0}
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        d = depths[current]
        for neighbour in adjacency.get(current, ()):
            if neighbour not in depths:
                depths[neighbour] = d + 1
                queue.append(neighbour)
    return depths


def compute_hint_order(manifest: PuzzleManifest) -> tuple[str, ...]:
    """Return the recommended placement order for non-starter pieces.

    See module docstring for algorithm and tie-breaking rules. The
    returned tuple is suitable for assignment to
    :attr:`PuzzleManifest.hint_order`.
    """
    adjacency: dict[str, set[str]] = {
        p.id: set(p.neighbors) for p in manifest.pieces
    }
    all_ids: set[str] = set(adjacency)
    starter = manifest.starter_piece_id
    if starter not in all_ids:
        raise ValueError(
            f"starter piece {starter!r} not present in manifest pieces"
        )
    depths = _bfs_depths(adjacency, starter)
    placed: set[str] = {starter}
    remaining: set[str] = all_ids - placed
    order: list[str] = []
    while remaining:
        candidates = [pid for pid in remaining if adjacency[pid] & placed]
        if not candidates:
            for pid in sorted(remaining):
                order.append(pid)
            return tuple(order)
        unreached_depth = max(depths.values(), default=0) + 1
        candidates.sort(
            key=lambda pid: (
                depths.get(pid, unreached_depth),
                -len(adjacency[pid] & placed),
                pid,
            )
        )
        chosen = candidates[0]
        order.append(chosen)
        placed.add(chosen)
        remaining.discard(chosen)
    return tuple(order)


__all__ = ["compute_hint_order"]
