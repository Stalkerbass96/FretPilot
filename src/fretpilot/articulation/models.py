"""Generic articulation models independent of any virtual instrument."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ArticulationDecision:
    note_index: int
    technique: str
    confidence: float
    reason: str
    source_note_index: int | None = None
    parameters: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class ArticulationPlan:
    track_index: int
    track_name: str
    decisions: list[ArticulationDecision] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
