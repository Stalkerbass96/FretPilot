"""Instrument definitions and playable-position generation."""

from __future__ import annotations

from dataclasses import dataclass

from fretpilot.guitar.models import FretPosition


@dataclass(frozen=True, slots=True)
class GuitarTuning:
    name: str
    # Guitar string number -> MIDI pitch of the open string.
    open_strings: tuple[tuple[int, int], ...]


STANDARD_TUNING = GuitarTuning(
    name="E2 A2 D3 G3 B3 E4",
    open_strings=(
        (6, 40),
        (5, 45),
        (4, 50),
        (3, 55),
        (2, 59),
        (1, 64),
    ),
)


def candidate_positions(
    pitch: int,
    *,
    tuning: GuitarTuning = STANDARD_TUNING,
    max_fret: int = 24,
) -> list[FretPosition]:
    """Return every playable string/fret location for a MIDI pitch."""

    positions: list[FretPosition] = []
    for string, open_pitch in tuning.open_strings:
        fret = pitch - open_pitch
        if 0 <= fret <= max_fret:
            positions.append(FretPosition(string=string, fret=fret, pitch=pitch))

    return positions
