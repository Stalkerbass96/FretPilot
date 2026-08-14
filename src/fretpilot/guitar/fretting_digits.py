"""Conservative 1-4 fretting-digit assignment over final string/fret choices."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from fretpilot.guitar.models import FingeringResult
from fretpilot.midi.models import NormalizedTrack


def _digit(offset: int) -> int:
    if offset <= 0:
        return 1
    if offset == 1:
        return 2
    if offset == 2:
        return 3
    return 4


def assign_digit_locations(
    entries: list[tuple[int, int, int | None, int | None]],
) -> list[int | None]:
    """Assign digits to ``(start_tick, pitch, string, fret)`` tuples."""

    onset_groups: dict[int, list[int]] = defaultdict(list)
    for index, entry in enumerate(entries):
        onset_groups[entry[0]].append(index)

    assignments: dict[int, int] = {}
    anchor_fret: int | None = None
    previous_fret: int | None = None
    previous_string: int | None = None

    for start_tick in sorted(onset_groups):
        indices = onset_groups[start_tick]
        fretted = [
            index
            for index in indices
            if entries[index][2] is not None
            and entries[index][3] is not None
            and int(entries[index][3]) > 0
        ]
        if not fretted:
            continue

        if len(indices) > 1:
            frets = [int(entries[index][3]) for index in fretted]
            if max(frets) - min(frets) <= 4:
                anchor_fret = min(frets)
                for index in fretted:
                    assignments[index] = _digit(int(entries[index][3]) - anchor_fret)
            anchor_index = min(fretted, key=lambda index: entries[index][1])
            previous_fret = int(entries[anchor_index][3])
            previous_string = entries[anchor_index][2]
            continue

        index = fretted[0]
        string = entries[index][2]
        fret = int(entries[index][3])

        shape_restart = (
            previous_fret is not None
            and previous_string is not None
            and string is not None
            and string >= previous_string + 2
            and fret <= previous_fret - 2
        )
        if anchor_fret is None or shape_restart:
            anchor_fret = fret

        stretched_same_string = (
            previous_fret == anchor_fret + 4
            and previous_string == string
            and fret == previous_fret + 1
        )
        if fret < anchor_fret or fret > anchor_fret + 4:
            if stretched_same_string:
                assignments[index] = 4
            else:
                anchor_fret = fret
                assignments[index] = 1
        else:
            assignments[index] = _digit(fret - anchor_fret)

        previous_fret = fret
        previous_string = string

    return [assignments.get(index) for index in range(len(entries))]


def assign_fretting_digits(
    track: NormalizedTrack,
    fingering: FingeringResult,
) -> FingeringResult:
    """Assign digits without changing any selected string/fret position."""

    if len(track.notes) != len(fingering.notes):
        raise ValueError("Track and fingering result contain different note counts.")

    digits = assign_digit_locations([
        (note.start_tick, note.pitch, placed.string, placed.fret)
        for note, placed in zip(track.notes, fingering.notes, strict=True)
    ])
    notes = [
        replace(item, fretting_digit=digits[index])
        for index, item in enumerate(fingering.notes)
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
