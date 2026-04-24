"""Pipeline CLI.

Usage::

    python -m pipeline.cli build cube_8 --out build/cube_8
    python -m pipeline.cli build sphere_8_slices --out build/sphere_8_slices
    python -m pipeline.cli build all --out build/

User actions are routed here:

    Operator -> ``python -m pipeline.cli build <id>``
        -> :func:`pipeline.generators.<id>.generate_*`
        -> writes ``manifest.json`` + ``pieces/*.obj`` into the bundle dir.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .generators import generate_cube_8, generate_sphere_8_slices

GENERATORS = {
    "cube_8": generate_cube_8,
    "sphere_8_slices": generate_sphere_8_slices,
}


def _cmd_build(args: argparse.Namespace) -> int:
    targets = list(GENERATORS) if args.puzzle == "all" else [args.puzzle]
    out_root = Path(args.out)
    for puzzle_id in targets:
        bundle_dir = out_root if args.puzzle != "all" else out_root / puzzle_id
        manifest = GENERATORS[puzzle_id](bundle_dir)
        print(
            f"built {manifest.id}: {len(manifest.pieces)} pieces, "
            f"{len(manifest.seams)} seams -> {bundle_dir}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kintsugi-pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build", help="generate a starter puzzle bundle")
    build.add_argument("puzzle", choices=[*GENERATORS, "all"])
    build.add_argument("--out", required=True, help="output bundle directory")
    build.set_defaults(func=_cmd_build)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
