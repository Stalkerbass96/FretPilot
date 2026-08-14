"""Deterministic right-hand pick/strum intent planning."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from fretpilot.guitar.models import FingeringResult
from fretpilot.knowledge.picking_research import PICKING_RESEARCH
from fretpilot.midi.models import NormalizedTrack
from fretpilot.picking.models import PickingDecision, PickingPlan

if TYPE_CHECKING:
    from fretpilot.knowledge.playing_contexts import PlayingContext


def _score(context: PlayingContext, group: str, key: str) -> float:
    return float(getattr(context, group).get(key, 0.0))


def _prior(family: str, key: str) -> float:
    branch = PICKING_RESEARCH.get(family, {})
    value = branch.get(key, 1.0) if isinstance(branch, dict) else 1.0
    return float(value) if isinstance(value, (int, float)) else 1.0


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


def _sweep_directions(
    track: NormalizedTrack,
    fingering: FingeringResult,
    groups: list[list[int]],
) -> dict[int, str]:
    """Find fast monotonic adjacent-string runs; return direction by onset position."""

    result: dict[int, str] = {}
    run: list[int] = []
    run_direction: str | None = None

    def flush() -> None:
        if len(run) >= 3 and run_direction is not None:
            for position in run:
                result[position] = run_direction

    for position in range(1, len(groups)):
        previous_indices = groups[position - 1]
        current_indices = groups[position]
        step_direction: str | None = None
        if len(previous_indices) == 1 and len(current_indices) == 1:
            previous_index = previous_indices[0]
            current_index = current_indices[0]
            previous_string = fingering.notes[previous_index].string
            current_string = fingering.notes[current_index].string
            gap = (
                track.notes[current_index].start_beat
                - track.notes[previous_index].start_beat
            )
            if previous_string is not None and current_string is not None and 0 < gap <= 0.25 + 1e-9:
                string_delta = current_string - previous_string
                if string_delta == -1:
                    step_direction = "down"
                elif string_delta == 1:
                    step_direction = "up"

        if step_direction is not None:
            if run_direction == step_direction and run and run[-1] == position - 1:
                run.append(position)
            else:
                flush()
                run = [position - 1, position]
                run_direction = step_direction
        else:
            flush()
            run = []
            run_direction = None

    flush()
    return result


def _rolled_strums(
    track: NormalizedTrack,
    fingering: FingeringResult,
    *,
    strumming_score: float,
    arpeggio_score: float,
) -> list[PickingDecision]:
    """Detect short staggered chord attacks from source timing and final strings."""

    if arpeggio_score >= 0.65:
        return []

    order = sorted(
        range(len(track.notes)),
        key=lambda index: (track.notes[index].start_beat, index),
    )
    decisions: list[PickingDecision] = []
    cursor = 0
    while cursor < len(order):
        first = order[cursor]
        first_start = track.notes[first].start_beat
        candidate = [first]
        position = cursor + 1
        while position < len(order) and len(candidate) < 6:
            index = order[position]
            note = track.notes[index]
            if note.start_beat - first_start > 0.12 + 1e-9:
                break
            previous = track.notes[candidate[-1]]
            if note.start_beat <= previous.start_beat + 1e-9:
                break
            candidate.append(index)
            position += 1

        accepted: list[int] | None = None
        direction: str | None = None
        for length in range(len(candidate), 2, -1):
            window = candidate[:length]
            strings = [fingering.notes[index].string for index in window]
            if any(string is None for string in strings):
                continue
            deltas = [
                int(current) - int(previous)
                for previous, current in zip(strings, strings[1:], strict=False)
            ]
            if not deltas or not all(delta == deltas[0] for delta in deltas):
                continue
            if deltas[0] not in (-1, 1):
                continue
            last_start = track.notes[window[-1]].start_beat
            minimum_end = min(
                track.notes[index].start_beat + track.notes[index].duration_beats
                for index in window
            )
            if minimum_end - last_start < 0.10 - 1e-9:
                continue
            accepted = window
            direction = "down" if deltas[0] == -1 else "up"
            break

        if accepted is None or direction is None:
            cursor += 1
            continue

        confidence = min(0.97, 0.90 + 0.05 * strumming_score)
        decisions.append(
            PickingDecision(
                note_indices=tuple(accepted),
                start_beat=track.notes[accepted[0]].start_beat,
                motion="strum",
                direction=direction,
                confidence=round(confidence, 6),
                reason=(
                    "Source notes enter as a short staggered, overlapping chord attack "
                    "across monotonic adjacent strings."
                ),
                technique="rolled_strum",
            )
        )
        consumed = set(accepted)
        cursor += 1
        while cursor < len(order) and order[cursor] in consumed:
            cursor += 1

    return decisions


def plan_picking(
    track: NormalizedTrack,
    fingering: FingeringResult,
    *,
    context: PlayingContext | None,
) -> PickingPlan:
    """Infer conservative right-hand direction from context plus physical/MIDI evidence."""

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
    sweep_directions = _sweep_directions(track, fingering, groups)
    decisions: list[PickingDecision] = _rolled_strums(
        track,
        fingering,
        strumming_score=strumming,
        arpeggio_score=arpeggio,
    )
    consumed_notes = {
        index
        for decision in decisions
        for index in decision.note_indices
    }
    pick_phase = 0
    tremolo_phase = 0
    previous_tremolo_position: int | None = None
    strum_phase = 0

    for position, note_indices in enumerate(groups):
        if consumed_notes.intersection(note_indices):
            continue
        if not all(fingering.notes[index].playable for index in note_indices):
            continue
        start = track.notes[note_indices[0]].start_beat

        if len(note_indices) >= 2 and strumming >= 0.50:
            direction = "down" if strum_phase % 2 == 0 else "up"
            strum_phase += 1
            decisions.append(
                PickingDecision(
                    tuple(note_indices), start, "strum", direction,
                    round(min(0.95, 0.72 + 0.18 * strumming), 6),
                    "Chordal onset in an active strumming context.",
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
            research = _prior("tremolo", "rapid_repeated_pitch_bias")
            confidence = 0.84 + 0.06 * context_support + 0.04 * (research - 1.0)
            decisions.append(
                PickingDecision(
                    tuple(note_indices), start, "pick", direction,
                    round(min(0.96, confidence), 6),
                    "Very rapid repeated-pitch run satisfies tremolo evidence; context and research only confidence-weight it.",
                    technique="tremolo",
                )
            )
            continue

        previous_tremolo_position = None
        sweep_direction = sweep_directions.get(position)
        if arpeggio >= 0.65 and sweep_direction is not None:
            research = _prior("sweep", "adjacent_string_arpeggio")
            confidence = 0.78 + 0.10 * arpeggio + 0.04 * (research - 1.0)
            decisions.append(
                PickingDecision(
                    tuple(note_indices), start, "pick", sweep_direction,
                    round(min(0.95, confidence), 6),
                    "Fast arpeggio follows a monotonic adjacent-string path in the final fingering.",
                    technique="sweep",
                )
            )
            continue

        if riff >= 0.50 and metal >= 0.45 and _tight_low_repeat(track, groups, position):
            research = _prior("downstroke", "tight_repeated_rhythm_bias")
            confidence = 0.70 + 0.12 * riff + 0.08 * metal + 0.04 * (research - 1.0)
            decisions.append(
                PickingDecision(
                    tuple(note_indices), start, "pick", "down",
                    round(min(0.96, confidence), 6),
                    "Tight low-register repeated riff favors controlled downstrokes.",
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
            research = _prior("alternate", "fast_single_note_bias")
            confidence = 0.66 + 0.18 * evidence + 0.04 * (research - 1.0)
            decisions.append(
                PickingDecision(
                    tuple(note_indices), start, "pick", direction,
                    round(min(0.92, confidence), 6),
                    "Sequential single-note passage favors alternate picking.",
                )
            )

    decisions.sort(key=lambda item: (item.start_beat, item.note_indices[0]))
    return PickingPlan(track.index, track.name, decisions)
