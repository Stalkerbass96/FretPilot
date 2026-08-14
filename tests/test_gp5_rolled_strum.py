from pathlib import Path

import guitarpro as gp

from fretpilot.exporters.guitar_pro import export_gp5
from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
    IRFingering,
    IRRightHandIntent,
    IRTempoEvent,
    IRTimeSignatureEvent,
    PerformanceTiming,
    ScoreTiming,
)


def _project(source_starts):
    pitches = [45, 52, 59]
    strings = [6, 5, 4]
    frets = [5, 7, 9]
    intent = IRRightHandIntent(
        motion="strum",
        direction="down",
        confidence=0.95,
        reason="observed stagger",
        technique="rolled_strum",
    )
    events = [
        GuitarNoteEvent(
            id=f"n-{index}",
            source_note_index=index,
            pitch=pitches[index],
            score=ScoreTiming(0.0, 1.0, 1, 0.0),
            performance=PerformanceTiming(source_starts[index], 1.0, 90),
            fingering=IRFingering(strings[index], frets[index]),
            right_hand=intent,
        )
        for index in range(3)
    ]
    return GuitarProjectIR(
        title="strum",
        source="fixture.mid",
        tempo_map=[IRTempoEvent(0.0, 120.0)],
        time_signatures=[IRTimeSignatureEvent(0.0, 4, 4)],
        tracks=[GuitarTrackIR(
            id="guitar-1",
            name="Guitar",
            source_stream_id=None,
            role="strumming",
            tuning=[40, 45, 50, 55, 59, 64],
            fret_count=24,
            measures=[GuitarMeasure(1, 0.0, 4.0, 4, 4, events)],
        )],
    )


def _first_note_beat(parsed):
    return next(
        beat
        for beat in parsed.tracks[0].measures[0].voices[0].beats
        if beat.notes
    )


def test_gp5_uses_beat_stroke_for_observed_source_spread(tmp_path: Path):
    output = tmp_path / "rolled.gp5"
    export_gp5(_project([0.0, 0.04, 0.08]), output)
    beat = _first_note_beat(gp.parse(output))

    assert beat.effect.stroke.direction == gp.BeatStrokeDirection.down
    assert beat.effect.stroke.value == 64
    assert beat.effect.pickStroke == gp.BeatStrokeDirection.none


def test_gp5_does_not_invent_stroke_duration_for_simultaneous_source(tmp_path: Path):
    output = tmp_path / "simultaneous.gp5"
    export_gp5(_project([0.0, 0.0, 0.0]), output)
    beat = _first_note_beat(gp.parse(output))

    assert beat.effect.stroke.direction == gp.BeatStrokeDirection.none
    assert beat.effect.pickStroke == gp.BeatStrokeDirection.down
