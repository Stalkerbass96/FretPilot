"""Data models for guitar-aware note placement."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class FretPosition:
    string: int
    fret: int
    pitch: int


@dataclass(slots=True)
class FingeredNote:
    note_index: int
    pitch: int
    start_beat: float
    duration_beats: float
    string: int | None
    fret: int | None
    local_cost: float | None = None

    @property
    def playable(self) -> bool:
        return self.string is not None and self.fret is not None


@dataclass(slots=True)
class FingeringDiagnostic:
    code: str
    message: str
    note_index: int
    pitch: int


@dataclass(slots=True)
class FingeringResult:
    track_index: int
    track_name: str
    tuning: str
    max_fret: int
    notes: list[FingeredNote] = field(default_factory=list)
    diagnostics: list[FingeringDiagnostic] = field(default_factory=list)
    total_cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
