"""Public Guitar IR builder with generic analysis provenance enrichment."""

from __future__ import annotations

from dataclasses import asdict

from fretpilot.analysis.guitar import GuitarTrackAnalysis
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
    """Build canonical Guitar IR and retain time-varying guitar knowledge.

    The low-level builder remains responsible for score/performance note events.
    This public wrapper adds generic musical provenance produced by the analysis
    stack. Product-specific virtual-instrument controls remain downstream.
    """

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
    ir_track.section_contexts = [
        item.to_dict() for item in analysis.section_contexts
    ]
    ir_track.hand_positions = [asdict(item) for item in analysis.hand_positions]
    return project
