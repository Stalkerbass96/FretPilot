from __future__ import annotations

from fretpilot.analysis import analyze_guitar_stream_section_aware, analyze_guitar_track
from fretpilot.detection.models import InstrumentStream
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    PitchWheelEvent,
    PitchWheelRangeEvent,
    TempoEvent,
    TimeSignatureEvent,
)


def _track(
    pitches: list[int],
    *,
    onsets: list[float] | None = None,
    durations: list[float] | None = None,
) -> NormalizedTrack:
    active_onsets = onsets or [index * 0.5 for index in range(len(pitches))]
    active_durations = durations or [0.5] * len(pitches)
    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Lead Guitar",
            channel=0,
            pitch=pitch,
            velocity=90,
            start_tick=round(active_onsets[index] * 480),
            duration_ticks=round(active_durations[index] * 480),
            start_beat=active_onsets[index],
            duration_beats=active_durations[index],
            program=29,
        )
        for index, pitch in enumerate(pitches)
    ]
    return NormalizedTrack(index=0, name="Lead Guitar", notes=notes)


def test_analysis_combines_rhythm_fingering_and_articulation() -> None:
    track = _track(
        [64, 66, 71],
        onsets=[0.02, 0.49, 1.01],
        durations=[0.47, 0.50, 1.50],
    )
    analysis = analyze_guitar_track(track)
    assert analysis.playing_context is None
    assert analysis.rhythm.selected_grid.name == "eighth"
    assert all(note.playable for note in analysis.fingering.notes)
    assert any(decision.technique == "hammer_on" for decision in analysis.articulations.decisions)
    assert any(decision.technique == "slide" for decision in analysis.articulations.decisions)
    assert any(decision.technique == "vibrato" for decision in analysis.articulations.decisions)


def test_analysis_threads_explicit_playing_context_into_result() -> None:
    track = _track([64, 66, 67, 69])
    context = compose_playing_context({"solo": 1.0})
    analysis = analyze_guitar_track(track, playing_context=context)
    assert analysis.playing_context is context
    serialized = analysis.to_dict()["playing_context"]
    assert serialized["role_scores"] == {"solo": 1.0}
    assert serialized["knowledge_version"] == context.knowledge_version
    assert all(note.playable for note in analysis.fingering.notes)


def test_stream_analysis_attaches_explicit_pitch_raise_parameters() -> None:
    track = _track([64], onsets=[0.0], durations=[1.0])
    stream = InstrumentStream(
        stream_id="t0:ch0:p29",
        source_track_index=0,
        source_track_name="Lead Guitar",
        channel=0,
        program=29,
        program_name="Overdriven Guitar",
        program_family="guitar",
        instrument_name=None,
        notes=track.notes,
    )
    timeline = NormalizedTimeline(
        source="wheel.mid",
        midi_type=1,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(0, 0.0, 120.0)],
        time_signature_events=[TimeSignatureEvent(0, 0.0, 4, 4)],
        tracks=[track],
        pitch_wheel_events=[
            PitchWheelEvent(0, 0, 120, 0.25, 4096),
            PitchWheelEvent(0, 0, 240, 0.5, 0),
        ],
        pitch_wheel_range_events=[
            PitchWheelRangeEvent(0, 0, 0, 0.0, 2, 0),
        ],
    )

    analysis = analyze_guitar_stream_section_aware(timeline, stream)
    decision = next(
        item for item in analysis.articulations.decisions
        if item.technique == "pitch_raise"
    )
    assert decision.note_index == 0
    assert decision.parameters["semitones"] == 1.0
    assert decision.parameters["range_semitones"] == 2.0
    assert decision.confidence == 0.94
