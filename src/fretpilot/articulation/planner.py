"""Deterministic guitar articulation planning.

This layer emits generic musical techniques. It does not know about Ample
Guitar keyswitches; plugin-specific rendering belongs in an exporter/adapter.
"""

from __future__ import annotations

from fretpilot.articulation.models import ArticulationDecision, ArticulationPlan
from fretpilot.guitar.models import FingeringResult
from fretpilot.midi.models import NormalizedTrack


def _connected(previous_end: float, current_start: float, tolerance: float = 0.10) -> bool:
    return current_start - previous_end <= tolerance


def plan_articulations(
    track: NormalizedTrack,
    fingering: FingeringResult,
) -> ArticulationPlan:
    """Create conservative generic guitar-technique decisions for a phrase.

    V0 recognizes hammer-ons, pull-offs, slides, and phrase-ending/long-note
    vibrato. Palm muting and style-heavy techniques are intentionally deferred
    until FretPilot has phrase/style context.
    """

    if len(track.notes) != len(fingering.notes):
        raise ValueError("Track and fingering result contain different note counts.")

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
                            confidence=0.82,
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
                            confidence=0.76,
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
            confidence = 0.85 if phrase_end else 0.72
            decisions.append(
                ArticulationDecision(
                    note_index=note_index,
                    technique="vibrato",
                    confidence=confidence,
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
