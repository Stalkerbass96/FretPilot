from __future__ import annotations

from fretpilot.articulation import plan_articulations
from fretpilot.guitar import optimize_fingering
from fretpilot.knowledge import ArticulationPreferences, compose_playing_context
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


def _decision(plan, technique: str):
    return next(
        decision for decision in plan.decisions if decision.technique == technique
    )


def test_small_connected_ascending_interval_becomes_hammer_on() -> None:
    track = _track([64, 66])
    fingering = optimize_fingering(track)

    plan = plan_articulations(track, fingering)

    decision = _decision(plan, "hammer_on")
    assert decision.note_index == 1
    assert decision.confidence == 0.82


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


def test_articulation_preferences_rank_existing_valid_techniques() -> None:
    track = _track([64, 66])
    fingering = optimize_fingering(track)

    neutral = plan_articulations(track, fingering)
    stronger_legato = plan_articulations(
        track,
        fingering,
        preferences=ArticulationPreferences(hammer_pull=1.35),
    )

    assert _decision(stronger_legato, "hammer_on").confidence > _decision(
        neutral, "hammer_on"
    ).confidence
    assert {decision.technique for decision in stronger_legato.decisions} == {
        decision.technique for decision in neutral.decisions
    }


def test_solo_context_increases_vibrato_confidence_without_changing_eligibility() -> None:
    track = _track([64, 67], durations=[0.5, 1.5])
    context = compose_playing_context({"solo": 1.0})
    fingering = optimize_fingering(track, preferences=context.fingering)

    neutral = plan_articulations(track, fingering)
    solo = plan_articulations(
        track,
        fingering,
        preferences=context.articulation,
    )

    assert _decision(solo, "vibrato").confidence > _decision(
        neutral, "vibrato"
    ).confidence
    assert {decision.technique for decision in solo.decisions} == {
        decision.technique for decision in neutral.decisions
    }
