"""Resolve heterogeneous style-prior dictionaries into one strategy view."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from fretpilot.knowledge.strategy_priors import STYLE_STRATEGY_PRIORS

FINGERING_KEYS = {
    "adjacent_string_arpeggio", "same_string_legato", "hand_position_stability",
    "shape_reuse", "open_string_usage", "low_register_bias",
    "compact_chord_voicing", "wide_interval_position_shift",
}
ARTICULATION_KEYS = {"hammer_pull", "slide", "bend", "vibrato", "palm_mute", "let_ring", "staccato"}
PERFORMANCE_KEYS = {"velocity_variation", "timing_looseness", "note_overlap", "accent_strength"}


@dataclass(slots=True)
class ResolvedStrategy:
    fingering: dict[str, float] = field(default_factory=dict)
    articulation: dict[str, float] = field(default_factory=dict)
    performance: dict[str, float] = field(default_factory=dict)
    score: dict[str, Any] = field(default_factory=dict)
    source_ids: list[str] = field(default_factory=list)
    styles: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _branch_weights(role_scores: Mapping[str, float], technique_scores: Mapping[str, float]) -> dict[str, float]:
    return {
        "lead": float(role_scores.get("solo", 0.0)),
        "rhythm": max(float(role_scores.get("riff", 0.0)), float(role_scores.get("strumming", 0.0))),
        "arpeggio": max(float(technique_scores.get("rock_arpeggio", 0.0)), float(role_scores.get("riff", 0.0)) * .6),
    }


def _iter_rules(prior: Mapping[str, Any], branches: Mapping[str, float]):
    for key, value in prior.items():
        if key == "source_ids":
            continue
        if isinstance(value, Mapping):
            weight = float(branches.get(key, 0.0))
            if weight > 0:
                for nested_key, nested_value in value.items():
                    yield nested_key, nested_value, weight
        else:
            yield key, value, 1.0


def _add_weight(target: dict[str, float], key: str, value: float, evidence: float) -> None:
    current = target.get(key, 1.0)
    target[key] = round(max(.25, min(2.5, current + evidence * (value - 1.0))), 6)


def resolve_style_strategy(
    style_scores: Mapping[str, float],
    *,
    role_scores: Mapping[str, float] | None = None,
    technique_scores: Mapping[str, float] | None = None,
    minimum_style_score: float = .45,
) -> ResolvedStrategy:
    """Blend applicable style priors without choosing one exclusive genre."""

    result = ResolvedStrategy()
    branches = _branch_weights(role_scores or {}, technique_scores or {})

    for style, raw_score in style_scores.items():
        score = max(0.0, min(1.0, float(raw_score)))
        prior = STYLE_STRATEGY_PRIORS.get(style)
        if prior is None or score < minimum_style_score:
            continue
        result.styles[style] = score
        result.source_ids.extend(str(item) for item in prior.get("source_ids", ()))

        for key, value, branch_weight in _iter_rules(prior, branches):
            evidence = score * branch_weight
            if isinstance(value, bool):
                if value and evidence >= .35:
                    result.score[key] = True
                continue
            if isinstance(value, (int, float)):
                if key in FINGERING_KEYS:
                    _add_weight(result.fingering, key, float(value), evidence)
                elif key in ARTICULATION_KEYS:
                    _add_weight(result.articulation, key, float(value), evidence)
                elif key in PERFORMANCE_KEYS:
                    _add_weight(result.performance, key, float(value), evidence)
                else:
                    _add_weight(result.score, key, float(value), evidence)
            elif isinstance(value, str):
                result.score.setdefault("strategies", []).append(value)

    result.source_ids = sorted(set(result.source_ids))
    return result
