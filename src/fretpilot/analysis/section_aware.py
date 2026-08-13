"""Section-aware guitar analysis.

This module closes the loop between musical segmentation and guitar execution:
each stable section gets its own PlayingContext, then fingering and articulation
are solved independently inside that section before results are remapped to the
original stream-wide note indices.

Section boundaries intentionally act as phrase boundaries in this baseline. A
future hand-position planner may carry explicit state across selected boundaries,
but the current behavior is safer than allowing a riff/solo context from one
region to leak into another.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from fretpilot.analysis.guitar import GuitarTrackAnalysis
from fretpilot.analysis.section_contexts import (
    SectionContextAnalysis,
    analyze_section_contexts,
)
from fretpilot.analysis.sections import segment_instrument_stream
from fretpilot.articulation import ArticulationDecision, ArticulationPlan, plan_articulations
from fretpilot.detection.models import InstrumentStream
from fretpilot.guitar import optimize_fingering
from fretpilot.guitar.instrument import STANDARD_TUNING
from fretpilot.guitar.models import (
    FingeredNote,
    FingeringDiagnostic,
    FingeringResult,
)
from fretpilot.midi.models import NormalizedTimeline, NormalizedTrack
from fretpilot.rhythm import analyze_track_rhythm

if TYPE_CHECKING:
    from fretpilot.knowledge.playing_contexts import PlayingContext

_EPSILON = 1e-9


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
    merged_notes: dict[int, FingeredNote] = {}
    diagnostics: list[FingeringDiagnostic] = []
    decisions: list[ArticulationDecision] = []
    total_cost = 0.0
    seen_note_indices: set[int] = set()

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
        local_track = _subtrack(track, note_indices)
        local_fingering = optimize_fingering(
            local_track,
            max_fret=max_fret,
            preferences=context.fingering,
        )
        remapped_notes, remapped_diagnostics = _remap_fingering(
            local_fingering,
            note_indices,
        )
        merged_notes.update({item.note_index: item for item in remapped_notes})
        diagnostics.extend(remapped_diagnostics)
        total_cost += local_fingering.total_cost

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
