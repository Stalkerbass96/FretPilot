"""Target-neutral guitar performance intent models.

These models describe *how the guitarist should perform* canonical Guitar IR.
They must never contain vendor keyswitches, CC numbers, MIDI control notes, or
plugin state-machine details; those belong to the VI adapter layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


PERFORMANCE_PLAN_VERSION = "0.1"


@dataclass(slots=True)
class PerformanceSectionIntent:
    section_id: str
    start_beat: float
    end_beat: float
    role_scores: dict[str, float] = field(default_factory=dict)
    style_scores: dict[str, float] = field(default_factory=dict)
    technique_scores: dict[str, float] = field(default_factory=dict)
    performance_preferences: dict[str, float] = field(default_factory=dict)
    knowledge_version: str | None = None


@dataclass(slots=True)
class PerformanceNoteIntent:
    source_note_index: int
    pitch: int
    section_id: str | None
    source_start_beat: float
    source_duration_beats: float
    source_velocity: int
    target_start_beat: float
    target_duration_beats: float
    target_velocity: int
    timing_offset_beats: float
    duration_delta_beats: float
    velocity_delta: int
    metric_accent: float
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GuitarPerformancePlan:
    source: str
    track_id: str
    source_stream_id: str | None
    notes: list[PerformanceNoteIntent] = field(default_factory=list)
    sections: list[PerformanceSectionIntent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    version: str = PERFORMANCE_PLAN_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
