"""Evidence-backed fretboard planning priors."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


FRETBOARD_RESEARCH_VERSION = "0.1"


@dataclass(frozen=True, slots=True)
class FretboardKnowledge:
    rule_id: str
    statement: str
    hints: dict[str, float | int | bool]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


RULES: tuple[FretboardKnowledge, ...] = (
    FretboardKnowledge(
        "track-hand-position",
        "Treat fretting-hand position as persistent phrase state rather than only pairwise note motion.",
        {"track_hand_position": True, "phrase_local_optimization": True, "cross_phrase_transition": True},
        ("bontempi-rich-tab-2024",),
    ),
    FretboardKnowledge(
        "middle-neck-weak-prior",
        "Use positions 5 through 12 as a weak lead-guitar prior, never as a hard restriction.",
        {"preferred_fret_min": 5, "preferred_fret_max": 12, "preferred_zone_strength": 0.35},
        ("bontempi-rich-tab-2024",),
    ),
    FretboardKnowledge(
        "ioi-aware-shifts",
        "Penalize large hand and string moves more strongly when inter-onset time is short.",
        {"ioi_aware_position_shift": True, "ioi_aware_string_change": True},
        ("bontempi-rich-tab-2024",),
    ),
    FretboardKnowledge(
        "previous-voicing-context",
        "Rank a chord voicing in context of the previous voicing to improve hand and texture continuity.",
        {"previous_voicing_context": True, "texture_continuity_weight": 1.35, "hand_transition_weight": 1.30},
        ("dhooge-chord-context-2024", "fretboardflow-2025"),
    ),
)


def snapshot() -> dict[str, Any]:
    return {"version": FRETBOARD_RESEARCH_VERSION, "rules": [item.to_dict() for item in RULES]}
