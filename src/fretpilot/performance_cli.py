"""Standalone CLI for inspecting target-neutral guitar performance intent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from fretpilot.analysis import analyze_guitar_stream_section_aware
from fretpilot.detection import classify_timeline
from fretpilot.detection.models import GuitarStreamCandidate
from fretpilot.ir import build_guitar_ir
from fretpilot.midi import load_midi
from fretpilot.midi.models import NormalizedTimeline
from fretpilot.performance import build_performance_plan


def _select_candidate(
    timeline: NormalizedTimeline,
    *,
    stream_id: str | None,
) -> GuitarStreamCandidate:
    report = classify_timeline(timeline)

    if stream_id is not None:
        candidate = next(
            (item for item in report.candidates if item.stream.stream_id == stream_id),
            None,
        )
        if candidate is None:
            available = ", ".join(
                item.stream.stream_id for item in report.candidates
            )
            raise SystemExit(
                f"Unknown stream ID {stream_id!r}. Available: {available or 'none'}."
            )
        return candidate

    likely = [item for item in report.candidates if item.decision == "likely_guitar"]
    if len(likely) == 1:
        return likely[0]
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
        prog="fretpilot-performance-plan",
        description=(
            "Build target-neutral guitarist performance intent from a selected "
            "MIDI guitar stream without applying any virtual-instrument mapping"
        ),
    )
    parser.add_argument("midi_file", type=Path)
    parser.add_argument("--stream-id")
    parser.add_argument("--max-fret", type=int, default=24)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)

    if args.max_fret < 0:
        raise SystemExit("--max-fret must be zero or greater.")

    timeline = load_midi(args.midi_file)
    candidate = _select_candidate(timeline, stream_id=args.stream_id)
    analysis = analyze_guitar_stream_section_aware(
        timeline,
        candidate.stream,
        max_fret=args.max_fret,
    )
    track = candidate.stream.as_track()
    project = build_guitar_ir(
        timeline,
        track,
        analysis,
        source_stream_id=candidate.stream.stream_id,
    )
    plan = build_performance_plan(project)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            plan.to_dict(),
            ensure_ascii=False,
            indent=None if args.compact else 2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "output": str(args.output),
                "stream_id": candidate.stream.stream_id,
                "plan_version": plan.version,
                "note_count": len(plan.notes),
                "section_count": len(plan.sections),
                "warnings": plan.warnings,
            },
            ensure_ascii=False,
            indent=None if args.compact else 2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
