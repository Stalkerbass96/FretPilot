from pathlib import Path

import guitarpro as gp

from fretpilot.exporters.guitar_pro import export_gp5
from fretpilot.ir.models import (
    GuitarMeasure, GuitarNoteEvent, GuitarProjectIR, GuitarTrackIR,
    IRArticulation, IRFingering, IRTempoEvent, IRTimeSignatureEvent,
    PerformanceTiming, ScoreTiming,
)


def test_gp5_round_trips_palm_mute_and_staccato(tmp_path: Path):
    event = GuitarNoteEvent(
        id="n-1", source_note_index=0, pitch=40,
        score=ScoreTiming(0.0, 0.25, 1, 0.0),
        performance=PerformanceTiming(0.0, 0.25, 95),
        fingering=IRFingering(6, 0),
        articulations=[
            IRArticulation("palm_mute", 0.8, "fixture"),
            IRArticulation("staccato", 0.8, "fixture"),
        ],
    )
    project = GuitarProjectIR(
        title="effects", source="effects.mid",
        tempo_map=[IRTempoEvent(0.0, 120.0)],
        time_signatures=[IRTimeSignatureEvent(0.0, 4, 4)],
        tracks=[GuitarTrackIR(
            id="guitar-1", name="Guitar", source_stream_id=None,
            role="riff", tuning=[40, 45, 50, 55, 59, 64], fret_count=24,
            measures=[GuitarMeasure(1, 0.0, 4.0, 4, 4, [event])],
        )],
    )
    output = tmp_path / "effects.gp5"
    export_gp5(project, output)
    parsed = gp.parse(output)
    notes = [
        note
        for beat in parsed.tracks[0].measures[0].voices[0].beats
        for note in beat.notes
    ]
    assert notes[0].effect.palmMute is True
    assert notes[0].effect.staccato is True
