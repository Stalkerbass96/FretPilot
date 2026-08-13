"""Section-aware guitar analysis.

This module closes the loop between musical segmentation and guitar execution:
each stable section gets its own PlayingContext, then fingering and articulation
are solved independently inside that section before results are remapped to the
original stream-wide note indices.

Section boundaries carry explicit musical strength. Weak boundaries pass the
prior exit hand state into the next section's optimizer; strong boundaries
allow a deliberate reset. Context preferences remain section-local.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Mapping

from fretpilot.analysis.guitar import GuitarTrackAnalysis, align_track_onsets_to_rhythm
from fretpilot.analysis.section_contexts import (
    SectionContextAnalysis,
    analyze_section_contexts,
)
from fretpilot.analysis.sections import segment_instrument_stream
from fretpilot.articulation.models import ArticulationDecision, ArticulationPlan
from fretpilot.articulation.planner import plan_articulations
from fretpilot.detection.models import InstrumentStream
from fretpilot.guitar import optimize_fingering
from fretpilot.guitar.instrument import STANDARD_TUNING
from fretpilot.guitar.models import (
    FingeredNote,
    FingeringDiagnostic,
    FingeringResult,
    HandPositionPlan,
    HandPositionState,
    HandPositionTransition,
    SectionHandPosition,
)
from fretpilot.midi.models import NormalizedTimeline, NormalizedTrack
from fretpilot.rhythm import analyze_track_rhythm

if TYPE_CHECKING:
    from fretpilot.knowledge.playing_contexts import PlayingContext

_EPSILON = 1e-9
_STRONG_BOUNDARY_THRESHOLD = 0.75


def _dominant_score(scores: Mapping[str, float]) -> tuple[str, float] | None:
    if not scores:
        return None
    key = max(scores, key=scores.get)
    return key, scores[key]


def _effective_boundary_strength(
    previous: SectionContextAnalysis,
    current: SectionContextAnalysis,
    *,
    silence_gap_beats: float,
) -> tuple[float, str]:
    """Combine segmentation, semantic change, and phrase silence evidence."""

    strength = current.boundary_strength
    reasons = [current.boundary_reason]
    previous_role = _dominant_score(previous.playing_context.role_scores)
    current_role = _dominant_score(current.playing_context.role_scores)
    if (
        previous_role is not None
        and current_role is not None
        and previous_role[0] != current_role[0]
        and min(previous_role[1], current_role[1]) >= 0.50
    ):
        strength = max(strength, 0.85)
        reasons.append(f"role_change={previous_role[0]}->{current_role[0]}")

    previous_style = _dominant_score(previous.playing_context.style_scores)
    current_style = _dominant_score(current.playing_context.style_scores)
    if (
        previous_style is not None
        and current_style is not None
        and previous_style[0] != current_style[0]
        and min(previous_style[1], current_style[1]) >= 0.50
    ):
        strength = max(strength, 0.75)
        reasons.append(f"style_change={previous_style[0]}->{current_style[0]}")

    if silence_gap_beats >= 1.0:
        strength = max(strength, 0.85)
        reasons.append(f"silence_gap={silence_gap_beats:g}_beats")
    elif silence_gap_beats >= 0.5:
        strength = max(strength, 0.65)
        reasons.append(f"silence_gap={silence_gap_beats:g}_beats")
    return round(min(1.0, max(0.0, strength)), 6), ";".join(reasons)


def _continuity_strength(boundary_strength: float) -> float:
    if boundary_strength >= _STRONG_BOUNDARY_THRESHOLD:
        return 0.0
    return round(1.0 - boundary_strength / _STRONG_BOUNDARY_THRESHOLD, 6)


def _transition(
    previous_section: SectionContextAnalysis,
    current_section: SectionContextAnalysis,
    previous_exit: HandPositionState | None,
    current_entry: HandPositionState | None,
    *,
    boundary_strength: float,
    continuity_strength: float,
    reason: str,
) -> HandPositionTransition:
    from_center = previous_exit.center_fret if previous_exit is not None else None
    to_center = current_entry.center_fret if current_entry is not None else None
    shift_distance = (
        abs(to_center - from_center)
        if from_center is not None and to_center is not None
        else 0.0
    )
    if boundary_strength >= _STRONG_BOUNDARY_THRESHOLD:
        action = "reset"
    elif shift_distance <= 2.0:
        action = "carry"
    else:
        action = "deliberate_shift"
    stability = max(
        0.25,
        current_section.playing_context.fingering.hand_position_stability,
    )
    return HandPositionTransition(
        from_section_id=previous_section.section_id,
        to_section_id=current_section.section_id,
        boundary_strength=boundary_strength,
        continuity_strength=continuity_strength,
        from_center_fret=from_center,
        to_center_fret=to_center,
        shift_distance=round(shift_distance, 3),
        shift_cost=round(shift_distance * continuity_strength * stability, 6),
        action=action,
        reason=reason,
    )


def _section_note_indices(
    track: NormalizedTrack,
    section: SectionContextAnalysis,
) -> list[int]:
    return [
        note_index
        for note_index, note in enumerate(track.notes)
        if section.start_beat - _EPSILON
        <= note.start_beat
        < section.end_beat - _EPSILON
    ]


def _subtrack(track: NormalizedTrack, note_indices: list[int]) -> NormalizedTrack:
    return NormalizedTrack(
        index=track.index,
        name=track.name,
        notes=[track.notes[index] for index in note_indices],
        instrument_name=track.instrument_name,
    )


def _remap_fingering(
    local: FingeringResult,
    note_indices: list[int],
) -> tuple[list[FingeredNote], list[FingeringDiagnostic]]:
    notes = [
        FingeredNote(
            note_index=note_indices[item.note_index],
            pitch=item.pitch,
            start_beat=item.start_beat,
            duration_beats=item.duration_beats,
            string=item.string,
            fret=item.fret,
            local_cost=item.local_cost,
        )
        for item in local.notes
    ]
    diagnostics = [
        FingeringDiagnostic(
            code=item.code,
            message=item.message,
            note_index=note_indices[item.note_index],
            pitch=item.pitch,
        )
        for item in local.diagnostics
    ]
    return notes, diagnostics


def _remap_articulations(
    local: ArticulationPlan,
    note_indices: list[int],
) -> list[ArticulationDecision]:
    decisions: list[ArticulationDecision] = []
    for item in local.decisions:
        decisions.append(
            ArticulationDecision(
                note_index=note_indices[item.note_index],
                technique=item.technique,
                confidence=item.confidence,
                reason=item.reason,
                source_note_index=(
                    note_indices[item.source_note_index]
                    if item.source_note_index is not None
                    else None
                ),
            )
        )
    return decisions


def analyze_guitar_track_by_sections(
    track: NormalizedTrack,
    section_contexts: list[SectionContextAnalysis],
    *,
    max_fret: int = 24,
    context_overrides: Mapping[str, PlayingContext] | None = None,
) -> GuitarTrackAnalysis:
    """Analyze one track using a separate PlayingContext for each section.

    ``context_overrides`` is intentionally keyed by stable ``section_id``. It
    supports future user review/correction and makes the context-to-engine
    contract testable without hard-coding one hand-authored style profile as
    musical truth.
    """

    if max_fret < 0:
        raise ValueError("max_fret must be zero or greater.")
    if not section_contexts:
        raise ValueError("section_contexts must contain at least one section.")

    rhythm = analyze_track_rhythm(track)
    fingering_track = align_track_onsets_to_rhythm(track, rhythm)
    merged_notes: dict[int, FingeredNote] = {}
    diagnostics: list[FingeringDiagnostic] = []
    decisions: list[ArticulationDecision] = []
    total_cost = 0.0
    seen_note_indices: set[int] = set()
    hand_sections: list[SectionHandPosition] = []
    hand_transitions: list[HandPositionTransition] = []
    previous_section: SectionContextAnalysis | None = None
    previous_exit: HandPositionState | None = None
    previous_note_end: float | None = None

    for section in section_contexts:
        note_indices = _section_note_indices(track, section)
        if not note_indices:
            continue

        overlap = seen_note_indices.intersection(note_indices)
        if overlap:
            raise ValueError(
                f"Section contexts overlap on source note indices: {sorted(overlap)}"
            )
        seen_note_indices.update(note_indices)

        context = (
            context_overrides.get(section.section_id, section.playing_context)
            if context_overrides is not None
            else section.playing_context
        )
        active_section = replace(section, playing_context=context)
        local_track = _subtrack(track, note_indices)
        local_fingering_track = _subtrack(fingering_track, note_indices)
        current_note_start = min(note.start_beat for note in local_track.notes)
        silence_gap = (
            max(0.0, current_note_start - previous_note_end)
            if previous_note_end is not None
            else 0.0
        )
        boundary_strength, boundary_reason = (
            _effective_boundary_strength(
                previous_section,
                active_section,
                silence_gap_beats=silence_gap,
            )
            if previous_section is not None
            else (1.0, section.boundary_reason)
        )
        continuity = (
            _continuity_strength(boundary_strength)
            if previous_section is not None
            else 0.0
        )
        local_fingering = optimize_fingering(
            local_fingering_track,
            max_fret=max_fret,
            preferences=context.fingering,
            initial_hand_position=(previous_exit if continuity > 0.0 else None),
            continuity_strength=continuity,
        )
        remapped_notes, remapped_diagnostics = _remap_fingering(
            local_fingering,
            note_indices,
        )
        merged_notes.update({item.note_index: item for item in remapped_notes})
        diagnostics.extend(remapped_diagnostics)
        total_cost += local_fingering.total_cost

        hand_sections.append(
            SectionHandPosition(
                section_id=section.section_id,
                entry=local_fingering.entry_hand_position,
                exit=local_fingering.exit_hand_position,
                note_count=len(note_indices),
            )
        )
        if previous_section is not None:
            hand_transitions.append(
                _transition(
                    previous_section,
                    active_section,
                    previous_exit,
                    local_fingering.entry_hand_position,
                    boundary_strength=boundary_strength,
                    continuity_strength=continuity,
                    reason=boundary_reason,
                )
            )
        previous_section = active_section
        previous_exit = local_fingering.exit_hand_position
        previous_note_end = max(note.end_beat for note in local_track.notes)

        local_articulations = plan_articulations(
            local_track,
            local_fingering,
            preferences=context.articulation,
        )
        decisions.extend(_remap_articulations(local_articulations, note_indices))

    expected = set(range(len(track.notes)))
    missing = sorted(expected - seen_note_indices)
    if missing:
        raise ValueError(
            "Section contexts do not cover all source notes; missing indices: "
            + ", ".join(str(index) for index in missing[:20])
            + ("..." if len(missing) > 20 else "")
        )

    fingering = FingeringResult(
        track_index=track.index,
        track_name=track.name,
        tuning=STANDARD_TUNING.name,
        max_fret=max_fret,
        notes=[merged_notes[index] for index in range(len(track.notes))],
        diagnostics=sorted(diagnostics, key=lambda item: item.note_index),
        total_cost=total_cost,
        entry_hand_position=(hand_sections[0].entry if hand_sections else None),
        exit_hand_position=(hand_sections[-1].exit if hand_sections else None),
    )
    articulations = ArticulationPlan(
        track_index=track.index,
        track_name=track.name,
        decisions=sorted(
            decisions,
            key=lambda item: (
                item.note_index,
                item.source_note_index if item.source_note_index is not None else -1,
                item.technique,
            ),
        ),
    )

    return GuitarTrackAnalysis(
        track_index=track.index,
        track_name=track.name,
        rhythm=rhythm,
        fingering=fingering,
        articulations=articulations,
        playing_context=None,
        section_contexts=section_contexts,
        hand_position_plan=HandPositionPlan(
            sections=hand_sections,
            transitions=hand_transitions,
            strong_boundary_threshold=_STRONG_BOUNDARY_THRESHOLD,
        ),
    )


def analyze_guitar_stream_section_aware(
    timeline: NormalizedTimeline,
    stream: InstrumentStream,
    *,
    max_fret: int = 24,
    window_measures: int = 2,
    change_threshold: float = 0.22,
    minimum_behavior_score: float = 0.50,
    context_overrides: Mapping[str, PlayingContext] | None = None,
) -> GuitarTrackAnalysis:
    """Derive time-varying contexts and use them to analyze one guitar stream."""

    segmentation = segment_instrument_stream(
        timeline,
        stream,
        window_measures=window_measures,
        change_threshold=change_threshold,
    )
    section_contexts = analyze_section_contexts(
        segmentation,
        minimum_behavior_score=minimum_behavior_score,
    )
    return analyze_guitar_track_by_sections(
        stream.as_track(),
        section_contexts,
        max_fret=max_fret,
        context_overrides=context_overrides,
    )
