"""Re-rank simultaneous guitar chord positions using score-strategy priors."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from itertools import product
from typing import Any, Mapping, Protocol

from fretpilot.guitar.instrument import STANDARD_TUNING, candidate_positions
from fretpilot.guitar.models import FingeredNote, FingeringResult, FretPosition
from fretpilot.midi.models import NormalizedTrack


class VoicingPreferences(Protocol):
    compact_chord_voicing: float
    open_string_usage: float


def _center(positions: tuple[FretPosition, ...]) -> float:
    frets = [item.fret for item in positions if item.fret > 0]
    values = frets or [item.fret for item in positions]
    return sum(values) / len(values)


def _shape(positions: tuple[FretPosition, ...]) -> tuple[tuple[int, int], ...]:
    ordered = sorted(positions, key=lambda item: item.pitch)
    anchor = ordered[0]
    return tuple((item.string - anchor.string, item.fret - anchor.fret) for item in ordered)


def _number(strategy: Mapping[str, Any], key: str) -> float:
    value = strategy.get(key, 1.0)
    return float(value) if isinstance(value, (int, float)) else 1.0


def _power_shape(track: NormalizedTrack, indices: tuple[int, ...]) -> bool:
    pitches = sorted(track.notes[index].pitch for index in indices)
    if len(pitches) not in {2, 3}:
        return False
    intervals = {(pitch - pitches[0]) % 12 for pitch in pitches}
    return intervals.issubset({0, 7}) and 7 in intervals


def _cost(
    track: NormalizedTrack,
    indices: tuple[int, ...],
    positions: tuple[FretPosition, ...],
    current: dict[int, FingeredNote],
    previous: tuple[FretPosition, ...] | None,
    preferences: VoicingPreferences,
    strategy: Mapping[str, Any],
) -> float:
    cost = 0.0
    for index, position in zip(indices, positions, strict=True):
        old = current[index]
        if old.fret is not None and old.string is not None:
            cost += abs(position.fret - old.fret) * .035
            cost += abs(position.string - old.string) * .08
        if position.fret == 0 and preferences.open_string_usage < 1.0:
            cost += (1.0 - preferences.open_string_usage) * .35

    frets = [item.fret for item in positions if item.fret > 0]
    if frets:
        cost += (max(frets) - min(frets)) * .10 * max(.25, preferences.compact_chord_voicing)

    if previous is not None and strategy.get("previous_voicing_context") is True:
        cost += abs(_center(positions) - _center(previous)) * .22 * _number(strategy, "voice_leading_weight")
        if len(previous) == len(positions) and _shape(previous) == _shape(positions):
            cost -= .65 * max(0.0, _number(strategy, "moveable_voicing_family_bias") - 1.0)

    if _power_shape(track, indices) and _number(strategy, "power_chord_bias") > 1.0:
        strings = sorted(item.string for item in positions)
        if all(right - left == 1 for left, right in zip(strings, strings[1:])):
            cost -= .45 * (_number(strategy, "power_chord_bias") - 1.0)
    return cost


def apply_chord_voicing_strategy(
    track: NormalizedTrack,
    fingering: FingeringResult,
    *,
    preferences: VoicingPreferences,
    score_strategy: Mapping[str, Any],
    max_fret: int = 24,
) -> FingeringResult:
    if not score_strategy:
        return fingering

    groups: dict[int, list[int]] = defaultdict(list)
    for index, note in enumerate(track.notes):
        groups[note.start_tick].append(index)
    current = {item.note_index: item for item in fingering.notes}
    replacements: dict[int, FretPosition] = {}
    previous: tuple[FretPosition, ...] | None = None

    for tick in sorted(groups):
        indices = tuple(sorted(groups[tick], key=lambda index: track.notes[index].pitch))
        if len(indices) < 2 or len(indices) > 6:
            continue
        candidate_sets = [candidate_positions(track.notes[index].pitch, max_fret=max_fret) for index in indices]
        choices = [
            positions for positions in product(*candidate_sets)
            if len({item.string for item in positions}) == len(positions)
        ]
        if not choices:
            previous = None
            continue
        selected = min(
            choices,
            key=lambda positions: _cost(
                track, indices, positions, current, previous, preferences, score_strategy
            ),
        )
        replacements.update(zip(indices, selected, strict=True))
        previous = selected

    if not replacements:
        return fingering
    notes = [
        replace(item, string=replacements[item.note_index].string, fret=replacements[item.note_index].fret)
        if item.note_index in replacements else item
        for item in fingering.notes
    ]
    return FingeringResult(
        track_index=fingering.track_index,
        track_name=fingering.track_name,
        tuning=fingering.tuning,
        max_fret=fingering.max_fret,
        notes=notes,
        diagnostics=list(fingering.diagnostics),
        total_cost=fingering.total_cost,
    )
