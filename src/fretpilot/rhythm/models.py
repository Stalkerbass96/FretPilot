"""Data models for FretPilot's rhythm-repair layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class GridProfile:
    """A candidate notation grid measured in quarter-note beats."""

    name: str
    step_beats: float
    family: str
    complexity_penalty: float = 0.0


@dataclass(slots=True)
class GridScore:
    profile: GridProfile
    mean_absolute_error_beats: float
    max_absolute_error_beats: float
    objective: float


@dataclass(slots=True)
class RhythmSuggestion:
    track_index: int
    note_index: int
    pitch: int
    source_start_beat: float
    target_start_beat: float
    delta_beats: float
    confidence: float


@dataclass(slots=True)
class RhythmAnalysis:
    track_index: int
    track_name: str
    selected_grid: GridProfile
    grid_scores: list[GridScore]
    suggestions: list[RhythmSuggestion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
