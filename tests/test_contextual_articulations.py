from fretpilot.articulation import plan_articulations
from fretpilot.guitar import optimize_fingering
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def _riff():
    return NormalizedTrack(
        index=0,
        name="Riff",
        notes=[
            NormalizedNote(
                track_index=0, track_name="Riff", channel=0,
                pitch=pitch, velocity=95, start_tick=index * 240,
                duration_ticks=120, start_beat=index * 0.5, duration_beats=0.25,
            )
            for index, pitch in enumerate([40, 40, 42, 40, 40, 42])
        ],
    )


def test_context_is_required_for_style_heavy_short_note_effects():
    track = _riff()
    fingering = optimize_fingering(track)
    neutral = plan_articulations(track, fingering)
    assert not {"palm_mute", "staccato"}.intersection(
        decision.technique for decision in neutral.decisions
    )


def test_metal_riff_context_enables_evidence_backed_palm_mute_and_staccato():
    track = _riff()
    context = compose_playing_context({"riff": 1.0, "metal": 1.0})
    fingering = optimize_fingering(track, preferences=context.fingering)
    plan = plan_articulations(track, fingering, preferences=context.articulation)
    techniques = {decision.technique for decision in plan.decisions}
    assert "palm_mute" in techniques
    assert "staccato" in techniques
