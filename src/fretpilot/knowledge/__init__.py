"""Versioned musical knowledge used by FretPilot analysis and score planning."""

from fretpilot.knowledge.guitar_behaviors import (
    LIBRARY_VERSION,
    PROFILES as BEHAVIOR_PROFILES,
    match_behavior_profiles,
)
from fretpilot.knowledge.playing_contexts import (
    PLAYING_KNOWLEDGE_VERSION,
    PROFILES as PLAYING_PROFILES,
    ArticulationPreferences,
    FingeringPreferences,
    PerformancePreferences,
    PlayingContext,
    PlayingProfile,
    compose_playing_context,
    context_from_behavior_matches,
    get_playing_profile,
)
from fretpilot.knowledge.research_sources import (
    RESEARCH_SOURCE_VERSION,
    SOURCES as RESEARCH_SOURCES,
    get_source as get_research_source,
)
from fretpilot.knowledge.strategy_priors import (
    STYLE_STRATEGY_PRIORS,
    TECHNIQUE_STRATEGY_PRIORS,
)

# Backward-compatible alias for callers that used the old Layer-4 name.
PROFILES = BEHAVIOR_PROFILES

__all__ = [
    "LIBRARY_VERSION",
    "PLAYING_KNOWLEDGE_VERSION",
    "RESEARCH_SOURCE_VERSION",
    "PROFILES",
    "BEHAVIOR_PROFILES",
    "PLAYING_PROFILES",
    "RESEARCH_SOURCES",
    "STYLE_STRATEGY_PRIORS",
    "TECHNIQUE_STRATEGY_PRIORS",
    "FingeringPreferences",
    "ArticulationPreferences",
    "PerformancePreferences",
    "PlayingContext",
    "PlayingProfile",
    "match_behavior_profiles",
    "get_playing_profile",
    "get_research_source",
    "compose_playing_context",
    "context_from_behavior_matches",
]
