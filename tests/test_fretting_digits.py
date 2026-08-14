from fretpilot.guitar import optimize_fingering
from fretpilot.guitar.fretting_digits import assign_fretting_digits
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def _track(pitches):
    return NormalizedTrack(
        index=0,
        name="Guitar",
        notes=[
            NormalizedNote(
                track_index=0,
                track_name="Guitar",
                channel=0,
                pitch=pitch,
                velocity=90,
                start_tick=index * 240,
                duration_ticks=240,
                start_beat=index * 0.5,
                duration_beats=0.5,
            )
            for index, pitch in enumerate(pitches)
        ],
    )


def test_movable_sus2_shapes_reuse_digit_pattern():
    track = _track([
        49, 56, 63,
        45, 52, 59,
        47, 54, 61,
        42, 49, 56, 57,
    ])
    fingering = optimize_fingering(track)
    assigned = assign_fretting_digits(track, fingering)

    assert [note.fretting_digit for note in assigned.notes] == [
        1, 3, 4,
        1, 3, 4,
        1, 3, 4,
        1, 3, 4, 4,
    ]
    assert [(n.string, n.fret) for n in assigned.notes] == [
        (n.string, n.fret) for n in fingering.notes
    ]


def test_open_string_has_no_fretting_digit():
    track = _track([64, 66, 67])
    assigned = assign_fretting_digits(track, optimize_fingering(track))
    assert [note.fretting_digit for note in assigned.notes] == [None, 1, 2]
