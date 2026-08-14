"""Versioned musical knowledge used by FretPilot analysis and score planning."""

from fretpilot.knowledge.models import (
    KnowledgeEntry,
    KnowledgeEvaluation,
    KnowledgeProvenance,
    KnowledgeSource,
    KnowledgeSnapshot,
)
from fretpilot.knowledge.registry import (
    BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION,
    KnowledgeRegistry,
    SUPPORTED_KNOWLEDGE_SCHEMA_VERSION,
    get_builtin_knowledge_registry,
    load_knowledge_snapshot,
)
from fretpilot.knowledge.shapes import (
    GuitarShapePrototype,
    ShapeNote,
    get_guitar_shape,
    list_guitar_shapes,
)

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
    "BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION",
    "SUPPORTED_KNOWLEDGE_SCHEMA_VERSION",
    "KnowledgeEntry",
    "KnowledgeEvaluation",
    "KnowledgeProvenance",
    "KnowledgeSource",
    "KnowledgeSnapshot",
    "KnowledgeRegistry",
    "get_builtin_knowledge_registry",
    "load_knowledge_snapshot",
    "ShapeNote",
    "GuitarShapePrototype",
    "get_guitar_shape",
    "list_guitar_shapes",
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
