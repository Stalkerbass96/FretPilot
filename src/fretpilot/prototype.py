"""One-command prototype package generation for real MIDI evaluation."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from fretpilot.analysis import analyze_guitar_stream_section_aware
from fretpilot.detection import classify_timeline
from fretpilot.detection.models import GuitarStreamCandidate
from fretpilot.exporters.ample_guitar import export_ample_sc_midi
from fretpilot.exporters.guitar_pro import UnsupportedGuitarIR, export_gp5
from fretpilot.ir import build_guitar_ir
from fretpilot.midi.models import NormalizedTimeline
from fretpilot.rewrite import (
    DEFAULT_MIDI_FIDELITY,
    NoteRewriteResult,
    rewrite_instrument_stream,
)


@dataclass(slots=True)
class PrototypeOutputStatus:
    path: str | None
    status: str
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(slots=True)
class PrototypeStreamResult:
    stream_id: str
    directory: str
    analysis: PrototypeOutputStatus
    rewrite: PrototypeOutputStatus
    guitar_ir: PrototypeOutputStatus
    gp5: PrototypeOutputStatus
    ample_sc_midi: PrototypeOutputStatus
    report: PrototypeOutputStatus

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PrototypeManifest:
    source: str
    output_directory: str
    stream_results: list[PrototypeStreamResult]
    selected_stream_ids: list[str]
    format_version: str = "0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_json(path: Path, data: dict[str, Any], *, compact: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=None if compact else 2,
            sort_keys=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _safe_stream_name(stream_id: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in stream_id)


def _count_transformations(changes: list[Any]) -> dict[str, int]:
    return dict(Counter(change.stage for change in changes))


def _count_articulations(analysis: Any) -> dict[str, int]:
    return dict(
        Counter(decision.technique for decision in analysis.articulations.decisions)
    )


def _build_processing_report(
    candidate: GuitarStreamCandidate,
    rewrite: NoteRewriteResult,
    analysis: Any,
    project: Any,
    *,
    gp5_status: PrototypeOutputStatus,
    ample_status: PrototypeOutputStatus,
) -> dict[str, Any]:
    low_confidence_rhythm = [
        suggestion.note_index
        for suggestion in analysis.rhythm.suggestions
        if suggestion.confidence < 0.60
    ]
    unplayable = [
        item.note_index
        for item in analysis.fingering.notes
        if not item.playable
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

    section_summary = [
        {
            "section_id": item.section_id,
            "start_measure": item.start_measure,
            "end_measure": item.end_measure,
            "role_scores": item.playing_context.role_scores,
            "style_scores": item.playing_context.style_scores,
            "technique_scores": item.playing_context.technique_scores,
            "source_profiles": item.playing_context.source_profiles,
        }
        for item in analysis.section_contexts
    ]

    return {
        "format_version": "0.1",
        "source": project.source,
        "stream": candidate.stream.to_summary_dict(),
        "detection": {
            "guitar_probability": candidate.guitar_probability,
            "confidence": candidate.confidence,
            "decision": candidate.decision,
            "layers": [asdict(layer) for layer in candidate.layers],
            "behavior_profiles": [
                asdict(profile) for profile in candidate.behavior_profiles
            ],
        },
        "sections": {
            "count": len(section_summary),
            "items": section_summary,
        },
        "note_rewrite": {
            "midi_fidelity": rewrite.midi_fidelity,
            "rationality_weight": rewrite.rationality_weight,
            "original_note_count": rewrite.original_note_count,
            "rewritten_note_count": len(rewrite.stream.notes),
            "change_counts": dict(
                Counter(change.operation for change in rewrite.changes)
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
            "counts": _count_articulations(analysis),
            "decision_count": len(analysis.articulations.decisions),
        },
        "guitar_ir": {
            "schema_version": project.schema_version,
            "measure_count": sum(len(track.measures) for track in project.tracks),
            "event_count": len(ir_events),
            "transformation_counts": _count_transformations(project.changes),
            "let_ring_source_note_indices": let_ring_sources,
            "let_ring_count": len(let_ring_sources),
            "warnings": project.warnings,
        },
        "outputs": {
            "gp5": asdict(gp5_status),
            "ample_sc_midi": asdict(ample_status),
        },
        "review_required": bool(
            rewrite.changes
            or low_confidence_rhythm
            or unplayable
            or project.warnings
            or gp5_status.status != "success"
            or gp5_status.warnings
            or ample_status.status != "success"
            or ample_status.warnings
        ),
    }


def _select_candidates(
    timeline: NormalizedTimeline,
    *,
    stream_id: str | None,
    all_likely_guitars: bool,
) -> list[GuitarStreamCandidate]:
    report = classify_timeline(timeline)

    if stream_id is not None:
        candidate = next(
            (
                item
                for item in report.candidates
                if item.stream.stream_id == stream_id
            ),
            None,
        )
        if candidate is None:
            available = ", ".join(
                item.stream.stream_id for item in report.candidates
            )
            raise ValueError(
                f"Unknown stream ID {stream_id!r}. Available streams: {available or 'none'}."
            )
        return [candidate]

    likely = [
        item for item in report.candidates if item.decision == "likely_guitar"
    ]
    if all_likely_guitars:
        if not likely:
            raise ValueError("No likely guitar streams were detected.")
        return likely

    if len(likely) == 1:
        return likely
    if not likely:
        raise ValueError(
            "No likely guitar stream was detected. Select a stream explicitly."
        )
    options = ", ".join(item.stream.stream_id for item in likely)
    raise ValueError(
        "Multiple likely guitar streams were detected. Use --all-likely-guitars "
        f"or select one stream explicitly. Candidates: {options}."
    )


def generate_prototype_package(
    timeline: NormalizedTimeline,
    output_directory: str | Path,
    *,
    stream_id: str | None = None,
    all_likely_guitars: bool = False,
    max_fret: int = 24,
    midi_fidelity: float = DEFAULT_MIDI_FIDELITY,
    compact_json: bool = False,
) -> PrototypeManifest:
    """Generate section-aware analysis, IR, GP5, Ample MIDI, and reports."""

    if stream_id is not None and all_likely_guitars:
        raise ValueError("stream_id and all_likely_guitars are mutually exclusive.")
    if max_fret < 0:
        raise ValueError("max_fret must be zero or greater.")
    if not 0.0 <= midi_fidelity <= 1.0:
        raise ValueError("midi_fidelity must be between 0.0 and 1.0.")

    root = Path(output_directory)
    root.mkdir(parents=True, exist_ok=True)
    candidates = _select_candidates(
        timeline,
        stream_id=stream_id,
        all_likely_guitars=all_likely_guitars,
    )

    results: list[PrototypeStreamResult] = []
    for candidate in candidates:
        stream_name = _safe_stream_name(candidate.stream.stream_id)
        stream_dir = root / stream_name
        stream_dir.mkdir(parents=True, exist_ok=True)
        prefix = stream_dir / stream_name

        rewrite = rewrite_instrument_stream(
            candidate.stream,
            midi_fidelity=midi_fidelity,
            max_fret=max_fret,
            ticks_per_beat=timeline.ticks_per_beat,
        )
        rewritten_stream = rewrite.stream
        track = rewritten_stream.as_track()
        analysis = analyze_guitar_stream_section_aware(
            timeline,
            rewritten_stream,
            max_fret=max_fret,
        )
        project = build_guitar_ir(
            timeline,
            track,
            analysis,
            source_stream_id=candidate.stream.stream_id,
            source_note_indices=rewrite.source_note_indices,
            source_note_origins=rewrite.source_note_origins,
            rewrite_changes=rewrite.changes,
        )

        rewrite_path = prefix.with_suffix(".rewrite.json")
        analysis_path = prefix.with_suffix(".analysis.json")
        ir_path = prefix.with_suffix(".guitar-ir.json")
        gp5_path = prefix.with_suffix(".gp5")
        ample_path = prefix.with_suffix(".ample-sc.mid")
        report_path = prefix.with_suffix(".report.json")

        _write_json(rewrite_path, rewrite.to_dict(), compact=compact_json)
        _write_json(analysis_path, analysis.to_dict(), compact=compact_json)
        _write_json(ir_path, project.to_dict(), compact=compact_json)

        rewrite_status = PrototypeOutputStatus(
            path=str(rewrite_path),
            status="success",
        )
        analysis_status = PrototypeOutputStatus(
            path=str(analysis_path),
            status="success",
        )
        ir_status = PrototypeOutputStatus(path=str(ir_path), status="success")

        try:
            gp5_result = export_gp5(project, gp5_path)
            gp5_status = PrototypeOutputStatus(
                path=str(gp5_path),
                status="success",
                warnings=gp5_result.warnings,
            )
        except (UnsupportedGuitarIR, ValueError) as exc:
            gp5_status = PrototypeOutputStatus(
                path=None,
                status="unsupported",
                error=str(exc),
            )

        try:
            ample_result = export_ample_sc_midi(project, ample_path)
            ample_status = PrototypeOutputStatus(
                path=str(ample_path),
                status="success",
                warnings=ample_result.warnings,
            )
        except ValueError as exc:
            ample_status = PrototypeOutputStatus(
                path=None,
                status="unsupported",
                error=str(exc),
            )

        processing_report = _build_processing_report(
            candidate,
            rewrite,
            analysis,
            project,
            gp5_status=gp5_status,
            ample_status=ample_status,
        )
        _write_json(report_path, processing_report, compact=compact_json)
        report_status = PrototypeOutputStatus(
            path=str(report_path),
            status="success",
        )

        results.append(
            PrototypeStreamResult(
                stream_id=candidate.stream.stream_id,
                directory=str(stream_dir),
                analysis=analysis_status,
                rewrite=rewrite_status,
                guitar_ir=ir_status,
                gp5=gp5_status,
                ample_sc_midi=ample_status,
                report=report_status,
            )
        )

    manifest = PrototypeManifest(
        source=timeline.source,
        output_directory=str(root),
        selected_stream_ids=[candidate.stream.stream_id for candidate in candidates],
        stream_results=results,
    )
    _write_json(root / "manifest.json", manifest.to_dict(), compact=compact_json)
    return manifest
