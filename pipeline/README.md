# Kintsugi puzzle pipeline

Authoring pipeline that produces puzzle bundles consumable by the
runtime. Bundles are engine-agnostic: a manifest in JSON plus per-piece
Wavefront OBJ meshes.

## Bundle layout

```
<bundle>/
    manifest.json
    pieces/
        <piece_id>.obj
        ...
```

The manifest schema is defined in [`pipeline/manifest.py`](pipeline/manifest.py)
and validated on every read and write. See `SCHEMA_VERSION` for the
current contract version; bumps are breaking changes.

## Available generators

- `cube_8` — unit cube fractured into a 2×2×2 grid of sub-cubes.
- `sphere_8_slices` — unit sphere sliced into 8 parallel sheets along Y.

A Blender exporter that produces the same bundle format is planned but
not yet implemented (Blender is not available in this environment).

## Build a bundle

```bash
python3 -m pipeline.cli build cube_8 --out build/cube_8
python3 -m pipeline.cli build sphere_8_slices --out build/sphere_8_slices
python3 -m pipeline.cli build all --out build/
```

## Tests

```bash
python3 -m pytest tests/pipeline
```

Tests cover the manifest schema (round-trip, validation), each
generator's structural invariants (piece counts, neighbour graph, seam
shapes, mesh extents), and an integration test that exercises the CLI.
