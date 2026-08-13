from __future__ import annotations

from fretpilot.guitar import candidate_positions, optimize_fingering
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def _track(pitches: list[int]) -> NormalizedTrack:
    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Lead Guitar",
            channel=0,
            pitch=pitch,
            velocity=90,
            start_tick=index * 240,
            duration_ticks=240,
            start_beat=index * 0.5,
            duration_beats=0.5,
        )
        for index, pitch in enumerate(pitches)
    ]
    return NormalizedTrack(index=0, name="Lead Guitar", notes=notes)


def test_e4_has_all_standard_guitar_positions() -> None:
    positions = candidate_positions(64)
    locations = {(position.string, position.fret) for position in positions}

    assert locations == {
        (1, 0),
        (2, 5),
        (3, 9),
        (4, 14),
        (5, 19),
        (6, 24),
    }


def test_phrase_optimizer_prefers_coherent_same_string_path() -> None:
    result = optimize_fingering(_track([64, 66, 67, 69]))

    assert not result.diagnostics
    assert [note.string for note in result.notes] == [1, 1, 1, 1]
    assert [note.fret for note in result.notes] == [0, 2, 3, 5]


def test_unplayable_pitch_is_retained_and_reported() -> None:
    result = optimize_fingering(_track([39, 40, 43]))

    assert result.notes[0].playable is False
    assert result.notes[0].string is None
    assert result.notes[0].fret is None
    assert result.notes[1].playable is True
    assert any(diagnostic.code == "unplayable_pitch" for diagnostic in result.diagnostics)
