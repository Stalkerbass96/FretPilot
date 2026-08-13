"""Standalone CLI for rendering a selected guitar stream as PDF TAB."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from fretpilot.analysis import analyze_guitar_track
from fretpilot.detection import classify_timeline, resolve_instrument_streams
from fretpilot.exporters.pdf_score import export_score_pdf
from fretpilot.ir import build_guitar_ir
from fretpilot.midi import load_midi
from fretpilot.midi.models import NormalizedTimeline, NormalizedTrack


def _select_source(
    timeline: NormalizedTimeline,
    *,
    stream_id: str | None,
    track_index: int | None,
) -> tuple[NormalizedTrack, str | None]:
    if stream_id is not None:
        stream = next(
            (
                item
                for item in resolve_instrument_streams(timeline)
                if item.stream_id == stream_id
            ),
            None,
        )
        if stream is None:
            raise SystemExit(f"Unknown stream ID: {stream_id}")
        return stream.as_track(), stream.stream_id

    if track_index is not None:
        if not 0 <= track_index < len(timeline.tracks):
            raise SystemExit(f"Track index {track_index} is out of range.")
        track = timeline.tracks[track_index]
        if not track.notes:
            raise SystemExit(f"Track {track_index} contains no notes.")
        return track, None

    report = classify_timeline(timeline)
    likely = [item for item in report.candidates if item.decision == "likely_guitar"]
    if len(likely) == 1:
        candidate = likely[0]
        return candidate.stream.as_track(), candidate.stream.stream_id
    if not likely:
        raise SystemExit(
            "No likely guitar stream was detected. Run `fretpilot tracks` and "
            "select one with --stream-id."
        )
    options = ", ".join(item.stream.stream_id for item in likely)
    raise SystemExit(
        "Multiple likely guitar streams were detected. Select one with "
        f"--stream-id. Candidates: {options}."
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fretpilot-pdf",
        description="Render a FretPilot guitar stream as landscape PDF TAB",
    )
    parser.add_argument("midi_file", type=Path)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--stream-id")
    source.add_argument("--track", type=int)
    parser.add_argument("--max-fret", type=int, default=24)
    parser.add_argument("--measures-per-system", type=int, default=4)
    parser.add_argument("--systems-per-page", type=int, default=5)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)

    if args.max_fret < 0:
        raise SystemExit("--max-fret must be zero or greater.")

    timeline = load_midi(args.midi_file)
    track, stream_id = _select_source(
        timeline,
        stream_id=args.stream_id,
        track_index=args.track,
    )
    analysis = analyze_guitar_track(track, max_fret=args.max_fret)
    project = build_guitar_ir(
        timeline,
        track,
        analysis,
        source_stream_id=stream_id,
    )
    result = export_score_pdf(
        project,
        args.output,
        measures_per_system=args.measures_per_system,
        systems_per_page=args.systems_per_page,
    )
    print(
        json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            indent=None if args.compact else 2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
