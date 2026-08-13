"""Phrase-level guitar fingering optimization.

The V0 engine uses dynamic programming instead of choosing the lowest fret for
one note at a time. That lets FretPilot prefer a coherent playable path across
a phrase while keeping the algorithm deterministic and inspectable.
"""

from __future__ import annotations

from dataclasses import dataclass

from fretpilot.guitar.instrument import STANDARD_TUNING, GuitarTuning, candidate_positions
from fretpilot.guitar.models import (
    FingeredNote,
    FingeringDiagnostic,
    FingeringResult,
    FretPosition,
)
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


@dataclass(slots=True)
class _SegmentItem:
    note_index: int
    note: NormalizedNote
    positions: list[FretPosition]


def _position_cost(position: FretPosition) -> float:
    # Prefer lower positions very slightly, without overriding phrase continuity.
    return position.fret * 0.015


def _transition_cost(previous: FretPosition, current: FretPosition) -> float:
    fret_distance = abs(current.fret - previous.fret)
    string_distance = abs(current.string - previous.string)

    # V0 is tuned for lead/riff material. String changes therefore cost more
    # than a modest same-string hand movement because staying on a string keeps
    # hammer-on, pull-off and slide possibilities available to the articulation
    # stage. Chord/rhythm-guitar modes will use different weights later.
    cost = fret_distance * 0.32 + string_distance * 1.45

    # Large hand relocations are possible but should need a musical reason.
    if fret_distance > 5:
        cost += (fret_distance - 5) * 0.45

    # Staying on one string is useful for legato/slide possibilities.
    if previous.string == current.string:
        cost -= 0.25

    return max(0.0, cost)


def _optimize_segment(
    items: list[_SegmentItem],
) -> tuple[dict[int, tuple[FretPosition, float]], float]:
    if not items:
        return {}, 0.0

    # Each layer maps candidate index -> (best cumulative cost, previous index).
    layers: list[dict[int, tuple[float, int | None]]] = []

    first_layer: dict[int, tuple[float, int | None]] = {}
    for position_index, position in enumerate(items[0].positions):
        first_layer[position_index] = (_position_cost(position), None)
    layers.append(first_layer)

    for item_index in range(1, len(items)):
        previous_item = items[item_index - 1]
        current_item = items[item_index]
        previous_layer = layers[-1]
        current_layer: dict[int, tuple[float, int | None]] = {}

        for current_index, current_position in enumerate(current_item.positions):
            best_cost = float("inf")
            best_previous_index: int | None = None

            for previous_index, previous_position in enumerate(previous_item.positions):
                previous_cost = previous_layer[previous_index][0]
                candidate_cost = (
                    previous_cost
                    + _transition_cost(previous_position, current_position)
                    + _position_cost(current_position)
                )
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_previous_index = previous_index

            current_layer[current_index] = (best_cost, best_previous_index)

        layers.append(current_layer)

    last_index = min(layers[-1], key=lambda index: layers[-1][index][0])
    total_cost = layers[-1][last_index][0]

    selected_indices = [last_index]
    for layer_index in range(len(layers) - 1, 0, -1):
        previous_index = layers[layer_index][selected_indices[-1]][1]
        assert previous_index is not None
        selected_indices.append(previous_index)
    selected_indices.reverse()

    result: dict[int, tuple[FretPosition, float]] = {}
    previous_position: FretPosition | None = None

    for item, position_index in zip(items, selected_indices, strict=True):
        position = item.positions[position_index]
        local_cost = _position_cost(position)
        if previous_position is not None:
            local_cost += _transition_cost(previous_position, position)
        result[item.note_index] = (position, local_cost)
        previous_position = position

    return result, total_cost


def optimize_fingering(
    track: NormalizedTrack,
    *,
    tuning: GuitarTuning = STANDARD_TUNING,
    max_fret: int = 24,
) -> FingeringResult:
    """Assign a playable string/fret position to each note in a track.

    V0 targets monophonic lead/riff material. Unplayable pitches are retained in
    the result with ``string=None`` and ``fret=None`` and split the optimization
    into independent playable phrase segments.
    """

    diagnostics: list[FingeringDiagnostic] = []
    assignments: dict[int, tuple[FretPosition, float]] = {}
    total_cost = 0.0
    segment: list[_SegmentItem] = []

    def flush_segment() -> None:
        nonlocal total_cost
        if not segment:
            return
        optimized, segment_cost = _optimize_segment(segment)
        assignments.update(optimized)
        total_cost += segment_cost
        segment.clear()

    for note_index, note in enumerate(track.notes):
        positions = candidate_positions(note.pitch, tuning=tuning, max_fret=max_fret)
        if not positions:
            flush_segment()
            diagnostics.append(
                FingeringDiagnostic(
                    code="unplayable_pitch",
                    message=(
                        f"MIDI pitch {note.pitch} cannot be played in {tuning.name} "
                        f"with max fret {max_fret}."
                    ),
                    note_index=note_index,
                    pitch=note.pitch,
                )
            )
            continue

        segment.append(
            _SegmentItem(
                note_index=note_index,
                note=note,
                positions=positions,
            )
        )

    flush_segment()

    fingered_notes: list[FingeredNote] = []
    for note_index, note in enumerate(track.notes):
        assignment = assignments.get(note_index)
        if assignment is None:
            fingered_notes.append(
                FingeredNote(
                    note_index=note_index,
                    pitch=note.pitch,
                    start_beat=note.start_beat,
                    duration_beats=note.duration_beats,
                    string=None,
                    fret=None,
                    local_cost=None,
                )
            )
            continue

        position, local_cost = assignment
        fingered_notes.append(
            FingeredNote(
                note_index=note_index,
                pitch=note.pitch,
                start_beat=note.start_beat,
                duration_beats=note.duration_beats,
                string=position.string,
                fret=position.fret,
                local_cost=local_cost,
            )
        )

    return FingeringResult(
        track_index=track.index,
        track_name=track.name,
        tuning=tuning.name,
        max_fret=max_fret,
        notes=fingered_notes,
        diagnostics=diagnostics,
        total_cost=total_cost,
    )
