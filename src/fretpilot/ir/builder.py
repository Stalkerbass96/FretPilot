"""Build canonical Guitar IR from the current deterministic analysis stack."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from math import floor
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from fretpilot.analysis.guitar import GuitarTrackAnalysis
from fretpilot.guitar.instrument import STANDARD_TUNING
from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
    IRArticulation,
    IRFingering,
    IRTempoEvent,
    IRTimeSignatureEvent,
    NoteConfidence,
    PerformanceTiming,
    ScoreTiming,
    Transformation,
)
from fretpilot.midi.models import NormalizedNote, NormalizedTimeline, NormalizedTrack

if TYPE_CHECKING:
    from fretpilot.rewrite.models import NoteRewriteChange

_EPSILON = 1e-8


@dataclass(frozen=True, slots=True)
class _MeasureBoundary:
    number: int
    start_beat: float
    end_beat: float
    numerator: int
    denominator: int


@dataclass(frozen=True, slots=True)
class _NotatedNote:
    source_index: int
    note: NormalizedNote
    start_beat: float
    duration_beats: float
    rhythm_confidence: float
    let_ring_inferred: bool = False
    pre_overlap_duration_beats: float | None = None
    overlap_reasons: tuple[str, ...] = ()

    @property
    def end_beat(self) -> float:
        return self.start_beat + self.duration_beats


def _round_to_grid(value: float, step: float) -> float:
    if step <= 0:
        return value
    units = max(1, int(floor(value / step + 0.5)))
    return units * step


def _clip_notated_duration(
    item: _NotatedNote,
    *,
    duration_beats: float,
    reason: str,
) -> _NotatedNote:
    if item.duration_beats <= duration_beats + _EPSILON:
        return item
    return replace(
        item,
        duration_beats=duration_beats,
        let_ring_inferred=True,
        pre_overlap_duration_beats=(
            item.pre_overlap_duration_beats
            if item.pre_overlap_duration_beats is not None
            else item.duration_beats
        ),
        overlap_reasons=(*item.overlap_reasons, reason),
    )


def _normalize_ringing_overlaps(
    prepared: list[_NotatedNote],
) -> list[_NotatedNote]:
    """Create readable one-voice score timing while preserving performance.

    Two common guitar-MIDI patterns are normalized:

    * arpeggiated notes ring beyond the next pick attack;
    * notes struck as one chord have unequal source note-off times.

    In both cases FretPilot shortens only the written score duration and marks
    the affected note ``let_ring``. Original source timing remains available to
    performance renderers such as the Ample Guitar adapter.

    True independent polyphony still belongs to the later voice-separation
    stage and is not silently flattened here.
    """

    onset_groups: dict[float, list[int]] = defaultdict(list)
    for index, item in enumerate(prepared):
        onset_groups[round(item.start_beat, 9)].append(index)

    ordered_onsets = sorted(onset_groups)
    normalized = list(prepared)

    for onset_index, onset in enumerate(ordered_onsets[:-1]):
        next_onset = ordered_onsets[onset_index + 1]
        available_duration = next_onset - onset
        if available_duration <= _EPSILON:
            continue

        for note_index in onset_groups[onset]:
            normalized[note_index] = _clip_notated_duration(
                normalized[note_index],
                duration_beats=available_duration,
                reason="clip_written_duration_at_next_attack",
            )

    for onset in ordered_onsets:
        indices = onset_groups[onset]
        if len(indices) < 2:
            continue
        common_duration = min(normalized[index].duration_beats for index in indices)
        for note_index in indices:
            normalized[note_index] = _clip_notated_duration(
                normalized[note_index],
                duration_beats=common_duration,
                reason="normalize_same_onset_chord_duration",
            )

    return normalized


def _prepare_notated_notes(
    track: NormalizedTrack,
    analysis: GuitarTrackAnalysis,
) -> list[_NotatedNote]:
    suggestions = {item.note_index: item for item in analysis.rhythm.suggestions}
    step = analysis.rhythm.selected_grid.step_beats
    prepared: list[_NotatedNote] = []

    for note_index, note in enumerate(track.notes):
        suggestion = suggestions[note_index]
        duration = _round_to_grid(note.duration_beats, step)
        prepared.append(
            _NotatedNote(
                source_index=note_index,
                note=note,
                start_beat=suggestion.target_start_beat,
                duration_beats=duration,
                rhythm_confidence=suggestion.confidence,
            )
        )

    return _normalize_ringing_overlaps(prepared)


def _build_measure_boundaries(
    timeline: NormalizedTimeline,
    end_beat: float,
) -> tuple[list[_MeasureBoundary], list[str]]:
    signatures = sorted(timeline.time_signature_events, key=lambda event: event.beat)
    warnings: list[str] = []
    if not signatures:
        raise ValueError("NormalizedTimeline must contain at least one time signature.")

    boundaries: list[_MeasureBoundary] = []
    cursor = 0.0
    signature_index = 0
    current = signatures[0]
    measure_number = 1
    required_end = max(end_beat, 0.0)

    while cursor < required_end - _EPSILON or not boundaries:
        while (
            signature_index + 1 < len(signatures)
            and signatures[signature_index + 1].beat <= cursor + _EPSILON
        ):
            signature_index += 1
            current = signatures[signature_index]

        measure_length = current.numerator * (4.0 / current.denominator)
        if measure_length <= 0:
            raise ValueError("Time signature produced a non-positive measure length.")

        natural_end = cursor + measure_length
        next_change = (
            signatures[signature_index + 1].beat
            if signature_index + 1 < len(signatures)
            else None
        )
        measure_end = natural_end
        if (
            next_change is not None
            and next_change > cursor + _EPSILON
            and next_change < natural_end - _EPSILON
        ):
            measure_end = next_change
            warnings.append(
                "Time-signature change occurred inside a nominal measure; "
                f"measure {measure_number} was truncated at beat {next_change:.6f}."
            )

        boundaries.append(
            _MeasureBoundary(
                number=measure_number,
                start_beat=cursor,
                end_beat=measure_end,
                numerator=current.numerator,
                denominator=current.denominator,
            )
        )
        cursor = measure_end
        measure_number += 1

    return boundaries, warnings


def _find_measure(
    boundaries: list[_MeasureBoundary],
    beat: float,
) -> _MeasureBoundary:
    for boundary in boundaries:
        if boundary.start_beat - _EPSILON <= beat < boundary.end_beat - _EPSILON:
            return boundary
    return boundaries[-1]


def _split_across_measures(
    start_beat: float,
    duration_beats: float,
    boundaries: list[_MeasureBoundary],
) -> list[tuple[_MeasureBoundary, float, float]]:
    fragments: list[tuple[_MeasureBoundary, float, float]] = []
    cursor = start_beat
    end_beat = start_beat + duration_beats

    while cursor < end_beat - _EPSILON:
        measure = _find_measure(boundaries, cursor)
        fragment_end = min(end_beat, measure.end_beat)
        fragments.append((measure, cursor, fragment_end - cursor))
        cursor = fragment_end

    return fragments


def build_guitar_ir(
    timeline: NormalizedTimeline,
    track: NormalizedTrack,
    analysis: GuitarTrackAnalysis,
    *,
    source_stream_id: str | None = None,
    track_id: str = "guitar-1",
    role: str = "unknown",
    source_note_indices: Sequence[int] | None = None,
    source_note_origins: Sequence[str] | None = None,
    rewrite_changes: Sequence[NoteRewriteChange] = (),
) -> GuitarProjectIR:
    """Build schema-versioned, measure-aware Guitar IR.

    V0.1 quantizes note durations to the selected onset grid, normalizes common
    ringing and chord-release differences for readable one-voice notation,
    preserves source timing, and splits notes at measure boundaries with ties.
    """

    if len(track.notes) != len(analysis.rhythm.suggestions):
        raise ValueError("Track and rhythm analysis contain different note counts.")
    if len(track.notes) != len(analysis.fingering.notes):
        raise ValueError("Track and fingering analysis contain different note counts.")
    if source_note_indices is not None and len(source_note_indices) != len(track.notes):
        raise ValueError("source_note_indices must match the rewritten track note count.")
    if source_note_origins is not None and len(source_note_origins) != len(track.notes):
        raise ValueError("source_note_origins must match the rewritten track note count.")

    stable_source_indices = (
        list(source_note_indices)
        if source_note_indices is not None
        else list(range(len(track.notes)))
    )
    stable_source_origins = (
        list(source_note_origins)
        if source_note_origins is not None
        else ["midi"] * len(track.notes)
    )
    if any(origin not in {"midi", "synthetic"} for origin in stable_source_origins):
        raise ValueError("source_note_origins may only contain 'midi' or 'synthetic'.")

    prepared = _prepare_notated_notes(track, analysis)
    maximum_end = max((item.end_beat for item in prepared), default=0.0)
    boundaries, warnings = _build_measure_boundaries(timeline, maximum_end)

    measures = [
        GuitarMeasure(
            number=item.number,
            start_beat=item.start_beat,
            duration_beats=item.end_beat - item.start_beat,
            numerator=item.numerator,
            denominator=item.denominator,
        )
        for item in boundaries
    ]
    measures_by_number = {measure.number: measure for measure in measures}

    fingering_by_index = {
        item.note_index: item for item in analysis.fingering.notes
    }
    articulations_by_index = defaultdict(list)
    for decision in analysis.articulations.decisions:
        articulations_by_index[decision.note_index].append(decision)

    operation_stages = {
        "transpose": "note_rewrite_pitch",
        "delete": "note_rewrite_delete",
        "insert": "note_rewrite_insert",
    }
    changes: list[Transformation] = [
        Transformation(
            id=change.id,
            stage=operation_stages.get(
                change.operation,
                f"note_rewrite_{change.operation}",
            ),
            source_note_index=change.source_note_index,
            before=change.before,
            after=change.after,
            confidence=change.confidence,
            reason=change.reason,
        )
        for change in rewrite_changes
    ]
    event_id_by_working_index: dict[int, str] = {}

    for item in prepared:
        stable_source_index = stable_source_indices[item.source_index]
        source_origin = stable_source_origins[item.source_index]
        base_id = f"n-{stable_source_index + 1:05d}"
        fragments = _split_across_measures(
            item.start_beat,
            item.duration_beats,
            boundaries,
        )
        fragment_event_ids = [
            base_id if len(fragments) == 1 else f"{base_id}-{index + 1}"
            for index in range(len(fragments))
        ]
        fingering = fingering_by_index[item.source_index]
        decisions = articulations_by_index[item.source_index]

        if abs(item.start_beat - item.note.start_beat) > _EPSILON:
            changes.append(
                Transformation(
                    id=f"chg-onset-{item.source_index + 1:05d}",
                    stage="rhythm_onset",
                    source_note_index=stable_source_index,
                    before={"start_beat": item.note.start_beat},
                    after={"start_beat": item.start_beat},
                    confidence=item.rhythm_confidence,
                    reason=f"snap_to_{analysis.rhythm.selected_grid.name}_grid",
                )
            )

        initial_grid_duration = (
            item.pre_overlap_duration_beats
            if item.pre_overlap_duration_beats is not None
            else item.duration_beats
        )
        if abs(initial_grid_duration - item.note.duration_beats) > _EPSILON:
            changes.append(
                Transformation(
                    id=f"chg-duration-{item.source_index + 1:05d}",
                    stage="rhythm_duration",
                    source_note_index=stable_source_index,
                    before={"duration_beats": item.note.duration_beats},
                    after={"duration_beats": initial_grid_duration},
                    confidence=item.rhythm_confidence,
                    reason=f"spell_on_{analysis.rhythm.selected_grid.name}_grid",
                )
            )

        if item.let_ring_inferred and item.pre_overlap_duration_beats is not None:
            changes.append(
                Transformation(
                    id=f"chg-overlap-{item.source_index + 1:05d}",
                    stage="rhythm_overlap",
                    source_note_index=stable_source_index,
                    before={"score_duration_beats": item.pre_overlap_duration_beats},
                    after={"score_duration_beats": item.duration_beats},
                    confidence=0.8,
                    reason=";".join(item.overlap_reasons),
                )
            )

        for fragment_index, (measure, fragment_start, fragment_duration) in enumerate(
            fragments
        ):
            event_id = fragment_event_ids[fragment_index]
            is_first = fragment_index == 0
            is_last = fragment_index == len(fragments) - 1

            ir_articulations: list[IRArticulation] = []
            if is_first:
                if item.let_ring_inferred:
                    ir_articulations.append(
                        IRArticulation(
                            type="let_ring",
                            confidence=0.8,
                            reason=(
                                "Written duration was shortened for readable one-voice "
                                "notation while source performance timing keeps the ring."
                            ),
                        )
                    )
                for decision in decisions:
                    source_note_id = (
                        event_id_by_working_index.get(decision.source_note_index)
                        if decision.source_note_index is not None
                        else None
                    )
                    ir_articulations.append(
                        IRArticulation(
                            type=decision.technique,
                            confidence=decision.confidence,
                            reason=decision.reason,
                            source_note_id=source_note_id,
                        )
                    )

            articulation_confidence = (
                max(
                    [decision.confidence for decision in decisions]
                    + ([0.8] if item.let_ring_inferred else []),
                    default=None,
                )
                if is_first
                else None
            )
            note_event = GuitarNoteEvent(
                id=event_id,
                source_note_index=stable_source_index,
                pitch=item.note.pitch,
                score=ScoreTiming(
                    start_beat=fragment_start,
                    duration_beats=fragment_duration,
                    measure_number=measure.number,
                    beat_in_measure=fragment_start - measure.start_beat,
                    tie_in=not is_first,
                    tie_out=not is_last,
                ),
                performance=PerformanceTiming(
                    source_start_beat=item.note.start_beat,
                    source_duration_beats=item.note.duration_beats,
                    velocity=item.note.velocity,
                ),
                fingering=IRFingering(
                    string=fingering.string,
                    fret=fingering.fret,
                ),
                articulations=ir_articulations,
                confidence=NoteConfidence(
                    rhythm=item.rhythm_confidence,
                    fingering=1.0 if fingering.playable else 0.0,
                    articulation=articulation_confidence,
                ),
                source_note_origin=source_origin,
            )
            measures_by_number[measure.number].events.append(note_event)

        if fragment_event_ids:
            event_id_by_working_index[item.source_index] = fragment_event_ids[-1]

    for measure in measures:
        measure.events.sort(
            key=lambda event: (event.score.start_beat, event.pitch, event.id)
        )

    tuning = [pitch for _string, pitch in STANDARD_TUNING.open_strings]
    guitar_track = GuitarTrackIR(
        id=track_id,
        name=track.name,
        source_stream_id=source_stream_id,
        role=role,
        tuning=tuning,
        fret_count=analysis.fingering.max_fret,
        measures=measures,
        playing_context=(
            analysis.playing_context.to_dict()
            if analysis.playing_context is not None
            else None
        ),
    )

    return GuitarProjectIR(
        title=Path(timeline.source).stem or "Untitled",
        source=timeline.source,
        tempo_map=[
            IRTempoEvent(beat=event.beat, bpm=event.bpm)
            for event in timeline.tempo_events
        ],
        time_signatures=[
            IRTimeSignatureEvent(
                beat=event.beat,
                numerator=event.numerator,
                denominator=event.denominator,
            )
            for event in timeline.time_signature_events
        ],
        tracks=[guitar_track],
        changes=changes,
        warnings=warnings,
    )
