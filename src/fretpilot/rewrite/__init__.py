"""Explainable source-note rewriting before guitar analysis."""

from fretpilot.rewrite.engine import rewrite_instrument_stream
from fretpilot.rewrite.models import (
    DEFAULT_MIDI_FIDELITY,
    NoteRewriteChange,
    NoteRewriteResult,
)

__all__ = [
    "DEFAULT_MIDI_FIDELITY",
    "NoteRewriteChange",
    "NoteRewriteResult",
    "rewrite_instrument_stream",
]
