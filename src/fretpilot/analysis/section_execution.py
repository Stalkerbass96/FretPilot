"""Section-aware guitar execution with explicit hand-position continuity."""

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from fretpilot.analysis.guitar import (
    GuitarTrackAnalysis,
    align_track_onsets_to_rhythm,
)
from fretpilot.analysis.section_contexts import SectionContextAnalysis
from fretpilot.analysis.sections import segment_instrument_stream
from fretpilot.analysis.style_contexts import analyze_style_aware_section_contexts
from fretpilot.articulation.models import ArticulationDecision, ArticulationPlan
from fretpilot.articulation.planner import plan_articulations
from fretpilot.detection.models import InstrumentStream
from fretpilot.guitar import optimize_fingering
from fretpilot.guitar.chord_voicing import apply_chord_voicing_strategy
from fretpilot.guitar.fretting_digits import assign_fretting_digits
from fretpilot.guitar.hand_position import (
    HandPositionState,
    carry_hand_position_into_section,
    summarize_hand_position,
)
from fretpilot.guitar.instrument import STANDARD_TUNING
from fretpilot.guitar.models import (
    FingeredNote,
    FingeringDiagnostic,
    FingeringResult,
)
from fretpilot.knowledge.context_strategy import apply_style_scores_to_context
from fretpilot.knowledge.strategy_resolver import resolve_style_strategy
from fretpilot.harmony import plan_harmony_by_sections
from fretpilot.midi.models import NormalizedTimeline, NormalizedTrack
from fretpilot.midi.pitch_wheel import extract_monophonic_pitch_raises
from fretpilot.picking.sections import plan_picking_by_sections
from fretpilot.rhythm import analyze_track_rhythm

if TYPE_CHECKING:
    from fretpilot.knowledge.playing_contexts import PlayingContext

_EPSILON = 1e-9
_DEFAULT_CARRY_BOUNDARY_STRENGTH_MAX = 1.35


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
    carry_boundary_strength_max: float = _DEFAULT_CARRY_BOUNDARY_STRENGTH_MAX,
) -> GuitarTrackAnalysis:
    """Analyze a track with per-section context and hand-position continuity."""

    if max_fret < 0:
        raise ValueError("max_fret must be zero or greater.")
    if carry_boundary_strength_max < 0.0:
        raise ValueError("carry_boundary_strength_max must be zero or greater.")
    if not section_contexts:
        raise ValueError("section_contexts must contain at least one section.")

    rhythm = analyze_track_rhythm(track)
    fingering_track = align_track_onsets_to_rhythm(track, rhythm)
    merged_notes: dict[int, FingeredNote] = {}
    diagnostics: list[FingeringDiagnostic] = []
    decisions: list[ArticulationDecision] = []
    hand_positions: list[HandPositionState] = []
    total_cost = 0.0
    seen_note_indices: set[int] = set()
    previous_exit_fret_center: float | None = None

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

        automatic_context = section.playing_context
        arpeggio_match = next(
            (
                item
                for item in section.behavior_profiles
                if item.profile_id == "arpeggio" and item.score >= 0.50
            ),
            None,
        )
        if arpeggio_match is not None:
            automatic_context.technique_scores["rock_arpeggio"] = max(
                automatic_context.technique_scores.get("rock_arpeggio", 0.0),
                arpeggio_match.score,
            )
            apply_style_scores_to_context(
                automatic_context,
                dict(automatic_context.style_scores),
            )

        context = (
            context_overrides.get(section.section_id, automatic_context)
            if context_overrides is not None
            else automatic_context
        )
        local_track = _subtrack(track, note_indices)
        local_fingering_track = _subtrack(fingering_track, note_indices)
        local_fingering = optimize_fingering(
            local_fingering_track,
            max_fret=max_fret,
            preferences=context.fingering,
        )

        carried_from_previous = (
            previous_exit_fret_center is not None
            and section.boundary_strength <= carry_boundary_strength_max
        )
        if carried_from_previous:
            local_fingering = carry_hand_position_into_section(
                local_fingering_track,
                local_fingering,
                preferred_fret_center=previous_exit_fret_center,
                preferences=context.fingering,
                max_fret=max_fret,
            )

        score_strategy = resolve_style_strategy(
            context.style_scores,
            role_scores=context.role_scores,
            technique_scores=context.technique_scores,
        ).score
        local_fingering = apply_chord_voicing_strategy(
            local_fingering_track,
            local_fingering,
            preferences=context.fingering,
            score_strategy=score_strategy,
            max_fret=max_fret,
        )

        hand_position = summarize_hand_position(
            local_fingering,
            section_id=section.section_id,
            start_measure=section.start_measure,
            end_measure=section.end_measure,
            previous_exit_fret_center=previous_exit_fret_center,
            boundary_strength=section.boundary_strength,
            carried_from_previous=carried_from_previous,
            hand_position_stability=context.fingering.hand_position_stability,
        )
        hand_positions.append(hand_position)
        if hand_position.exit_fret_center is not None:
            previous_exit_fret_center = hand_position.exit_fret_center

        remapped_notes, remapped_diagnostics = _remap_fingering(
            local_fingering,
            note_indices,
        )
        merged_notes.update({item.note_index: item for item in remapped_notes})
        diagnostics.extend(remapped_diagnostics)
        total_cost += local_fingering.total_cost + hand_position.transition_cost

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
    )
    fingering = assign_fretting_digits(track, fingering)
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
    harmony = plan_harmony_by_sections(track, fingering, section_contexts)
    picking = plan_picking_by_sections(
        track,
        fingering,
        section_contexts,
        context_overrides,
    )

    return GuitarTrackAnalysis(
        track_index=track.index,
        track_name=track.name,
        rhythm=rhythm,
        fingering=fingering,
        articulations=articulations,
        picking=picking,
        harmony=harmony,
        playing_context=None,
        section_contexts=section_contexts,
        hand_positions=hand_positions,
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
    carry_boundary_strength_max: float = _DEFAULT_CARRY_BOUNDARY_STRENGTH_MAX,
) -> GuitarTrackAnalysis:
    """Derive style-aware time-varying contexts and execute one guitar stream."""

    segmentation = segment_instrument_stream(
        timeline,
        stream,
        window_measures=window_measures,
        change_threshold=change_threshold,
    )
    section_contexts = analyze_style_aware_section_contexts(
        segmentation,
        stream,
        minimum_behavior_score=minimum_behavior_score,
    )
    result = analyze_guitar_track_by_sections(
        stream.as_track(),
        section_contexts,
        max_fret=max_fret,
        context_overrides=context_overrides,
        carry_boundary_strength_max=carry_boundary_strength_max,
    )
    for gesture in extract_monophonic_pitch_raises(timeline, stream):
        semitones = float(gesture["semitones"])
        result.articulations.decisions.append(
            ArticulationDecision(
                note_index=int(gesture["note_index"]),
                technique="pitch_raise",
                confidence=0.94 if gesture["returned_to_center"] else 0.86,
                reason=(
                    f"Explicit wheel gesture raises pitch by about {semitones:.2f} "
                    "semitones with a declared range on a monophonic stream."
                ),
                parameters={
                    "semitones": semitones,
                    "peak_wheel": float(gesture["peak_wheel"]),
                    "range_semitones": float(gesture["range_semitones"]),
                    "peak_position": float(gesture["peak_position"]),
                    "return_position": float(gesture["return_position"]),
                    "returned_to_center": (
                        1.0 if gesture["returned_to_center"] else 0.0
                    ),
                },
            )
        )
    result.articulations.decisions.sort(
        key=lambda item: (
            item.note_index,
            item.source_note_index if item.source_note_index is not None else -1,
            item.technique,
        )
    )
    return result
