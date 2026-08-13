from __future__ import annotations

from fretpilot.analysis import segment_instrument_stream
from fretpilot.detection.models import InstrumentStream
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)


def _note(pitch: int, start_beat: float, duration: float = 0.5) -> NormalizedNote:
    return NormalizedNote(
        track_index=0,
        track_name="Guitar",
        channel=0,
        pitch=pitch,
        velocity=90,
        start_tick=round(start_beat * 480),
        duration_ticks=round(duration * 480),
        start_beat=start_beat,
        duration_beats=duration,
        program=27,
    )


def _fixture() -> tuple[NormalizedTimeline, InstrumentStream]:
    notes: list[NormalizedNote] = []

    # Bars 1-2: low repeated riff, monophonic eighth-note pedal behavior.
    for step in range(16):
        notes.append(_note(40 if step % 4 else 43, step * 0.5))

    # Bars 3-4: block-chord rhythm, three notes on every quarter-note onset.
    for step in range(8):
        onset = 8.0 + step
        for pitch in (52, 59, 64):
            notes.append(_note(pitch, onset, 0.75))

    # Bars 5-6: high single-note lead line with broad pitch movement.
    solo_pitches = [64, 67, 71, 74, 76, 79, 83, 86, 84, 81, 77, 74, 72, 69, 67, 64]
    for step, pitch in enumerate(solo_pitches):
        notes.append(_note(pitch, 16.0 + step * 0.5))

    track = NormalizedTrack(index=0, name="Guitar", notes=notes)
    timeline = NormalizedTimeline(
        source="sections.mid",
        midi_type=1,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(tick=0, beat=0.0, bpm=120.0)],
        time_signature_events=[
            TimeSignatureEvent(tick=0, beat=0.0, numerator=4, denominator=4)
        ],
        tracks=[track],
    )
    stream = InstrumentStream(
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
    return timeline, stream


def test_two_measure_windows_detect_three_behavior_regions() -> None:
    timeline, stream = _fixture()

    result = segment_instrument_stream(
        timeline,
        stream,
        window_measures=2,
        change_threshold=0.20,
    )

    assert result.stream_id == stream.stream_id
    assert [(section.start_measure, section.end_measure) for section in result.sections] == [
        (1, 2),
        (3, 4),
        (5, 6),
    ]
    assert result.sections[0].features["repeated_pitch_ratio"] > 0.5
    assert result.sections[1].features["chord_onset_ratio"] == 1.0
    assert result.sections[2].features["monophonic_onset_ratio"] == 1.0
    assert all(section.boundary_confidence >= 0.0 for section in result.sections)


def test_similar_adjacent_windows_merge_into_one_section() -> None:
    timeline, stream = _fixture()
    # Keep only the first four bars of repeated-riff material by duplicating the
    # same behavior into bars 3-4 instead of the chord block.
    notes = [_note(40 if step % 4 else 43, step * 0.5) for step in range(32)]
    stream.notes = notes
    timeline.tracks[0].notes = notes

    result = segment_instrument_stream(
        timeline,
        stream,
        window_measures=2,
        change_threshold=0.20,
    )

    assert len(result.sections) == 1
    assert result.sections[0].start_measure == 1
    assert result.sections[0].end_measure == 4
