from __future__ import annotations

from fretpilot.guitar import candidate_positions, optimize_fingering
from fretpilot.knowledge import FingeringPreferences
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


def _chord_track(pitches: list[int]) -> NormalizedTrack:
    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Chord Guitar",
            channel=0,
            pitch=pitch,
            velocity=90,
            start_tick=0,
            duration_ticks=480,
            start_beat=0.0,
            duration_beats=1.0,
        )
        for pitch in pitches
    ]
    return NormalizedTrack(index=0, name="Chord Guitar", notes=notes)


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


def test_fingering_preferences_can_change_valid_candidate_ranking() -> None:
    track = _track([64, 66, 67, 69])
    neutral = optimize_fingering(track)
    closed_position = optimize_fingering(
        track,
        preferences=FingeringPreferences(open_string_usage=0.0),
    )

    # Neutral/default output is intentionally backward-compatible and starts on
    # the open high E string. A strong explicit open-string avoidance prior
    # moves the same physically valid phrase into a closed B-string position.
    assert [(note.string, note.fret) for note in neutral.notes] == [
        (1, 0),
        (1, 2),
        (1, 3),
        (1, 5),
    ]
    assert [(note.string, note.fret) for note in closed_position.notes] == [
        (2, 5),
        (2, 7),
        (2, 8),
        (2, 10),
    ]


def test_stacked_fifths_use_adjacent_strings_instead_of_one_string_ladder() -> None:
    # C#sus2-like cell from the Message in a Bottle reference: the same pitches
    # could be forced onto the low E string at frets 9/16/23, but a guitarist
    # naturally keeps the closed movable shape across A/D/G at 4/6/8.
    result = optimize_fingering(_track([49, 56, 63]))

    assert [note.string for note in result.notes] == [5, 4, 3]
    assert [note.fret for note in result.notes] == [4, 6, 8]


def test_repeating_sus2_riff_preserves_movable_shape_family() -> None:
    # Golden fingering pattern derived from the supplied original TAB reference:
    # C#sus2  A4-D6-G8
    # Asus2   E5-A7-D9
    # Bsus2   E7-A9-D11
    # F#sus2  E2-A4-D6, followed by a same-string 6->7 move.
    pitches = [
        49, 56, 63,
        45, 52, 59,
        47, 54, 61,
        42, 49, 56, 57,
    ]
    result = optimize_fingering(_track(pitches))

    assert [note.string for note in result.notes] == [
        5, 4, 3,
        6, 5, 4,
        6, 5, 4,
        6, 5, 4, 4,
    ]
    assert [note.fret for note in result.notes] == [
        4, 6, 8,
        5, 7, 9,
        7, 9, 11,
        2, 4, 6, 7,
    ]


def test_simultaneous_chord_notes_use_distinct_strings() -> None:
    result = optimize_fingering(_chord_track([64, 67, 71]))

    strings = [note.string for note in result.notes]
    assert all(note.playable for note in result.notes)
    assert len(set(strings)) == len(strings)
    assert not any(
        diagnostic.code == "unplayable_chord_shape"
        for diagnostic in result.diagnostics
    )


def test_unplayable_pitch_is_retained_and_reported() -> None:
    result = optimize_fingering(_track([39, 40, 43]))

    assert result.notes[0].playable is False
    assert result.notes[0].string is None
    assert result.notes[0].fret is None
    assert result.notes[1].playable is True
    assert any(diagnostic.code == "unplayable_pitch" for diagnostic in result.diagnostics)
