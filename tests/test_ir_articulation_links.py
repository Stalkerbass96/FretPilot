from __future__ import annotations

from fretpilot.analysis import analyze_guitar_track
from fretpilot.ir import build_guitar_ir
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)


def _note(*, pitch: int, start_beat: float, duration_beats: float) -> NormalizedNote:
    ticks_per_beat = 480
    return NormalizedNote(
        track_index=0,
        track_name="Lead Guitar",
        channel=0,
        pitch=pitch,
        velocity=90,
        start_tick=round(start_beat * ticks_per_beat),
        duration_ticks=round(duration_beats * ticks_per_beat),
        start_beat=start_beat,
        duration_beats=duration_beats,
        program=27,
    )


def test_hammer_source_uses_final_fragment_of_tied_note() -> None:
    track = NormalizedTrack(
        index=0,
        name="Lead Guitar",
        notes=[
            _note(pitch=64, start_beat=3.5, duration_beats=1.0),
            _note(pitch=66, start_beat=4.5, duration_beats=0.5),
        ],
    )
    timeline = NormalizedTimeline(
        source="tied-hammer.mid",
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

    analysis = analyze_guitar_track(track)
    project = build_guitar_ir(timeline, track, analysis)

    target_event = next(
        event
        for measure in project.tracks[0].measures
        for event in measure.events
        if event.source_note_index == 1
    )
    hammer = next(
        articulation
        for articulation in target_event.articulations
        if articulation.type == "hammer_on"
    )

    assert hammer.source_note_id == "n-00001-2"
