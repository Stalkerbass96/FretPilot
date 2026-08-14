from __future__ import annotations

import argparse
import json
from pathlib import Path

from fretpilot.midi import load_midi
from fretpilot.performance.json_export import export_performance_plan_json
from fretpilot.prototype import generate_prototype_package


def generate_prototype_with_performance(
    timeline,
    output_directory,
    **kwargs,
):
    manifest = generate_prototype_package(timeline, output_directory, **kwargs)
    sidecars = []

    for result in manifest.stream_results:
        if result.guitar_ir.status != "success" or result.guitar_ir.path is None:
            sidecars.append({
                "stream_id": result.stream_id,
                "status": "unavailable",
                "path": None,
            })
            continue

        source = Path(result.guitar_ir.path)
        output = source.with_name(
            source.name.replace(".guitar-ir.json", ".performance-plan.json")
        )
        try:
            plan = export_performance_plan_json(source, output)
            sidecars.append({
                "stream_id": result.stream_id,
                "status": "success",
                "path": str(output),
                "note_count": len(plan.notes),
                "section_count": len(plan.sections),
                "warnings": list(plan.warnings),
            })
        except (OSError, ValueError, KeyError, TypeError) as exc:
            sidecars.append({
                "stream_id": result.stream_id,
                "status": "error",
                "path": None,
                "error": str(exc),
            })

    index = Path(output_directory) / "performance-plans.json"
    index.write_text(
        json.dumps({"performance_plans": sidecars}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest, sidecars, index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the prototype package plus target-neutral PerformancePlan JSON files."
    )
    parser.add_argument("midi")
    parser.add_argument("output_directory")
    parser.add_argument("--stream-id")
    parser.add_argument("--all-likely-guitars", action="store_true")
    parser.add_argument("--max-fret", type=int, default=24)
    parser.add_argument("--compact-json", action="store_true")
    args = parser.parse_args(argv)

    timeline = load_midi(args.midi)
    manifest, sidecars, index = generate_prototype_with_performance(
        timeline,
        args.output_directory,
        stream_id=args.stream_id,
        all_likely_guitars=args.all_likely_guitars,
        max_fret=args.max_fret,
        compact_json=args.compact_json,
    )
    print(json.dumps({
        "prototype": manifest.to_dict(),
        "performance_plans": sidecars,
        "performance_index": str(index),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
