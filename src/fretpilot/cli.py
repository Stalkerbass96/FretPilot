"""Command-line interface for FretPilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from fretpilot import __version__
from fretpilot.analysis import analyze_guitar_track
from fretpilot.detection import classify_timeline, resolve_instrument_streams
from fretpilot.exporters.ample_guitar import export_ample_sc_midi
from fretpilot.exporters.guitar_pro import UnsupportedGuitarIR, export_gp5
from fretpilot.guitar import optimize_fingering
from fretpilot.ir import build_guitar_ir
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


def _add_source_selector(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--stream-id",
        help=(
            "Logical InstrumentStream ID returned by `fretpilot tracks`, "
            "for example t0:ch2:p27."
        ),
    )
    group.add_argument(
        "--track",
        type=int,
        help="Legacy zero-based physical MIDI track index.",
    )


def _add_max_fret_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--max-fret",
        type=int,
        default=24,
        help="Highest allowed fret (default: 24)",
    )


def _add_file_export_arguments(
    parser: argparse.ArgumentParser,
    *,
    help_text: str,
) -> None:
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help=help_text,
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit a compact JSON export report",
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

    tracks_parser = subparsers.add_parser(
        "tracks",
        help="Resolve instrument streams and rank guitar candidates using layered evidence",
    )
    tracks_parser.add_argument("midi_file", type=Path, help="Path to a .mid/.midi file")
    _add_json_output_arguments(tracks_parser)

    rhythm_parser = subparsers.add_parser(
        "rhythm",
        help="Analyze likely notation grids and propose repaired note-on positions",
    )
    rhythm_parser.add_argument("midi_file", type=Path, help="Path to a .mid/.midi file")
    _add_source_selector(rhythm_parser)
    _add_json_output_arguments(rhythm_parser)

    fingering_parser = subparsers.add_parser(
        "fingering",
        help="Assign playable guitar string/fret positions across a phrase",
    )
    fingering_parser.add_argument("midi_file", type=Path, help="Path to a .mid/.midi file")
    _add_source_selector(fingering_parser)
    _add_max_fret_argument(fingering_parser)
    _add_json_output_arguments(fingering_parser)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run rhythm, fingering, and articulation analysis on a guitar stream",
    )
    analyze_parser.add_argument("midi_file", type=Path, help="Path to a .mid/.midi file")
    _add_source_selector(analyze_parser)
    _add_max_fret_argument(analyze_parser)
    _add_json_output_arguments(analyze_parser)

    ir_parser = subparsers.add_parser(
        "build-ir",
        help="Build measure-aware canonical Guitar IR for a selected guitar stream",
    )
    ir_parser.add_argument("midi_file", type=Path, help="Path to a .mid/.midi file")
    _add_source_selector(ir_parser)
    _add_max_fret_argument(ir_parser)
    _add_json_output_arguments(ir_parser)

    gp5_parser = subparsers.add_parser(
        "export-gp5",
        help="Build Guitar IR and export the supported subset as Guitar Pro 5.1",
    )
    gp5_parser.add_argument("midi_file", type=Path, help="Path to a .mid/.midi file")
    _add_source_selector(gp5_parser)
    _add_max_fret_argument(gp5_parser)
    _add_file_export_arguments(gp5_parser, help_text="Destination .gp5 file")

    ample_parser = subparsers.add_parser(
        "export-ample-sc",
        help="Build Guitar IR and render performance MIDI for Ample Guitar SC 4.x",
    )
    ample_parser.add_argument("midi_file", type=Path, help="Path to a .mid/.midi file")
    _add_source_selector(ample_parser)
    _add_max_fret_argument(ample_parser)
    _add_file_export_arguments(
        ample_parser,
        help_text="Destination Ample Guitar performance .mid file",
    )

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


def _select_analysis_source(
    timeline: NormalizedTimeline,
    *,
    track_index: int | None,
    stream_id: str | None,
) -> tuple[NormalizedTrack, str | None]:
    if stream_id is not None:
        streams = resolve_instrument_streams(timeline)
        stream = next(
            (candidate for candidate in streams if candidate.stream_id == stream_id),
            None,
        )
        if stream is None:
            available = ", ".join(candidate.stream_id for candidate in streams)
            raise SystemExit(
                f"Unknown stream ID {stream_id!r}. Available streams: {available or 'none'}."
            )
        return stream.as_track(), stream.stream_id

    if track_index is not None:
        if track_index < 0 or track_index >= len(timeline.tracks):
            raise SystemExit(
                f"Track index {track_index} is out of range; "
                f"file contains {len(timeline.tracks)} physical tracks."
            )
        track = timeline.tracks[track_index]
        if not track.notes:
            raise SystemExit(f"Track {track_index} ({track.name}) contains no notes.")
        return track, None

    report = classify_timeline(timeline)
    likely = [
        candidate
        for candidate in report.candidates
        if candidate.decision == "likely_guitar"
    ]
    if len(likely) == 1:
        candidate = likely[0]
        return candidate.stream.as_track(), candidate.stream.stream_id
    if not likely:
        raise SystemExit(
            "No high-confidence guitar stream was found. Run `fretpilot tracks` "
            "and select a candidate with --stream-id."
        )

    options = ", ".join(candidate.stream.stream_id for candidate in likely)
    raise SystemExit(
        "Multiple likely guitar streams were found. Run `fretpilot tracks` and "
        f"choose one with --stream-id. Candidates: {options}."
    )


def _validate_max_fret(max_fret: int) -> None:
    if max_fret < 0:
        raise SystemExit("--max-fret must be zero or greater.")


def _build_project(args: argparse.Namespace):
    _validate_max_fret(args.max_fret)
    timeline = load_midi(args.midi_file)
    track, stream_id = _select_analysis_source(
        timeline,
        track_index=args.track,
        stream_id=args.stream_id,
    )
    analysis = analyze_guitar_track(track, max_fret=args.max_fret)
    project = build_guitar_ir(
        timeline,
        track,
        analysis,
        source_stream_id=stream_id,
    )
    return project


def _run_inspect(args: argparse.Namespace) -> int:
    timeline = load_midi(args.midi_file)
    _emit_json(timeline.to_dict(), args.output, args.compact)
    return 0


def _run_tracks(args: argparse.Namespace) -> int:
    timeline = load_midi(args.midi_file)
    report = classify_timeline(timeline)
    _emit_json(report.to_dict(), args.output, args.compact)
    return 0


def _run_rhythm(args: argparse.Namespace) -> int:
    timeline = load_midi(args.midi_file)
    track, _stream_id = _select_analysis_source(
        timeline,
        track_index=args.track,
        stream_id=args.stream_id,
    )
    analysis = analyze_track_rhythm(track)
    _emit_json(analysis.to_dict(), args.output, args.compact)
    return 0


def _run_fingering(args: argparse.Namespace) -> int:
    _validate_max_fret(args.max_fret)
    timeline = load_midi(args.midi_file)
    track, _stream_id = _select_analysis_source(
        timeline,
        track_index=args.track,
        stream_id=args.stream_id,
    )
    result = optimize_fingering(track, max_fret=args.max_fret)
    _emit_json(result.to_dict(), args.output, args.compact)
    return 0


def _run_analyze(args: argparse.Namespace) -> int:
    _validate_max_fret(args.max_fret)
    timeline = load_midi(args.midi_file)
    track, _stream_id = _select_analysis_source(
        timeline,
        track_index=args.track,
        stream_id=args.stream_id,
    )
    result = analyze_guitar_track(track, max_fret=args.max_fret)
    _emit_json(result.to_dict(), args.output, args.compact)
    return 0


def _run_build_ir(args: argparse.Namespace) -> int:
    project = _build_project(args)
    _emit_json(project.to_dict(), args.output, args.compact)
    return 0


def _run_export_gp5(args: argparse.Namespace) -> int:
    project = _build_project(args)
    try:
        result = export_gp5(project, args.output)
    except UnsupportedGuitarIR as exc:
        raise SystemExit(f"GP5 export is not supported for this stream: {exc}") from exc
    _emit_json(result.to_dict(), None, args.compact)
    return 0


def _run_export_ample_sc(args: argparse.Namespace) -> int:
    project = _build_project(args)
    result = export_ample_sc_midi(project, args.output)
    _emit_json(result.to_dict(), None, args.compact)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        return _run_inspect(args)
    if args.command == "tracks":
        return _run_tracks(args)
    if args.command == "rhythm":
        return _run_rhythm(args)
    if args.command == "fingering":
        return _run_fingering(args)
    if args.command == "analyze":
        return _run_analyze(args)
    if args.command == "build-ir":
        return _run_build_ir(args)
    if args.command == "export-gp5":
        return _run_export_gp5(args)
    if args.command == "export-ample-sc":
        return _run_export_ample_sc(args)

    parser.error(f"Unknown command: {args.command}")
    return 2
