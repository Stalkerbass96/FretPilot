"""Deterministic measure-aware section segmentation baseline.

This module answers only *where guitar behavior changes*. It deliberately does
not decide whether a region is a riff, solo, metal passage, etc.; those labels
belong to the behavior/PlayingContext layer that consumes these stable regions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from fretpilot.detection.guitar_classifier import extract_behavior_features
from fretpilot.detection.models import InstrumentStream
from fretpilot.midi.models import NormalizedTimeline


@dataclass(frozen=True, slots=True)
class MeasureRegion:
    number: int
    start_beat: float
    end_beat: float
    numerator: int
    denominator: int


@dataclass(slots=True)
class GuitarSection:
    section_id: str
    stream_id: str
    start_measure: int
    end_measure: int
    start_beat: float
    end_beat: float
    features: dict[str, Any]
    boundary_confidence: float
    boundary_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SectionSegmentation:
    stream_id: str
    window_measures: int
    change_threshold: float
    sections: list[GuitarSection]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_FEATURE_DISTANCE_KEYS = (
    "monophonic_onset_ratio",
    "chord_onset_ratio",
    "repeated_pitch_ratio",
    "low_register_ratio",
    "short_note_ratio",
    "adjacent_interval_within_octave_ratio",
)


def _measure_regions(timeline: NormalizedTimeline, end_beat: float) -> list[MeasureRegion]:
    signatures = sorted(timeline.time_signature_events, key=lambda event: event.beat)
    if not signatures:
        raise ValueError("NormalizedTimeline must contain at least one time signature.")

    regions: list[MeasureRegion] = []
    cursor = 0.0
    signature_index = 0
    current = signatures[0]
    number = 1

    while cursor < end_beat - 1e-9 or not regions:
        while (
            signature_index + 1 < len(signatures)
            and signatures[signature_index + 1].beat <= cursor + 1e-9
        ):
            signature_index += 1
            current = signatures[signature_index]

        length = current.numerator * (4.0 / current.denominator)
        if length <= 0:
            raise ValueError("Time signature produced a non-positive measure length.")

        natural_end = cursor + length
        next_change = (
            signatures[signature_index + 1].beat
            if signature_index + 1 < len(signatures)
            else None
        )
        region_end = natural_end
        if next_change is not None and cursor < next_change < natural_end:
            region_end = next_change

        regions.append(
            MeasureRegion(
                number=number,
                start_beat=cursor,
                end_beat=region_end,
                numerator=current.numerator,
                denominator=current.denominator,
            )
        )
        cursor = region_end
        number += 1

    return regions


def _window_stream(
    stream: InstrumentStream,
    *,
    start_beat: float,
    end_beat: float,
) -> InstrumentStream:
    notes = [
        note
        for note in stream.notes
        if start_beat <= note.start_beat < end_beat
    ]
    return replace(stream, notes=notes)


def _features_for_range(
    stream: InstrumentStream,
    *,
    start_beat: float,
    end_beat: float,
) -> dict[str, Any]:
    return extract_behavior_features(
        _window_stream(stream, start_beat=start_beat, end_beat=end_beat)
    ).to_dict()


def _feature_distance(previous: dict[str, Any], current: dict[str, Any]) -> float:
    values: list[float] = []
    for key in _FEATURE_DISTANCE_KEYS:
        values.append(abs(float(current[key]) - float(previous[key])))

    # Polyphony contains useful change information but has a different numeric
    # scale, so normalize it to a guitar-sized six-string range.
    previous_polyphony = min(6.0, float(previous["mean_onset_polyphony"])) / 6.0
    current_polyphony = min(6.0, float(current["mean_onset_polyphony"])) / 6.0
    values.append(abs(current_polyphony - previous_polyphony))

    # Pitch range is normalized to four octaves so lead/riff register changes
    # matter without dominating chord/monophony changes.
    previous_range = min(48.0, float(previous["pitch_range_semitones"])) / 48.0
    current_range = min(48.0, float(current["pitch_range_semitones"])) / 48.0
    values.append(abs(current_range - previous_range))

    return sum(values) / len(values) if values else 0.0


def segment_instrument_stream(
    timeline: NormalizedTimeline,
    stream: InstrumentStream,
    *,
    window_measures: int = 2,
    change_threshold: float = 0.22,
) -> SectionSegmentation:
    """Split one instrument stream at coarse behavior-feature change points.

    The baseline uses non-overlapping measure windows. Adjacent windows merge
    when their normalized behavior-feature distance stays below the threshold.
    This is intentionally deterministic and conservative; future segmentation
    models may improve the boundary ranking while preserving this data contract.
    """

    if window_measures <= 0:
        raise ValueError("window_measures must be positive.")
    if not 0.0 <= change_threshold <= 1.0:
        raise ValueError("change_threshold must be between 0 and 1.")

    end_beat = max((note.end_beat for note in stream.notes), default=0.0)
    measures = _measure_regions(timeline, end_beat)

    windows: list[tuple[int, int, float, float, dict[str, Any]]] = []
    for index in range(0, len(measures), window_measures):
        group = measures[index : index + window_measures]
        if not group:
            continue
        start = group[0].start_beat
        end = group[-1].end_beat
        features = _features_for_range(stream, start_beat=start, end_beat=end)
        windows.append((group[0].number, group[-1].number, start, end, features))

    if not windows:
        return SectionSegmentation(
            stream_id=stream.stream_id,
            window_measures=window_measures,
            change_threshold=change_threshold,
            sections=[],
        )

    grouped: list[list[tuple[int, int, float, float, dict[str, Any]]]] = [[windows[0]]]
    boundary_distances: list[float] = [0.0]

    for window in windows[1:]:
        previous = grouped[-1][-1]
        distance = _feature_distance(previous[4], window[4])
        if distance >= change_threshold:
            grouped.append([window])
            boundary_distances.append(distance)
        else:
            grouped[-1].append(window)

    sections: list[GuitarSection] = []
    for index, group in enumerate(grouped):
        start_measure = group[0][0]
        end_measure = group[-1][1]
        start_beat = group[0][2]
        end_beat = group[-1][3]
        distance = boundary_distances[index]
        sections.append(
            GuitarSection(
                section_id=f"{stream.stream_id}:sec{index + 1}",
                stream_id=stream.stream_id,
                start_measure=start_measure,
                end_measure=end_measure,
                start_beat=start_beat,
                end_beat=end_beat,
                features=_features_for_range(
                    stream,
                    start_beat=start_beat,
                    end_beat=end_beat,
                ),
                boundary_confidence=(
                    1.0
                    if index == 0
                    else round(min(1.0, distance / max(change_threshold, 1e-9)), 6)
                ),
                boundary_reason=(
                    "start_of_stream"
                    if index == 0
                    else f"behavior_feature_distance={distance:.6f}"
                ),
            )
        )

    return SectionSegmentation(
        stream_id=stream.stream_id,
        window_measures=window_measures,
        change_threshold=change_threshold,
        sections=sections,
    )
