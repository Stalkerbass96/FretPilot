"""Compatibility wrapper for the canonical section-aware execution path.

`section_execution.py` is the single implementation truth. This module remains
for callers that imported the older path directly.
"""

from fretpilot.analysis.section_execution import (
    analyze_guitar_stream_section_aware,
    analyze_guitar_track_by_sections,
)

__all__ = [
    "analyze_guitar_stream_section_aware",
    "analyze_guitar_track_by_sections",
]
