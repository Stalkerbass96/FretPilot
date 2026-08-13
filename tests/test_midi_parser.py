from __future__ import annotations

from pathlib import Path

import mido

from fretpilot.midi import load_midi


def _write_test_midi(path: Path) -> None:
    midi = mido.MidiFile(type=1, ticks_per_beat=480)

    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(96), time=0))
    meta.append(
        mido.MetaMessage(
            "time_signature",
            numerator=4,
            denominator=4,
            time=0,
        )
    )
    midi.tracks.append(meta)

    guitar = mido.MidiTrack()
    guitar.append(mido.MetaMessage("track_name", name="Lead Guitar", time=0))
    guitar.append(mido.Message("note_on", note=64, velocity=90, channel=0, time=0))
    guitar.append(mido.Message("note_off", note=64, velocity=0, channel=0, time=240))
    guitar.append(mido.Message("note_on", note=67, velocity=100, channel=0, time=240))
    guitar.append(mido.Message("note_off", note=67, velocity=0, channel=0, time=480))
    midi.tracks.append(guitar)

    midi.save(path)


def test_load_midi_normalizes_notes_to_beats(tmp_path: Path) -> None:
    midi_path = tmp_path / "phrase.mid"
    _write_test_midi(midi_path)

    timeline = load_midi(midi_path)

    assert timeline.midi_type == 1
    assert timeline.ticks_per_beat == 480
    assert timeline.note_count == 2
    assert timeline.tempo_events[0].bpm == 96.0
    assert timeline.time_signature_events[0].numerator == 4
    assert timeline.time_signature_events[0].denominator == 4

    guitar = timeline.tracks[1]
    assert guitar.name == "Lead Guitar"

    first, second = guitar.notes
    assert first.pitch == 64
    assert first.start_tick == 0
    assert first.duration_ticks == 240
    assert first.start_beat == 0.0
    assert first.duration_beats == 0.5

    assert second.pitch == 67
    assert second.start_tick == 480
    assert second.duration_ticks == 480
    assert second.start_beat == 1.0
    assert second.duration_beats == 1.0
    assert timeline.duration_beats == 2.0


def test_missing_meta_uses_midi_defaults(tmp_path: Path) -> None:
    midi_path = tmp_path / "defaults.mid"
    midi = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.Message("note_on", note=60, velocity=80, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, time=480))
    midi.tracks.append(track)
    midi.save(midi_path)

    timeline = load_midi(midi_path)
    codes = {diagnostic.code for diagnostic in timeline.diagnostics}

    assert timeline.tempo_events[0].bpm == 120.0
    assert timeline.time_signature_events[0].numerator == 4
    assert timeline.time_signature_events[0].denominator == 4
    assert "default_tempo" in codes
    assert "default_time_signature" in codes


def test_unclosed_note_is_reported(tmp_path: Path) -> None:
    midi_path = tmp_path / "broken.mid"
    midi = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.Message("note_on", note=60, velocity=80, time=0))
    midi.tracks.append(track)
    midi.save(midi_path)

    timeline = load_midi(midi_path)

    assert timeline.note_count == 0
    assert any(diagnostic.code == "unclosed_note" for diagnostic in timeline.diagnostics)


def test_invalid_key_signature_is_ignored_without_losing_notes(
    tmp_path: Path,
) -> None:
    midi_path = tmp_path / "invalid-key.mid"
    midi = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("key_signature", key="C", time=0))
    track.append(mido.Message("note_on", note=64, velocity=90, time=0))
    track.append(mido.Message("note_off", note=64, velocity=0, time=480))
    midi.tracks.append(track)
    midi.save(midi_path)

    raw = bytearray(midi_path.read_bytes())
    signature = raw.find(b"\xff\x59\x02\x00\x00")
    assert signature >= 0
    raw[signature + 3] = 18
    raw[signature + 4] = 1
    midi_path.write_bytes(raw)

    timeline = load_midi(midi_path)

    assert timeline.note_count == 1
    diagnostic = next(
        item
        for item in timeline.diagnostics
        if item.code == "invalid_key_signature"
    )
    assert diagnostic.track_index == 0
    assert diagnostic.tick == 0
    assert "18 sharps/flats" in diagnostic.message
