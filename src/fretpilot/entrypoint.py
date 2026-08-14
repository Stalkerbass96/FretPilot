from __future__ import annotations

import json
from pathlib import Path
import sys

from fretpilot.cli import main as _base_main
from fretpilot.performance.json_export import export_performance_plan_json
from fretpilot.virtual_instruments.json_export import (
    DEFAULT_PROFILE_ID,
    export_capability_report_json,
)


def _prototype_output_directory(argv: list[str]) -> Path | None:
    if not argv or argv[0] != "prototype":
        return None
    for index, item in enumerate(argv):
        if item in {"-o", "--output-directory"} and index + 1 < len(argv):
            return Path(argv[index + 1])
        if item.startswith("--output-directory="):
            return Path(item.split("=", 1)[1])
    return None


def enrich_prototype_directory(output_directory: str | Path) -> Path | None:
    root = Path(output_directory)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        return None

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    performance_sidecars = []
    capability_sidecars = []

    for result in payload.get("stream_results", []):
        stream_id = result.get("stream_id")
        ir_output = result.get("guitar_ir", {})
        ir_path = ir_output.get("path")
        if ir_output.get("status") != "success" or not ir_path:
            unavailable = {
                "stream_id": stream_id,
                "status": "unavailable",
                "path": None,
            }
            performance_sidecars.append(dict(unavailable))
            capability_sidecars.append({
                **unavailable,
                "profile_id": DEFAULT_PROFILE_ID,
                "performance_plan_included": False,
            })
            continue

        source = Path(ir_path)
        performance_destination = source.with_name(
            source.name.replace(".guitar-ir.json", ".performance-plan.json")
        )
        performance_plan = None
        try:
            performance_plan = export_performance_plan_json(
                source,
                performance_destination,
            )
            performance_sidecars.append({
                "stream_id": stream_id,
                "status": "success",
                "path": str(performance_destination),
                "note_count": len(performance_plan.notes),
                "section_count": len(performance_plan.sections),
                "warnings": list(performance_plan.warnings),
            })
        except (OSError, ValueError, KeyError, TypeError) as exc:
            performance_sidecars.append({
                "stream_id": stream_id,
                "status": "error",
                "path": None,
                "error": str(exc),
            })

        capability_destination = source.with_name(
            source.name.replace(".guitar-ir.json", ".vi-capabilities.json")
        )
        try:
            capability_report = export_capability_report_json(
                source,
                capability_destination,
                profile_id=DEFAULT_PROFILE_ID,
                performance_plan=performance_plan,
            )
            capability_sidecars.append({
                "stream_id": stream_id,
                "status": "success",
                "path": str(capability_destination),
                "profile_id": capability_report.profile_id,
                "requirement_count": len(capability_report.requirements),
                "native_occurrences": capability_report.native_count,
                "approximated_occurrences": capability_report.approximated_count,
                "unsupported_occurrences": capability_report.unsupported_count,
                "performance_plan_included": performance_plan is not None,
            })
        except (OSError, ValueError, KeyError, TypeError) as exc:
            capability_sidecars.append({
                "stream_id": stream_id,
                "status": "error",
                "path": None,
                "profile_id": DEFAULT_PROFILE_ID,
                "performance_plan_included": performance_plan is not None,
                "error": str(exc),
            })

    performance_index = root / "performance-plans.json"
    performance_index.write_text(
        json.dumps(
            {"performance_plans": performance_sidecars},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    capability_index = root / "vi-capabilities.json"
    capability_index.write_text(
        json.dumps(
            {
                "profile_id": DEFAULT_PROFILE_ID,
                "capability_reports": capability_sidecars,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return performance_index


def main(argv: list[str] | None = None) -> int:
    active_argv = list(sys.argv[1:] if argv is None else argv)
    result = _base_main(active_argv)
    if result == 0:
        output_directory = _prototype_output_directory(active_argv)
        if output_directory is not None:
            enrich_prototype_directory(output_directory)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
