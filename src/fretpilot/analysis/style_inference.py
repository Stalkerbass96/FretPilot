"""Soft guitar-style priors derived from deterministic MIDI behavior."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from fretpilot.detection.guitar_classifier import extract_behavior_features
from fretpilot.detection.models import InstrumentStream


@dataclass(slots=True)
class StyleInference:
    scope: str
    style_scores: dict[str, float]
    reasons: dict[str, list[str]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _score(rules: list[tuple[bool, float, str]]) -> tuple[float, list[str]]:
    value = 0.0
    reasons: list[str] = []
    for matched, weight, reason in rules:
        if matched:
            value += weight
            reasons.append(reason)
    return round(min(1.0, value), 6), reasons


def infer_style_from_features(
    features: Mapping[str, Any],
    *,
    program: int | None = None,
    scope: str = "section",
) -> StyleInference:
    """Return multiple soft style scores; never a hard genre label."""

    mono = float(features.get("monophonic_onset_ratio", 0.0))
    chord = float(features.get("chord_onset_ratio", 0.0))
    repeated = float(features.get("repeated_pitch_ratio", 0.0))
    low = float(features.get("low_register_ratio", 0.0))
    short = float(features.get("short_note_ratio", 0.0))
    adjacent = float(features.get("adjacent_interval_within_octave_ratio", 0.0))
    poly = float(features.get("mean_onset_polyphony", 0.0))
    pitch_range = float(features.get("pitch_range_semitones", 0.0))

    clean = program in {26, 27, 28}
    driven = program in {29, 30}
    acoustic = program in {24, 25}

    definitions = {
        "metal": [
            (driven, .30, "driven_program"), (low >= .50, .25, "low_register"),
            (repeated >= .14, .18, "repeated_riff"), (short >= .50, .17, "short_notes"),
        ],
        "rock": [
            (clean or driven, .25, "rock_guitar_program"), (repeated >= .10, .20, "pattern_reuse"),
            (.35 <= short <= .85, .20, "rhythmic_density"), (.12 <= chord <= .70, .15, "mixed_texture"),
            (10 <= pitch_range <= 36, .20, "guitar_sized_range"),
        ],
        "jazz": [
            (program in {26, 27}, .25, "jazz_or_clean_program"), (chord >= .40, .30, "chord_texture"),
            (poly >= 2.3, .25, "voicing_polyphony"), (12 <= pitch_range <= 40, .20, "voicing_range"),
        ],
        "blues": [
            (program in {27, 29}, .20, "clean_or_overdrive_program"), (mono >= .65, .25, "lead_texture"),
            (10 <= pitch_range <= 30, .20, "box_sized_range"), (adjacent >= .75, .20, "compact_intervals"),
            (short <= .70, .15, "sustained_note_room"),
        ],
        "funk": [
            (program in {27, 28}, .30, "clean_or_muted_program"), (short >= .55, .30, "percussive_notes"),
            (chord >= .25, .20, "partial_chords"), (poly <= 4.5, .20, "compact_texture"),
        ],
        "fingerstyle": [
            (acoustic, .35, "acoustic_program"), (1.2 <= poly <= 3.8, .20, "mixed_polyphony"),
            (.15 <= chord <= .65, .15, "arpeggio_chord_mix"), (pitch_range >= 18, .15, "wide_register"),
            (.20 <= low <= .75, .15, "bass_presence"),
        ],
    }

    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    for style, rules in definitions.items():
        scores[style], reasons[style] = _score(rules)

    scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
    return StyleInference(scope=scope, style_scores=scores, reasons=reasons)


def infer_song_style_prior(stream: InstrumentStream) -> StyleInference:
    return infer_style_from_features(
        extract_behavior_features(stream).to_dict(),
        program=stream.program,
        scope="song",
    )


def blend_style_scores(
    song_scores: Mapping[str, float],
    section_scores: Mapping[str, float],
    *,
    section_weight: float = .70,
) -> dict[str, float]:
    section_weight = max(0.0, min(1.0, section_weight))
    song_weight = 1.0 - section_weight
    return {
        style: round(song_weight * float(song_scores.get(style, 0.0)) + section_weight * float(section_scores.get(style, 0.0)), 6)
        for style in set(song_scores) | set(section_scores)
    }
