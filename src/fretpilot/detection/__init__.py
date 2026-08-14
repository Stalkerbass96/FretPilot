"""Layered instrument-stream and guitar detection.

The package keeps its data models cheap to import. Classifier/stream helpers are
loaded lazily so modules that only depend on ``detection.models`` do not trigger
the full classifier and knowledge graph, preventing circular imports as the
playing-knowledge layer grows.
"""

from __future__ import annotations

from typing import Any

from fretpilot.detection.models import (
    GuitarDetectionReport,
    GuitarStreamCandidate,
    InstrumentStream,
)

__all__ = [
    "GuitarDetectionReport",
    "GuitarStreamCandidate",
    "InstrumentStream",
    "classify_guitar_stream",
    "classify_timeline",
    "extract_behavior_features",
    "resolve_instrument_streams",
    "build_guitar_review_summary",
]


def __getattr__(name: str) -> Any:
    if name in {
        "classify_guitar_stream",
        "classify_timeline",
        "extract_behavior_features",
    }:
        from fretpilot.detection import guitar_classifier

        return getattr(guitar_classifier, name)

    if name == "resolve_instrument_streams":
        from fretpilot.detection.streams import resolve_instrument_streams

        return resolve_instrument_streams

    if name == "build_guitar_review_summary":
        from fretpilot.detection.review import build_guitar_review_summary

        return build_guitar_review_summary

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
