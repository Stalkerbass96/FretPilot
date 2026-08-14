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


def _plan(track):
    fingering = assign_fretting_digits(track, optimize_fingering(track))
    return plan_harmony(track, fingering)


def test_simultaneous_first_inversion_major_triad_uses_slash_symbol():
    track = _track([52, 55, 60], starts=[0.0, 0.0, 0.0])
    plan = _plan(track)
    assert len(plan.decisions) == 1
    assert plan.decisions[0].symbol == "C/E"
    assert plan.decisions[0].root_pitch_class == 0


def test_octave_closed_sequential_triad_keeps_single_chord_label():
    track = _track([48, 52, 55, 60])
    plan = _plan(track)
    assert len(plan.decisions) == 1
    assert plan.decisions[0].symbol == "C"
    assert plan.decisions[0].note_indices == (0, 1, 2, 3)


def test_repeated_interior_tone_does_not_expand_previous_triad_cell():
    track = _track([45, 52, 59, 59, 54, 61])
    plan = _plan(track)
    assert plan.decisions[0].symbol == "Asus2"
    assert plan.decisions[0].note_indices == (0, 1, 2)
