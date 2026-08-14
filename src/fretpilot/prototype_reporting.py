"""Human-review processing report for one prototype stream."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Any

from fretpilot.detection.models import GuitarStreamCandidate
from fretpilot.knowledge import BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION
from fretpilot.prototype_models import PrototypeOutputStatus
from fretpilot.rewrite import NoteRewriteResult


def build_processing_report(
    candidate: GuitarStreamCandidate,
    rewrite: NoteRewriteResult,
    analysis: Any,
    project: Any,
    *,
    pdf_status: PrototypeOutputStatus,
    gp5_status: PrototypeOutputStatus,
    ample_status: PrototypeOutputStatus,
    performance_status: PrototypeOutputStatus,
    capability_status: PrototypeOutputStatus,
) -> dict[str, Any]:
    low_confidence_rhythm = [
        item.note_index
        for item in analysis.rhythm.suggestions
        if item.confidence < 0.60
    ]
    unplayable = [
        item.note_index for item in analysis.fingering.notes if not item.playable
    ]
    ir_events = [
        event
        for track in project.tracks
        for measure in track.measures
        for event in measure.events
    ]
    let_ring_sources = sorted(
        {
            event.source_note_index
            for event in ir_events
            if any(item.type == "let_ring" for item in event.articulations)
        }
    )
    sections = [
        {
            "section_id": item.section_id,
            "start_measure": item.start_measure,
            "end_measure": item.end_measure,
            "role_scores": item.playing_context.role_scores,
            "style_scores": item.playing_context.style_scores,
            "technique_scores": item.playing_context.technique_scores,
            "source_profiles": item.playing_context.source_profiles,
            "knowledge_version": item.playing_context.knowledge_version,
            "knowledge_entry_ids": item.playing_context.knowledge_entry_ids,
            "boundary_confidence": item.boundary_confidence,
            "boundary_strength": item.boundary_strength,
            "boundary_reason": item.boundary_reason,
        }
        for item in analysis.section_contexts
    ]
    output_statuses = {
        "pdf": pdf_status,
        "gp5": gp5_status,
        "ample_sc_midi": ample_status,
        "performance_plan": performance_status,
        "vi_capabilities": capability_status,
    }

    return {
        "format_version": "0.1",
        "source": project.source,
        "stream": candidate.stream.to_summary_dict(),
        "detection": {
            "guitar_probability": candidate.guitar_probability,
            "confidence": candidate.confidence,
            "decision": candidate.decision,
            "layers": [asdict(item) for item in candidate.layers],
            "behavior_profiles": [
                asdict(item) for item in candidate.behavior_profiles
            ],
        },
        "sections": {"count": len(sections), "items": sections},
        "note_rewrite": {
            "midi_fidelity": rewrite.midi_fidelity,
            "rationality_weight": rewrite.rationality_weight,
            "original_note_count": rewrite.original_note_count,
            "rewritten_note_count": len(rewrite.stream.notes),
            "change_counts": dict(
                Counter(item.operation for item in rewrite.changes)
            ),
            "change_count": len(rewrite.changes),
        },
        "rhythm": {
            "selected_grid": asdict(analysis.rhythm.selected_grid),
            "note_count": len(analysis.rhythm.suggestions),
            "low_confidence_note_indices": low_confidence_rhythm,
            "low_confidence_count": len(low_confidence_rhythm),
        },
        "fingering": {
            "tuning": analysis.fingering.tuning,
            "max_fret": analysis.fingering.max_fret,
            "unplayable_note_indices": unplayable,
            "unplayable_count": len(unplayable),
            "diagnostics": [asdict(item) for item in analysis.fingering.diagnostics],
        },
        "articulations": {
            "counts": dict(
                Counter(item.technique for item in analysis.articulations.decisions)
            ),
            "decision_count": len(analysis.articulations.decisions),
        },
        "guitar_ir": {
            "schema_version": project.schema_version,
            "measure_count": sum(len(track.measures) for track in project.tracks),
            "event_count": len(ir_events),
            "voice_counts": dict(
                Counter(str(item.score.voice) for item in ir_events)
            ),
            "transformation_counts": dict(
                Counter(item.stage for item in project.changes)
            ),
            "let_ring_source_note_indices": let_ring_sources,
            "let_ring_count": len(let_ring_sources),
            "warnings": project.warnings,
        },
        "outputs": {name: asdict(status) for name, status in output_statuses.items()},
        "knowledge": (
            asdict(project.knowledge)
            if project.knowledge is not None
            else {
                "snapshot_version": BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION,
                "entry_ids": [],
            }
        ),
        "review_required": bool(
            rewrite.changes
            or low_confidence_rhythm
            or unplayable
            or project.warnings
            or any(
                status.status not in {"success", "skipped"} or status.warnings
                for status in output_statuses.values()
            )
        ),
    }
