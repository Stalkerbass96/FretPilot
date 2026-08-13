"""Versioned knowledge library for guitar roles, techniques, and styles.

Layer 4 answers a different question from guitar detection: after layers 1–3
estimate whether a stream is guitar, this library describes what kind of guitar
behavior it resembles. Profiles are intentionally data-like and inspectable so
they can later move to JSON/YAML or a learned model without changing callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from fretpilot.detection.models import BehaviorProfileMatch

LIBRARY_VERSION = "0.1"


@dataclass(frozen=True, slots=True)
class FeatureRule:
    feature: str
    weight: float
    minimum: float | None = None
    maximum: float | None = None

    def evaluate(self, features: Mapping[str, float | int]) -> tuple[bool, float] | None:
        if self.feature not in features:
            return None
        value = float(features[self.feature])
        matched = True
        if self.minimum is not None and value < self.minimum:
            matched = False
        if self.maximum is not None and value > self.maximum:
            matched = False
        return matched, self.weight


@dataclass(frozen=True, slots=True)
class GuitarBehaviorProfile:
    profile_id: str
    label: str
    category: str
    description: str
    rules: tuple[FeatureRule, ...]
    maturity: str = "experimental"


PROFILES: tuple[GuitarBehaviorProfile, ...] = (
    GuitarBehaviorProfile(
        profile_id="solo",
        label="Solo / Lead",
        category="role",
        description="Mostly monophonic melodic playing with manageable intervals.",
        rules=(
            FeatureRule("monophonic_onset_ratio", 0.35, minimum=0.80),
            FeatureRule("mean_onset_polyphony", 0.20, maximum=1.35),
            FeatureRule("pitch_range_semitones", 0.15, minimum=12),
            FeatureRule("adjacent_interval_within_octave_ratio", 0.30, minimum=0.75),
        ),
    ),
    GuitarBehaviorProfile(
        profile_id="riff",
        label="Riff",
        category="role",
        description="Repeated, compact melodic/harmonic figures with strong pitch reuse.",
        rules=(
            FeatureRule("repeated_pitch_ratio", 0.30, minimum=0.12),
            FeatureRule("pitch_range_semitones", 0.20, maximum=24),
            FeatureRule("short_note_ratio", 0.20, minimum=0.45),
            FeatureRule("adjacent_interval_within_octave_ratio", 0.30, minimum=0.80),
        ),
    ),
    GuitarBehaviorProfile(
        profile_id="strumming",
        label="Strumming / Chord Rhythm",
        category="technique",
        description="Frequent chord onsets with guitar-sized voicings.",
        rules=(
            FeatureRule("chord_onset_ratio", 0.40, minimum=0.35),
            FeatureRule("mean_onset_polyphony", 0.25, minimum=2.0, maximum=6.0),
            FeatureRule("max_onset_polyphony", 0.20, maximum=6.0),
            FeatureRule("short_note_ratio", 0.15, minimum=0.35),
        ),
    ),
    GuitarBehaviorProfile(
        profile_id="breakdown",
        label="Breakdown / Heavy Low Riff",
        category="style_behavior",
        description="Low-register repeated notes and compact rhythmic figures.",
        rules=(
            FeatureRule("low_register_ratio", 0.35, minimum=0.55),
            FeatureRule("repeated_pitch_ratio", 0.30, minimum=0.18),
            FeatureRule("short_note_ratio", 0.25, minimum=0.55),
            FeatureRule("pitch_range_semitones", 0.10, maximum=20),
        ),
    ),
    GuitarBehaviorProfile(
        profile_id="jazz_comping",
        label="Jazz Comping",
        category="style_behavior",
        description="Chord-heavy accompaniment; harmony-quality features come later.",
        rules=(
            FeatureRule("chord_onset_ratio", 0.45, minimum=0.45),
            FeatureRule("mean_onset_polyphony", 0.25, minimum=2.5, maximum=6.0),
            FeatureRule("max_onset_polyphony", 0.15, maximum=6.0),
            FeatureRule("pitch_range_semitones", 0.15, minimum=12, maximum=40),
        ),
    ),
)


def match_behavior_profiles(
    features: Mapping[str, float | int],
) -> list[BehaviorProfileMatch]:
    """Score current features against the experimental Layer-4 library."""

    matches: list[BehaviorProfileMatch] = []
    for profile in PROFILES:
        earned = 0.0
        available = 0.0
        matched_features: list[str] = []
        missing_features: list[str] = []

        for rule in profile.rules:
            evaluation = rule.evaluate(features)
            if evaluation is None:
                missing_features.append(rule.feature)
                continue
            matched, weight = evaluation
            available += weight
            if matched:
                earned += weight
                matched_features.append(rule.feature)

        score = earned / available if available else 0.0
        status = "strong" if score >= 0.75 else "possible" if score >= 0.50 else "weak"
        matches.append(
            BehaviorProfileMatch(
                profile_id=profile.profile_id,
                label=profile.label,
                score=round(score, 6),
                status=status,
                matched_features=matched_features,
                missing_features=missing_features,
            )
        )

    matches.sort(key=lambda match: match.score, reverse=True)
    return matches
