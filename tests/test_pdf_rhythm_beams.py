from fretpilot.exporters.pdf_score.rhythm import (
    BeamSegment,
    measure_beam_segments,
    measure_rhythm_onsets,
)
from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    IRFingering,
    PerformanceTiming,
    ScoreTiming,
)


def _event(index: int, start: float, duration: float) -> GuitarNoteEvent:
    return GuitarNoteEvent(
        id=f"n-{index}",
        source_note_index=index,
        pitch=60 + index,
        score=ScoreTiming(
            start_beat=start,
            duration_beats=duration,
            measure_number=1,
            beat_in_measure=start,
        ),
        performance=PerformanceTiming(
            source_start_beat=start,
            source_duration_beats=duration,
            velocity=90,
        ),
        fingering=IRFingering(string=1, fret=index),
    )


def _measure(events, *, numerator=4, denominator=4):
    return GuitarMeasure(
        number=1,
        start_beat=0.0,
        duration_beats=numerator * (4.0 / denominator),
        numerator=numerator,
        denominator=denominator,
        events=list(events),
    )


def test_simultaneous_chord_collapses_to_one_rhythm_onset():
    onsets = measure_rhythm_onsets(
        _measure([_event(0, 0.0, 0.5), _event(1, 0.0, 0.5)])
    )
    assert len(onsets) == 1
    assert onsets[0].start_beat == 0.0
    assert onsets[0].beam_level == 1


def test_four_eighths_beam_in_pairs_by_quarter_beat_in_four_four():
    measure = _measure(
        [
            _event(0, 0.0, 0.5),
            _event(1, 0.5, 0.5),
            _event(2, 1.0, 0.5),
            _event(3, 1.5, 0.5),
        ]
    )
    onsets = measure_rhythm_onsets(measure)
    assert [item.metric_group for item in onsets] == [0, 0, 1, 1]
    assert measure_beam_segments(measure, onsets) == [
        BeamSegment(0, 1, 1),
        BeamSegment(2, 3, 1),
    ]


def test_sixteenth_run_gets_primary_and_secondary_beams():
    measure = _measure(
        [
            _event(0, 0.0, 0.25),
            _event(1, 0.25, 0.25),
            _event(2, 0.5, 0.25),
            _event(3, 0.75, 0.25),
        ]
    )
    onsets = measure_rhythm_onsets(measure)
    assert measure_beam_segments(measure, onsets) == [
        BeamSegment(0, 3, 1),
        BeamSegment(0, 3, 2),
    ]


def test_beam_does_not_cross_explicit_silent_gap():
    measure = _measure(
        [
            _event(0, 0.0, 0.25),
            _event(1, 0.5, 0.25),
        ]
    )
    assert measure_beam_segments(measure) == []


def test_six_eight_groups_eighth_notes_in_dotted_quarter_pulses():
    measure = _measure(
        [_event(index, index * 0.5, 0.5) for index in range(6)],
        numerator=6,
        denominator=8,
    )
    onsets = measure_rhythm_onsets(measure)
    assert [item.metric_group for item in onsets] == [0, 0, 0, 1, 1, 1]
    assert measure_beam_segments(measure, onsets) == [
        BeamSegment(0, 2, 1),
        BeamSegment(3, 5, 1),
    ]
