"""Conservative harmony labels from explicit chord tones and final fretboard paths."""

from __future__ import annotations

from collections import defaultdict

from fretpilot.guitar.models import FingeringResult
from fretpilot.harmony.models import HarmonyDecision, HarmonyPlan
from fretpilot.midi.models import NormalizedTrack


_NOTE_NAMES = (
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B",
)

_TEMPLATES: tuple[tuple[str, frozenset[int], str], ...] = (
    ("maj7", frozenset({0, 4, 7, 11}), "maj7"),
    ("7", frozenset({0, 4, 7, 10}), "7"),
    ("m7", frozenset({0, 3, 7, 10}), "m7"),
    ("major", frozenset({0, 4, 7}), ""),
    ("minor", frozenset({0, 3, 7}), "m"),
    ("sus2", frozenset({0, 2, 7}), "sus2"),
    ("sus4", frozenset({0, 5, 7}), "sus4"),
    ("diminished", frozenset({0, 3, 6}), "dim"),
    ("power", frozenset({0, 7}), "5"),
)


def _identify(pitches: list[int]) -> tuple[int, str, str] | None:
    pitch_classes = frozenset(pitch % 12 for pitch in pitches)
    if len(pitch_classes) < 2:
        return None

    bass_pc = min(pitches) % 12
    roots = [bass_pc] + [pc for pc in sorted(pitch_classes) if pc != bass_pc]
    for root in roots:
        intervals = frozenset((pc - root) % 12 for pc in pitch_classes)
        for quality, template, suffix in _TEMPLATES:
            if intervals != template:
                continue
            if quality == "power" and root != bass_pc:
                continue
            symbol = _NOTE_NAMES[root] + suffix
            if len(pitch_classes) >= 3 and bass_pc != root:
                symbol += "/" + _NOTE_NAMES[bass_pc]
            return root, quality, symbol
    return None


def _simultaneous_decisions(track: NormalizedTrack) -> list[HarmonyDecision]:
    onset_groups: dict[int, list[int]] = defaultdict(list)
    for index, note in enumerate(track.notes):
        onset_groups[note.start_tick].append(index)

    decisions: list[HarmonyDecision] = []
    for indices in onset_groups.values():
        if len(indices) < 2:
            continue
        pitches = [track.notes[index].pitch for index in indices]
        identified = _identify(pitches)
        if identified is None:
            continue
        root, quality, symbol = identified
        decisions.append(
            HarmonyDecision(
                note_indices=tuple(indices),
                start_beat=min(track.notes[index].start_beat for index in indices),
                symbol=symbol,
                root_pitch_class=root,
                quality=quality,
                confidence=0.96,
                reason="Simultaneous source onset matches a known pitch-class chord template.",
            )
        )
    return decisions


def _monotonic_string_path(
    fingering: FingeringResult,
    indices: list[int],
    *,
    max_string_step: int,
) -> bool:
    strings = [fingering.notes[index].string for index in indices]
    if any(string is None for string in strings):
        return False
    deltas = [
        int(current) - int(previous)
        for previous, current in zip(strings, strings[1:], strict=False)
    ]
    if not deltas or any(abs(delta) > max_string_step for delta in deltas):
        return False
    nonzero = [delta for delta in deltas if delta != 0]
    if not nonzero:
        return False
    direction = 1 if nonzero[0] > 0 else -1
    if any((1 if delta > 0 else -1) != direction for delta in nonzero):
        return False
    return deltas.count(0) <= 1


def _guitar_arpeggio_path(
    fingering: FingeringResult,
    indices: list[int],
) -> bool:
    return _monotonic_string_path(fingering, indices, max_string_step=1)


def _four_note_pitch_classes_are_safe(notes) -> bool:
    pitch_classes = [note.pitch % 12 for note in notes]
    unique_count = len(set(pitch_classes))
    if unique_count == 4:
        return True
    return unique_count == 3 and pitch_classes[-1] == pitch_classes[0]


def _octave_closure_path(
    fingering: FingeringResult,
    indices: list[int],
    pitches: list[int],
) -> bool:
    if len(indices) != 4 or len(pitches) != 4:
        return False
    if pitches[-1] - pitches[0] != 12:
        return False
    if pitches[-1] % 12 != pitches[0] % 12:
        return False
    # Ordinary three-note cells remain strictly adjacent-string.  Only the
    # repeated-root closing note may require a single string skip, and the
    # whole path must still move monotonically without reversing direction.
    if not _guitar_arpeggio_path(fingering, indices[:3]):
        return False
    return _monotonic_string_path(fingering, indices, max_string_step=2)


def _sequential_decisions(
    track: NormalizedTrack,
    fingering: FingeringResult,
) -> list[HarmonyDecision]:
    order = sorted(
        range(len(track.notes)),
        key=lambda index: (track.notes[index].start_beat, index),
    )
    decisions: list[HarmonyDecision] = []
    cursor = 0

    while cursor < len(order):
        matched = None
        for length in (4, 3):
            window = order[cursor : cursor + length]
            if len(window) != length:
                continue
            notes = [track.notes[index] for index in window]
            starts = [note.start_beat for note in notes]
            if len(set(starts)) != length:
                continue
            if length == 4 and not _four_note_pitch_classes_are_safe(notes):
                continue
            if starts[-1] - starts[0] > 1.5 + 1e-9:
                continue
            if not all(
                current.start_beat > previous.start_beat
                for previous, current in zip(notes, notes[1:], strict=False)
            ):
                continue
            pitches = [note.pitch for note in notes]
            path_ok = _guitar_arpeggio_path(fingering, window)
            if not path_ok and length == 4:
                path_ok = _octave_closure_path(fingering, window, pitches)
            if not path_ok:
                continue
            identified = _identify(pitches)
            if identified is None:
                continue
            matched = (window, identified)
            break

        if matched is None:
            cursor += 1
            continue

        window, identified = matched
        root, quality, symbol = identified
        decisions.append(
            HarmonyDecision(
                note_indices=tuple(window),
                start_beat=track.notes[window[0]].start_beat,
                symbol=symbol,
                root_pitch_class=root,
                quality=quality,
                confidence=0.90,
                reason=(
                    "Sequential notes match a known chord template and follow a "
                    "monotonic guitar path in the final fingering."
                ),
            )
        )
        cursor += len(window)

    return decisions


def plan_harmony(
    track: NormalizedTrack,
    fingering: FingeringResult,
) -> HarmonyPlan:
    """Label explicit chords and strongly evidenced guitar arpeggio cells."""

    if len(track.notes) != len(fingering.notes):
        raise ValueError("Track and fingering result contain different note counts.")

    simultaneous = _simultaneous_decisions(track)
    covered = {index for decision in simultaneous for index in decision.note_indices}
    sequential = [
        decision
        for decision in _sequential_decisions(track, fingering)
        if not covered.intersection(decision.note_indices)
    ]
    decisions = sorted(
        simultaneous + sequential,
        key=lambda item: (item.start_beat, item.note_indices[0]),
    )
    return HarmonyPlan(track.index, track.name, decisions)
