"""Apply inferred style priors to a PlayingContext without weakening hard rules."""

from __future__ import annotations

from dataclasses import fields
from typing import Any, TypeVar

from fretpilot.knowledge.playing_contexts import (
    PlayingContext,
    compose_playing_context,
    get_playing_profile,
)
from fretpilot.knowledge.strategy_resolver import ResolvedStrategy, resolve_style_strategy

T = TypeVar("T")


def _scaled_preferences(base: T, factors: dict[str, float]) -> T:
    values: dict[str, Any] = {}
    for item in fields(base):
        value = float(getattr(base, item.name))
        factor = float(factors.get(item.name, 1.0))
        values[item.name] = max(.25, min(2.5, value * factor))
    return type(base)(**values)


def apply_style_scores_to_context(
    context: PlayingContext,
    style_scores: dict[str, float],
) -> ResolvedStrategy:
    """Mutate one context with soft style knowledge and return score metadata."""

    merged_styles = dict(context.style_scores)
    for style, score in style_scores.items():
        merged_styles[style] = max(merged_styles.get(style, 0.0), float(score))

    modeled_scores: dict[str, float] = {}
    modeled_scores.update(context.role_scores)
    modeled_scores.update(context.technique_scores)
    modeled_scores.update(
        {style: score for style, score in merged_styles.items() if get_playing_profile(style) is not None}
    )
    modeled = compose_playing_context(modeled_scores)

    unmodeled = {
        style: score
        for style, score in merged_styles.items()
        if get_playing_profile(style) is None
    }
    preference_strategy = resolve_style_strategy(
        unmodeled,
        role_scores=context.role_scores,
        technique_scores=context.technique_scores,
    )
    score_strategy = resolve_style_strategy(
        merged_styles,
        role_scores=context.role_scores,
        technique_scores=context.technique_scores,
    )

    context.style_scores = merged_styles
    context.fingering = _scaled_preferences(modeled.fingering, preference_strategy.fingering)
    context.articulation = _scaled_preferences(modeled.articulation, preference_strategy.articulation)
    context.performance = _scaled_preferences(modeled.performance, preference_strategy.performance)
    context.source_profiles = list(dict.fromkeys(
        [*modeled.source_profiles, *(f"strategy:{name}" for name in score_strategy.styles)]
    ))
    context.knowledge_version = modeled.knowledge_version
    context.knowledge_entry_ids = list(
        dict.fromkeys([*context.knowledge_entry_ids, *modeled.knowledge_entry_ids])
    )
    return score_strategy
