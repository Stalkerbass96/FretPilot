from __future__ import annotations

from fretpilot.analysis import analyze_guitar_track
from fretpilot.detection.models import InstrumentStream
from fretpilot.ir import build_guitar_ir
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)
from fretpilot.rewrite import DEFAULT_MIDI_FIDELITY, rewrite_instrument_stream


def _note(
    pitch: int,
    start_beat: float,
    *,
    duration: float = 0.5,
    velocity: int = 90,
) -> NormalizedNote:
    return NormalizedNote(
        track_index=0,
        track_name="Guitar",
        channel=0,
        pitch=pitch,
        velocity=velocity,
        start_tick=round(start_beat * 480),
        duration_ticks=max(1, round(duration * 480)),
        start_beat=start_beat,
        duration_beats=duration,
        program=27,
    )


def _stream(notes: list[NormalizedNote]) -> InstrumentStream:
    return InstrumentStream(
        stream_id="t0:ch0:p27",
        source_track_index=0,
        source_track_name="Guitar",
        channel=0,
        program=27,
        program_name="Electric Guitar (clean)",
        program_family="guitar",
        instrument_name=None,
        notes=notes,
    )


def test_full_midi_fidelity_is_an_exact_passthrough() -> None:
    source = _stream(
        [
            _note(36, 0.0),
            _note(64, 0.5),
            _note(64, 0.5),
        ]
    )

    result = rewrite_instrument_stream(source, midi_fidelity=1.0)

    assert result.stream.notes == source.notes
    assert result.source_note_indices == [0, 1, 2]
    assert result.source_note_origins == ["midi", "midi", "midi"]
    assert result.changes == []


def test_default_policy_repairs_out_of_range_pitch_and_records_provenance() -> None:
    source = _stream([_note(36, 0.0), _note(64, 0.5)])

    result = rewrite_instrument_stream(source)

    assert DEFAULT_MIDI_FIDELITY < 0.5
    assert [note.pitch for note in result.stream.notes] == [48, 64]
    assert result.source_note_indices == [0, 1]
    assert result.source_note_origins == ["midi", "midi"]
    change = result.changes[0]
    assert change.operation == "transpose"
    assert change.source_note_index == 0
    assert change.before == {"pitch": 36}
    assert change.after == {"pitch": 48}
    assert change.reason == "fit_standard_guitar_range_by_octave"


def test_default_policy_removes_an_exact_duplicate() -> None:
    source = _stream(
        [
            _note(64, 0.0, duration=0.25, velocity=70),
            _note(64, 0.0, duration=0.5, velocity=90),
            _note(66, 0.5),
        ]
    )

    result = rewrite_instrument_stream(source)

    assert [(note.pitch, note.start_beat, note.duration_beats) for note in result.stream.notes] == [
        (64, 0.0, 0.5),
        (66, 0.5, 0.5),
    ]
    assert result.source_note_indices == [1, 2]
    deleted = next(change for change in result.changes if change.operation == "delete")
    assert deleted.source_note_index == 0
    assert deleted.reason == "duplicate_same_pitch_onset"


def test_default_policy_fills_one_strong_missing_repeated_pulse() -> None:
    source = _stream(
        [
            _note(52, 0.0),
            _note(52, 0.5),
            _note(52, 1.5),
            _note(52, 2.0),
        ]
    )

    result = rewrite_instrument_stream(source)

    assert [note.start_beat for note in result.stream.notes] == [0.0, 0.5, 1.0, 1.5, 2.0]
    inserted_index = result.stream.notes.index(next(note for note in result.stream.notes if note.start_beat == 1.0))
    assert result.source_note_origins[inserted_index] == "synthetic"
    assert result.source_note_indices[inserted_index] == len(source.notes)
    inserted = next(change for change in result.changes if change.operation == "insert")
    assert inserted.source_note_index == len(source.notes)
    assert inserted.reason == "fill_missing_repeated_pulse"


def test_fidelity_continuum_applies_only_high_confidence_rewrites_near_midi_end() -> None:
    source = _stream(
        [
            _note(36, 0.0),
            _note(52, 0.5),
            _note(52, 1.0),
            _note(52, 2.0),
            _note(52, 2.5),
        ]
    )

    result = rewrite_instrument_stream(source, midi_fidelity=0.90)

    # The physically impossible pitch is a higher-confidence repair than the
    # inferred missing pulse, so the continuum does not behave like a binary preset.
    assert result.stream.notes[0].pitch == 48
    assert not any(change.operation == "insert" for change in result.changes)


def test_rewrite_provenance_is_carried_into_guitar_ir() -> None:
    source = _stream(
        [
            _note(52, 0.0),
            _note(52, 0.5),
            _note(52, 1.5),
            _note(52, 2.0),
        ]
    )
    timeline = NormalizedTimeline(
        source="rewrite.mid",
        midi_type=1,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(tick=0, beat=0.0, bpm=120.0)],
        time_signature_events=[
            TimeSignatureEvent(tick=0, beat=0.0, numerator=4, denominator=4)
        ],
        tracks=[NormalizedTrack(index=0, name="Guitar", notes=source.notes)],
    )
    rewrite = rewrite_instrument_stream(source)
    track = rewrite.stream.as_track()
    analysis = analyze_guitar_track(track)

    project = build_guitar_ir(
        timeline,
        track,
        analysis,
        source_stream_id=source.stream_id,
        source_note_indices=rewrite.source_note_indices,
        source_note_origins=rewrite.source_note_origins,
        rewrite_changes=rewrite.changes,
    )

    events = [event for measure in project.tracks[0].measures for event in measure.events]
    inserted = next(event for event in events if event.performance.source_start_beat == 1.0)
    assert inserted.source_note_index == 4
    assert inserted.source_note_origin == "synthetic"
    assert any(
        change.stage == "note_rewrite_insert"
        and change.source_note_index == 4
        for change in project.changes
    )
