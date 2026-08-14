from fretpilot.exporters.pdf_score.layout import (
    allocate_measure_widths,
    chunk_measures_for_systems,
    measure_required_width,
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
        fingering=IRFingering(string=1, fret=index % 12),
    )


def _measure(number: int, step: float, count: int) -> GuitarMeasure:
    start = (number - 1) * 4.0
    return GuitarMeasure(
        number=number,
        start_beat=start,
        duration_beats=4.0,
        numerator=4,
        denominator=4,
        events=[
            _event(index, start + index * step, step)
            for index in range(count)
        ],
    )


def test_required_width_grows_from_eighths_to_sixteenths_to_thirty_seconds():
    eighths = _measure(1, 0.5, 8)
    sixteenths = _measure(1, 0.25, 16)
    thirty_seconds = _measure(1, 0.125, 32)

    assert measure_required_width(eighths) == 112.0
    assert measure_required_width(sixteenths) == 190.0
    assert measure_required_width(thirty_seconds) == 366.0


def test_sparse_four_measure_line_stays_together():
    measures = [_measure(index + 1, 0.5, 8) for index in range(4)]
    chunks = chunk_measures_for_systems(
        measures,
        max_measures_per_system=4,
        available_width=720.0,
    )
    assert [[measure.number for measure in chunk] for chunk in chunks] == [
        [1, 2, 3, 4]
    ]


def test_dense_sixteenth_measures_break_before_spacing_is_compressed():
    measures = [_measure(index + 1, 0.25, 16) for index in range(4)]
    chunks = chunk_measures_for_systems(
        measures,
        max_measures_per_system=4,
        available_width=720.0,
    )
    assert [[measure.number for measure in chunk] for chunk in chunks] == [
        [1, 2, 3],
        [4],
    ]


def test_dense_measure_receives_more_width_than_sparse_neighbor():
    sparse = _measure(1, 0.5, 8)
    dense = _measure(2, 0.25, 16)
    widths = allocate_measure_widths(
        [sparse, dense],
        available_width=400.0,
    )
    assert widths[1] > widths[0]
    assert abs(sum(widths) - 400.0) < 1e-7


def test_single_extreme_measure_uses_full_system_width_without_reordering():
    extreme = _measure(1, 0.0625, 64)
    chunks = chunk_measures_for_systems(
        [extreme],
        max_measures_per_system=4,
        available_width=600.0,
    )
    assert chunks == [[extreme]]
    assert allocate_measure_widths([extreme], available_width=600.0) == [600.0]
