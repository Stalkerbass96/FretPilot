"""Score-layout rhythm helpers for the PDF/TAB renderer.

These helpers operate only on canonical score timing.  They do not inspect
performance timing and they do not mutate Guitar IR.
"""

from __future__ import annotations

from dataclasses import dataclass

from fretpilot.ir.models import GuitarMeasure


_EPSILON = 1e-9


@dataclass(frozen=True, slots=True)
class RestSpan:
    """A silent score-time interval inside one measure."""

    start_beat: float
    duration_beats: float

    @property
    def end_beat(self) -> float:
        return self.start_beat + self.duration_beats


def measure_rest_spans(measure: GuitarMeasure) -> list[RestSpan]:
    """Return deterministic silent spans after merging all score-event coverage.

    The current PDF renderer is a single-voice review layout, so overlapping
    notes/chords are treated as one occupied score interval.  Event intervals
    are clipped to the measure; gaps are emitted as rests in absolute score
    beats.
    """

    measure_start = float(measure.start_beat)
    measure_end = measure_start + float(measure.duration_beats)
    if measure_end <= measure_start + _EPSILON:
        return []

    intervals: list[tuple[float, float]] = []
    for event in measure.events:
        start = max(measure_start, float(event.score.start_beat))
        end = min(
            measure_end,
            float(event.score.start_beat) + float(event.score.duration_beats),
        )
        if end > start + _EPSILON:
            intervals.append((start, end))

    if not intervals:
        return [RestSpan(measure_start, measure_end - measure_start)]

    intervals.sort(key=lambda item: (item[0], item[1]))
    merged: list[list[float]] = []
    for start, end in intervals:
        if not merged or start > merged[-1][1] + _EPSILON:
            merged.append([start, end])
            continue
        merged[-1][1] = max(merged[-1][1], end)

    rests: list[RestSpan] = []
    cursor = measure_start
    for start, end in merged:
        if start > cursor + _EPSILON:
            rests.append(RestSpan(cursor, start - cursor))
        cursor = max(cursor, end)
    if measure_end > cursor + _EPSILON:
        rests.append(RestSpan(cursor, measure_end - cursor))
    return rests
