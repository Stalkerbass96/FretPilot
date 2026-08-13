"""High-level musical analysis pipelines."""

from fretpilot.analysis.guitar import GuitarTrackAnalysis, analyze_guitar_track
from fretpilot.analysis.sections import (
    GuitarSection,
    SectionSegmentation,
    segment_instrument_stream,
)

__all__ = [
    "GuitarSection",
    "GuitarTrackAnalysis",
    "SectionSegmentation",
    "analyze_guitar_track",
    "segment_instrument_stream",
]
