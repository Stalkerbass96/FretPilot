from pathlib import Path

import guitarpro as gp

from fretpilot.analysis import analyze_guitar_track
from fretpilot.exporters.guitar_pro import export_gp5
from fretpilot.ir import build_guitar_ir
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
    PerformanceTiming,
    ScoreTiming,
)
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)


def test_builder_attaches_downstrokes_for_metal_riff() -> None:
    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Guitar",
            channel=0,
            pitch=40,
            velocity=90,
            start_tick=i * 120,
            duration_ticks=96,
            start_beat=i * 0.25,
            duration_beats=0.2,
            program=29,
        )
        for i in range(4)
    ]
    track = NormalizedTrack(0, "Guitar", notes)
    timeline = NormalizedTimeline(
        source="riff.mid",
        midi_type=1,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(0, 0.0, 120.0)],
        time_signature_events=[TimeSignatureEvent(0, 0.0, 4, 4)],
        tracks=[track],
    )
    context = compose_playing_context({"riff": 1.0, "metal": 1.0})
    analysis = analyze_guitar_track(track, playing_context=context)
    project = build_guitar_ir(timeline, track, analysis)
    events = project.tracks[0].measures[0].events
    assert [event.right_hand.direction for event in events] == ["down"] * 4
    assert all(event.right_hand.motion == "pick" for event in events)


def test_gp5_round_trips_pick_direction(tmp_path: Path) -> None:
    event = GuitarNoteEvent(
        id="n-1",
        source_note_index=0,
        pitch=52,
        score=ScoreTiming(0.0, 0.5, 1, 0.0),
        performance=PerformanceTiming(0.0, 0.5, 90),
        fingering=IRFingering(5, 7),
        right_hand=IRRightHandIntent("pick", "down", 0.9, "fixture"),
    )
    project = GuitarProjectIR(
        title="right-hand",
        source="fixture.mid",
        tempo_map=[IRTempoEvent(0.0, 120.0)],
        time_signatures=[IRTimeSignatureEvent(0.0, 4, 4)],
        tracks=[GuitarTrackIR(
            id="guitar-1",
            name="Guitar",
            source_stream_id=None,
            role="riff",
            tuning=[40, 45, 50, 55, 59, 64],
            fret_count=24,
            measures=[GuitarMeasure(1, 0.0, 4.0, 4, 4, [event])],
        )],
    )
    output = tmp_path / "right-hand.gp5"
    export_gp5(project, output)
    parsed = gp.parse(output)
    beat = next(
        beat
        for beat in parsed.tracks[0].measures[0].voices[0].beats
        if beat.notes
    )
    assert beat.effect.pickStroke == gp.BeatStrokeDirection.down


def test_gp5_round_trips_pitch_raise_curve(tmp_path: Path) -> None:
    event = GuitarNoteEvent(
        id="n-raise",
        source_note_index=0,
        pitch=64,
        score=ScoreTiming(0.0, 1.0, 1, 0.0),
        performance=PerformanceTiming(0.0, 1.0, 90),
        fingering=IRFingering(2, 5),
        articulations=[
            IRArticulation(
                type="pitch_raise",
                confidence=0.94,
                reason="fixture",
                parameters={
                    "semitones": 1.0,
                    "peak_position": 0.25,
                    "return_position": 0.5,
                    "returned_to_center": 1.0,
                },
            )
        ],
    )
    project = GuitarProjectIR(
        title="pitch-raise",
        source="fixture.mid",
        tempo_map=[IRTempoEvent(0.0, 120.0)],
        time_signatures=[IRTimeSignatureEvent(0.0, 4, 4)],
        tracks=[GuitarTrackIR(
            id="guitar-1",
            name="Guitar",
            source_stream_id=None,
            role="solo",
            tuning=[40, 45, 50, 55, 59, 64],
            fret_count=24,
            measures=[GuitarMeasure(1, 0.0, 4.0, 4, 4, [event])],
        )],
    )
    output = tmp_path / "pitch-raise.gp5"
    export_gp5(project, output)
    parsed = gp.parse(output)
    note = next(
        note
        for beat in parsed.tracks[0].measures[0].voices[0].beats
        for note in beat.notes
    )
    assert note.effect.bend.type == gp.BendType.bendRelease
    assert note.effect.bend.value == 1
    assert [(point.position, point.value) for point in note.effect.bend.points] == [
        (0, 0),
        (3, 1),
        (6, 0),
        (12, 0),
    ]
