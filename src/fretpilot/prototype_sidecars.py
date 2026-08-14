"""Performance and VI diagnostic artifacts for one prototype stream."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fretpilot.performance.json_export import export_performance_plan_json
from fretpilot.performance.models import GuitarPerformancePlan
from fretpilot.prototype_models import PrototypeOutputStatus
from fretpilot.virtual_instruments.json_export import (
    DEFAULT_PROFILE_ID,
    export_capability_report_json,
)


@dataclass(slots=True)
class PrototypeSidecars:
    performance_status: PrototypeOutputStatus
    performance_index_entry: dict[str, Any]
    capability_status: PrototypeOutputStatus
    capability_index_entry: dict[str, Any]


def _export_performance(
    stream_id: str,
    ir_path: Path,
    output_path: Path,
) -> tuple[PrototypeOutputStatus, dict[str, Any], GuitarPerformancePlan | None]:
    try:
        plan = export_performance_plan_json(ir_path, output_path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        error = str(exc)
        return (
            PrototypeOutputStatus(None, "error", error=error),
            {
                "stream_id": stream_id,
                "status": "error",
                "path": None,
                "error": error,
            },
            None,
        )

    warnings = list(plan.warnings)
    return (
        PrototypeOutputStatus(str(output_path), "success", warnings),
        {
            "stream_id": stream_id,
            "status": "success",
            "path": str(output_path),
            "note_count": len(plan.notes),
            "section_count": len(plan.sections),
            "warnings": warnings,
        },
        plan,
    )


def _export_capabilities(
    stream_id: str,
    ir_path: Path,
    output_path: Path,
    performance_plan: GuitarPerformancePlan | None,
) -> tuple[PrototypeOutputStatus, dict[str, Any]]:
    try:
        report = export_capability_report_json(
            ir_path,
            output_path,
            profile_id=DEFAULT_PROFILE_ID,
            performance_plan=performance_plan,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        error = str(exc)
        return PrototypeOutputStatus(None, "error", error=error), {
            "stream_id": stream_id,
            "status": "error",
            "path": None,
            "profile_id": DEFAULT_PROFILE_ID,
            "performance_plan_included": performance_plan is not None,
            "error": error,
        }

    return PrototypeOutputStatus(str(output_path), "success"), {
        "stream_id": stream_id,
        "status": "success",
        "path": str(output_path),
        "profile_id": report.profile_id,
        "requirement_count": len(report.requirements),
        "native_occurrences": report.native_count,
        "approximated_occurrences": report.approximated_count,
        "unsupported_occurrences": report.unsupported_count,
        "performance_plan_included": performance_plan is not None,
    }


def export_prototype_sidecars(
    stream_id: str,
    ir_path: Path,
    performance_path: Path,
    capability_path: Path,
) -> PrototypeSidecars:
    performance_status, performance_entry, plan = _export_performance(
        stream_id,
        ir_path,
        performance_path,
    )
    capability_status, capability_entry = _export_capabilities(
        stream_id,
        ir_path,
        capability_path,
        plan,
    )
    return PrototypeSidecars(
        performance_status,
        performance_entry,
        capability_status,
        capability_entry,
    )
