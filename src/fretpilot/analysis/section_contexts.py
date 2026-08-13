"""Section-level behavior matching and PlayingContext derivation.

Segmentation and interpretation stay separate: ``sections.py`` decides where a
behavioral region exists, while this module applies the current experimental
Layer-4 behavior library to each stable region and bridges supported evidence
into the composable PlayingContext knowledge model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fretpilot.analysis.sections import SectionSegmentation
from fretpilot.detection.models import BehaviorProfileMatch
from fretpilot.knowledge.guitar_behaviors import match_behavior_profiles
from fretpilot.knowledge.playing_contexts import (
    PlayingContext,
    context_from_behavior_matches,
)


@dataclass(slots=True)
class SectionContextAnalysis:
    section_id: str
    stream_id: str
    start_measure: int
    end_measure: int
    start_beat: float
    end_beat: float
    behavior_profiles: list[BehaviorProfileMatch]
    playing_context: PlayingContext
    # Manual/legacy section contexts default to a strong/unknown boundary so
    # existing callers retain reset behavior unless they explicitly opt in to
    # cross-section hand-position continuity.
    boundary_confidence: float = 1.0
    boundary_strength: float = 2.0
    boundary_reason: str = "manual_or_unknown_boundary"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_section_contexts(
    segmentation: SectionSegmentation,
    *,
    minimum_behavior_score: float = 0.50,
) -> list[SectionContextAnalysis]:
    """Match behavior profiles independently for every segmented region.

    All profile matches remain visible for diagnostics, but only matches at or
    above ``minimum_behavior_score`` contribute to PlayingContext. This prevents
    weak whole-vocabulary evidence from contaminating every section while the
    Layer-4 library is still experimental.
    """

    if not 0.0 <= minimum_behavior_score <= 1.0:
        raise ValueError("minimum_behavior_score must be between 0 and 1.")

    results: list[SectionContextAnalysis] = []
    for section in segmentation.sections:
        matches = match_behavior_profiles(section.features)
        context_matches = [
            match for match in matches if match.score >= minimum_behavior_score
        ]
        context = context_from_behavior_matches(context_matches)
        results.append(
            SectionContextAnalysis(
                section_id=section.section_id,
                stream_id=section.stream_id,
                start_measure=section.start_measure,
                end_measure=section.end_measure,
                start_beat=section.start_beat,
                end_beat=section.end_beat,
                behavior_profiles=matches,
                playing_context=context,
                boundary_confidence=section.boundary_confidence,
                boundary_strength=section.boundary_strength,
                boundary_reason=section.boundary_reason,
            )
        )

    return results
