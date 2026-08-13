"""Command-line interface for FretPilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from fretpilot import __version__
from fretpilot.midi import load_midi


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fretpilot",
        description="FretPilot MIDI-to-guitar processing toolkit",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Parse a MIDI file and emit FretPilot's normalized timeline as JSON",
    )
    inspect_parser.add_argument("midi_file", type=Path, help="Path to a .mid/.midi file")
    inspect_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write JSON to a file instead of stdout",
    )
    inspect_parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of pretty-printed JSON",
    )

    return parser


def _run_inspect(args: argparse.Namespace) -> int:
    timeline = load_midi(args.midi_file)
    indent = None if args.compact else 2
    payload = json.dumps(
        timeline.to_dict(),
        ensure_ascii=False,
        indent=indent,
        sort_keys=False,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        return _run_inspect(args)

    parser.error(f"Unknown command: {args.command}")
    return 2
