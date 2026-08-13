"""Phrase-level guitar fingering optimization.

The engine combines three deterministic passes:

1. melodic dynamic programming for local continuity;
2. movable arpeggio/riff-shape repair for repeated stacked-interval figures;
3. simultaneous-chord repair that enforces one distinct string per note.

The arpeggio pass intentionally models a common guitar reality that pure
note-by-note optimization misses: a guitarist often preserves a movable shape
across adjacent strings instead of chasing the globally lowest fret.

All physical candidates remain deterministic. Optional fingering preferences
only rank valid alternatives, so style/role knowledge can influence choices
without bypassing fretboard constraints. The guitar engine consumes a small
structural preference interface instead of importing the knowledge package,
which keeps the dependency direction one-way and avoids classifier cycles.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import product
from statistics import median
from typing import Protocol

from fretpilot.guitar.instrument import STANDARD_TUNING, GuitarTuning, candidate_positions
from fretpilot.guitar.models import (
    FingeredNote,
    FingeringDiagnostic,
    FingeringResult,
    FretPosition,
    HandPositionState,
)
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


class FingeringPreferenceView(Protocol):
    adjacent_string_arpeggio: float
    same_string_legato: float
    hand_position_stability: float
    shape_reuse: float
    open_string_usage: float
    low_register_bias: float
    compact_chord_voicing: float
    wide_interval_position_shift: float


@dataclass(frozen=True, slots=True)
class _NeutralFingeringPreferences:
    adjacent_string_arpeggio: float = 1.0
    same_string_legato: float = 1.0
    hand_position_stability: float = 1.0
    shape_reuse: float = 1.0
    open_string_usage: float = 1.0
    low_register_bias: float = 1.0
    compact_chord_voicing: float = 1.0
    wide_interval_position_shift: float = 1.0


_NEUTRAL_PREFERENCES = _NeutralFingeringPreferences()


@dataclass(slots=True)
class _SegmentItem:
    note_index: int
    note: NormalizedNote
    positions: list[FretPosition]


@dataclass(frozen=True, slots=True)
class _ArpeggioShape:
    note_indices: tuple[int, ...]
    strings: tuple[int, ...]
    frets: tuple[int, ...]
    pitches: tuple[int, ...]

    @property
    def fret_center(self) -> float:
        return sum(self.frets) / len(self.frets)


def _position_cost(
    position: FretPosition,
    preferences: FingeringPreferenceView,
) -> float:
    # Lower positions are a weak preference only. Stronger musical structure
    # such as a movable riff shape is allowed to override this.
    cost = position.fret * 0.015

    # Neutral value 1.0 is exactly backward-compatible. Values below 1.0 make
    # open strings less attractive (lead/jazz contexts); values above 1.0 keep
    # the existing open-string advantage and can be used by riff/strum styles.
    if position.fret == 0 and preferences.open_string_usage < 1.0:
        cost += (1.0 - preferences.open_string_usage) * 0.60

    return cost


def _transition_cost(
    previous: FretPosition,
    current: FretPosition,
    preferences: FingeringPreferenceView,
) -> float:
    fret_distance = abs(current.fret - previous.fret)
    string_distance = abs(current.string - previous.string)
    pitch_interval = abs(current.pitch - previous.pitch)
    position_stability = max(0.25, preferences.hand_position_stability)

    # Stepwise melodic material, including a single fourth, can legitimately
    # stay on one string for hammer-ons, pull-offs and slides.
    if pitch_interval <= 5:
        cost = fret_distance * 0.32 * position_stability + string_distance * 1.45
        if fret_distance > 5:
            cost += (fret_distance - 5) * 0.45 * position_stability
        if previous.string == current.string:
            cost -= 0.25 * max(0.25, preferences.same_string_legato)
        return max(0.0, cost)

    # Sixth/fifth-like motion is frequently an arpeggio across neighbouring
    # strings. The dedicated arpeggio pass below handles repeated 5-9 semitone
    # cells, while this pairwise cost avoids obvious one-string ladders.
    if 6 <= pitch_interval <= 9:
        adjacent_bias = max(0.25, preferences.adjacent_string_arpeggio)
        cost = fret_distance * 0.42 * position_stability + string_distance * 0.75
        if previous.string == current.string:
            cost += 2.0 * adjacent_bias
        elif string_distance == 1:
            cost -= 0.55 * adjacent_bias
        elif string_distance > 1:
            cost += (string_distance - 1) * 0.85 * adjacent_bias
        if fret_distance > 5:
            cost += (fret_distance - 5) * 0.35 * position_stability
        return max(0.0, cost)

    # Large melodic leaps should not force the whole phrase onto one string.
    # ``wide_interval_position_shift`` above 1 means a context is more willing
    # to move the hand for a large leap, partially counteracting stability cost.
    shift_willingness = max(0.25, preferences.wide_interval_position_shift)
    cost = (
        fret_distance * 0.38 * position_stability / shift_willingness
        + string_distance * 0.9
    )
    if previous.string == current.string:
        cost += 1.4
    if fret_distance > 5:
        cost += (
            (fret_distance - 5)
            * 0.45
            * position_stability
            / shift_willingness
        )
    return max(0.0, cost)


def _entry_position_cost(
    position: FretPosition,
    state: HandPositionState | None,
    continuity_strength: float,
    preferences: FingeringPreferenceView,
) -> float:
    if state is None or continuity_strength <= 0.0:
        return 0.0
    # An open string can sound without moving the fretting hand. It therefore
    # inherits the current hand center for transition-cost purposes.
    effective_fret = state.center_fret if position.fret == 0 else float(position.fret)
    distance = abs(effective_fret - state.center_fret)
    stability = max(0.25, preferences.hand_position_stability)
    return distance * 0.15 * continuity_strength * stability


def _optimize_segment(
    items: list[_SegmentItem],
    preferences: FingeringPreferenceView,
    *,
    initial_hand_position: HandPositionState | None = None,
    continuity_strength: float = 0.0,
) -> tuple[dict[int, tuple[FretPosition, float]], float]:
    if not items:
        return {}, 0.0

    layers: list[dict[int, tuple[float, int | None]]] = []

    first_layer: dict[int, tuple[float, int | None]] = {}
    for position_index, position in enumerate(items[0].positions):
        first_layer[position_index] = (
            _position_cost(position, preferences)
            + _entry_position_cost(
                position,
                initial_hand_position,
                continuity_strength,
                preferences,
            ),
            None,
        )
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
                    + _transition_cost(previous_position, current_position, preferences)
                    + _position_cost(current_position, preferences)
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
        local_cost = _position_cost(position, preferences)
        if previous_position is None:
            local_cost += _entry_position_cost(
                position,
                initial_hand_position,
                continuity_strength,
                preferences,
            )
        else:
            local_cost += _transition_cost(previous_position, position, preferences)
        result[item.note_index] = (position, local_cost)
        previous_position = position

    return result, total_cost


def _estimate_hand_position(
    notes: list[FingeredNote],
    *,
    from_end: bool,
    window_size: int = 6,
) -> HandPositionState | None:
    playable = [item for item in notes if item.playable]
    if not playable:
        return None
    window = playable[-window_size:] if from_end else playable[:window_size]
    frets = [item.fret for item in window if item.fret is not None and item.fret > 0]
    if not frets:
        frets = [0]
    strings = [item.string for item in window if item.string is not None]
    minimum = min(frets)
    maximum = max(frets)
    return HandPositionState(
        center_fret=round(float(median(frets)), 3),
        minimum_fret=minimum,
        maximum_fret=maximum,
        fret_span=maximum - minimum,
        anchor_string=(round(float(median(strings))) if strings else None),
        note_count=len(window),
    )


def _lowest_note_per_onset(track: NormalizedTrack) -> list[int]:
    """Return the lowest-pitch note index for each unique source onset."""
    onset_groups: dict[int, list[int]] = defaultdict(list)
    for note_index, note in enumerate(track.notes):
        onset_groups[note.start_tick].append(note_index)

    anchors: list[int] = []
    for start_tick in sorted(onset_groups):
        indices = onset_groups[start_tick]
        anchors.append(min(indices, key=lambda index: (track.notes[index].pitch, index)))
    return anchors


def _detect_arpeggio_runs(track: NormalizedTrack) -> list[list[int]]:
    """Detect short ascending stacked-interval figures.

    V0.2 intentionally targets a narrow but common riff/arpeggio pattern:
    at least three consecutive onset anchors, rising by 5-9 semitones per note
    with no long timing gap. A descending/reset interval ends the run.
    """
    anchors = _lowest_note_per_onset(track)
    if len(anchors) < 3:
        return []

    runs: list[list[int]] = []
    current: list[int] = [anchors[0]]

    for previous_index, current_index in zip(anchors, anchors[1:], strict=False):
        previous = track.notes[previous_index]
        current_note = track.notes[current_index]
        interval = current_note.pitch - previous.pitch
        gap = current_note.start_beat - previous.start_beat

        if 5 <= interval <= 9 and 0 < gap <= 1.25:
            current.append(current_index)
            continue

        if len(current) >= 3:
            runs.append(current)
        current = [current_index]

    if len(current) >= 3:
        runs.append(current)

    return runs


def _enumerate_adjacent_string_shapes(
    track: NormalizedTrack,
    note_indices: list[int],
    *,
    tuning: GuitarTuning,
    max_fret: int,
) -> list[_ArpeggioShape]:
    candidates_per_note: list[list[FretPosition]] = []
    for note_index in note_indices:
        positions = candidate_positions(
            track.notes[note_index].pitch,
            tuning=tuning,
            max_fret=max_fret,
        )
        if not positions:
            return []
        candidates_per_note.append(positions)

    shapes: list[_ArpeggioShape] = []
    for combination in product(*candidates_per_note):
        if not all(
            current.string == previous.string - 1
            for previous, current in zip(combination, combination[1:], strict=False)
        ):
            continue

        shapes.append(
            _ArpeggioShape(
                note_indices=tuple(note_indices),
                strings=tuple(position.string for position in combination),
                frets=tuple(position.fret for position in combination),
                pitches=tuple(position.pitch for position in combination),
            )
        )
    return shapes


def _arpeggio_shape_cost(
    shape: _ArpeggioShape,
    previous_shape: _ArpeggioShape | None,
    preferences: FingeringPreferenceView,
    *,
    initial_hand_position: HandPositionState | None = None,
    continuity_strength: float = 0.0,
) -> float:
    cost = sum(
        _position_cost(
            FretPosition(string=string, fret=fret, pitch=pitch),
            preferences,
        )
        for string, fret, pitch in zip(
            shape.strings,
            shape.frets,
            shape.pitches,
            strict=True,
        )
    )

    # Preserve the old neutral 1.8 open-string penalty for movable arpeggio
    # cells, then modulate it with explicit open-string preference.
    open_penalty_scale = max(0.25, 2.0 - preferences.open_string_usage)
    cost += sum(1.8 * open_penalty_scale for fret in shape.frets if fret == 0)

    fret_span = max(shape.frets) - min(shape.frets)
    compactness = max(0.25, preferences.compact_chord_voicing)
    cost += fret_span * 0.08 * compactness
    if fret_span > 5:
        cost += (fret_span - 5) * 0.8 * compactness

    if previous_shape is None:
        if initial_hand_position is not None and continuity_strength > 0.0:
            cost += (
                abs(shape.fret_center - initial_hand_position.center_fret)
                * 0.15
                * continuity_strength
                * max(0.25, preferences.hand_position_stability)
            )
        return cost
    if len(previous_shape.frets) != len(shape.frets):
        return cost

    shape_reuse = max(0.25, preferences.shape_reuse)
    if shape.strings == previous_shape.strings:
        cost -= 0.9 * shape_reuse

    string_offsets = tuple(
        current - previous
        for previous, current in zip(
            previous_shape.strings,
            shape.strings,
            strict=True,
        )
    )
    if len(set(string_offsets)) == 1:
        cost -= 0.25 * shape_reuse

    fret_offsets = tuple(
        current - previous
        for previous, current in zip(
            previous_shape.frets,
            shape.frets,
            strict=True,
        )
    )
    if len(set(fret_offsets)) == 1:
        cost -= 0.25 * shape_reuse

    cost += (
        abs(shape.fret_center - previous_shape.fret_center)
        * 0.10
        * max(0.25, preferences.hand_position_stability)
    )
    return cost


def _repair_arpeggio_shapes(
    track: NormalizedTrack,
    assignments: dict[int, tuple[FretPosition, float]],
    *,
    tuning: GuitarTuning,
    max_fret: int,
    preferences: FingeringPreferenceView,
    initial_hand_position: HandPositionState | None = None,
    continuity_strength: float = 0.0,
) -> None:
    previous_shape: _ArpeggioShape | None = None

    for note_indices in _detect_arpeggio_runs(track):
        shapes = _enumerate_adjacent_string_shapes(
            track,
            note_indices,
            tuning=tuning,
            max_fret=max_fret,
        )
        if not shapes:
            previous_shape = None
            continue

        selected = min(
            shapes,
            key=lambda shape: _arpeggio_shape_cost(
                shape,
                previous_shape,
                preferences,
                initial_hand_position=initial_hand_position,
                continuity_strength=continuity_strength,
            ),
        )
        selected_cost = _arpeggio_shape_cost(
            selected,
            previous_shape,
            preferences,
            initial_hand_position=initial_hand_position,
            continuity_strength=continuity_strength,
        )

        for note_index, string, fret, pitch in zip(
            selected.note_indices,
            selected.strings,
            selected.frets,
            selected.pitches,
            strict=True,
        ):
            position = FretPosition(string=string, fret=fret, pitch=pitch)
            assignments[note_index] = (position, selected_cost)

        previous_shape = selected


def _shape_cost(
    chosen: list[tuple[_SegmentItem, FretPosition]],
    melodic_assignments: dict[int, tuple[FretPosition, float]],
    preferences: FingeringPreferenceView,
) -> float:
    cost = 0.0
    frets: list[int] = []
    strings: list[int] = []

    for item, position in chosen:
        frets.append(position.fret)
        strings.append(position.string)
        cost += _position_cost(position, preferences)
        original = melodic_assignments.get(item.note_index)
        if original is not None:
            original_position = original[0]
            cost += abs(position.string - original_position.string) * 0.55
            cost += abs(position.fret - original_position.fret) * 0.12

    if frets:
        fretted = [fret for fret in frets if fret > 0]
        if fretted:
            span = max(fretted) - min(fretted)
            compactness = max(0.25, preferences.compact_chord_voicing)
            cost += span * 0.18 * compactness
            if span > 5:
                cost += (span - 5) * 1.2 * compactness

    if strings:
        cost += (max(strings) - min(strings)) * 0.04

    return cost


def _solve_chord_shape(
    items: list[_SegmentItem],
    melodic_assignments: dict[int, tuple[FretPosition, float]],
    preferences: FingeringPreferenceView,
) -> dict[int, tuple[FretPosition, float]] | None:
    """Choose one distinct string per simultaneous note."""
    if len(items) > 6:
        return None

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
            cost = _shape_cost(chosen, melodic_assignments, preferences)
            if cost < best_cost:
                best_cost = cost
                best = list(chosen)
            return

        item = ordered[item_index]
        original = melodic_assignments.get(item.note_index)
        positions = sorted(
            item.positions,
            key=lambda position: (
                0 if original is not None and position == original[0] else 1,
                _position_cost(position, preferences),
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
        item.note_index: (position, _position_cost(position, preferences))
        for item, position in best
    }


def _repair_simultaneous_chords(
    track: NormalizedTrack,
    assignments: dict[int, tuple[FretPosition, float]],
    *,
    tuning: GuitarTuning,
    max_fret: int,
    diagnostics: list[FingeringDiagnostic],
    preferences: FingeringPreferenceView,
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

        shape = _solve_chord_shape(items, assignments, preferences)
        if shape is None:
            first_index = note_indices[0]
            # A source-tick chord or a quantized score chord that cannot use
            # distinct strings is physically unplayable. Do not retain the
            # melodic pass's same-string assignments as if they were valid.
            for note_index in note_indices:
                assignments.pop(note_index, None)
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
    preferences: FingeringPreferenceView | None = None,
    initial_hand_position: HandPositionState | None = None,
    continuity_strength: float = 0.0,
) -> FingeringResult:
    """Assign playable string/fret positions to melodic, riff and chord material.

    Pass 1 optimizes local melodic continuity.
    Pass 2 repairs stacked-interval arpeggio/riff cells into reusable adjacent-
    string shapes.
    Pass 3 enforces one distinct guitar string per simultaneous note.

    ``preferences`` is a soft ranking prior. ``None`` uses neutral values and is
    intentionally backward-compatible with the pre-PlayingContext optimizer.
    """
    active_preferences = preferences or _NEUTRAL_PREFERENCES
    if not 0.0 <= continuity_strength <= 1.0:
        raise ValueError("continuity_strength must be between 0 and 1.")
    diagnostics: list[FingeringDiagnostic] = []
    assignments: dict[int, tuple[FretPosition, float]] = {}
    total_cost = 0.0
    segment: list[_SegmentItem] = []
    initial_state_available = initial_hand_position

    def flush_segment() -> None:
        nonlocal total_cost, initial_state_available
        if not segment:
            return
        optimized, segment_cost = _optimize_segment(
            segment,
            active_preferences,
            initial_hand_position=initial_state_available,
            continuity_strength=(
                continuity_strength if initial_state_available is not None else 0.0
            ),
        )
        assignments.update(optimized)
        total_cost += segment_cost
        initial_state_available = None
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

    _repair_arpeggio_shapes(
        track,
        assignments,
        tuning=tuning,
        max_fret=max_fret,
        preferences=active_preferences,
        initial_hand_position=initial_hand_position,
        continuity_strength=continuity_strength,
    )
    _repair_simultaneous_chords(
        track,
        assignments,
        tuning=tuning,
        max_fret=max_fret,
        diagnostics=diagnostics,
        preferences=active_preferences,
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

    result = FingeringResult(
        track_index=track.index,
        track_name=track.name,
        tuning=tuning.name,
        max_fret=max_fret,
        notes=fingered_notes,
        diagnostics=diagnostics,
        total_cost=total_cost,
    )
    result.entry_hand_position = _estimate_hand_position(
        result.notes,
        from_end=False,
    )
    result.exit_hand_position = _estimate_hand_position(
        result.notes,
        from_end=True,
    )
    return result
