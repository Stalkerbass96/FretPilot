"""High-level musical analysis pipelines."""

from fretpilot.analysis.guitar import GuitarTrackAnalysis, analyze_guitar_track
from fretpilot.analysis.section_aware import (
    analyze_guitar_stream_section_aware,
    analyze_guitar_track_by_sections,
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
