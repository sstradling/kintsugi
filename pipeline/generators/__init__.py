"""Procedural puzzle generators.

These produce the same on-disk format as a real Blender exporter would,
so the runtime loader is exercised end-to-end before any artist content
exists. Today's generators are :func:`generate_cube_8` and
:func:`generate_sphere_8_slices`; the brief calls them out by name as
the two starter puzzles.
"""

from __future__ import annotations

from .cube_8 import generate_cube_8
from .sphere_8_slices import generate_sphere_8_slices

__all__ = ["generate_cube_8", "generate_sphere_8_slices"]
