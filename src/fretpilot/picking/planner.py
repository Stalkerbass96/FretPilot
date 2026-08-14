"""Deterministic right-hand pick/strum intent planning."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from fretpilot.guitar.models import FingeringResult
from fretpilot.midi.models import NormalizedTrack
from fretpilot.picking.models import PickingDecision, PickingPlan

if TYPE_CHECKING:
    from fretpilot.knowledge.playing_contexts import PlayingContext


def _score(context: PlayingContext, group: str, key: str) -> float:
    return float(getattr(context, group).get(key, 0.0))


def _onset_groups(track: NormalizedTrack) -> list[list[int]]:
    groups: dict[int, list[int]] = defaultdict(list)
    for index, note in enumerate(track.notes):
        groups[note.start_tick].append(index)
    return [groups[tick] for tick in sorted(groups)]


def _tight_low_repeat(track: NormalizedTrack, groups: list[list[int]], pos: int) -> bool:
    indices = groups[pos]
    if len(indices) != 1:
        return False
    note = track.notes[indices[0]]
    if note.pitch > 57 or note.duration_beats > 0.5:
        return False
    for neighbor_pos in (pos - 1, pos + 1):
        if not 0 <= neighbor_pos < len(groups) or len(groups[neighbor_pos]) != 1:
            continue
        other = track.notes[groups[neighbor_pos][0]]
        gap = abs(other.start_beat - note.start_beat)
        if 0 < gap <= 0.75 and abs(other.pitch - note.pitch) <= 2:
            return True
    return False


def _tremolo_positions(track: NormalizedTrack, groups: list[list[int]]) -> set[int]:
    """Find very rapid, consecutive monophonic repeats with strong MIDI evidence."""

    positions: set[int] = set()
    run: list[int] = []
    previous_position: int | None = None

    for position, indices in enumerate(groups):
        extends = False
        if len(indices) == 1 and previous_position is not None:
            previous_indices = groups[previous_position]
            if len(previous_indices) == 1:
                previous = track.notes[previous_indices[0]]
                current = track.notes[indices[0]]
                gap = current.start_beat - previous.start_beat
                extends = current.pitch == previous.pitch and 0 < gap <= 0.125 + 1e-9

        if extends:
            run.append(position)
        else:
            if len(run) >= 4:
                positions.update(run)
            run = [position] if len(indices) == 1 else []
        previous_position = position if len(indices) == 1 else None

    if len(run) >= 4:
        positions.update(run)
    return positions


def plan_picking(
    track: NormalizedTrack,
    fingering: FingeringResult,
    *,
    context: PlayingContext | None,
) -> PickingPlan:
    """Infer conservative right-hand direction from context plus MIDI evidence."""

    if len(track.notes) != len(fingering.notes):
        raise ValueError("Track and fingering result contain different note counts.")
    if context is None:
        return PickingPlan(track.index, track.name)

    riff = _score(context, "role_scores", "riff")
    strumming = _score(context, "role_scores", "strumming")
    solo = _score(context, "role_scores", "solo")
    metal = _score(context, "style_scores", "metal")
    arpeggio = _score(context, "technique_scores", "rock_arpeggio")

    groups = _onset_groups(track)
    tremolo_positions = _tremolo_positions(track, groups)
    decisions: list[PickingDecision] = []
    pick_phase = 0
    tremolo_phase = 0
    previous_tremolo_position: int | None = None
    strum_phase = 0

    for position, note_indices in enumerate(groups):
        if not all(fingering.notes[index].playable for index in note_indices):
            continue
        start = track.notes[note_indices[0]].start_beat

        if len(note_indices) >= 2 and strumming >= 0.50:
            direction = "down" if strum_phase % 2 == 0 else "up"
            strum_phase += 1
            decisions.append(
                PickingDecision(
                    note_indices=tuple(note_indices),
                    start_beat=start,
                    motion="strum",
                    direction=direction,
                    confidence=round(min(0.95, 0.72 + 0.18 * strumming), 6),
                    reason="Chordal onset in an active strumming context.",
                )
            )
            continue

        if len(note_indices) != 1:
            continue

        if position in tremolo_positions:
            if previous_tremolo_position is None or position != previous_tremolo_position + 1:
                tremolo_phase = 0
            direction = "down" if tremolo_phase % 2 == 0 else "up"
            tremolo_phase += 1
            previous_tremolo_position = position
            context_support = max(riff, solo, metal, arpeggio)
            decisions.append(
                PickingDecision(
                    note_indices=tuple(note_indices),
                    start_beat=start,
                    motion="pick",
                    direction=direction,
                    confidence=round(min(0.96, 0.86 + 0.08 * context_support), 6),
                    reason=(
                        "Four-or-more consecutive same-pitch attacks occur at very rapid "
                        "intervals; context only confidence-weights the tremolo evidence."
                    ),
                    technique="tremolo",
                )
            )
            continue

        previous_tremolo_position = None
        if riff >= 0.50 and metal >= 0.45 and _tight_low_repeat(track, groups, position):
            decisions.append(
                PickingDecision(
                    note_indices=tuple(note_indices),
                    start_beat=start,
                    motion="pick",
                    direction="down",
                    confidence=round(min(0.96, 0.72 + 0.12 * riff + 0.10 * metal), 6),
                    reason="Tight low-register repeated riff favors controlled downstrokes.",
                )
            )
            continue

        use_alternate = arpeggio >= 0.50
        if not use_alternate and solo >= 0.65 and position + 1 < len(groups):
            next_indices = groups[position + 1]
            if len(next_indices) == 1:
                gap = track.notes[next_indices[0]].start_beat - start
                use_alternate = 0 < gap <= 0.5

        if use_alternate:
            direction = "down" if pick_phase % 2 == 0 else "up"
            pick_phase += 1
            evidence = max(arpeggio, solo)
            decisions.append(
                PickingDecision(
                    note_indices=tuple(note_indices),
                    start_beat=start,
                    motion="pick",
                    direction=direction,
                    confidence=round(min(0.92, 0.68 + 0.18 * evidence), 6),
                    reason="Sequential single-note passage favors alternate picking.",
                )
            )

    return PickingPlan(track.index, track.name, decisions)
