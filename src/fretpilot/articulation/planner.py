"""Deterministic guitar articulation planning.

This layer emits generic musical techniques. It does not know about Ample
Guitar keyswitches; plugin-specific rendering belongs in an exporter/adapter.

Optional articulation preferences may rank/confidence-weight techniques that
are already physically eligible. They never create a technique that failed the
hard deterministic eligibility rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fretpilot.articulation.models import ArticulationDecision, ArticulationPlan
from fretpilot.guitar.models import FingeringResult
from fretpilot.midi.models import NormalizedTrack


class ArticulationPreferenceView(Protocol):
    hammer_pull: float
    slide: float
    bend: float
    vibrato: float
    palm_mute: float
    let_ring: float
    staccato: float


@dataclass(frozen=True, slots=True)
class _NeutralArticulationPreferences:
    hammer_pull: float = 1.0
    slide: float = 1.0
    bend: float = 1.0
    vibrato: float = 1.0
    palm_mute: float = 1.0
    let_ring: float = 1.0
    staccato: float = 1.0


_NEUTRAL_PREFERENCES = _NeutralArticulationPreferences()


def _connected(previous_end: float, current_start: float, tolerance: float = 0.10) -> bool:
    return current_start - previous_end <= tolerance


def _weighted_confidence(base: float, preference: float) -> float:
    """Apply a bounded soft prior while preserving neutral confidence exactly."""
    if preference == 1.0:
        return base
    # Keep knowledge priors influential but conservative. The deterministic
    # eligibility rule remains the primary evidence, and confidence never
    # reaches certainty merely because a style profile strongly prefers it.
    factor = min(1.25, max(0.50, preference))
    return round(min(0.99, max(0.01, base * factor)), 6)


def plan_articulations(
    track: NormalizedTrack,
    fingering: FingeringResult,
    *,
    preferences: ArticulationPreferenceView | None = None,
) -> ArticulationPlan:
    """Create conservative generic guitar-technique decisions for a phrase.

    V0 recognizes hammer-ons, pull-offs, slides, and phrase-ending/long-note
    vibrato. Palm muting and style-heavy techniques remain deferred until their
    own deterministic eligibility/context features exist.

    ``preferences`` only changes confidence for already-valid decisions. A
    neutral/omitted preference object preserves historical output exactly.
    """

    if len(track.notes) != len(fingering.notes):
        raise ValueError("Track and fingering result contain different note counts.")

    active_preferences = preferences or _NEUTRAL_PREFERENCES
    decisions: list[ArticulationDecision] = []

    for note_index, current in enumerate(track.notes):
        current_fingering = fingering.notes[note_index]

        if note_index > 0:
            previous = track.notes[note_index - 1]
            previous_fingering = fingering.notes[note_index - 1]

            both_playable = previous_fingering.playable and current_fingering.playable
            same_string = (
                both_playable
                and previous_fingering.string == current_fingering.string
            )
            semitone_delta = current.pitch - previous.pitch
            interval = abs(semitone_delta)
            connected = _connected(previous.end_beat, current.start_beat)
            inter_onset = current.start_beat - previous.start_beat

            if same_string and connected and inter_onset <= 0.75:
                if 1 <= interval <= 3:
                    technique = "hammer_on" if semitone_delta > 0 else "pull_off"
                    decisions.append(
                        ArticulationDecision(
                            note_index=note_index,
                            source_note_index=note_index - 1,
                            technique=technique,
                            confidence=_weighted_confidence(
                                0.82,
                                active_preferences.hammer_pull,
                            ),
                            reason=(
                                "Connected notes are on the same string with a small "
                                f"{interval}-semitone movement."
                            ),
                        )
                    )
                elif 4 <= interval <= 7:
                    decisions.append(
                        ArticulationDecision(
                            note_index=note_index,
                            source_note_index=note_index - 1,
                            technique="slide",
                            confidence=_weighted_confidence(
                                0.76,
                                active_preferences.slide,
                            ),
                            reason=(
                                "Connected notes remain on the same string and move "
                                f"{interval} semitones."
                            ),
                        )
                    )

        next_note = track.notes[note_index + 1] if note_index + 1 < len(track.notes) else None
        phrase_end = next_note is None or next_note.start_beat - current.end_beat >= 0.5
        long_note = current.duration_beats >= 1.0
        very_long_note = current.duration_beats >= 1.5

        if current_fingering.playable and long_note and (phrase_end or very_long_note):
            base_confidence = 0.85 if phrase_end else 0.72
            decisions.append(
                ArticulationDecision(
                    note_index=note_index,
                    technique="vibrato",
                    confidence=_weighted_confidence(
                        base_confidence,
                        active_preferences.vibrato,
                    ),
                    reason=(
                        "Long playable note at a phrase boundary."
                        if phrase_end
                        else "Sustained playable note is long enough for expressive vibrato."
                    ),
                )
            )

    return ArticulationPlan(
        track_index=track.index,
        track_name=track.name,
        decisions=decisions,
    )
