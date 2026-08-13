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
        track_name="Lead Guitar",
        channel=0,
        pitch=pitch,
        velocity=velocity,
        start_tick=round(start_beat * ticks_per_beat),
        duration_ticks=round(duration_beats * ticks_per_beat),
        start_beat=start_beat,
        duration_beats=duration_beats,
        program=27,
    )


def test_gp5_export_round_trips_supported_subset(tmp_path: Path) -> None:
    track = NormalizedTrack(
        index=0,
        name="Lead Guitar",
        notes=[
            _note(pitch=64, start_beat=0.0, duration_beats=0.5),
            _note(pitch=67, start_beat=0.5, duration_beats=0.5),
            _note(pitch=69, start_beat=3.5, duration_beats=1.0),
        ],
    )
    timeline = NormalizedTimeline(
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
    analysis = analyze_guitar_track(track)
    project = build_guitar_ir(timeline, track, analysis)
    output = tmp_path / "prototype.gp5"

    result = export_gp5(project, output)

    assert output.exists()
    assert result.measure_count == 2
    parsed = gp.parse(output)
    assert parsed.title == "fixture"
    assert len(parsed.measureHeaders) == 2
    assert len(parsed.tracks) == 1
    assert [string.value for string in parsed.tracks[0].strings] == [
        64,
        59,
        55,
        50,
        45,
        40,
    ]

    first_voice = parsed.tracks[0].measures[0].voices[0]
    second_voice = parsed.tracks[0].measures[1].voices[0]
    assert any(beat.status == gp.BeatStatus.rest for beat in first_voice.beats)
    assert any(
        note.type == gp.NoteType.tie
        for beat in second_voice.beats
        for note in beat.notes
    )
