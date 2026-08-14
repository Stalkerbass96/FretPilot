from fretpilot.guitar import optimize_fingering
from fretpilot.guitar.fretting_digits import assign_fretting_digits
from fretpilot.harmony import plan_harmony
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def _track(pitches, starts=None):
    active_starts = starts or [index * 0.5 for index in range(len(pitches))]
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
                start_tick=round(active_starts[index] * 480),
                duration_ticks=240,
                start_beat=active_starts[index],
                duration_beats=0.5,
                program=27,
            )
            for index, pitch in enumerate(pitches)
        ],
    )


def test_movable_sus2_arpeggios_receive_expected_symbols():
    track = _track([
        49, 56, 63,
        45, 52, 59,
        47, 54, 61,
        42, 49, 56, 57,
    ])
    fingering = assign_fretting_digits(track, optimize_fingering(track))
    plan = plan_harmony(track, fingering)

    assert [item.symbol for item in plan.decisions] == [
        "C#sus2", "Asus2", "Bsus2", "F#sus2",
    ]
    assert [item.note_indices for item in plan.decisions] == [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (9, 10, 11),
    ]


def test_simultaneous_major_triad_receives_chord_symbol():
    track = _track([52, 56, 59], starts=[0.0, 0.0, 0.0])
    fingering = assign_fretting_digits(track, optimize_fingering(track))
    plan = plan_harmony(track, fingering)

    assert len(plan.decisions) == 1
    assert plan.decisions[0].symbol == "E"
    assert plan.decisions[0].quality == "major"
    assert plan.decisions[0].confidence == 0.96
