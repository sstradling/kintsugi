"""Pipeline CLI.

Usage::

    python3 -m pipeline.cli build cube_8 --out build/cube_8
    python3 -m pipeline.cli build sphere_8_slices --out build/sphere_8_slices
    python3 -m pipeline.cli build all --out build/
    python3 -m pipeline.cli validate build/cube_8

User actions are routed here:

    Operator -> ``python3 -m pipeline.cli build <id>``
        -> :func:`pipeline.generators.<id>.generate_*`
        -> writes ``manifest.json`` + ``pieces/*.obj`` into the bundle dir
        -> :func:`pipeline.validator.validate_bundle` is run automatically
           and any errors abort the build.

    Operator -> ``python3 -m pipeline.cli validate <bundle>``
        -> :func:`pipeline.validator.validate_bundle`
        -> prints a human-readable report and exits non-zero on errors.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .generators import generate_cube_8, generate_sphere_8_slices
from .validator import format_report, validate_bundle

GENERATORS = {
    "cube_8": generate_cube_8,
    "sphere_8_slices": generate_sphere_8_slices,
}


def _cmd_build(args: argparse.Namespace) -> int:
    targets = list(GENERATORS) if args.puzzle == "all" else [args.puzzle]
    out_root = Path(args.out)
    failed: list[str] = []
    for puzzle_id in targets:
        bundle_dir = out_root if args.puzzle != "all" else out_root / puzzle_id
        manifest = GENERATORS[puzzle_id](bundle_dir)
        print(
            f"built {manifest.id}: {len(manifest.pieces)} pieces, "
            f"{len(manifest.seams)} seams -> {bundle_dir}"
        )
        if args.skip_validate:
            continue
        report = validate_bundle(bundle_dir)
        if not report.ok:
            failed.append(puzzle_id)
            print(f"validation FAILED for {puzzle_id}:", file=sys.stderr)
            print(format_report(report), file=sys.stderr)
        elif report.warnings:
            print(format_report(report))
    return 1 if failed else 0


def _cmd_validate(args: argparse.Namespace) -> int:
    report = validate_bundle(args.bundle)
    print(format_report(report))
    return 0 if report.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kintsugi-pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    build = sub.add_parser("build", help="generate a starter puzzle bundle")
    build.add_argument("puzzle", choices=[*GENERATORS, "all"])
    build.add_argument("--out", required=True, help="output bundle directory")
    build.add_argument(
        "--skip-validate",
        action="store_true",
        help="skip post-build validation (useful for debugging generators)",
    )
    build.set_defaults(func=_cmd_build)

    validate = sub.add_parser("validate", help="validate an existing bundle")
    validate.add_argument("bundle", help="bundle directory to validate")
    validate.set_defaults(func=_cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
