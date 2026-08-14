"""Deterministic target-neutral guitar performance planning."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import fmean
from typing import Any

from fretpilot.ir.models import GuitarNoteEvent, GuitarProjectIR, GuitarTrackIR
from fretpilot.performance.models import (
    GuitarPerformancePlan,
    PerformanceNoteIntent,
    PerformanceSectionIntent,
)

_EPSILON = 1e-9
_PATTERN = (-1.0, 0.5, 1.0, -0.5)


@dataclass(frozen=True, slots=True)
class _SourceRecord:
    event: GuitarNoteEvent
    section_id: str | None
    preferences: dict[str, float]


def _clamp_velocity(value: int) -> int:
    return max(1, min(127, value))


def _metric_accent(event: GuitarNoteEvent) -> float:
    beat = event.score.beat_in_measure
    nearest = round(beat)
    if abs(beat - nearest) > 1e-6:
        return 0.0
    if abs(beat) <= 1e-6:
        return 1.0
    return 0.5


def _performance_preferences(context: dict[str, Any] | None) -> dict[str, float]:
    if not context:
        return {}
    performance = context.get("performance", {})
    if not isinstance(performance, dict):
        return {}
    return {
        str(key): float(value)
        for key, value in performance.items()
        if isinstance(value, (int, float))
    }


def _preference(preferences: dict[str, float], key: str) -> float:
    return max(0.0, float(preferences.get(key, 1.0)))


def _section_intents(track: GuitarTrackIR) -> list[PerformanceSectionIntent]:
    results: list[PerformanceSectionIntent] = []
    for index, raw in enumerate(track.section_contexts):
        context = raw.get("playing_context", {})
        if not isinstance(context, dict):
            context = {}
        results.append(
            PerformanceSectionIntent(
                section_id=str(raw.get("section_id", f"section-{index + 1:03d}")),
                start_beat=float(raw.get("start_beat", 0.0)),
                end_beat=float(raw.get("end_beat", 0.0)),
                role_scores=dict(context.get("role_scores", {})),
                style_scores=dict(context.get("style_scores", {})),
                technique_scores=dict(context.get("technique_scores", {})),
                performance_preferences=_performance_preferences(context),
                knowledge_version=(
                    str(context["knowledge_version"])
                    if context.get("knowledge_version") is not None
                    else None
                ),
            )
        )
    return results


def _section_for_beat(
    sections: list[PerformanceSectionIntent],
    beat: float,
) -> PerformanceSectionIntent | None:
    for section in sections:
        if section.start_beat - _EPSILON <= beat < section.end_beat - _EPSILON:
            return section
    return None


def _source_events(track: GuitarTrackIR) -> list[GuitarNoteEvent]:
    """Return one performance event per original source note.

    Score notes may be split across measures with ties. Performance timing is
    source-note based, so the first score fragment is enough to represent the
    original note in the performance plan.
    """

    by_source: dict[int, GuitarNoteEvent] = {}
    events = [event for measure in track.measures for event in measure.events]
    for event in sorted(events, key=lambda item: (item.score.start_beat, item.id)):
        by_source.setdefault(event.source_note_index, event)
    return sorted(
        by_source.values(),
        key=lambda item: (
            item.performance.source_start_beat,
            item.source_note_index,
        ),
    )


def _records(
    track: GuitarTrackIR,
    sections: list[PerformanceSectionIntent],
) -> list[_SourceRecord]:
    records: list[_SourceRecord] = []
    for event in _source_events(track):
        section = _section_for_beat(
            sections,
            event.performance.source_start_beat,
        )
        if section is not None:
            preferences = section.performance_preferences
            section_id = section.section_id
        else:
            preferences = _performance_preferences(track.playing_context)
            section_id = None
        records.append(
            _SourceRecord(
                event=event,
                section_id=section_id,
                preferences=preferences,
            )
        )
    return records


def _section_velocity_means(records: list[_SourceRecord]) -> dict[str | None, float]:
    grouped: dict[str | None, list[int]] = defaultdict(list)
    for item in records:
        grouped[item.section_id].append(item.event.performance.velocity)
    return {key: fmean(values) for key, values in grouped.items() if values}


def _next_later_onset(records: list[_SourceRecord]) -> dict[float, float | None]:
    onsets = sorted({item.event.performance.source_start_beat for item in records})
    result: dict[float, float | None] = {}
    for index, onset in enumerate(onsets):
        result[onset] = onsets[index + 1] if index + 1 < len(onsets) else None
    return result


def _target_start(
    event: GuitarNoteEvent,
    *,
    timing_looseness: float,
    pattern: float,
) -> tuple[float, str | None]:
    source = event.performance.source_start_beat
    if timing_looseness < 1.0:
        amount = min(1.0, 1.0 - timing_looseness)
        target = source + (event.score.start_beat - source) * amount
        return max(0.0, target), "tighten_toward_score_grid"
    if timing_looseness > 1.0:
        offset = pattern * 0.02 * (timing_looseness - 1.0)
        return max(0.0, source + offset), "apply_context_microtiming"
    return source, None


def _target_duration(
    event: GuitarNoteEvent,
    *,
    next_onset: float | None,
    note_overlap: float,
) -> tuple[float, str | None]:
    source_duration = event.performance.source_duration_beats
    source_start = event.performance.source_start_beat
    if next_onset is None or next_onset <= source_start + _EPSILON:
        return source_duration, None

    onset_distance = next_onset - source_start
    source_overlap = max(0.0, source_duration - onset_distance)

    if note_overlap < 1.0 and source_overlap > 0.0:
        target = onset_distance + source_overlap * note_overlap
        return max(0.01, target), "reduce_source_note_overlap"

    if note_overlap > 1.0:
        if source_overlap > 0.0:
            target = onset_distance + source_overlap * note_overlap
        else:
            target = source_duration + min(
                onset_distance * 0.25,
                0.03 * (note_overlap - 1.0),
            )
        return max(0.01, target), "increase_note_overlap_intent"

    return source_duration, None


def build_performance_plan(
    project: GuitarProjectIR,
    *,
    track_index: int = 0,
) -> GuitarPerformancePlan:
    """Convert canonical Guitar IR into target-neutral guitarist performance intent.

    Neutral preferences preserve source timing, duration, and velocity. Context
    preferences may deterministically tighten/loosen timing, even out or vary
    velocity, strengthen metric accents, and alter overlap intent. No target
    plugin controls are emitted here.
    """

    if not 0 <= track_index < len(project.tracks):
        raise ValueError("track_index is outside the GuitarProjectIR track list.")

    track = project.tracks[track_index]
    sections = _section_intents(track)
    records = _records(track, sections)
    velocity_means = _section_velocity_means(records)
    next_onsets = _next_later_onset(records)
    warnings: list[str] = []

    if not sections and track.playing_context is None:
        warnings.append(
            "No PlayingContext provenance was available; neutral performance preferences were used."
        )

    notes: list[PerformanceNoteIntent] = []
    for sequence_index, item in enumerate(records):
        event = item.event
        preferences = item.preferences
        pattern = _PATTERN[sequence_index % len(_PATTERN)]
        reasons: list[str] = []

        timing_looseness = _preference(preferences, "timing_looseness")
        velocity_variation = _preference(preferences, "velocity_variation")
        note_overlap = _preference(preferences, "note_overlap")
        accent_strength = _preference(preferences, "accent_strength")

        target_start, timing_reason = _target_start(
            event,
            timing_looseness=timing_looseness,
            pattern=pattern,
        )
        if timing_reason is not None and abs(
            target_start - event.performance.source_start_beat
        ) > _EPSILON:
            reasons.append(timing_reason)

        target_duration, duration_reason = _target_duration(
            event,
            next_onset=next_onsets[event.performance.source_start_beat],
            note_overlap=note_overlap,
        )
        if duration_reason is not None and abs(
            target_duration - event.performance.source_duration_beats
        ) > _EPSILON:
            reasons.append(duration_reason)

        source_velocity = event.performance.velocity
        target_velocity = float(source_velocity)
        section_mean = velocity_means.get(item.section_id, float(source_velocity))

        if velocity_variation < 1.0:
            target_velocity += (
                section_mean - source_velocity
            ) * min(1.0, 1.0 - velocity_variation)
            if abs(target_velocity - source_velocity) >= 0.5:
                reasons.append("even_section_velocity")
        elif velocity_variation > 1.0:
            target_velocity += pattern * 6.0 * (velocity_variation - 1.0)
            if abs(target_velocity - source_velocity) >= 0.5:
                reasons.append("apply_context_velocity_variation")

        accent = _metric_accent(event)
        accent_delta = accent * 8.0 * (accent_strength - 1.0)
        if abs(accent_delta) >= 0.5:
            target_velocity += accent_delta
            reasons.append("apply_metric_accent_strength")

        final_velocity = _clamp_velocity(round(target_velocity))
        notes.append(
            PerformanceNoteIntent(
                source_note_index=event.source_note_index,
                pitch=event.pitch,
                section_id=item.section_id,
                source_start_beat=event.performance.source_start_beat,
                source_duration_beats=event.performance.source_duration_beats,
                source_velocity=source_velocity,
                target_start_beat=target_start,
                target_duration_beats=target_duration,
                target_velocity=final_velocity,
                timing_offset_beats=(
                    target_start - event.performance.source_start_beat
                ),
                duration_delta_beats=(
                    target_duration - event.performance.source_duration_beats
                ),
                velocity_delta=final_velocity - source_velocity,
                metric_accent=accent,
                reasons=reasons,
            )
        )

    return GuitarPerformancePlan(
        source=project.source,
        track_id=track.id,
        source_stream_id=track.source_stream_id,
        notes=notes,
        sections=sections,
        warnings=warnings,
    )
