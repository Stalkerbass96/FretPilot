"""Data models for guitar-aware note placement."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class FretPosition:
    string: int
    fret: int
    pitch: int


@dataclass(frozen=True, slots=True)
class HandPositionState:
    """Compact estimate of the fretting hand over a short note window."""

    center_fret: float
    minimum_fret: int
    maximum_fret: int
    fret_span: int
    anchor_string: int | None
    note_count: int


@dataclass(slots=True)
class SectionHandPosition:
    section_id: str
    entry: HandPositionState | None
    exit: HandPositionState | None
    note_count: int


@dataclass(slots=True)
class HandPositionTransition:
    from_section_id: str
    to_section_id: str
    boundary_strength: float
    continuity_strength: float
    from_center_fret: float | None
    to_center_fret: float | None
    shift_distance: float
    shift_cost: float
    action: str
    reason: str


@dataclass(slots=True)
class HandPositionPlan:
    sections: list[SectionHandPosition] = field(default_factory=list)
    transitions: list[HandPositionTransition] = field(default_factory=list)
    strong_boundary_threshold: float = 0.75

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    entry_hand_position: HandPositionState | None = None
    exit_hand_position: HandPositionState | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
