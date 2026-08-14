"""Public exports for layered instrument-stream and guitar detection.

Classifier helpers stay lazy so model-only users do not load the knowledge
registry and classifier implementation.
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
