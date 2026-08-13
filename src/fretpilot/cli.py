"""Command-line interface for FretPilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from fretpilot import __version__
from fretpilot.guitar import optimize_fingering
from fretpilot.midi import load_midi
from fretpilot.midi.models import NormalizedTimeline, NormalizedTrack
from fretpilot.rhythm import analyze_track_rhythm


def _add_json_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write JSON to a file instead of stdout",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of pretty-printed JSON",
    )


def _add_track_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--track",
        type=int,
        help="Zero-based MIDI track index. Defaults to the first track containing notes.",
    )


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
    _add_json_output_arguments(inspect_parser)

    rhythm_parser = subparsers.add_parser(
        "rhythm",
        help="Analyze likely notation grids and propose repaired note-on positions",
    )
    rhythm_parser.add_argument("midi_file", type=Path, help="Path to a .mid/.midi file")
    _add_track_argument(rhythm_parser)
    _add_json_output_arguments(rhythm_parser)

    fingering_parser = subparsers.add_parser(
        "fingering",
        help="Assign playable guitar string/fret positions across a phrase",
    )
    fingering_parser.add_argument("midi_file", type=Path, help="Path to a .mid/.midi file")
    _add_track_argument(fingering_parser)
    fingering_parser.add_argument(
        "--max-fret",
        type=int,
        default=24,
        help="Highest allowed fret (default: 24)",
    )
    _add_json_output_arguments(fingering_parser)

    return parser


def _emit_json(data: dict[str, Any], output: Path | None, compact: bool) -> None:
    payload = json.dumps(
        data,
        ensure_ascii=False,
        indent=None if compact else 2,
        sort_keys=False,
    )

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


def _select_track(timeline: NormalizedTimeline, track_index: int | None) -> NormalizedTrack:
    if track_index is None:
        track = next((candidate for candidate in timeline.tracks if candidate.notes), None)
        if track is None:
            raise SystemExit("No MIDI track containing notes was found.")
        return track

    if track_index < 0 or track_index >= len(timeline.tracks):
        raise SystemExit(
            f"Track index {track_index} is out of range; "
            f"file contains {len(timeline.tracks)} tracks."
        )

    track = timeline.tracks[track_index]
    if not track.notes:
        raise SystemExit(f"Track {track_index} ({track.name}) contains no notes.")
    return track


def _run_inspect(args: argparse.Namespace) -> int:
    timeline = load_midi(args.midi_file)
    _emit_json(timeline.to_dict(), args.output, args.compact)
    return 0


def _run_rhythm(args: argparse.Namespace) -> int:
    timeline = load_midi(args.midi_file)
    track = _select_track(timeline, args.track)
    analysis = analyze_track_rhythm(track)
    _emit_json(analysis.to_dict(), args.output, args.compact)
    return 0


def _run_fingering(args: argparse.Namespace) -> int:
    if args.max_fret < 0:
        raise SystemExit("--max-fret must be zero or greater.")

    timeline = load_midi(args.midi_file)
    track = _select_track(timeline, args.track)
    result = optimize_fingering(track, max_fret=args.max_fret)
    _emit_json(result.to_dict(), args.output, args.compact)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        return _run_inspect(args)
    if args.command == "rhythm":
        return _run_rhythm(args)
    if args.command == "fingering":
        return _run_fingering(args)

    parser.error(f"Unknown command: {args.command}")
    return 2
