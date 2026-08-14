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
    """Return multiple conservative soft style scores, never a hard genre label."""

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
    arpeggio_like = mono >= .60 and adjacent >= .75 and short <= .55

    definitions = {
        "metal": [
            (driven, .30, "driven_program"), (low >= .50, .25, "low_register"),
            (repeated >= .14, .18, "repeated_riff"), (short >= .50, .17, "short_notes"),
        ],
        "rock": [
            (clean or driven, .20, "rock_guitar_program"), (arpeggio_like, .30, "guitar_arpeggio_texture"),
            (repeated >= .10, .15, "pattern_reuse"), (.10 <= chord <= .70, .10, "mixed_texture"),
            (10 <= pitch_range <= 48, .15, "guitar_sized_range"), (.35 <= short <= .85, .10, "rhythmic_density"),
        ],
        "pop": [
            (acoustic or program == 27, .15, "acoustic_or_clean_program"), (.20 <= chord <= .75, .20, "song_chord_texture"),
            (.25 <= short <= .75, .15, "moderate_rhythm_density"), (10 <= pitch_range <= 42, .15, "arrangement_range"),
            (repeated >= .08, .10, "repeating_song_pattern"),
        ],
        "punk": [
            (driven, .30, "driven_program"), (short >= .62, .30, "persistent_short_attacks"),
            (chord >= .25, .15, "frequent_chord_attacks"), (repeated >= .12, .15, "repeated_shape_rhythm"),
            (pitch_range <= 24, .10, "compact_register"),
        ],
        "jazz": [
            (program == 26, .20, "jazz_guitar_program"), (program == 27, .08, "clean_guitar_program"),
            (chord >= .40, .35, "chord_texture"), (poly >= 2.3, .30, "voicing_polyphony"),
            (12 <= pitch_range <= 40, .12, "voicing_range"),
        ],
        "blues": [
            (program in {27, 29}, .10, "clean_or_overdrive_program"), (mono >= .65, .15, "lead_texture"),
            (10 <= pitch_range <= 30, .30, "box_sized_range"), (adjacent >= .75, .10, "compact_intervals"),
            (short <= .70, .05, "sustained_note_room"),
        ],
        "funk": [
            (program == 28, .30, "muted_guitar_program"), (program == 27, .08, "clean_guitar_program"),
            (short >= .55, .35, "percussive_notes"), (chord >= .25 and short >= .45, .17, "short_partial_chords"),
            (poly <= 4.5, .10, "compact_texture"),
        ],
        "rnb": [
            (program in {27, 28}, .10, "clean_or_muted_program"), (chord >= .25 and poly >= 1.5, .20, "chordal_accompaniment"),
            (1.5 <= poly <= 5.0, .30, "partial_chord_polyphony"), (.30 <= short <= .80, .15, "mixed_note_lengths"),
            (pitch_range >= 12, .10, "extended_voicing_range"),
        ],
        "country": [
            (acoustic, .35, "acoustic_program"), (program == 27, .05, "clean_program"),
            (mono >= .55, .10, "single_note_roll_texture"), (adjacent >= .80, .10, "compact_cross_string_motion"),
            (pitch_range >= 12, .10, "wide_register"), (low <= .60, .10, "not_low_register_dominated"),
        ],
        "fingerstyle": [
            (acoustic, .45, "acoustic_program"), (1.2 <= poly <= 3.8, .15, "mixed_polyphony"),
            (.15 <= chord <= .65, .10, "arpeggio_chord_mix"), (pitch_range >= 18, .10, "wide_register"),
            (.20 <= low <= .75, .10, "bass_presence"),
        ],
    }

    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    for style, rules in definitions.items():
        scores[style], reasons[style] = _score(rules)

    # Country/fingerstyle need stronger evidence than a generic clean electric
    # guitar part; otherwise arpeggiated rock/pop material gets contaminated.
    if not acoustic:
        scores["country"] = min(scores["country"], .35)
        scores["fingerstyle"] = min(scores["fingerstyle"], .30)

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
