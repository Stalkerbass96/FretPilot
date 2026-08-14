"""Bounded, privacy-conscious context for shadow MIDI rewrite advice."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fretpilot.ai.models import ShadowRewritePolicy, ShadowRewriteRequest
from fretpilot.detection.guitar_classifier import extract_behavior_features
from fretpilot.detection.models import InstrumentStream
from fretpilot.knowledge import BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION
from fretpilot.midi.models import NormalizedTimeline
from fretpilot.rewrite import NoteRewriteResult


def build_shadow_policy(
    midi_fidelity: float,
    *,
    context_note_count: int,
    max_context_notes: int,
) -> ShadowRewritePolicy:
    if not 0.0 <= midi_fidelity <= 1.0:
        raise ValueError("midi_fidelity must be between 0.0 and 1.0.")
    if context_note_count < 0 or max_context_notes < 1:
        raise ValueError("AI context note limits must be positive.")

    rationality = 1.0 - midi_fidelity
    delete_count = int(context_note_count * rationality * 0.10)
    transpose_count = int(context_note_count * rationality * 0.12)
    if context_note_count and rationality >= 0.25:
        delete_count = max(delete_count, 1)
        transpose_count = max(transpose_count, 1)

    operations: list[str] = []
    if delete_count:
        operations.append("delete")
    if transpose_count:
        operations.append("transpose")
    return ShadowRewritePolicy(
        midi_fidelity=midi_fidelity,
        allowed_operations=tuple(operations),
        max_delete_count=delete_count,
        max_transpose_count=transpose_count,
        max_pitch_shift=12 if transpose_count else 0,
        max_context_notes=max_context_notes,
    )


def _context_indices(
    note_count: int,
    changed_indices: set[int],
    max_notes: int,
) -> list[int]:
    if note_count <= max_notes:
        return list(range(note_count))

    selected: set[int] = set()
    for center in sorted(changed_indices):
        for index in range(max(0, center - 4), min(note_count, center + 5)):
            selected.add(index)
            if len(selected) >= max_notes:
                return sorted(selected)
    for index in range(note_count):
        selected.add(index)
        if len(selected) >= max_notes:
            break
    return sorted(selected)


def build_shadow_rewrite_request(
    timeline: NormalizedTimeline,
    source_stream: InstrumentStream,
    baseline: NoteRewriteResult,
    *,
    max_context_notes: int = 256,
) -> ShadowRewriteRequest:
    """Describe source notes and baseline edits without sending binary MIDI."""

    if max_context_notes < 1:
        raise ValueError("max_context_notes must be at least 1.")
    changed_indices = {item.source_note_index for item in baseline.changes}
    selected_indices = _context_indices(
        len(source_stream.notes),
        changed_indices,
        max_context_notes,
    )
    selected_set = set(selected_indices)
    outputs_by_source: dict[int, list[dict[str, int]]] = {}
    for output_index, source_index in enumerate(baseline.source_note_indices):
        outputs_by_source.setdefault(source_index, []).append(
            {
                "output_note_index": output_index,
                "pitch": baseline.stream.notes[output_index].pitch,
            }
        )
    changes_by_source: dict[int, list[dict[str, object]]] = {}
    for change in baseline.changes:
        changes_by_source.setdefault(change.source_note_index, []).append(
            {
                "operation": change.operation,
                "after": change.after,
                "confidence": change.confidence,
                "reason": change.reason,
            }
        )

    notes = tuple(
        {
            "source_note_index": index,
            "pitch": source_stream.notes[index].pitch,
            "start_beat": source_stream.notes[index].start_beat,
            "duration_beats": source_stream.notes[index].duration_beats,
            "velocity": source_stream.notes[index].velocity,
            "baseline_outputs": outputs_by_source.get(index, []),
            "baseline_changes": changes_by_source.get(index, []),
        }
        for index in selected_indices
    )
    policy = build_shadow_policy(
        baseline.midi_fidelity,
        context_note_count=len(notes),
        max_context_notes=max_context_notes,
    )
    return ShadowRewriteRequest(
        source_label=Path(timeline.source).name,
        stream=source_stream.to_summary_dict(),
        musical_features=extract_behavior_features(source_stream).to_dict(),
        policy=policy,
        notes=notes,
        deterministic_changes=tuple(
            asdict(item)
            for item in baseline.changes
            if item.source_note_index in selected_set
        ),
        knowledge_snapshot_version=BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION,
        context_truncated=len(source_stream.notes) > len(notes),
    )
