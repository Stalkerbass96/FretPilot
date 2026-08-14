"""Evidence-backed articulation priors for guitar transcription."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ARTICULATION_RESEARCH_VERSION = "0.1"


@dataclass(frozen=True, slots=True)
class ArticulationKnowledge:
    rule_id: str
    statement: str
    hints: dict[str, float | bool]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


RULES: tuple[ArticulationKnowledge, ...] = (
    ArticulationKnowledge(
        "hammer-pull-feasibility",
        "Prefer hammer-ons and pull-offs on one string when pitch direction and fretting order are physically valid.",
        {"same_string_required": True, "pitch_direction_sensitive": True, "open_string_pull_off_allowed": True},
        ("bontempi-rich-tab-2024",),
    ),
    ArticulationKnowledge(
        "slide-feasibility",
        "Prefer legato slides between consecutive notes on the same string with compatible fretting-hand motion.",
        {"same_string_required": True, "same_finger_preferred": True},
        ("bontempi-rich-tab-2024",),
    ),
    ArticulationKnowledge(
        "vibrato-duration",
        "Long sustained fretted notes are stronger vibrato candidates; open strings are excluded from fretting-hand vibrato.",
        {"duration_bias": 1.50, "exclude_open_string": True},
        ("bontempi-rich-tab-2024",),
    ),
    ArticulationKnowledge(
        "bend-register",
        "Prefer bends on suitable higher strings and sustained notes; penalize low-string bends and reward common return-to-unison pitch cells.",
        {"low_string_penalty": 1.50, "high_string_bias": 1.35, "unison_return_bias": 1.40, "duration_sensitive": True},
        ("bontempi-rich-tab-2024",),
    ),
)


def snapshot() -> dict[str, Any]:
    return {"version": ARTICULATION_RESEARCH_VERSION, "rules": [item.to_dict() for item in RULES]}
