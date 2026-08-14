from __future__ import annotations

from pathlib import Path

import guitarpro as gp

from fretpilot.analysis import analyze_guitar_track
from fretpilot.exporters.guitar_pro import export_gp5
from fretpilot.ir import build_guitar_ir
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)


def _note(*, pitch: int, duration_beats: float) -> NormalizedNote:
    ticks_per_beat = 480
    return NormalizedNote(
        track_index=0,
        track_name="Chord Guitar",
        channel=0,
        pitch=pitch,
        velocity=90,
        start_tick=0,
        duration_ticks=round(duration_beats * ticks_per_beat),
        start_beat=0.0,
        duration_beats=duration_beats,
        program=27,
    )


def test_longer_chord_member_becomes_independent_second_voice(tmp_path: Path) -> None:
    track = NormalizedTrack(
        index=0,
        name="Chord Guitar",
        notes=[
            _note(pitch=64, duration_beats=1.0),
            _note(pitch=67, duration_beats=1.5),
        ],
    )
    timeline = NormalizedTimeline(
        source="unequal-chord.mid",
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

    project = build_guitar_ir(timeline, track, analyze_guitar_track(track))
    events = project.tracks[0].measures[0].events

    assert {event.score.duration_beats for event in events} == {1.0, 2.0}
    longer = next(event for event in events if event.pitch == 67)
    shorter = next(event for event in events if event.pitch == 64)
    assert shorter.score.voice == 1
    assert longer.score.voice == 2
    assert longer.performance.source_duration_beats == 1.5
    assert not any(item.type == "let_ring" for item in longer.articulations)
    assert any(
        change.stage == "voice_assignment"
        and change.source_note_index == longer.source_note_index
        and change.after == {"voice": 2}
        for change in project.changes
    )

    output = tmp_path / "unequal-chord.gp5"
    report = export_gp5(project, output)
    parsed = gp.parse(output)
    first_voice_beat = next(
        beat
        for beat in parsed.tracks[0].measures[0].voices[0].beats
        if beat.status == gp.BeatStatus.normal
    )
    second_voice_beat = next(
        beat
        for beat in parsed.tracks[0].measures[0].voices[1].beats
        if beat.status == gp.BeatStatus.normal
    )
    assert len(first_voice_beat.notes) == 1
    assert len(second_voice_beat.notes) == 1
    assert first_voice_beat.duration.time != second_voice_beat.duration.time
    assert not any("Omitted partial let-ring" in warning for warning in report.warnings)
