"""JSON sidecar export for read-only virtual-instrument capability diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

from fretpilot.ir.serde import load_guitar_ir
from fretpilot.performance.models import GuitarPerformancePlan
from fretpilot.virtual_instruments.capability_report import (
    CapabilityReport,
    build_capability_report,
)
from fretpilot.virtual_instruments.registry import get_profile


DEFAULT_PROFILE_ID = "ample-guitar-sc-v4"


def export_capability_report_json(
    ir_path: str | Path,
    output_path: str | Path,
    *,
    profile_id: str = DEFAULT_PROFILE_ID,
    performance_plan: GuitarPerformancePlan | None = None,
) -> CapabilityReport:
    """Write one diagnostic capability report without rendering target MIDI."""

    project = load_guitar_ir(ir_path)
    profile = get_profile(profile_id)
    report = build_capability_report(
        project,
        profile,
        performance_plan=performance_plan,
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report
