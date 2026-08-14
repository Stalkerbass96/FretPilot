from fretpilot.guitar.models import FingeredNote, FingeringResult
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import NormalizedNote, NormalizedTrack
from fretpilot.picking import plan_picking


def _note(pitch, start, duration):
    return NormalizedNote(
        track_index=0,
        track_name="Guitar",
        channel=0,
        pitch=pitch,
        velocity=90,
        start_tick=round(start * 480),
        duration_ticks=round(duration * 480),
        start_beat=start,
        duration_beats=duration,
        program=27,
    )


def _fingering(track, strings, frets):
    return FingeringResult(
        track_index=0,
        track_name="Guitar",
        tuning="fixture",
        max_fret=24,
        notes=[
            FingeredNote(
                note_index=i,
                pitch=note.pitch,
                start_beat=note.start_beat,
                duration_beats=note.duration_beats,
                string=strings[i],
                fret=frets[i],
            )
            for i, note in enumerate(track.notes)
        ],
    )


def test_staggered_overlapping_chord_uses_observed_down_strum():
    track = NormalizedTrack(
        0,
        "Guitar",
        [
            _note(45, 0.00, 0.80),
            _note(52, 0.04, 0.80),
            _note(59, 0.08, 0.80),
        ],
    )
    fingering = _fingering(track, [6, 5, 4], [5, 7, 9])
    plan = plan_picking(track, fingering, context=compose_playing_context({}))

    assert len(plan.decisions) == 1
    decision = plan.decisions[0]
    assert decision.note_indices == (0, 1, 2)
    assert decision.motion == "strum"
    assert decision.direction == "down"
    assert decision.technique == "rolled_strum"
    assert decision.confidence >= 0.9


def test_tight_non_overlapping_arpeggio_is_not_rolled_strum():
    track = NormalizedTrack(
        0,
        "Guitar",
        [
            _note(45, 0.00, 0.035),
            _note(52, 0.04, 0.035),
            _note(59, 0.08, 0.035),
        ],
    )
    fingering = _fingering(track, [6, 5, 4], [5, 7, 9])
    plan = plan_picking(
        track,
        fingering,
        context=compose_playing_context({"rock_arpeggio": 1.0}),
    )

    assert not any(item.technique == "rolled_strum" for item in plan.decisions)
