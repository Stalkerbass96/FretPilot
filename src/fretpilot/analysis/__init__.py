"""High-level musical analysis pipelines."""

from fretpilot.analysis.guitar import GuitarTrackAnalysis, analyze_guitar_track
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
    "analyze_guitar_track",
    "analyze_section_contexts",
    "segment_instrument_stream",
]
