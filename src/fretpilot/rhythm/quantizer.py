"""Rhythm-grid analysis for imperfect MIDI timing.

V0 intentionally produces *suggestions* rather than mutating note data. This
keeps the raw performance timing intact and lets later phrase-level logic decide
whether a repair is musically justified.
"""

from __future__ import annotations

from statistics import mean

from fretpilot.midi.models import NormalizedTrack
from fretpilot.rhythm.models import (
    GridProfile,
    GridScore,
    RhythmAnalysis,
    RhythmSuggestion,
)

GRID_PROFILES: tuple[GridProfile, ...] = (
    GridProfile("quarter", 1.0, "straight", 0.000),
    GridProfile("eighth", 0.5, "straight", 0.004),
    GridProfile("eighth_triplet", 1.0 / 3.0, "triplet", 0.008),
    GridProfile("sixteenth", 0.25, "straight", 0.010),
    GridProfile("sixteenth_triplet", 1.0 / 6.0, "triplet", 0.016),
)


def _snap(value: float, step: float) -> float:
    return round(value / step) * step


def _score_profile(track: NormalizedTrack, profile: GridProfile) -> GridScore:
    if not track.notes:
        return GridScore(
            profile=profile,
            mean_absolute_error_beats=0.0,
            max_absolute_error_beats=0.0,
            objective=profile.complexity_penalty,
        )

    errors = [
        abs(note.start_beat - _snap(note.start_beat, profile.step_beats))
        for note in track.notes
    ]
    mean_error = mean(errors)
    max_error = max(errors)

    # The small complexity penalty prevents an unnecessarily dense grid from
    # winning just because every coarse-grid point also exists on a finer grid.
    objective = mean_error + profile.complexity_penalty

    return GridScore(
        profile=profile,
        mean_absolute_error_beats=mean_error,
        max_absolute_error_beats=max_error,
        objective=objective,
    )


def analyze_track_rhythm(track: NormalizedTrack) -> RhythmAnalysis:
    """Rank notation grids and propose repaired note-on positions.

    This is deliberately conservative. V0 only repairs onset placement; note
    duration spelling, ties, swing interpretation, tuplets across phrases, and
    polyphonic voice separation belong to later rhythm-engine stages.
    """

    scores = [_score_profile(track, profile) for profile in GRID_PROFILES]
    scores.sort(key=lambda score: score.objective)
    selected = scores[0].profile

    suggestions: list[RhythmSuggestion] = []
    tolerance = selected.step_beats / 2.0

    for note_index, note in enumerate(track.notes):
        target = _snap(note.start_beat, selected.step_beats)
        delta = target - note.start_beat
        relative_error = abs(delta) / tolerance if tolerance > 0 else 0.0
        confidence = max(0.0, min(1.0, 1.0 - relative_error))

        suggestions.append(
            RhythmSuggestion(
                track_index=track.index,
                note_index=note_index,
                pitch=note.pitch,
                source_start_beat=note.start_beat,
                target_start_beat=target,
                delta_beats=delta,
                confidence=confidence,
            )
        )

    return RhythmAnalysis(
        track_index=track.index,
        track_name=track.name,
        selected_grid=selected,
        grid_scores=scores,
        suggestions=suggestions,
    )
