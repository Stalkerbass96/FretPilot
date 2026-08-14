"""Deterministic, confidence-gated MIDI note rewriting for guitar.

The rewriter is intentionally conservative and explainable. It only performs
edits for which there is a strong local or physical signal, and every edit is
gated by the user-controlled MIDI-fidelity continuum.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from statistics import median

from fretpilot.detection.models import InstrumentStream
from fretpilot.guitar.instrument import STANDARD_TUNING
from fretpilot.midi.models import NormalizedNote
from fretpilot.rewrite.models import (
    DEFAULT_MIDI_FIDELITY,
    NoteRewriteChange,
    NoteRewriteResult,
)

_EPSILON = 1e-9


@dataclass(slots=True)
class _WorkingNote:
    note: NormalizedNote
    source_note_index: int
    origin: str


def _validate_inputs(midi_fidelity: float, max_fret: int) -> None:
    if not 0.0 <= midi_fidelity <= 1.0:
        raise ValueError("midi_fidelity must be between 0.0 and 1.0.")
    if max_fret < 0:
        raise ValueError("max_fret must be zero or greater.")


def _should_apply(rationality: float, confidence: float) -> bool:
    """Continuously gate edits instead of selecting a binary preset."""

    return rationality + confidence >= 1.0 - _EPSILON


def _note_sort_key(item: _WorkingNote) -> tuple[float, int, int]:
    return (item.note.start_beat, item.note.pitch, item.source_note_index)


def _onset_groups(notes: list[_WorkingNote]) -> list[list[_WorkingNote]]:
    groups: list[list[_WorkingNote]] = []
    for item in sorted(notes, key=_note_sort_key):
        if not groups or abs(groups[-1][0].note.start_beat - item.note.start_beat) > _EPSILON:
            groups.append([item])
        else:
            groups[-1].append(item)
    return groups


def _octave_candidates(pitch: int, minimum: int, maximum: int) -> list[int]:
    return [
        candidate
        for candidate in range(minimum, maximum + 1)
        if candidate % 12 == pitch % 12
    ]


def _record_change(
    changes: list[NoteRewriteChange],
    *,
    operation: str,
    item: _WorkingNote,
    before: dict[str, object],
    after: dict[str, object],
    confidence: float,
    reason: str,
) -> None:
    changes.append(
        NoteRewriteChange(
            id=f"rewrite-{len(changes) + 1:05d}",
            operation=operation,
            source_note_index=item.source_note_index,
            output_note_index=None,
            before=before,
            after=after,
            confidence=round(confidence, 6),
            reason=reason,
        )
    )


def _repair_guitar_range(
    notes: list[_WorkingNote],
    *,
    rationality: float,
    max_fret: int,
    changes: list[NoteRewriteChange],
) -> None:
    minimum = min(pitch for _string, pitch in STANDARD_TUNING.open_strings)
    maximum = max(pitch for _string, pitch in STANDARD_TUNING.open_strings) + max_fret

    for item in notes:
        pitch = item.note.pitch
        if minimum <= pitch <= maximum:
            continue
        candidates = _octave_candidates(pitch, minimum, maximum)
        if not candidates:
            continue
        target = min(candidates, key=lambda candidate: (abs(candidate - pitch), candidate))
        distance = abs(target - pitch)
        confidence = min(0.99, 0.94 + distance / 240.0)
        if not _should_apply(rationality, confidence):
            continue
        item.note = replace(item.note, pitch=target)
        _record_change(
            changes,
            operation="transpose",
            item=item,
            before={"pitch": pitch},
            after={"pitch": target},
            confidence=confidence,
            reason="fit_standard_guitar_range_by_octave",
        )


def _repair_isolated_octave_outliers(
    notes: list[_WorkingNote],
    *,
    rationality: float,
    max_fret: int,
    changes: list[NoteRewriteChange],
) -> None:
    minimum = min(pitch for _string, pitch in STANDARD_TUNING.open_strings)
    maximum = max(pitch for _string, pitch in STANDARD_TUNING.open_strings) + max_fret
    groups = _onset_groups(notes)

    for index in range(1, len(groups) - 1):
        previous, current, following = groups[index - 1 : index + 2]
        if len(previous) != 1 or len(current) != 1 or len(following) != 1:
            continue
        before = previous[0].note
        item = current[0]
        after = following[0].note
        if after.start_beat - before.start_beat > 4.0:
            continue
        if abs(before.pitch - after.pitch) > 5:
            continue
        current_cost = abs(item.note.pitch - before.pitch) + abs(item.note.pitch - after.pitch)
        if min(abs(item.note.pitch - before.pitch), abs(item.note.pitch - after.pitch)) < 10:
            continue
        candidates = _octave_candidates(item.note.pitch, minimum, maximum)
        target = min(
            candidates,
            key=lambda pitch: abs(pitch - before.pitch) + abs(pitch - after.pitch),
        )
        target_cost = abs(target - before.pitch) + abs(target - after.pitch)
        improvement = current_cost - target_cost
        if target == item.note.pitch or improvement < 12:
            continue
        confidence = min(0.94, 0.72 + improvement / 96.0)
        if not _should_apply(rationality, confidence):
            continue
        source_pitch = item.note.pitch
        item.note = replace(item.note, pitch=target)
        _record_change(
            changes,
            operation="transpose",
            item=item,
            before={"pitch": source_pitch},
            after={"pitch": target},
            confidence=confidence,
            reason="repair_isolated_octave_register_outlier",
        )


def _remove_exact_duplicates(
    notes: list[_WorkingNote],
    *,
    rationality: float,
    changes: list[NoteRewriteChange],
) -> list[_WorkingNote]:
    by_key: dict[tuple[int, int], list[_WorkingNote]] = {}
    for item in notes:
        key = (item.note.start_tick, item.note.pitch)
        by_key.setdefault(key, []).append(item)

    deleted: set[int] = set()
    for duplicates in by_key.values():
        if len(duplicates) < 2 or not _should_apply(rationality, 0.995):
            continue
        keep = max(
            duplicates,
            key=lambda item: (
                item.note.duration_ticks,
                item.note.velocity,
                -item.source_note_index,
            ),
        )
        for item in duplicates:
            if item is keep:
                continue
            deleted.add(id(item))
            _record_change(
                changes,
                operation="delete",
                item=item,
                before={
                    "pitch": item.note.pitch,
                    "start_beat": item.note.start_beat,
                    "duration_beats": item.note.duration_beats,
                    "velocity": item.note.velocity,
                },
                after={},
                confidence=0.995,
                reason="duplicate_same_pitch_onset",
            )
    return [item for item in notes if id(item) not in deleted]


def _remove_short_spike_outliers(
    notes: list[_WorkingNote],
    *,
    rationality: float,
    changes: list[NoteRewriteChange],
) -> list[_WorkingNote]:
    groups = _onset_groups(notes)
    deleted: set[int] = set()
    for index in range(1, len(groups) - 1):
        previous, current, following = groups[index - 1 : index + 2]
        if len(previous) != 1 or len(current) != 1 or len(following) != 1:
            continue
        before, item, after = previous[0], current[0], following[0]
        if item.note.duration_beats > 0.125 + _EPSILON:
            continue
        if abs(before.note.pitch - after.note.pitch) > 3:
            continue
        leap = min(
            abs(item.note.pitch - before.note.pitch),
            abs(item.note.pitch - after.note.pitch),
        )
        if leap < 8:
            continue
        low_velocity = item.note.velocity <= 0.75 * median(
            [before.note.velocity, after.note.velocity]
        )
        confidence = 0.90 if low_velocity else 0.78
        if not _should_apply(rationality, confidence):
            continue
        deleted.add(id(item))
        _record_change(
            changes,
            operation="delete",
            item=item,
            before={
                "pitch": item.note.pitch,
                "start_beat": item.note.start_beat,
                "duration_beats": item.note.duration_beats,
                "velocity": item.note.velocity,
            },
            after={},
            confidence=confidence,
            reason="remove_short_isolated_pitch_spike",
        )
    return [item for item in notes if id(item) not in deleted]


def _fill_missing_repeated_pulses(
    notes: list[_WorkingNote],
    *,
    rationality: float,
    ticks_per_beat: int,
    next_source_index: int,
    changes: list[NoteRewriteChange],
) -> tuple[list[_WorkingNote], int]:
    if not _should_apply(rationality, 0.86):
        return notes, next_source_index

    groups = _onset_groups(notes)
    additions: list[_WorkingNote] = []
    occupied_onsets = {round(group[0].note.start_beat, 9) for group in groups}

    for index in range(1, len(groups) - 2):
        quartet = groups[index - 1 : index + 3]
        if any(len(group) != 1 for group in quartet):
            continue
        pitches = [group[0].note.pitch for group in quartet]
        if len(set(pitches)) != 1:
            continue
        onsets = [group[0].note.start_beat for group in quartet]
        left_step = onsets[1] - onsets[0]
        gap = onsets[2] - onsets[1]
        right_step = onsets[3] - onsets[2]
        expected = median([left_step, right_step])
        if not 0.125 - _EPSILON <= expected <= 2.0 + _EPSILON:
            continue
        if abs(left_step - right_step) > max(0.03, expected * 0.10):
            continue
        if abs(gap - 2.0 * expected) > max(0.03, expected * 0.12):
            continue
        start_beat = onsets[1] + expected
        if round(start_beat, 9) in occupied_onsets:
            continue

        left = quartet[1][0].note
        right = quartet[2][0].note
        duration = min(expected, median([left.duration_beats, right.duration_beats]))
        duration_ticks = max(1, round(duration * ticks_per_beat))
        synthetic = _WorkingNote(
            note=replace(
                left,
                velocity=round(median([left.velocity, right.velocity])),
                start_tick=round(start_beat * ticks_per_beat),
                duration_ticks=duration_ticks,
                start_beat=start_beat,
                duration_beats=duration,
            ),
            source_note_index=next_source_index,
            origin="synthetic",
        )
        next_source_index += 1
        additions.append(synthetic)
        occupied_onsets.add(round(start_beat, 9))
        _record_change(
            changes,
            operation="insert",
            item=synthetic,
            before={},
            after={
                "pitch": synthetic.note.pitch,
                "start_beat": synthetic.note.start_beat,
                "duration_beats": synthetic.note.duration_beats,
                "velocity": synthetic.note.velocity,
            },
            confidence=0.86,
            reason="fill_missing_repeated_pulse",
        )

    return [*notes, *additions], next_source_index


def rewrite_instrument_stream(
    stream: InstrumentStream,
    *,
    midi_fidelity: float = DEFAULT_MIDI_FIDELITY,
    max_fret: int = 24,
    ticks_per_beat: int = 480,
) -> NoteRewriteResult:
    """Rewrite one logical stream according to a MIDI↔reasonableness continuum.

    ``midi_fidelity=1.0`` is a strict passthrough. Lower values permit more
    confidence-gated edits; the default (0.35) deliberately favors a plausible,
    playable guitar result while retaining source provenance for every note.
    """

    _validate_inputs(midi_fidelity, max_fret)
    if ticks_per_beat <= 0:
        raise ValueError("ticks_per_beat must be greater than zero.")

    original_count = len(stream.notes)
    working = [
        _WorkingNote(note=note, source_note_index=index, origin="midi")
        for index, note in enumerate(stream.notes)
    ]
    changes: list[NoteRewriteChange] = []
    rationality = 1.0 - midi_fidelity

    if midi_fidelity < 1.0 - _EPSILON:
        _repair_guitar_range(
            working,
            rationality=rationality,
            max_fret=max_fret,
            changes=changes,
        )
        _repair_isolated_octave_outliers(
            working,
            rationality=rationality,
            max_fret=max_fret,
            changes=changes,
        )
        working = _remove_exact_duplicates(
            working,
            rationality=rationality,
            changes=changes,
        )
        working = _remove_short_spike_outliers(
            working,
            rationality=rationality,
            changes=changes,
        )
        working, _next_source_index = _fill_missing_repeated_pulses(
            working,
            rationality=rationality,
            ticks_per_beat=ticks_per_beat,
            next_source_index=original_count,
            changes=changes,
        )

    working.sort(key=_note_sort_key)
    output_index_by_source = {
        item.source_note_index: output_index
        for output_index, item in enumerate(working)
    }
    for change in changes:
        change.output_note_index = output_index_by_source.get(change.source_note_index)

    rewritten_stream = replace(
        stream,
        notes=[item.note for item in working],
    )
    return NoteRewriteResult(
        stream=rewritten_stream,
        midi_fidelity=midi_fidelity,
        original_note_count=original_count,
        source_note_indices=[item.source_note_index for item in working],
        source_note_origins=[item.origin for item in working],
        changes=changes,
    )
