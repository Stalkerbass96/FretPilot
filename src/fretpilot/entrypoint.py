from __future__ import annotations

import json
from pathlib import Path
import sys

from fretpilot.cli import main as _base_main
from fretpilot.performance.json_export import export_performance_plan_json


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
    sidecars = []
    for result in payload.get("stream_results", []):
        stream_id = result.get("stream_id")
        ir_output = result.get("guitar_ir", {})
        ir_path = ir_output.get("path")
        if ir_output.get("status") != "success" or not ir_path:
            sidecars.append({
                "stream_id": stream_id,
                "status": "unavailable",
                "path": None,
            })
            continue

        source = Path(ir_path)
        destination = source.with_name(
            source.name.replace(".guitar-ir.json", ".performance-plan.json")
        )
        try:
            plan = export_performance_plan_json(source, destination)
            sidecars.append({
                "stream_id": stream_id,
                "status": "success",
                "path": str(destination),
                "note_count": len(plan.notes),
                "section_count": len(plan.sections),
                "warnings": list(plan.warnings),
            })
        except (OSError, ValueError, KeyError, TypeError) as exc:
            sidecars.append({
                "stream_id": stream_id,
                "status": "error",
                "path": None,
                "error": str(exc),
            })

    index = root / "performance-plans.json"
    index.write_text(
        json.dumps({"performance_plans": sidecars}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return index


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
