"""Deterministic guitar articulation planning.

This layer emits generic musical techniques. It does not know about Ample
Guitar keyswitches; plugin-specific rendering belongs in an exporter/adapter.

Optional articulation preferences may rank/confidence-weight techniques that
are already physically or contextually eligible. They never bypass fretboard
or timing evidence.
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
    if preference == 1.0:
        return base
    factor = min(1.25, max(0.50, preference))
    return round(min(0.99, max(0.01, base * factor)), 6)


def _neighbor_at_different_onset(track: NormalizedTrack, index: int, step: int):
    current_start = track.notes[index].start_beat
    cursor = index + step
    while 0 <= cursor < len(track.notes):
        note = track.notes[cursor]
        if abs(note.start_beat - current_start) > 1e-9:
            return note
        cursor += step
    return None


def _staccato_eligible(track: NormalizedTrack, index: int) -> bool:
    current = track.notes[index]
    next_note = _neighbor_at_different_onset(track, index, 1)
    if next_note is None:
        return False
    inter_onset = next_note.start_beat - current.start_beat
    if inter_onset <= 0:
        return False
    return current.duration_beats <= 0.5 and current.duration_beats / inter_onset <= 0.55


def _palm_mute_eligible(track: NormalizedTrack, index: int) -> bool:
    current = track.notes[index]
    if current.pitch > 57 or current.duration_beats > 0.5:
        return False
    previous = _neighbor_at_different_onset(track, index, -1)
    next_note = _neighbor_at_different_onset(track, index, 1)
    neighbors = [item for item in (previous, next_note) if item is not None]
    if not neighbors:
        return False
    return any(
        abs(item.pitch - current.pitch) <= 2
        and 0 < abs(item.start_beat - current.start_beat) <= 0.75
        for item in neighbors
    )


def plan_articulations(
    track: NormalizedTrack,
    fingering: FingeringResult,
    *,
    preferences: ArticulationPreferenceView | None = None,
) -> ArticulationPlan:
    """Create conservative generic guitar-technique decisions for a phrase."""

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
                            confidence=_weighted_confidence(0.82, active_preferences.hammer_pull),
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
                            confidence=_weighted_confidence(0.76, active_preferences.slide),
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
                    confidence=_weighted_confidence(base_confidence, active_preferences.vibrato),
                    reason=(
                        "Long playable note at a phrase boundary."
                        if phrase_end
                        else "Sustained playable note is long enough for expressive vibrato."
                    ),
                )
            )

        if (
            current_fingering.playable
            and active_preferences.staccato > 1.05
            and _staccato_eligible(track, note_index)
        ):
            decisions.append(
                ArticulationDecision(
                    note_index=note_index,
                    technique="staccato",
                    confidence=_weighted_confidence(0.70, active_preferences.staccato),
                    reason="MIDI note-off is distinctly short relative to the next attack.",
                )
            )

        if (
            current_fingering.playable
            and active_preferences.palm_mute > 1.10
            and _palm_mute_eligible(track, note_index)
        ):
            decisions.append(
                ArticulationDecision(
                    note_index=note_index,
                    technique="palm_mute",
                    confidence=_weighted_confidence(0.68, active_preferences.palm_mute),
                    reason=(
                        "Low-register short note occurs in a tight repeated/pedal-tone "
                        "figure and the active playing context favors palm muting."
                    ),
                )
            )

    return ArticulationPlan(
        track_index=track.index,
        track_name=track.name,
        decisions=decisions,
    )
