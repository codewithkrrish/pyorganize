"""Command-line interface for pyorganize."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .organizer import UNDO_FILENAME, apply_moves, load_rules, plan_moves, undo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyorganize",
        description="Auto-organize a messy folder by file type. Zero dependencies.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Folder to organize (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would move without moving anything",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Restore the last organize operation",
    )
    parser.add_argument(
        "--rules",
        metavar="PATH",
        help="JSON file with custom category -> extensions rules",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Include files inside subfolders",
    )
    parser.add_argument(
        "--by",
        choices=["type", "date"],
        default="type",
        help="Organize by file type (default) or by modified date (YYYY-MM)",
    )
    parser.add_argument("--version", action="version", version="pyorganize 1.0.0")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    directory = Path(args.directory).expanduser()

    if args.undo:
        try:
            restored = undo(directory)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Restored {restored} file(s).")
        return 0

    try:
        rules = load_rules(args.rules)
        moves = plan_moves(directory, rules, recursive=args.recursive, by=args.by)
    except (NotADirectoryError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not moves:
        print("Nothing to organize — folder is already tidy.")
        return 0

    if args.dry_run:
        print(f"Would move {len(moves)} file(s):\n")
        for move in moves:
            print(f"  {move.src.name}  ->  {move.dest.parent.name}/")
        return 0

    apply_moves(moves, directory)
    print(f"Organized {len(moves)} file(s) in {directory.resolve()}")
    print(f"Undo anytime: pyorganize --undo   (log: {UNDO_FILENAME})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
