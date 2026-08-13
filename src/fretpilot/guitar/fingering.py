"""Phrase-level guitar fingering optimization.

The V0 engine uses dynamic programming for melodic continuity and a local chord
shape solver for simultaneous notes. This keeps lead/riff paths coherent while
ensuring that a written chord never assigns two different frets to one string.
"""

from __future__ import annotations

from collections import defaultdict
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
    # stage. Chord groups are corrected by a separate distinct-string solver.
    cost = fret_distance * 0.32 + string_distance * 1.45

    if fret_distance > 5:
        cost += (fret_distance - 5) * 0.45

    if previous.string == current.string:
        cost -= 0.25

    return max(0.0, cost)


def _optimize_segment(
    items: list[_SegmentItem],
) -> tuple[dict[int, tuple[FretPosition, float]], float]:
    if not items:
        return {}, 0.0

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


def _shape_cost(
    chosen: list[tuple[_SegmentItem, FretPosition]],
    melodic_assignments: dict[int, tuple[FretPosition, float]],
) -> float:
    cost = 0.0
    frets: list[int] = []
    strings: list[int] = []

    for item, position in chosen:
        frets.append(position.fret)
        strings.append(position.string)
        cost += _position_cost(position)
        original = melodic_assignments.get(item.note_index)
        if original is not None:
            original_position = original[0]
            cost += abs(position.string - original_position.string) * 0.55
            cost += abs(position.fret - original_position.fret) * 0.12

    if frets:
        fretted = [fret for fret in frets if fret > 0]
        if fretted:
            span = max(fretted) - min(fretted)
            cost += span * 0.18
            if span > 5:
                cost += (span - 5) * 1.2

    if strings:
        cost += (max(strings) - min(strings)) * 0.04

    return cost


def _solve_chord_shape(
    items: list[_SegmentItem],
    melodic_assignments: dict[int, tuple[FretPosition, float]],
) -> dict[int, tuple[FretPosition, float]] | None:
    """Choose one distinct string per simultaneous note.

    The search space is bounded by six guitar strings and typical chord sizes,
    so a deterministic backtracking search is sufficient for V0.1.
    """

    if len(items) > 6:
        return None

    # Notes with fewer possible strings are placed first to prune impossible
    # combinations early. The final mapping still uses source note indices.
    ordered = sorted(items, key=lambda item: (len(item.positions), item.note.pitch))
    best_cost = float("inf")
    best: list[tuple[_SegmentItem, FretPosition]] | None = None

    def search(
        item_index: int,
        used_strings: set[int],
        chosen: list[tuple[_SegmentItem, FretPosition]],
    ) -> None:
        nonlocal best_cost, best
        if item_index == len(ordered):
            cost = _shape_cost(chosen, melodic_assignments)
            if cost < best_cost:
                best_cost = cost
                best = list(chosen)
            return

        item = ordered[item_index]
        original = melodic_assignments.get(item.note_index)
        positions = sorted(
            item.positions,
            key=lambda position: (
                0
                if original is not None and position == original[0]
                else 1,
                position.fret,
                position.string,
            ),
        )
        for position in positions:
            if position.string in used_strings:
                continue
            used_strings.add(position.string)
            chosen.append((item, position))
            search(item_index + 1, used_strings, chosen)
            chosen.pop()
            used_strings.remove(position.string)

    search(0, set(), [])
    if best is None:
        return None

    return {
        item.note_index: (position, _position_cost(position))
        for item, position in best
    }


def _repair_simultaneous_chords(
    track: NormalizedTrack,
    assignments: dict[int, tuple[FretPosition, float]],
    *,
    tuning: GuitarTuning,
    max_fret: int,
    diagnostics: list[FingeringDiagnostic],
) -> None:
    onset_groups: dict[int, list[int]] = defaultdict(list)
    for note_index, note in enumerate(track.notes):
        onset_groups[note.start_tick].append(note_index)

    for note_indices in onset_groups.values():
        if len(note_indices) < 2:
            continue

        items: list[_SegmentItem] = []
        missing = False
        for note_index in note_indices:
            note = track.notes[note_index]
            positions = candidate_positions(
                note.pitch,
                tuning=tuning,
                max_fret=max_fret,
            )
            if not positions:
                missing = True
                break
            items.append(
                _SegmentItem(
                    note_index=note_index,
                    note=note,
                    positions=positions,
                )
            )

        if missing:
            continue

        shape = _solve_chord_shape(items, assignments)
        if shape is None:
            first_index = note_indices[0]
            diagnostics.append(
                FingeringDiagnostic(
                    code="unplayable_chord_shape",
                    message=(
                        f"Simultaneous onset at tick {track.notes[first_index].start_tick} "
                        "cannot be assigned to distinct strings in the current tuning."
                    ),
                    note_index=first_index,
                    pitch=track.notes[first_index].pitch,
                )
            )
            continue

        assignments.update(shape)


def optimize_fingering(
    track: NormalizedTrack,
    *,
    tuning: GuitarTuning = STANDARD_TUNING,
    max_fret: int = 24,
) -> FingeringResult:
    """Assign playable string/fret positions to melodic and chord material.

    The first pass optimizes phrase continuity. The second pass treats notes with
    the same source onset as a chord and enforces one distinct guitar string per
    note. Unplayable notes remain visible with ``string=None`` and ``fret=None``.
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
    _repair_simultaneous_chords(
        track,
        assignments,
        tuning=tuning,
        max_fret=max_fret,
        diagnostics=diagnostics,
    )

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
