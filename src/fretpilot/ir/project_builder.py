"""Public Guitar IR builder with generic analysis provenance enrichment."""

from __future__ import annotations

from dataclasses import asdict

from fretpilot.analysis.guitar import GuitarTrackAnalysis
from fretpilot.analysis.score_strategies import build_section_score_strategies
from fretpilot.guitar.models import FingeredNote, FingeringResult
from fretpilot.harmony import plan_harmony, plan_harmony_by_sections
from fretpilot.ir.builder import build_guitar_ir as _build_core_guitar_ir
from fretpilot.ir.models import GuitarProjectIR, IRHarmonyRegion, IRRightHandIntent
from fretpilot.midi.models import NormalizedTimeline, NormalizedTrack
from fretpilot.picking import PickingDecision, PickingPlan, plan_picking


def _ensure_section_picking(track: NormalizedTrack, analysis: GuitarTrackAnalysis) -> None:
    if analysis.picking is not None or not analysis.section_contexts:
        return
    decisions: list[PickingDecision] = []
    for section in analysis.section_contexts:
        indices = [
            index for index, note in enumerate(track.notes)
            if section.start_beat - 1e-9 <= note.start_beat < section.end_beat - 1e-9
        ]
        if not indices:
            continue
        notes = [track.notes[index] for index in indices]
        local_track = NormalizedTrack(track.index, track.name, notes, track.instrument_name)
        local_fingering = FingeringResult(
            track_index=track.index,
            track_name=track.name,
            tuning=analysis.fingering.tuning,
            max_fret=analysis.fingering.max_fret,
            notes=[
                FingeredNote(
                    note_index=local_index,
                    pitch=notes[local_index].pitch,
                    start_beat=notes[local_index].start_beat,
                    duration_beats=notes[local_index].duration_beats,
                    string=analysis.fingering.notes[global_index].string,
                    fret=analysis.fingering.notes[global_index].fret,
                    local_cost=analysis.fingering.notes[global_index].local_cost,
                    fretting_digit=analysis.fingering.notes[global_index].fretting_digit,
                )
                for local_index, global_index in enumerate(indices)
            ],
        )
        local_plan = plan_picking(local_track, local_fingering, context=section.playing_context)
        for item in local_plan.decisions:
            decisions.append(
                PickingDecision(
                    note_indices=tuple(indices[index] for index in item.note_indices),
                    start_beat=item.start_beat,
                    motion=item.motion,
                    direction=item.direction,
                    confidence=item.confidence,
                    reason=item.reason,
                    technique=item.technique,
                )
            )
    analysis.picking = PickingPlan(track.index, track.name, decisions)


def _ensure_harmony(track: NormalizedTrack, analysis: GuitarTrackAnalysis) -> None:
    if analysis.harmony is not None:
        return
    if analysis.section_contexts:
        analysis.harmony = plan_harmony_by_sections(
            track,
            analysis.fingering,
            analysis.section_contexts,
        )
    else:
        analysis.harmony = plan_harmony(track, analysis.fingering)


def _attach_right_hand(project: GuitarProjectIR, analysis: GuitarTrackAnalysis) -> None:
    if not project.tracks or analysis.picking is None:
        return
    by_source: dict[int, IRRightHandIntent] = {}
    for decision in analysis.picking.decisions:
        intent = IRRightHandIntent(
            motion=decision.motion,
            direction=decision.direction,
            confidence=decision.confidence,
            reason=decision.reason,
            technique=decision.technique,
        )
        for source_index in decision.note_indices:
            by_source[source_index] = intent
    for measure in project.tracks[0].measures:
        for event in measure.events:
            if not event.score.tie_in:
                event.right_hand = by_source.get(event.source_note_index)


def _attach_fretting_digits(
    project: GuitarProjectIR,
    analysis: GuitarTrackAnalysis,
) -> None:
    if not project.tracks:
        return
    digits = {
        item.note_index: item.fretting_digit
        for item in analysis.fingering.notes
        if item.fretting_digit is not None
    }
    for measure in project.tracks[0].measures:
        for event in measure.events:
            event.fingering.fretting_digit = digits.get(event.source_note_index)


def _attach_articulation_parameters(
    project: GuitarProjectIR,
    analysis: GuitarTrackAnalysis,
) -> None:
    if not project.tracks:
        return
    parameter_map = {
        (decision.note_index, decision.technique): dict(decision.parameters)
        for decision in analysis.articulations.decisions
        if decision.parameters
    }
    if not parameter_map:
        return
    for measure in project.tracks[0].measures:
        for event in measure.events:
            for articulation in event.articulations:
                parameters = parameter_map.get(
                    (event.source_note_index, articulation.type)
                )
                if parameters is not None:
                    articulation.parameters = dict(parameters)


def _attach_harmony(project: GuitarProjectIR, analysis: GuitarTrackAnalysis) -> None:
    if not project.tracks or analysis.harmony is None:
        return
    project.tracks[0].harmony_regions = [
        IRHarmonyRegion(
            start_beat=item.start_beat,
            symbol=item.symbol,
            root_pitch_class=item.root_pitch_class,
            quality=item.quality,
            confidence=item.confidence,
            source_note_indices=list(item.note_indices),
            reason=item.reason,
        )
        for item in analysis.harmony.decisions
    ]


def build_guitar_ir(
    timeline: NormalizedTimeline,
    track: NormalizedTrack,
    analysis: GuitarTrackAnalysis,
    *,
    source_stream_id: str | None = None,
    track_id: str = "guitar-1",
    role: str = "unknown",
) -> GuitarProjectIR:
    """Build canonical Guitar IR and retain time-varying guitar knowledge."""

    _ensure_section_picking(track, analysis)
    _ensure_harmony(track, analysis)
    project = _build_core_guitar_ir(
        timeline,
        track,
        analysis,
        source_stream_id=source_stream_id,
        track_id=track_id,
        role=role,
    )
    _attach_right_hand(project, analysis)
    _attach_fretting_digits(project, analysis)
    _attach_articulation_parameters(project, analysis)
    _attach_harmony(project, analysis)
    if not project.tracks:
        return project

    ir_track = project.tracks[0]
    strategies = {
        item.section_id: item.to_dict()
        for item in build_section_score_strategies(analysis.section_contexts)
    }
    section_payloads: list[dict[str, object]] = []
    for item in analysis.section_contexts:
        payload = item.to_dict()
        payload["score_strategy"] = strategies[item.section_id]
        section_payloads.append(payload)

    ir_track.section_contexts = section_payloads
    ir_track.hand_positions = [asdict(item) for item in analysis.hand_positions]
    return project
