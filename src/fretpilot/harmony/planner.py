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
            if intervals == template:
                return root, quality, _NOTE_NAMES[root] + suffix
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


def _adjacent_string_run(
    fingering: FingeringResult,
    indices: list[int],
) -> bool:
    strings = [fingering.notes[index].string for index in indices]
    if any(string is None for string in strings):
        return False
    deltas = [
        int(current) - int(previous)
        for previous, current in zip(strings, strings[1:], strict=False)
    ]
    return bool(deltas) and all(delta == deltas[0] for delta in deltas) and abs(deltas[0]) == 1


def _sequential_decisions(
    track: NormalizedTrack,
    fingering: FingeringResult,
) -> list[HarmonyDecision]:
    order = sorted(range(len(track.notes)), key=lambda index: (track.notes[index].start_beat, index))
    decisions: list[HarmonyDecision] = []
    cursor = 0

    while cursor < len(order):
        matched = None
        for length in (4, 3, 2):
            window = order[cursor : cursor + length]
            if len(window) != length:
                continue
            notes = [track.notes[index] for index in window]
            starts = [note.start_beat for note in notes]
            if len(set(starts)) != length:
                continue
            if starts[-1] - starts[0] > 1.5 + 1e-9:
                continue
            if not all(
                current.start_beat > previous.start_beat
                for previous, current in zip(notes, notes[1:], strict=False)
            ):
                continue
            if not _adjacent_string_run(fingering, window):
                continue
            identified = _identify([note.pitch for note in notes])
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
                    "Sequential notes match a known chord template and follow a monotonic "
                    "adjacent-string path in the final fingering."
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
