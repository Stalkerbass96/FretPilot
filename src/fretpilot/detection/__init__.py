"""Layered instrument-stream and guitar detection."""

from fretpilot.detection.guitar_classifier import (
    classify_guitar_stream,
    classify_timeline,
    extract_behavior_features,
)
from fretpilot.detection.models import (
    GuitarDetectionReport,
    GuitarStreamCandidate,
    InstrumentStream,
)
from fretpilot.detection.streams import resolve_instrument_streams

__all__ = [
    "GuitarDetectionReport",
    "GuitarStreamCandidate",
    "InstrumentStream",
    "classify_guitar_stream",
    "classify_timeline",
    "extract_behavior_features",
    "resolve_instrument_streams",
]
