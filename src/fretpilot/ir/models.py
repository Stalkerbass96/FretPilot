"""Canonical FretPilot Guitar IR models.

The IR separates readable score timing from source/performance timing and stays
independent of Guitar Pro, Ample Guitar, or any other output adapter.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SCHEMA_VERSION = "0.1"


@dataclass(slots=True)
class IRTempoEvent:
    beat: float
    bpm: float


@dataclass(slots=True)
class IRTimeSignatureEvent:
    beat: float
    numerator: int
    denominator: int


@dataclass(slots=True)
class ScoreTiming:
    start_beat: float
    duration_beats: float
    measure_number: int
    beat_in_measure: float
    voice: int = 1
    tie_in: bool = False
    tie_out: bool = False


@dataclass(slots=True)
class PerformanceTiming:
    source_start_beat: float
    source_duration_beats: float
    velocity: int


@dataclass(slots=True)
class IRFingering:
    string: int | None
    fret: int | None

    @property
    def playable(self) -> bool:
        return self.string is not None and self.fret is not None


@dataclass(slots=True)
class IRArticulation:
    type: str
    confidence: float
    reason: str
    source_note_id: str | None = None


@dataclass(slots=True)
class NoteConfidence:
    rhythm: float
    fingering: float
    articulation: float | None = None


@dataclass(slots=True)
class GuitarNoteEvent:
    id: str
    source_note_index: int
    pitch: int
    score: ScoreTiming
    performance: PerformanceTiming
    fingering: IRFingering
    articulations: list[IRArticulation] = field(default_factory=list)
    confidence: NoteConfidence | None = None


@dataclass(slots=True)
class GuitarMeasure:
    number: int
    start_beat: float
    duration_beats: float
    numerator: int
    denominator: int
    events: list[GuitarNoteEvent] = field(default_factory=list)


@dataclass(slots=True)
class GuitarTrackIR:
    id: str
    name: str
    source_stream_id: str | None
    role: str
    tuning: list[int]
    fret_count: int
    measures: list[GuitarMeasure] = field(default_factory=list)


@dataclass(slots=True)
class Transformation:
    id: str
    stage: str
    source_note_index: int
    before: dict[str, Any]
    after: dict[str, Any]
    confidence: float
    reason: str


@dataclass(slots=True)
class GuitarProjectIR:
    title: str
    source: str
    tempo_map: list[IRTempoEvent]
    time_signatures: list[IRTimeSignatureEvent]
    tracks: list[GuitarTrackIR]
    changes: list[Transformation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
