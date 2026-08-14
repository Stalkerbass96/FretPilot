import json
from pathlib import Path

from fretpilot.ir.serde import load_guitar_ir
from fretpilot.performance.planner import build_performance_plan


def export_performance_plan_json(ir_path, output_path):
    project = load_guitar_ir(ir_path)
    plan = build_performance_plan(project)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(plan.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return plan
