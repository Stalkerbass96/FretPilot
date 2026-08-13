from __future__ import annotations

from pathlib import Path

import mido

from fretpilot.detection import classify_guitar_stream, classify_timeline
from fretpilot.detection.models import InstrumentStream
from fretpilot.midi import load_midi
from fretpilot.midi.models import NormalizedNote


def _note(
    *,
    pitch: int,
    start: int,
    duration: int = 240,
    channel: int = 0,
    track_name: str = "Track",
    program: int | None = None,
) -> NormalizedNote:
    return NormalizedNote(
        track_index=0,
        track_name=track_name,
        channel=channel,
        pitch=pitch,
        velocity=90,
        start_tick=start,
        duration_ticks=duration,
        start_beat=start / 480,
        duration_beats=duration / 480,
        program=program,
    )


def test_type_zero_is_split_into_channel_program_streams(tmp_path: Path) -> None:
    midi_path = tmp_path / "arrangement.mid"
    midi = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name="Full Arrangement", time=0))

    # Guitar: General MIDI Electric Guitar (clean), zero-based program 27.
    track.append(mido.Message("program_change", channel=0, program=27, time=0))
    track.append(mido.Message("note_on", channel=0, note=64, velocity=90, time=0))
    track.append(mido.Message("note_off", channel=0, note=64, velocity=0, time=240))
    track.append(mido.Message("note_on", channel=0, note=67, velocity=90, time=0))
    track.append(mido.Message("note_off", channel=0, note=67, velocity=0, time=240))

    # Bass on another channel.
    track.append(mido.Message("program_change", channel=1, program=32, time=0))
    track.append(mido.Message("note_on", channel=1, note=31, velocity=90, time=0))
    track.append(mido.Message("note_off", channel=1, note=31, velocity=0, time=480))

    # Drum channel (zero-based channel 9 / display channel 10).
    track.append(mido.Message("note_on", channel=9, note=36, velocity=100, time=0))
    track.append(mido.Message("note_off", channel=9, note=36, velocity=0, time=120))

    midi.tracks.append(track)
    midi.save(midi_path)

    timeline = load_midi(midi_path)
    report = classify_timeline(timeline)

    assert len(timeline.tracks) == 1
    assert len(timeline.program_events) == 2
    assert report.stream_count == 3

    top = report.candidates[0]
    assert top.stream.channel == 0
    assert top.stream.program_family == "guitar"
    assert top.decision == "likely_guitar"
    assert top.stream.stream_id in report.recommended_stream_ids

    drum = next(candidate for candidate in report.candidates if candidate.stream.channel == 9)
    assert drum.decision == "unlikely_guitar"
    assert drum.layers[1].score == 0.0


def test_guitar_track_keyword_is_strong_but_not_absolute() -> None:
    notes = [
        _note(
            pitch=60 + (index % 4),
            start=index * 240,
            track_name="Lead Guitar",
            program=0,  # Acoustic grand piano metadata conflicts with the name.
        )
        for index in range(12)
    ]
    stream = InstrumentStream(
        stream_id="t0:ch0:p0",
        source_track_index=0,
        source_track_name="Lead Guitar",
        channel=0,
        program=0,
        program_name="General MIDI program 1",
        program_family="piano",
        instrument_name=None,
        notes=notes,
    )

    candidate = classify_guitar_stream(stream)

    assert candidate.layers[0].status == "positive"
    assert candidate.layers[1].status == "negative"
    assert candidate.guitar_probability < 0.75
    assert candidate.decision == "possible_guitar"


def test_layer_four_profiles_are_separate_from_guitar_probability() -> None:
    notes = [
        _note(pitch=pitch, start=index * 240, program=27)
        for index, pitch in enumerate([64, 66, 67, 69, 67, 66, 64, 64])
    ]
    stream = InstrumentStream(
        stream_id="t0:ch0:p27",
        source_track_index=0,
        source_track_name="Solo Guitar",
        channel=0,
        program=27,
        program_name="Electric Guitar (clean)",
        program_family="guitar",
        instrument_name=None,
        notes=notes,
    )

    candidate = classify_guitar_stream(stream)

    assert candidate.decision == "likely_guitar"
    assert candidate.behavior_profiles
    assert {profile.profile_id for profile in candidate.behavior_profiles} >= {
        "solo",
        "riff",
        "strumming",
        "breakdown",
        "jazz_comping",
    }
