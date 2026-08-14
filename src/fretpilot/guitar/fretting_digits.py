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


def assign_fretting_digits(
    track: NormalizedTrack,
    fingering: FingeringResult,
) -> FingeringResult:
    """Assign digits without changing any selected string/fret position."""

    if len(track.notes) != len(fingering.notes):
        raise ValueError("Track and fingering result contain different note counts.")

    onset_groups: dict[int, list[int]] = defaultdict(list)
    for index, note in enumerate(track.notes):
        onset_groups[note.start_tick].append(index)

    assignments: dict[int, int] = {}
    anchor_fret: int | None = None
    previous_fret: int | None = None
    previous_string: int | None = None

    for start_tick in sorted(onset_groups):
        indices = onset_groups[start_tick]
        fretted = [
            index
            for index in indices
            if fingering.notes[index].playable
            and fingering.notes[index].fret is not None
            and fingering.notes[index].fret > 0
        ]
        if not fretted:
            continue

        if len(indices) > 1:
            frets = [int(fingering.notes[index].fret) for index in fretted]
            if max(frets) - min(frets) <= 4:
                anchor_fret = min(frets)
                for index in fretted:
                    fret = int(fingering.notes[index].fret)
                    assignments[index] = _digit(fret - anchor_fret)
            anchor_index = min(fretted, key=lambda index: track.notes[index].pitch)
            previous_fret = int(fingering.notes[anchor_index].fret)
            previous_string = fingering.notes[anchor_index].string
            continue

        index = fretted[0]
        item = fingering.notes[index]
        fret = int(item.fret)
        string = item.string

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
            anchor_fret is not None
            and previous_fret == anchor_fret + 4
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

    notes = [
        replace(item, fretting_digit=assignments.get(item.note_index))
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
