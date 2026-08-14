"""One-command prototype package generation for real MIDI evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fretpilot.analysis import analyze_guitar_stream_section_aware
from fretpilot.detection import classify_timeline
from fretpilot.detection.models import GuitarStreamCandidate
from fretpilot.exporters.ample_guitar import export_ample_sc_midi
from fretpilot.exporters.guitar_pro import UnsupportedGuitarIR, export_gp5
from fretpilot.exporters.pdf_score import export_score_pdf
from fretpilot.ir import build_guitar_ir
from fretpilot.knowledge import BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION
from fretpilot.midi.models import NormalizedTimeline
from fretpilot.prototype_models import (
    PrototypeManifest,
    PrototypeOutputStatus,
    PrototypeStreamResult,
)
from fretpilot.prototype_reporting import build_processing_report
from fretpilot.prototype_sidecars import export_prototype_sidecars
from fretpilot.rewrite import (
    DEFAULT_MIDI_FIDELITY,
    rewrite_instrument_stream,
)
from fretpilot.virtual_instruments.json_export import DEFAULT_PROFILE_ID


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
    include_pdf: bool = True,
    include_gp5: bool = True,
    include_ample_sc_midi: bool = True,
) -> PrototypeManifest:
    """Generate analysis, IR, selected end-user formats, and reports."""

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
    performance_sidecars: list[dict[str, Any]] = []
    capability_sidecars: list[dict[str, Any]] = []
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
        pdf_path = prefix.with_suffix(".pdf")
        gp5_path = prefix.with_suffix(".gp5")
        ample_path = prefix.with_suffix(".ample-sc.mid")
        performance_path = prefix.with_suffix(".performance-plan.json")
        capability_path = prefix.with_suffix(".vi-capabilities.json")
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

        pdf_status = PrototypeOutputStatus(path=None, status="skipped")
        if include_pdf:
            try:
                pdf_result = export_score_pdf(project, pdf_path)
                pdf_status = PrototypeOutputStatus(
                    path=str(pdf_path),
                    status="success",
                    warnings=pdf_result.warnings,
                )
            except ValueError as exc:
                pdf_status = PrototypeOutputStatus(
                    path=None,
                    status="unsupported",
                    error=str(exc),
                )

        gp5_status = PrototypeOutputStatus(path=None, status="skipped")
        if include_gp5:
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

        ample_status = PrototypeOutputStatus(path=None, status="skipped")
        if include_ample_sc_midi:
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

        sidecars = export_prototype_sidecars(
            candidate.stream.stream_id,
            ir_path,
            performance_path,
            capability_path,
        )
        performance_sidecars.append(sidecars.performance_index_entry)
        capability_sidecars.append(sidecars.capability_index_entry)

        processing_report = build_processing_report(
            candidate,
            rewrite,
            analysis,
            project,
            pdf_status=pdf_status,
            gp5_status=gp5_status,
            ample_status=ample_status,
            performance_status=sidecars.performance_status,
            capability_status=sidecars.capability_status,
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
                pdf=pdf_status,
                gp5=gp5_status,
                ample_sc_midi=ample_status,
                performance_plan=sidecars.performance_status,
                vi_capabilities=sidecars.capability_status,
                report=report_status,
            )
        )

    manifest = PrototypeManifest(
        source=timeline.source,
        output_directory=str(root),
        selected_stream_ids=[candidate.stream.stream_id for candidate in candidates],
        stream_results=results,
        knowledge_snapshot_version=BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION,
    )
    _write_json(
        root / "performance-plans.json",
        {"performance_plans": performance_sidecars},
        compact=compact_json,
    )
    _write_json(
        root / "vi-capabilities.json",
        {
            "profile_id": DEFAULT_PROFILE_ID,
            "capability_reports": capability_sidecars,
        },
        compact=compact_json,
    )
    _write_json(root / "manifest.json", manifest.to_dict(), compact=compact_json)
    return manifest
