"""Composable guitar-playing knowledge for downstream musical decisions.

This module deliberately separates *what a part is doing* (role/behavior) from
*what stylistic language it belongs to* (genre/style). A metal solo, for
example, can combine the ``solo`` role with the ``metal`` style. The merged
context produces deterministic preference weights that fingering, articulation,
and performance renderers can consume without hard-coding genre rules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from fretpilot.detection.models import BehaviorProfileMatch


PLAYING_KNOWLEDGE_VERSION = "0.1"


@dataclass(frozen=True, slots=True)
class FingeringPreferences:
    """Soft preferences used by a guitar fingering optimizer.

    Values are intentionally dimensionless. They describe relative tendencies,
    not absolute musical truths. Learned versions may later be estimated from
    licensed/open tablature corpora.
    """

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
    provenance: str = "hand-authored-v0"


@dataclass(slots=True)
class PlayingContext:
    """A merge of role/style evidence and the preferences derived from it."""

    role_scores: dict[str, float] = field(default_factory=dict)
    style_scores: dict[str, float] = field(default_factory=dict)
    technique_scores: dict[str, float] = field(default_factory=dict)
    fingering: FingeringPreferences = FingeringPreferences()
    articulation: ArticulationPreferences = ArticulationPreferences()
    performance: PerformancePreferences = PerformancePreferences()
    source_profiles: list[str] = field(default_factory=list)
    knowledge_version: str = PLAYING_KNOWLEDGE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PROFILES: tuple[PlayingProfile, ...] = (
    PlayingProfile(
        profile_id="solo",
        label="Solo / Lead",
        dimension="role",
        description="Melodic lead playing with phrasing, expressive articulation, and position-aware legato.",
        fingering=FingeringPreferences(
            adjacent_string_arpeggio=0.85,
            same_string_legato=1.35,
            hand_position_stability=1.15,
            shape_reuse=0.90,
            open_string_usage=0.65,
            wide_interval_position_shift=1.15,
        ),
        articulation=ArticulationPreferences(
            hammer_pull=1.35,
            slide=1.30,
            bend=1.45,
            vibrato=1.45,
            palm_mute=0.65,
            let_ring=0.85,
        ),
    ),
    PlayingProfile(
        profile_id="riff",
        label="Riff",
        dimension="role",
        description="Repeated phrase cells where shape memory and stable picking geometry are important.",
        fingering=FingeringPreferences(
            adjacent_string_arpeggio=1.20,
            same_string_legato=0.90,
            hand_position_stability=1.25,
            shape_reuse=1.45,
            open_string_usage=1.05,
            compact_chord_voicing=1.15,
        ),
        articulation=ArticulationPreferences(
            hammer_pull=0.90,
            slide=0.95,
            bend=0.55,
            vibrato=0.65,
            palm_mute=1.15,
            staccato=1.15,
        ),
        performance=PerformancePreferences(
            timing_looseness=0.80,
            accent_strength=1.20,
        ),
    ),
    PlayingProfile(
        profile_id="strumming",
        label="Strumming / Chord Rhythm",
        dimension="role",
        description="Chordal rhythm playing prioritizing playable voicings and hand-position continuity.",
        fingering=FingeringPreferences(
            adjacent_string_arpeggio=0.85,
            same_string_legato=0.45,
            hand_position_stability=1.40,
            shape_reuse=1.35,
            open_string_usage=1.25,
            compact_chord_voicing=1.45,
        ),
        articulation=ArticulationPreferences(
            hammer_pull=0.45,
            slide=0.55,
            bend=0.20,
            vibrato=0.25,
            let_ring=1.25,
        ),
        performance=PerformancePreferences(
            timing_looseness=1.15,
            velocity_variation=1.15,
            accent_strength=1.15,
        ),
    ),
    PlayingProfile(
        profile_id="metal",
        label="Metal",
        dimension="style",
        description="Tight low-register guitar language with palm mute, pedal tones, power shapes, and controlled shifts.",
        fingering=FingeringPreferences(
            adjacent_string_arpeggio=1.05,
            same_string_legato=0.75,
            hand_position_stability=1.35,
            shape_reuse=1.40,
            open_string_usage=1.25,
            low_register_bias=1.45,
            compact_chord_voicing=1.30,
        ),
        articulation=ArticulationPreferences(
            hammer_pull=0.85,
            slide=1.00,
            bend=0.70,
            vibrato=0.80,
            palm_mute=1.60,
            let_ring=0.55,
            staccato=1.35,
        ),
        performance=PerformancePreferences(
            timing_looseness=0.65,
            velocity_variation=0.75,
            note_overlap=0.70,
            accent_strength=1.35,
        ),
    ),
    PlayingProfile(
        profile_id="jazz",
        label="Jazz",
        dimension="style",
        description="Voice-leading-aware chord and melodic language with economical position changes and richer voicings.",
        fingering=FingeringPreferences(
            adjacent_string_arpeggio=1.05,
            same_string_legato=0.85,
            hand_position_stability=1.25,
            shape_reuse=1.10,
            open_string_usage=0.65,
            compact_chord_voicing=1.35,
            wide_interval_position_shift=1.20,
        ),
        articulation=ArticulationPreferences(
            hammer_pull=0.85,
            slide=0.95,
            bend=0.65,
            vibrato=0.85,
            palm_mute=0.45,
            let_ring=0.90,
            staccato=1.05,
        ),
        performance=PerformancePreferences(
            timing_looseness=1.20,
            velocity_variation=1.20,
            accent_strength=0.95,
        ),
    ),
    PlayingProfile(
        profile_id="rock_arpeggio",
        label="Rock Arpeggio",
        dimension="technique_family",
        description="Movable adjacent-string arpeggio shapes such as the Message in a Bottle reference pattern.",
        fingering=FingeringPreferences(
            adjacent_string_arpeggio=1.65,
            same_string_legato=0.75,
            hand_position_stability=1.30,
            shape_reuse=1.60,
            open_string_usage=0.65,
            compact_chord_voicing=1.15,
        ),
        articulation=ArticulationPreferences(let_ring=1.30),
    ),
)


_PROFILE_BY_ID = {profile.profile_id: profile for profile in PROFILES}


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
    """Merge role/style/technique profiles into one downstream context."""

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
        articulation=_weighted_average(weighted, "articulation", ArticulationPreferences()),
        performance=_weighted_average(weighted, "performance", PerformancePreferences()),
        source_profiles=[profile.profile_id for profile, _weight in weighted],
    )


def context_from_behavior_matches(
    matches: Iterable[BehaviorProfileMatch],
    *,
    explicit_styles: Mapping[str, float] | None = None,
    explicit_techniques: Mapping[str, float] | None = None,
) -> PlayingContext:
    """Bridge Layer-4 behavior matches into the playing-knowledge system.

    Detection behavior profiles currently include ``solo``, ``riff``,
    ``strumming``, ``breakdown`` and ``jazz_comping``. The latter two are mapped
    onto more orthogonal role/style concepts here instead of becoming one flat
    genre label.
    """

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
