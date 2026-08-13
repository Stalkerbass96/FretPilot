"""Enrich section PlayingContexts with song- and section-level style priors."""

from __future__ import annotations

from fretpilot.analysis.section_contexts import SectionContextAnalysis, analyze_section_contexts
from fretpilot.analysis.sections import SectionSegmentation
from fretpilot.analysis.style_inference import (
    blend_style_scores,
    infer_song_style_prior,
    infer_style_from_features,
)
from fretpilot.detection.models import InstrumentStream
from fretpilot.knowledge.context_strategy import apply_style_scores_to_context


def analyze_style_aware_section_contexts(
    segmentation: SectionSegmentation,
    stream: InstrumentStream,
    *,
    minimum_behavior_score: float = .50,
) -> list[SectionContextAnalysis]:
    """Apply broad song prior plus locally dominant section behavior."""

    contexts = analyze_section_contexts(
        segmentation,
        minimum_behavior_score=minimum_behavior_score,
    )
    song_style = infer_song_style_prior(stream)

    by_id = {item.section_id: item for item in segmentation.sections}
    for context in contexts:
        section = by_id[context.section_id]
        local = infer_style_from_features(
            section.features,
            program=stream.program,
            scope="section",
        )
        blended = blend_style_scores(song_style.style_scores, local.style_scores)
        apply_style_scores_to_context(context.playing_context, blended)

    return contexts
