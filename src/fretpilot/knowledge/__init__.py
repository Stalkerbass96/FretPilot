"""Versioned musical knowledge used by FretPilot classifiers and renderers."""

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

# Backward-compatible alias for callers that used the old Layer-4 name.
PROFILES = BEHAVIOR_PROFILES

__all__ = [
    "LIBRARY_VERSION",
    "PLAYING_KNOWLEDGE_VERSION",
    "PROFILES",
    "BEHAVIOR_PROFILES",
    "PLAYING_PROFILES",
    "FingeringPreferences",
    "ArticulationPreferences",
    "PerformancePreferences",
    "PlayingContext",
    "PlayingProfile",
    "match_behavior_profiles",
    "get_playing_profile",
    "compose_playing_context",
    "context_from_behavior_matches",
]
