"""Score-layout rhythm helpers for the PDF/TAB renderer.

These helpers operate only on canonical score timing. They do not inspect
performance timing and they do not mutate Guitar IR.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import floor

from fretpilot.ir.models import GuitarMeasure


_EPSILON = 1e-9
_REST_GRID = 48
_REST_VALUES: tuple[tuple[int, float], ...] = (
    (192, 4.0),
    (144, 3.0),
    (96, 2.0),
    (72, 1.5),
    (64, 4 / 3),
    (48, 1.0),
    (36, 0.75),
    (32, 2 / 3),
    (24, 0.5),
    (18, 0.375),
    (16, 1 / 3),
    (12, 0.25),
    (9, 0.1875),
    (8, 1 / 6),
    (6, 0.125),
)
_BINARY_BASES = (4.0, 2.0, 1.0, 0.5, 0.25, 0.125)


@dataclass(frozen=True, slots=True)
class RestSpan:
    """A silent score-time interval inside one measure."""

    start_beat: float
    duration_beats: float

    @property
    def end_beat(self) -> float:
        return self.start_beat + self.duration_beats


@dataclass(frozen=True, slots=True)
class RhythmOnset:
    """One written rhythmic onset after collapsing simultaneous chord notes."""

    start_beat: float
    duration_beats: float
    beam_level: int
    metric_group: int

    @property
    def stemmed(self) -> bool:
        return self.duration_beats < 4.0 - _EPSILON

    @property
    def dot_count(self) -> int:
        for base in _BINARY_BASES:
            if abs(self.duration_beats - base * 1.5) <= 1e-7:
                return 1
        return 0

    @property
    def tuplet_number(self) -> int | None:
        for base in _BINARY_BASES:
            if abs(self.duration_beats - base * (2.0 / 3.0)) <= 1e-7:
                return 3
        return None


@dataclass(frozen=True, slots=True)
class BeamSegment:
    """A beam connecting onset indices at one beam level."""

    first_onset: int
    last_onset: int
    level: int


@dataclass(frozen=True, slots=True)
class TupletGroup:
    """A consecutive tuplet run to annotate in the rhythm lane."""

    first_onset: int
    last_onset: int
    number: int


def measure_rest_spans(measure: GuitarMeasure) -> list[RestSpan]:
    """Return raw silent spans after merging all score-event coverage."""

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


def _rest_decomposition(duration_beats: float) -> list[float] | None:
    units = round(duration_beats * _REST_GRID)
    if units <= 0:
        return []
    if abs(units / _REST_GRID - duration_beats) > 1e-7:
        return None

    best: list[list[int] | None] = [None] * (units + 1)
    best[0] = []
    for total in range(1, units + 1):
        candidates: list[list[int]] = []
        for value_units, _ in _REST_VALUES:
            if value_units > total or best[total - value_units] is None:
                continue
            candidates.append([value_units, *best[total - value_units]])
        if candidates:
            best[total] = min(
                candidates,
                key=lambda path: (len(path), tuple(-item for item in path)),
            )

    path = best[units]
    if path is None:
        return None
    value_by_units = dict(_REST_VALUES)
    return [value_by_units[item] for item in path]


def measure_notated_rests(measure: GuitarMeasure) -> list[RestSpan]:
    """Split raw silent spans into exact displayable durations when possible.

    The decomposition uses a 1/48-beat grid so binary, dotted, and triplet
    values down through dotted thirty-seconds remain exact. Unsupported raw
    spans are preserved as-is so the renderer can show their literal beat
    length rather than rounding them to a different note value.
    """

    result: list[RestSpan] = []
    for raw in measure_rest_spans(measure):
        parts = _rest_decomposition(raw.duration_beats)
        if parts is None:
            result.append(raw)
            continue
        cursor = raw.start_beat
        for duration in parts:
            result.append(RestSpan(cursor, duration))
            cursor += duration
    return result


def _beam_level(duration_beats: float) -> int:
    if duration_beats <= 0.125 + _EPSILON:
        return 3
    if duration_beats <= 0.25 + _EPSILON:
        return 2
    if duration_beats <= 0.5 + _EPSILON:
        return 1
    return 0


def _metric_group_size(measure: GuitarMeasure) -> float:
    denominator_unit = 4.0 / float(measure.denominator)
    if measure.numerator > 3 and measure.numerator % 3 == 0:
        return denominator_unit * 3.0
    return denominator_unit


def measure_rhythm_onsets(measure: GuitarMeasure) -> list[RhythmOnset]:
    """Collapse score events into one deterministic rhythmic onset per start time."""

    grouped: dict[float, list[float]] = defaultdict(list)
    for event in measure.events:
        grouped[round(float(event.score.start_beat), 9)].append(
            float(event.score.duration_beats)
        )

    group_size = _metric_group_size(measure)
    result: list[RhythmOnset] = []
    for start, durations in sorted(grouped.items()):
        duration = min(durations)
        relative = max(0.0, start - float(measure.start_beat))
        metric_group = int(floor((relative + _EPSILON) / group_size))
        result.append(
            RhythmOnset(
                start_beat=start,
                duration_beats=duration,
                beam_level=_beam_level(duration),
                metric_group=metric_group,
            )
        )
    return result


def measure_beam_segments(
    measure: GuitarMeasure,
    onsets: list[RhythmOnset] | None = None,
) -> list[BeamSegment]:
    """Return conservative beam runs that do not cross metric groups or rests."""

    active = measure_rhythm_onsets(measure) if onsets is None else list(onsets)
    if len(active) < 2:
        return []

    primary_runs: list[list[int]] = []
    current: list[int] = []
    for index, onset in enumerate(active):
        if onset.beam_level < 1:
            if len(current) >= 2:
                primary_runs.append(current)
            current = []
            continue

        if not current:
            current = [index]
            continue

        previous = active[current[-1]]
        touches_previous = (
            onset.start_beat
            <= previous.start_beat + previous.duration_beats + _EPSILON
        )
        same_metric_group = onset.metric_group == previous.metric_group
        if touches_previous and same_metric_group:
            current.append(index)
        else:
            if len(current) >= 2:
                primary_runs.append(current)
            current = [index]

    if len(current) >= 2:
        primary_runs.append(current)

    segments: list[BeamSegment] = []
    for run in primary_runs:
        segments.append(BeamSegment(run[0], run[-1], 1))
        max_level = max(active[index].beam_level for index in run)
        for level in range(2, max_level + 1):
            subrun: list[int] = []
            for index in run:
                if active[index].beam_level >= level:
                    if subrun and index != subrun[-1] + 1:
                        if len(subrun) >= 2:
                            segments.append(
                                BeamSegment(subrun[0], subrun[-1], level)
                            )
                        subrun = []
                    subrun.append(index)
                else:
                    if len(subrun) >= 2:
                        segments.append(BeamSegment(subrun[0], subrun[-1], level))
                    subrun = []
            if len(subrun) >= 2:
                segments.append(BeamSegment(subrun[0], subrun[-1], level))

    return segments


def measure_tuplet_groups(
    measure: GuitarMeasure,
    onsets: list[RhythmOnset] | None = None,
) -> list[TupletGroup]:
    """Return exact consecutive groups of three equal triplet-duration onsets."""

    active = measure_rhythm_onsets(measure) if onsets is None else list(onsets)
    groups: list[TupletGroup] = []
    index = 0
    while index + 2 < len(active):
        window = active[index : index + 3]
        duration = window[0].duration_beats
        if not all(item.tuplet_number == 3 for item in window):
            index += 1
            continue
        if not all(abs(item.duration_beats - duration) <= 1e-7 for item in window[1:]):
            index += 1
            continue
        if not all(
            abs(current.start_beat - (previous.start_beat + duration)) <= 1e-7
            for previous, current in zip(window, window[1:], strict=False)
        ):
            index += 1
            continue
        groups.append(TupletGroup(index, index + 2, 3))
        index += 3
    return groups
