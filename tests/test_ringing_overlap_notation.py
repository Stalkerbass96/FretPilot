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


def _note(*, pitch: int, start_beat: float, duration_beats: float) -> NormalizedNote:
    ticks_per_beat = 480
    return NormalizedNote(
        track_index=0,
        track_name="Arpeggio Guitar",
        channel=0,
        pitch=pitch,
        velocity=90,
        start_tick=round(start_beat * ticks_per_beat),
        duration_ticks=round(duration_beats * ticks_per_beat),
        start_beat=start_beat,
        duration_beats=duration_beats,
        program=27,
    )


def test_ringing_overlap_becomes_let_ring_without_losing_source_duration(
    tmp_path: Path,
) -> None:
    track = NormalizedTrack(
        index=0,
        name="Arpeggio Guitar",
        notes=[
            _note(pitch=64, start_beat=0.0, duration_beats=1.5),
            _note(pitch=71, start_beat=0.5, duration_beats=1.0),
            _note(pitch=67, start_beat=1.0, duration_beats=0.5),
        ],
    )
    timeline = NormalizedTimeline(
        source="arpeggio.mid",
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
    events = project.tracks[0].measures[0].events
    first = next(event for event in events if event.source_note_index == 0)

    assert first.score.duration_beats == 0.5
    assert first.performance.source_duration_beats == 1.5
    assert any(item.type == "let_ring" for item in first.articulations)
    assert any(
        change.stage == "rhythm_overlap" and change.source_note_index == 0
        for change in project.changes
    )

    output = tmp_path / "arpeggio.gp5"
    export_gp5(project, output)
    parsed = gp.parse(output)
    parsed_first_note = next(
        note
        for beat in parsed.tracks[0].measures[0].voices[0].beats
        for note in beat.notes
        if note.type == gp.NoteType.normal
    )
    assert parsed_first_note.effect.letRing is True
