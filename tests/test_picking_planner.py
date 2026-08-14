from fretpilot.guitar import optimize_fingering
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import NormalizedNote, NormalizedTrack
from fretpilot.picking import plan_picking


def _note(pitch: int, start: float, duration: float = 0.2) -> NormalizedNote:
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
        program=29,
    )


def _track(notes: list[NormalizedNote]) -> NormalizedTrack:
    return NormalizedTrack(index=0, name="Guitar", notes=notes)


def test_neutral_context_does_not_invent_pick_direction() -> None:
    track = _track([_note(52, 0.0), _note(54, 0.25), _note(55, 0.5)])
    plan = plan_picking(track, optimize_fingering(track), context=None)
    assert plan.decisions == []


def test_metal_riff_repeated_low_notes_prefer_downstrokes() -> None:
    track = _track([_note(40, i * 0.25) for i in range(4)])
    context = compose_playing_context({"riff": 1.0, "metal": 1.0})
    fingering = optimize_fingering(track, preferences=context.fingering)
    plan = plan_picking(track, fingering, context=context)

    assert [item.attack for item in plan.decisions] == ["pick"] * 4
    assert [item.direction for item in plan.decisions] == ["down"] * 4


def test_arpeggio_context_uses_alternate_pick_direction() -> None:
    track = _track([
        _note(49, 0.0, 0.45),
        _note(56, 0.5, 0.45),
        _note(63, 1.0, 0.45),
        _note(56, 1.5, 0.45),
    ])
    context = compose_playing_context({"rock_arpeggio": 1.0})
    fingering = optimize_fingering(track, preferences=context.fingering)
    plan = plan_picking(track, fingering, context=context)

    assert [item.direction for item in plan.decisions] == ["down", "up", "down", "up"]
    assert all(item.attack == "pick" for item in plan.decisions)


def test_strumming_context_emits_chord_level_strum_intent() -> None:
    track = _track([
        _note(52, 0.0, 0.45), _note(59, 0.0, 0.45), _note(64, 0.0, 0.45),
        _note(54, 0.5, 0.45), _note(61, 0.5, 0.45), _note(66, 0.5, 0.45),
    ])
    context = compose_playing_context({"strumming": 1.0})
    fingering = optimize_fingering(track, preferences=context.fingering)
    plan = plan_picking(track, fingering, context=context)

    assert len(plan.decisions) == 2
    assert plan.decisions[0].note_indices == (0, 1, 2)
    assert plan.decisions[1].note_indices == (3, 4, 5)
    assert [item.attack for item in plan.decisions] == ["strum", "strum"]
    assert [item.direction for item in plan.decisions] == ["down", "up"]
