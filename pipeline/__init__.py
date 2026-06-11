"""Kintsugi puzzle authoring pipeline.

Produces puzzle bundles (per-piece meshes + a manifest) that the Unity
runtime loads. The pipeline is intentionally engine-agnostic and emits
plain OBJ + JSON so the same bundles can be inspected, diffed, and
unit-tested without Unity in the loop.

The two implementations available today are:

- Procedural generators (`pipeline.generators.*`) - used to produce the
  ``cube_8`` and ``sphere_8_slices`` starter puzzles needed for runtime
  bring-up before any artist content exists.
- (planned) A Blender exporter that wraps the Cell Fracture add-on and
  emits the same manifest format. Not implemented in this environment
  because Blender is not available; the schema is fixed so the exporter
  will be a drop-in producer.
"""

__version__ = "0.1.0"
