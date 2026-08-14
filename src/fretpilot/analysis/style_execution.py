"""Style-aware section execution using the existing deterministic guitar engine."""

from __future__ import annotations

from typing import Mapping, TYPE_CHECKING

from fretpilot.analysis.guitar import GuitarTrackAnalysis
from fretpilot.analysis.section_execution import analyze_guitar_track_by_sections
from fretpilot.analysis.sections import segment_instrument_stream
from fretpilot.analysis.style_contexts import analyze_style_aware_section_contexts
from fretpilot.detection.models import InstrumentStream
from fretpilot.midi.models import NormalizedTimeline

if TYPE_CHECKING:
    from fretpilot.knowledge.playing_contexts import PlayingContext


def analyze_guitar_stream_style_aware(
    timeline: NormalizedTimeline,
    stream: InstrumentStream,
    *,
    max_fret: int = 24,
    window_measures: int = 2,
    change_threshold: float = .22,
    minimum_behavior_score: float = .50,
    context_overrides: Mapping[str, PlayingContext] | None = None,
    carry_boundary_strength_max: float = 1.35,
) -> GuitarTrackAnalysis:
    """Use inferred song/section style priors before fingering and articulation."""

    segmentation = segment_instrument_stream(
        timeline,
        stream,
        window_measures=window_measures,
        change_threshold=change_threshold,
    )
    contexts = analyze_style_aware_section_contexts(
        segmentation,
        stream,
        minimum_behavior_score=minimum_behavior_score,
    )
    return analyze_guitar_track_by_sections(
        stream.as_track(),
        contexts,
        max_fret=max_fret,
        context_overrides=context_overrides,
        carry_boundary_strength_max=carry_boundary_strength_max,
    )
