"""Public Guitar IR builder with generic analysis provenance enrichment."""

from __future__ import annotations

from dataclasses import asdict

from fretpilot.analysis.guitar import GuitarTrackAnalysis
from fretpilot.analysis.score_strategies import build_section_score_strategies
from fretpilot.ir.builder import build_guitar_ir as _build_core_guitar_ir
from fretpilot.ir.models import GuitarProjectIR
from fretpilot.midi.models import NormalizedTimeline, NormalizedTrack


def build_guitar_ir(
    timeline: NormalizedTimeline,
    track: NormalizedTrack,
    analysis: GuitarTrackAnalysis,
    *,
    source_stream_id: str | None = None,
    track_id: str = "guitar-1",
    role: str = "unknown",
) -> GuitarProjectIR:
    """Build canonical Guitar IR and retain time-varying guitar knowledge."""

    project = _build_core_guitar_ir(
        timeline,
        track,
        analysis,
        source_stream_id=source_stream_id,
        track_id=track_id,
        role=role,
    )

    if not project.tracks:
        return project

    ir_track = project.tracks[0]
    strategies = {
        item.section_id: item.to_dict()
        for item in build_section_score_strategies(analysis.section_contexts)
    }
    section_payloads: list[dict[str, object]] = []
    for item in analysis.section_contexts:
        payload = item.to_dict()
        payload["score_strategy"] = strategies[item.section_id]
        section_payloads.append(payload)

    ir_track.section_contexts = section_payloads
    ir_track.hand_positions = [asdict(item) for item in analysis.hand_positions]
    return project
