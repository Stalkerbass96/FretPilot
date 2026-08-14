"""Density-aware system layout for the PDF/TAB review renderer.

The planner changes measure width and line breaks, never score-time ordering or
relative beat positions inside a measure.  This keeps the horizontal geometry
musically truthful while giving dense passages more room.
"""

from __future__ import annotations

from fretpilot.ir.models import GuitarMeasure


DEFAULT_MIN_ONSET_GAP = 11.0
DEFAULT_MIN_MEASURE_WIDTH = 112.0
DEFAULT_HORIZONTAL_PADDING = 14.0


def _distinct_onsets(measure: GuitarMeasure) -> list[float]:
    return sorted({round(float(event.score.start_beat), 9) for event in measure.events})


def measure_required_width(
    measure: GuitarMeasure,
    *,
    min_onset_gap: float = DEFAULT_MIN_ONSET_GAP,
    min_measure_width: float = DEFAULT_MIN_MEASURE_WIDTH,
    horizontal_padding: float = DEFAULT_HORIZONTAL_PADDING,
) -> float:
    """Width needed to preserve exact time ratios with a minimum onset gap."""

    starts = _distinct_onsets(measure)
    if len(starts) < 2 or measure.duration_beats <= 0:
        return float(min_measure_width)

    minimum_delta = min(
        current - previous
        for previous, current in zip(starts, starts[1:], strict=False)
        if current > previous
    )
    if minimum_delta <= 0:
        return float(min_measure_width)

    content_width = (
        float(min_onset_gap)
        * float(measure.duration_beats)
        / float(minimum_delta)
    )
    return max(
        float(min_measure_width),
        float(horizontal_padding) + content_width,
    )


def chunk_measures_for_systems(
    measures: list[GuitarMeasure],
    *,
    max_measures_per_system: int,
    available_width: float,
    min_onset_gap: float = DEFAULT_MIN_ONSET_GAP,
    min_measure_width: float = DEFAULT_MIN_MEASURE_WIDTH,
) -> list[list[GuitarMeasure]]:
    """Greedily break systems before density would force horizontal compression."""

    if max_measures_per_system < 1:
        raise ValueError("max_measures_per_system must be at least one")
    if available_width <= 0:
        raise ValueError("available_width must be positive")

    chunks: list[list[GuitarMeasure]] = []
    current: list[GuitarMeasure] = []
    current_required = 0.0

    for measure in measures:
        required = min(
            float(available_width),
            measure_required_width(
                measure,
                min_onset_gap=min_onset_gap,
                min_measure_width=min_measure_width,
            ),
        )
        would_overflow = (
            current
            and current_required + required > available_width + 1e-7
        )
        would_exceed_count = len(current) >= max_measures_per_system
        if would_overflow or would_exceed_count:
            chunks.append(current)
            current = []
            current_required = 0.0

        current.append(measure)
        current_required += required

    if current:
        chunks.append(current)
    return chunks


def allocate_measure_widths(
    measures: list[GuitarMeasure],
    *,
    available_width: float,
    min_onset_gap: float = DEFAULT_MIN_ONSET_GAP,
    min_measure_width: float = DEFAULT_MIN_MEASURE_WIDTH,
) -> list[float]:
    """Allocate one system's width while favoring measures that need more space."""

    if not measures:
        return []
    if available_width <= 0:
        raise ValueError("available_width must be positive")

    required = [
        min(
            float(available_width),
            measure_required_width(
                measure,
                min_onset_gap=min_onset_gap,
                min_measure_width=min_measure_width,
            ),
        )
        for measure in measures
    ]
    total_required = sum(required)
    if total_required <= available_width + 1e-7:
        extra = (available_width - total_required) / len(required)
        widths = [item + extra for item in required]
    else:
        scale = available_width / total_required
        widths = [item * scale for item in required]

    # Keep the total exact enough that the final barline lands on the system edge.
    correction = available_width - sum(widths)
    widths[-1] += correction
    return widths
