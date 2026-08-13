"""Resolve section PlayingContexts into target-neutral score-strategy regions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from fretpilot.analysis.section_contexts import SectionContextAnalysis
from fretpilot.knowledge.strategy_resolver import resolve_style_strategy


@dataclass(slots=True)
class SectionScoreStrategy:
    section_id: str
    start_beat: float
    end_beat: float
    style_scores: dict[str, float]
    fingering: dict[str, float]
    articulation: dict[str, float]
    performance: dict[str, float]
    score: dict[str, Any]
    source_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_section_score_strategies(
    contexts: Iterable[SectionContextAnalysis],
) -> list[SectionScoreStrategy]:
    results: list[SectionScoreStrategy] = []
    for item in contexts:
        context = item.playing_context
        resolved = resolve_style_strategy(
            context.style_scores,
            role_scores=context.role_scores,
            technique_scores=context.technique_scores,
        )
        results.append(
            SectionScoreStrategy(
                section_id=item.section_id,
                start_beat=item.start_beat,
                end_beat=item.end_beat,
                style_scores=dict(context.style_scores),
                fingering=dict(resolved.fingering),
                articulation=dict(resolved.articulation),
                performance=dict(resolved.performance),
                score=dict(resolved.score),
                source_ids=list(resolved.source_ids),
            )
        )
    return results
