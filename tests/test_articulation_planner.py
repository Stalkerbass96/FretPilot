from __future__ import annotations

from fretpilot.articulation import plan_articulations
from fretpilot.guitar import optimize_fingering
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def _track(pitches: list[int], durations: list[float] | None = None) -> NormalizedTrack:
    durations = durations or [0.5] * len(pitches)
    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Lead Guitar",
            channel=0,
            pitch=pitch,
            velocity=90,
            start_tick=index * 240,
            duration_ticks=round(durations[index] * 480),
            start_beat=index * 0.5,
            duration_beats=durations[index],
        )
        for index, pitch in enumerate(pitches)
    ]
    return NormalizedTrack(index=0, name="Lead Guitar", notes=notes)


def test_small_connected_ascending_interval_becomes_hammer_on() -> None:
    track = _track([64, 66])
    fingering = optimize_fingering(track)

    plan = plan_articulations(track, fingering)

    assert any(
        decision.note_index == 1 and decision.technique == "hammer_on"
        for decision in plan.decisions
    )


def test_small_connected_descending_interval_becomes_pull_off() -> None:
    track = _track([67, 65])
    fingering = optimize_fingering(track)

    plan = plan_articulations(track, fingering)

    assert any(
        decision.note_index == 1 and decision.technique == "pull_off"
        for decision in plan.decisions
    )


def test_larger_same_string_motion_can_become_slide() -> None:
    track = _track([64, 69])
    fingering = optimize_fingering(track)

    plan = plan_articulations(track, fingering)

    assert any(
        decision.note_index == 1 and decision.technique == "slide"
        for decision in plan.decisions
    )


def test_long_phrase_ending_note_gets_vibrato() -> None:
    track = _track([64, 67], durations=[0.5, 1.5])
    fingering = optimize_fingering(track)

    plan = plan_articulations(track, fingering)

    assert any(
        decision.note_index == 1 and decision.technique == "vibrato"
        for decision in plan.decisions
    )
