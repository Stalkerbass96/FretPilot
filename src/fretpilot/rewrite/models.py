"""Models for explainable source-MIDI note rewriting."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from fretpilot.detection.models import InstrumentStream


DEFAULT_MIDI_FIDELITY = 0.35


@dataclass(slots=True)
class NoteRewriteChange:
    """One deterministic edit made before guitar analysis."""

    id: str
    operation: str
    source_note_index: int
    output_note_index: int | None
    before: dict[str, Any]
    after: dict[str, Any]
    confidence: float
    reason: str


@dataclass(slots=True)
class NoteRewriteResult:
    """A rewritten stream plus a stable mapping back to source MIDI notes."""

    stream: InstrumentStream
    midi_fidelity: float
    original_note_count: int
    source_note_indices: list[int] = field(default_factory=list)
    source_note_origins: list[str] = field(default_factory=list)
    changes: list[NoteRewriteChange] = field(default_factory=list)

    @property
    def rationality_weight(self) -> float:
        return 1.0 - self.midi_fidelity

    def to_dict(self) -> dict[str, Any]:
        counts = Counter(change.operation for change in self.changes)
        return {
            "format_version": "0.1",
            "stream_id": self.stream.stream_id,
            "midi_fidelity": self.midi_fidelity,
            "rationality_weight": self.rationality_weight,
            "original_note_count": self.original_note_count,
            "rewritten_note_count": len(self.stream.notes),
            "change_counts": dict(counts),
            "source_map": [
                {
                    "output_note_index": output_index,
                    "source_note_index": source_index,
                    "origin": origin,
                }
                for output_index, (source_index, origin) in enumerate(
                    zip(
                        self.source_note_indices,
                        self.source_note_origins,
                        strict=True,
                    )
                )
            ],
            "changes": [asdict(change) for change in self.changes],
        }
