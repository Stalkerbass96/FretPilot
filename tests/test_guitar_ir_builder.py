from __future__ import annotations

from fretpilot.analysis import analyze_guitar_track
from fretpilot.ir import build_guitar_ir
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)


def _note(
    *,
    pitch: int,
    start_beat: float,
    duration_beats: float,
    velocity: int = 90,
) -> NormalizedNote:
    ticks_per_beat = 480
    return NormalizedNote(
        track_index=0,
        track_name="Guitar",
        channel=0,
        pitch=pitch,
        velocity=velocity,
        start_tick=round(start_beat * ticks_per_beat),
        duration_ticks=round(duration_beats * ticks_per_beat),
        start_beat=start_beat,
        duration_beats=duration_beats,
        program=27,
    )


def _timeline(track: NormalizedTrack) -> NormalizedTimeline:
    return NormalizedTimeline(
        source="fixture.mid",
        midi_type=1,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(tick=0, beat=0.0, bpm=120.0)],
        time_signature_events=[
            TimeSignatureEvent(
                tick=0,
                beat=0.0,
                numerator=4,
                denominator=4,
            )
        ],
        tracks=[track],
    )


def test_builder_splits_cross_measure_note_with_ties() -> None:
    track = NormalizedTrack(
        index=0,
        name="Guitar",
        notes=[
            _note(pitch=64, start_beat=0.0, duration_beats=0.5),
            _note(pitch=67, start_beat=3.5, duration_beats=1.0),
        ],
    )
    timeline = _timeline(track)
    analysis = analyze_guitar_track(track)

    project = build_guitar_ir(
        timeline,
        track,
        analysis,
        source_stream_id="t0:ch0:p27",
    )

    assert project.schema_version == "0.1"
    assert project.tracks[0].source_stream_id == "t0:ch0:p27"
    assert project.tracks[0].playing_context is None
    assert len(project.tracks[0].measures) == 2

    first_fragment = next(
        event
        for event in project.tracks[0].measures[0].events
        if event.source_note_index == 1
    )
    second_fragment = next(
        event
        for event in project.tracks[0].measures[1].events
        if event.source_note_index == 1
    )

    assert first_fragment.score.duration_beats == 0.5
    assert first_fragment.score.tie_in is False
    assert first_fragment.score.tie_out is True
    assert second_fragment.score.duration_beats == 0.5
    assert second_fragment.score.tie_in is True
    assert second_fragment.score.tie_out is False

    # Score fragments remain linked to the untouched source performance timing.
    assert first_fragment.performance.source_start_beat == 3.5
    assert first_fragment.performance.source_duration_beats == 1.0
    assert second_fragment.performance.source_start_beat == 3.5
    assert second_fragment.performance.source_duration_beats == 1.0


def test_builder_records_onset_and_duration_repairs() -> None:
    track = NormalizedTrack(
        index=0,
        name="Guitar",
        notes=[
            _note(pitch=64, start_beat=0.49, duration_beats=0.52),
            _note(pitch=67, start_beat=1.0, duration_beats=0.5),
        ],
    )
    timeline = _timeline(track)
    analysis = analyze_guitar_track(track)

    project = build_guitar_ir(timeline, track, analysis)
    event = project.tracks[0].measures[0].events[0]

    assert event.score.start_beat == 0.5
    assert event.score.duration_beats == 0.5
    assert event.performance.source_start_beat == 0.49
    assert event.performance.source_duration_beats == 0.52
    assert {change.stage for change in project.changes} >= {
        "rhythm_onset",
        "rhythm_duration",
    }


def test_builder_preserves_playing_context_metadata() -> None:
    track = NormalizedTrack(
        index=0,
        name="Lead Guitar",
        notes=[
            _note(pitch=64, start_beat=0.0, duration_beats=0.5),
            _note(pitch=66, start_beat=0.5, duration_beats=0.5),
        ],
    )
    timeline = _timeline(track)
    context = compose_playing_context({"solo": 0.9, "metal": 0.8})
    analysis = analyze_guitar_track(track, playing_context=context)

    project = build_guitar_ir(timeline, track, analysis)
    ir_context = project.tracks[0].playing_context

    assert ir_context is not None
    assert ir_context["role_scores"] == {"solo": 0.9}
    assert ir_context["style_scores"] == {"metal": 0.8}
    assert ir_context["knowledge_version"] == context.knowledge_version
