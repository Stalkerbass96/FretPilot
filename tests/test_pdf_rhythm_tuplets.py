from fretpilot.exporters.pdf_score.rhythm import (
    TupletGroup,
    measure_rhythm_onsets,
    measure_tuplet_groups,
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


def _measure(events) -> GuitarMeasure:
    return GuitarMeasure(
        number=1,
        start_beat=0.0,
        duration_beats=4.0,
        numerator=4,
        denominator=4,
        events=list(events),
    )


def test_dotted_eighth_keeps_one_beam_and_dot_semantics():
    onset = measure_rhythm_onsets(_measure([_event(0, 0.0, 0.75)]))[0]
    assert onset.dot_count == 1
    assert onset.tuplet_number is None
    assert onset.beam_level == 1


def test_dotted_sixteenth_keeps_two_beams():
    onset = measure_rhythm_onsets(_measure([_event(0, 0.0, 0.375)]))[0]
    assert onset.dot_count == 1
    assert onset.beam_level == 2


def test_eighth_triplet_has_one_beam_and_triplet_semantics():
    onset = measure_rhythm_onsets(_measure([_event(0, 0.0, 1 / 3)]))[0]
    assert onset.dot_count == 0
    assert onset.tuplet_number == 3
    assert onset.beam_level == 1


def test_quarter_triplet_is_triplet_but_unbeamed():
    onset = measure_rhythm_onsets(_measure([_event(0, 0.0, 2 / 3)]))[0]
    assert onset.tuplet_number == 3
    assert onset.beam_level == 0


def test_three_equal_triplet_onsets_form_one_group():
    measure = _measure(
        [_event(index, index / 3, 1 / 3) for index in range(3)]
    )
    assert measure_tuplet_groups(measure) == [TupletGroup(0, 2, 3)]


def test_six_equal_triplet_onsets_form_two_groups():
    measure = _measure(
        [_event(index, index / 3, 1 / 3) for index in range(6)]
    )
    assert measure_tuplet_groups(measure) == [
        TupletGroup(0, 2, 3),
        TupletGroup(3, 5, 3),
    ]


def test_incomplete_triplet_run_is_not_labeled():
    measure = _measure([_event(0, 0.0, 1 / 3), _event(1, 1 / 3, 1 / 3)])
    assert measure_tuplet_groups(measure) == []
