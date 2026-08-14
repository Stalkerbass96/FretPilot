from pathlib import Path

import guitarpro as gp

from fretpilot.exporters.guitar_pro import export_gp5
from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
    IRFingering,
    IRTempoEvent,
    IRTimeSignatureEvent,
    PerformanceTiming,
    ScoreTiming,
)


def _event(index, pitch, beat, fret):
    return GuitarNoteEvent(
        id=f"n-{index}",
        source_note_index=index,
        pitch=pitch,
        score=ScoreTiming(beat, 0.5, 1, beat),
        performance=PerformanceTiming(beat, 0.5, 90),
        fingering=IRFingering(2, fret),
    )


def test_gp5_round_trips_fretting_digits(tmp_path: Path) -> None:
    events = [
        _event(0, 64, 0.0, 5),
        _event(1, 66, 0.5, 7),
        _event(2, 67, 1.0, 8),
    ]
    project = GuitarProjectIR(
        title="digits",
        source="fixture.mid",
        tempo_map=[IRTempoEvent(0.0, 120.0)],
        time_signatures=[IRTimeSignatureEvent(0.0, 4, 4)],
        tracks=[GuitarTrackIR(
            id="guitar-1",
            name="Guitar",
            source_stream_id=None,
            role="lead",
            tuning=[40, 45, 50, 55, 59, 64],
            fret_count=24,
            measures=[GuitarMeasure(1, 0.0, 4.0, 4, 4, events)],
        )],
    )
    output = tmp_path / "digits.gp5"
    export_gp5(project, output)
    parsed = gp.parse(output)
    notes = [
        note
        for beat in parsed.tracks[0].measures[0].voices[0].beats
        for note in beat.notes
    ]
    assert [note.effect.leftHandFinger for note in notes] == [
        gp.Fingering.index,
        gp.Fingering.annular,
        gp.Fingering.little,
    ]
