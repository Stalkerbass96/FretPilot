from fretpilot.exporters.pdf_score.rhythm import RestSpan, measure_rest_spans
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


def test_middle_note_leaves_leading_and_trailing_rests():
    assert measure_rest_spans(_measure([_event(0, 1.0, 1.0)])) == [
        RestSpan(0.0, 1.0),
        RestSpan(2.0, 2.0),
    ]


def test_overlapping_chord_coverage_merges_before_rest_detection():
    assert measure_rest_spans(
        _measure([_event(0, 0.0, 2.0), _event(1, 0.0, 1.0)])
    ) == [RestSpan(2.0, 2.0)]


def test_measure_start_fragment_prevents_false_initial_rest():
    assert measure_rest_spans(_measure([_event(0, 0.0, 1.5)])) == [
        RestSpan(1.5, 2.5)
    ]


def test_full_measure_event_has_no_rest():
    assert measure_rest_spans(_measure([_event(0, 0.0, 4.0)])) == []


def test_empty_measure_is_one_full_measure_rest():
    assert measure_rest_spans(_measure([])) == [RestSpan(0.0, 4.0)]
