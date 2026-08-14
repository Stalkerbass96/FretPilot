"""Deterministic hand-position continuity for section-aware guitar analysis.

The baseline intentionally sits *after* the existing fingering optimizer. It
never creates impossible positions: every replacement comes from the canonical
fretboard candidate generator, and simultaneous notes must still occupy distinct
strings.

A weak section boundary may carry the previous section's exit hand center into a
small entry window. Strong boundaries keep the section-local fingering unchanged
and are treated as deliberate reposition opportunities.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from itertools import product
from typing import Protocol

from fretpilot.guitar.instrument import STANDARD_TUNING, GuitarTuning, candidate_positions
from fretpilot.guitar.models import FingeredNote, FingeringResult, FretPosition
from fretpilot.midi.models import NormalizedTrack


class HandPositionPreferenceView(Protocol):
    hand_position_stability: float
    open_string_usage: float


@dataclass(slots=True)
class HandPositionState:
    section_id: str
    start_measure: int
    end_measure: int
    entry_fret_center: float | None
    exit_fret_center: float | None
    min_fret: int | None
    max_fret: int | None
    previous_exit_fret_center: float | None
    boundary_strength: float
    carried_from_previous: bool
    shift_frets: float | None
    transition_cost: float
    transition_reason: str


def _fret_center(notes: list[FingeredNote]) -> float | None:
    playable = [item.fret for item in notes if item.playable and item.fret is not None]
    if not playable:
        return None
    fretted = [fret for fret in playable if fret > 0]
    values = fretted or playable
    return sum(values) / len(values)


def summarize_hand_position(
    fingering: FingeringResult,
    *,
    section_id: str,
    start_measure: int,
    end_measure: int,
    previous_exit_fret_center: float | None,
    boundary_strength: float,
    carried_from_previous: bool,
    hand_position_stability: float,
    entry_note_count: int = 4,
) -> HandPositionState:
    """Summarize the fretting-hand region used by one solved section."""

    playable = [item for item in fingering.notes if item.playable]
    frets = [item.fret for item in playable if item.fret is not None]
    fretted = [fret for fret in frets if fret > 0]
    range_values = fretted or frets

    entry = _fret_center(playable[:entry_note_count])
    exit_center = _fret_center(playable[-entry_note_count:])
    shift = (
        abs(entry - previous_exit_fret_center)
        if entry is not None and previous_exit_fret_center is not None
        else None
    )
    transition_cost = (
        shift * 0.12 * max(0.25, hand_position_stability)
        if shift is not None
        else 0.0
    )

    if previous_exit_fret_center is None:
        reason = "start_of_stream"
    elif carried_from_previous:
        reason = "carry_across_weak_section_boundary"
    else:
        reason = "reset_at_strong_section_boundary"

    return HandPositionState(
        section_id=section_id,
        start_measure=start_measure,
        end_measure=end_measure,
        entry_fret_center=entry,
        exit_fret_center=exit_center,
        min_fret=min(range_values) if range_values else None,
        max_fret=max(range_values) if range_values else None,
        previous_exit_fret_center=previous_exit_fret_center,
        boundary_strength=boundary_strength,
        carried_from_previous=carried_from_previous,
        shift_frets=shift,
        transition_cost=transition_cost,
        transition_reason=reason,
    )


def _candidate_cost(
    position: FretPosition,
    original: FingeredNote,
    *,
    preferred_fret_center: float,
    preferences: HandPositionPreferenceView,
    previous_position: FretPosition | None,
) -> float:
    stability = max(0.25, preferences.hand_position_stability)
    cost = 0.0

    # Open strings do not force the left hand to fret zero. They therefore avoid
    # the center-distance cost but still respect context-specific open-string use.
    if position.fret > 0:
        cost += abs(position.fret - preferred_fret_center) * 0.18 * stability
    elif preferences.open_string_usage < 1.0:
        cost += (1.0 - preferences.open_string_usage) * 0.60

    if original.playable and original.fret is not None and original.string is not None:
        cost += abs(position.fret - original.fret) * 0.04
        cost += abs(position.string - original.string) * 0.08

    if previous_position is not None:
        cost += abs(position.fret - previous_position.fret) * 0.12 * stability
        cost += abs(position.string - previous_position.string) * 0.10

    return cost


def _solve_onset_group(
    track: NormalizedTrack,
    fingering: FingeringResult,
    note_indices: list[int],
    *,
    preferred_fret_center: float,
    preferences: HandPositionPreferenceView,
    previous_position: FretPosition | None,
    tuning: GuitarTuning,
    max_fret: int,
) -> dict[int, FretPosition] | None:
    candidates: list[list[FretPosition]] = []
    for note_index in note_indices:
        positions = candidate_positions(
            track.notes[note_index].pitch,
            tuning=tuning,
            max_fret=max_fret,
        )
        if not positions:
            return None
        candidates.append(positions)

    best_cost = float("inf")
    best: tuple[FretPosition, ...] | None = None

    for combination in product(*candidates):
        if len({position.string for position in combination}) != len(combination):
            continue

        cost = 0.0
        fretted: list[int] = []
        for note_index, position in zip(note_indices, combination, strict=True):
            cost += _candidate_cost(
                position,
                fingering.notes[note_index],
                preferred_fret_center=preferred_fret_center,
                preferences=preferences,
                previous_position=previous_position,
            )
            if position.fret > 0:
                fretted.append(position.fret)

        if fretted:
            span = max(fretted) - min(fretted)
            cost += span * 0.08 * max(0.25, preferences.hand_position_stability)

        if cost < best_cost:
            best_cost = cost
            best = combination

    if best is None:
        return None

    return {
        note_index: position
        for note_index, position in zip(note_indices, best, strict=True)
    }


def carry_hand_position_into_section(
    track: NormalizedTrack,
    fingering: FingeringResult,
    *,
    preferred_fret_center: float,
    preferences: HandPositionPreferenceView,
    tuning: GuitarTuning = STANDARD_TUNING,
    max_fret: int = 24,
    lookahead_onsets: int = 3,
) -> FingeringResult:
    """Soft-repair the first few onsets toward a previous section hand center.

    The repair window is deliberately short. Its job is to prevent an arbitrary
    section split from causing an immediate unnecessary position jump; normal
    within-section fingering remains owned by ``optimize_fingering``.
    """

    if lookahead_onsets <= 0 or not track.notes:
        return fingering

    onset_groups: dict[int, list[int]] = defaultdict(list)
    for note_index, note in enumerate(track.notes):
        onset_groups[note.start_tick].append(note_index)

    selected_onsets = sorted(onset_groups)[:lookahead_onsets]
    replacements: dict[int, FretPosition] = {}
    previous_position: FretPosition | None = None

    for start_tick in selected_onsets:
        note_indices = onset_groups[start_tick]
        solved = _solve_onset_group(
            track,
            fingering,
            note_indices,
            preferred_fret_center=preferred_fret_center,
            preferences=preferences,
            previous_position=previous_position,
            tuning=tuning,
            max_fret=max_fret,
        )
        if solved is None:
            continue
        replacements.update(solved)

        anchor_index = min(
            note_indices,
            key=lambda index: (track.notes[index].pitch, index),
        )
        previous_position = solved.get(anchor_index, previous_position)

    if not replacements:
        return fingering

    repaired_notes: list[FingeredNote] = []
    for item in fingering.notes:
        position = replacements.get(item.note_index)
        if position is None:
            repaired_notes.append(item)
            continue
        repaired_notes.append(
            replace(
                item,
                string=position.string,
                fret=position.fret,
            )
        )

    return FingeringResult(
        track_index=fingering.track_index,
        track_name=fingering.track_name,
        tuning=fingering.tuning,
        max_fret=fingering.max_fret,
        notes=repaired_notes,
        diagnostics=list(fingering.diagnostics),
        total_cost=fingering.total_cost,
    )
