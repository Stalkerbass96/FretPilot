from __future__ import annotations

import argparse
import json
from pathlib import Path

from fretpilot.midi import load_midi
from fretpilot.prototype import generate_prototype_package


def generate_prototype_with_performance(
    timeline,
    output_directory,
    **kwargs,
):
    index = Path(output_directory) / "performance-plans.json"
    manifest = generate_prototype_package(timeline, output_directory, **kwargs)
    sidecars = json.loads(index.read_text(encoding="utf-8"))["performance_plans"]
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
