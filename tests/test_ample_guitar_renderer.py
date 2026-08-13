from __future__ import annotations

from pathlib import Path

import mido

from fretpilot.analysis import analyze_guitar_track
from fretpilot.exporters.ample_guitar import export_ample_sc_midi
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
        velocity=92,
        start_tick=round(start_beat * ticks_per_beat),
        duration_ticks=round(duration_beats * ticks_per_beat),
        start_beat=start_beat,
        duration_beats=duration_beats,
        program=27,
    )


def _absolute_messages(track: mido.MidiTrack):
    absolute = 0
    result = []
    for message in track:
        absolute += message.time
        result.append((absolute, message))
    return result


def test_ample_sc_renderer_adds_hp_keyswitch_and_note_overlap(tmp_path: Path) -> None:
    track = NormalizedTrack(
        index=0,
        name="Lead Guitar",
        notes=[
            _note(pitch=64, start_beat=0.0, duration_beats=0.5),
            _note(pitch=66, start_beat=0.5, duration_beats=0.5),
        ],
    )
    timeline = NormalizedTimeline(
        source="legato.mid",
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
    output = tmp_path / "ample-sc.mid"

    report = export_ample_sc_midi(project, output)

    assert output.exists()
    assert report.profile_id == "ample-guitar-sc-v4"
    assert report.source_note_count == 2
    assert report.keyswitch_count >= 2  # Sustain plus HP.

    rendered = mido.MidiFile(output)
    messages = _absolute_messages(rendered.tracks[1])

    assert any(
        tick == 0
        and message.type == "note_on"
        and message.note == 29  # F0 / Hammer-On & Pull-Off keyswitch.
        for tick, message in messages
    )

    first_on = next(
        tick
        for tick, message in messages
        if message.type == "note_on" and message.velocity > 0 and message.note == 64
    )
    second_on = next(
        tick
        for tick, message in messages
        if message.type == "note_on" and message.velocity > 0 and message.note == 66
    )
    first_off = next(
        tick
        for tick, message in messages
        if message.type == "note_off" and message.note == 64
    )

    assert first_on == 30
    assert second_on == 270
    assert first_off >= second_on + 30
