"""High-level musical analysis pipelines."""

from fretpilot.analysis.guitar import GuitarTrackAnalysis, analyze_guitar_track
from fretpilot.analysis.section_execution import (
    analyze_guitar_stream_section_aware as _base_stream,
    analyze_guitar_track_by_sections as _base_sections,
)
from fretpilot.analysis.section_contexts import (
    SectionContextAnalysis,
    analyze_section_contexts,
)
from fretpilot.analysis.sections import (
    GuitarSection,
    SectionSegmentation,
    segment_instrument_stream,
)
from fretpilot.picking.sections import plan_picking_by_sections


def analyze_guitar_track_by_sections(track, section_contexts, **kwargs):
    result = _base_sections(track, section_contexts, **kwargs)
    result.picking = plan_picking_by_sections(
        track,
        result.fingering,
        result.section_contexts,
        kwargs.get("context_overrides"),
    )
    return result


def analyze_guitar_stream_section_aware(timeline, stream, **kwargs):
    result = _base_stream(timeline, stream, **kwargs)
    result.picking = plan_picking_by_sections(
        stream.as_track(),
        result.fingering,
        result.section_contexts,
        kwargs.get("context_overrides"),
    )
    return result


__all__ = [
    "GuitarSection",
    "GuitarTrackAnalysis",
    "SectionContextAnalysis",
    "SectionSegmentation",
    "analyze_guitar_stream_section_aware",
    "analyze_guitar_track",
    "analyze_guitar_track_by_sections",
    "analyze_section_contexts",
    "segment_instrument_stream",
]
