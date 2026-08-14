"""Composable guitar-playing knowledge for downstream musical decisions.

Role, style, and technique-family evidence stay separate. Their approved,
versioned profiles are loaded from the pinned knowledge snapshot and merged
into soft preferences. Deterministic fretboard constraints remain authoritative.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from fretpilot.knowledge.models import BehaviorProfileMatch, KnowledgeEntry
from fretpilot.knowledge.registry import get_builtin_knowledge_registry


_REGISTRY = get_builtin_knowledge_registry()
PLAYING_KNOWLEDGE_VERSION = _REGISTRY.snapshot.snapshot_version


@dataclass(frozen=True, slots=True)
class FingeringPreferences:
    adjacent_string_arpeggio: float = 1.0
    same_string_legato: float = 1.0
    hand_position_stability: float = 1.0
    shape_reuse: float = 1.0
    open_string_usage: float = 1.0
    low_register_bias: float = 1.0
    compact_chord_voicing: float = 1.0
    wide_interval_position_shift: float = 1.0


@dataclass(frozen=True, slots=True)
class ArticulationPreferences:
    hammer_pull: float = 1.0
    slide: float = 1.0
    bend: float = 1.0
    vibrato: float = 1.0
    palm_mute: float = 1.0
    let_ring: float = 1.0
    staccato: float = 1.0


@dataclass(frozen=True, slots=True)
class PerformancePreferences:
    velocity_variation: float = 1.0
    timing_looseness: float = 1.0
    note_overlap: float = 1.0
    accent_strength: float = 1.0


@dataclass(frozen=True, slots=True)
class PlayingProfile:
    profile_id: str
    label: str
    dimension: str  # role | style | technique_family
    description: str
    fingering: FingeringPreferences = FingeringPreferences()
    articulation: ArticulationPreferences = ArticulationPreferences()
    performance: PerformancePreferences = PerformancePreferences()
    maturity: str = "experimental"
    provenance: str = "hand_authored"
    knowledge_id: str = ""
    knowledge_version: str = PLAYING_KNOWLEDGE_VERSION


@dataclass(slots=True)
class PlayingContext:
    """A merge of context evidence and the exact knowledge entries it used."""

    role_scores: dict[str, float] = field(default_factory=dict)
    style_scores: dict[str, float] = field(default_factory=dict)
    technique_scores: dict[str, float] = field(default_factory=dict)
    fingering: FingeringPreferences = FingeringPreferences()
    articulation: ArticulationPreferences = ArticulationPreferences()
    performance: PerformancePreferences = PerformancePreferences()
    source_profiles: list[str] = field(default_factory=list)
    knowledge_version: str = PLAYING_KNOWLEDGE_VERSION
    knowledge_entry_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _profile_from_entry(entry: KnowledgeEntry) -> PlayingProfile:
    payload = entry.payload
    dimension = str(payload["dimension"])
    if dimension not in {"role", "style", "technique_family"}:
        raise ValueError(
            f"Unsupported playing-profile dimension {dimension!r} in "
            f"{entry.knowledge_id}."
        )
    return PlayingProfile(
        profile_id=str(payload["profile_id"]),
        label=str(payload["label"]),
        dimension=dimension,
        description=str(payload["description"]),
        fingering=FingeringPreferences(**dict(payload.get("fingering", {}))),
        articulation=ArticulationPreferences(
            **dict(payload.get("articulation", {}))
        ),
        performance=PerformancePreferences(
            **dict(payload.get("performance", {}))
        ),
        maturity=str(payload.get("maturity", "experimental")),
        provenance=entry.provenance.source_type,
        knowledge_id=entry.knowledge_id,
        knowledge_version=entry.knowledge_version,
    )


PROFILES: tuple[PlayingProfile, ...] = tuple(
    _profile_from_entry(entry)
    for entry in _REGISTRY.query(
        domain="guitar_playing",
        kind="playing_profile",
        statuses={"approved"},
    )
)
_PROFILE_BY_ID = {profile.profile_id: profile for profile in PROFILES}
if len(_PROFILE_BY_ID) != len(PROFILES):
    raise ValueError("Playing profile IDs must be unique within one snapshot.")


def get_playing_profile(profile_id: str) -> PlayingProfile | None:
    return _PROFILE_BY_ID.get(profile_id)


def _weighted_average(
    weighted_profiles: list[tuple[PlayingProfile, float]],
    attr_name: str,
    defaults: object,
):
    fields = defaults.__dataclass_fields__  # type: ignore[attr-defined]
    values: dict[str, float] = {}
    total_weight = sum(weight for _profile, weight in weighted_profiles)
    if total_weight <= 0:
        return defaults

    for field_name in fields:
        numerator = 0.0
        for profile, weight in weighted_profiles:
            group = getattr(profile, attr_name)
            numerator += float(getattr(group, field_name)) * weight
        values[field_name] = numerator / total_weight
    return type(defaults)(**values)


def compose_playing_context(
    profile_scores: Mapping[str, float],
) -> PlayingContext:
    """Merge approved role/style/technique profiles into one context."""

    weighted: list[tuple[PlayingProfile, float]] = []
    role_scores: dict[str, float] = {}
    style_scores: dict[str, float] = {}
    technique_scores: dict[str, float] = {}

    for profile_id, raw_score in profile_scores.items():
        profile = get_playing_profile(profile_id)
        if profile is None:
            continue
        score = max(0.0, min(1.0, float(raw_score)))
        if score <= 0:
            continue
        weighted.append((profile, score))
        if profile.dimension == "role":
            role_scores[profile_id] = score
        elif profile.dimension == "style":
            style_scores[profile_id] = score
        else:
            technique_scores[profile_id] = score

    return PlayingContext(
        role_scores=role_scores,
        style_scores=style_scores,
        technique_scores=technique_scores,
        fingering=_weighted_average(weighted, "fingering", FingeringPreferences()),
        articulation=_weighted_average(
            weighted,
            "articulation",
            ArticulationPreferences(),
        ),
        performance=_weighted_average(
            weighted,
            "performance",
            PerformancePreferences(),
        ),
        source_profiles=[profile.profile_id for profile, _weight in weighted],
        knowledge_version=PLAYING_KNOWLEDGE_VERSION,
        knowledge_entry_ids=[profile.knowledge_id for profile, _weight in weighted],
    )


def context_from_behavior_matches(
    matches: Iterable[BehaviorProfileMatch],
    *,
    explicit_styles: Mapping[str, float] | None = None,
    explicit_techniques: Mapping[str, float] | None = None,
) -> PlayingContext:
    """Bridge Layer-4 behavior matches into the playing-knowledge system."""

    scores: dict[str, float] = {}
    for match in matches:
        score = max(0.0, min(1.0, float(match.score)))
        if match.profile_id in {"solo", "riff", "strumming"}:
            scores[match.profile_id] = max(scores.get(match.profile_id, 0.0), score)
        elif match.profile_id == "breakdown":
            scores["riff"] = max(scores.get("riff", 0.0), score)
            scores["metal"] = max(scores.get("metal", 0.0), score)
        elif match.profile_id == "jazz_comping":
            scores["strumming"] = max(scores.get("strumming", 0.0), score)
            scores["jazz"] = max(scores.get("jazz", 0.0), score)

    for source in (explicit_styles or {}, explicit_techniques or {}):
        for profile_id, score in source.items():
            scores[profile_id] = max(scores.get(profile_id, 0.0), float(score))

    return compose_playing_context(scores)
