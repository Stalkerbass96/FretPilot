from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
    IRArticulation,
    IRFingering,
    IRRightHandIntent,
    IRTempoEvent,
    IRTimeSignatureEvent,
    NoteConfidence,
    PerformanceTiming,
    ScoreTiming,
    Transformation,
)


def project_from_dict(data: dict[str, Any]) -> GuitarProjectIR:
    tracks: list[GuitarTrackIR] = []
    for raw_track in data.get("tracks", []):
        measures: list[GuitarMeasure] = []
        for raw_measure in raw_track.get("measures", []):
            events: list[GuitarNoteEvent] = []
            for raw_event in raw_measure.get("events", []):
                right_hand = raw_event.get("right_hand")
                confidence = raw_event.get("confidence")
                events.append(
                    GuitarNoteEvent(
                        id=str(raw_event["id"]),
                        source_note_index=int(raw_event["source_note_index"]),
                        pitch=int(raw_event["pitch"]),
                        score=ScoreTiming(**raw_event["score"]),
                        performance=PerformanceTiming(**raw_event["performance"]),
                        fingering=IRFingering(**raw_event["fingering"]),
                        articulations=[
                            IRArticulation(**item)
                            for item in raw_event.get("articulations", [])
                        ],
                        confidence=(
                            NoteConfidence(**confidence)
                            if isinstance(confidence, dict)
                            else None
                        ),
                        right_hand=(
                            IRRightHandIntent(**right_hand)
                            if isinstance(right_hand, dict)
                            else None
                        ),
                    )
                )
            measures.append(
                GuitarMeasure(
                    number=int(raw_measure["number"]),
                    start_beat=float(raw_measure["start_beat"]),
                    duration_beats=float(raw_measure["duration_beats"]),
                    numerator=int(raw_measure["numerator"]),
                    denominator=int(raw_measure["denominator"]),
                    events=events,
                )
            )
        tracks.append(
            GuitarTrackIR(
                id=str(raw_track["id"]),
                name=str(raw_track["name"]),
                source_stream_id=raw_track.get("source_stream_id"),
                role=str(raw_track.get("role", "unknown")),
                tuning=[int(item) for item in raw_track.get("tuning", [])],
                fret_count=int(raw_track.get("fret_count", 24)),
                measures=measures,
                playing_context=raw_track.get("playing_context"),
                section_contexts=list(raw_track.get("section_contexts", [])),
                hand_positions=list(raw_track.get("hand_positions", [])),
            )
        )

    return GuitarProjectIR(
        title=str(data.get("title", "")),
        source=str(data.get("source", "")),
        tempo_map=[IRTempoEvent(**item) for item in data.get("tempo_map", [])],
        time_signatures=[
            IRTimeSignatureEvent(**item)
            for item in data.get("time_signatures", [])
        ],
        tracks=tracks,
        changes=[Transformation(**item) for item in data.get("changes", [])],
        warnings=[str(item) for item in data.get("warnings", [])],
        schema_version=str(data.get("schema_version", "0.1")),
    )


def load_guitar_ir(path: str | Path) -> GuitarProjectIR:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Guitar IR JSON root must be an object.")
    return project_from_dict(payload)
