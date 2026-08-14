from fretpilot.ir.models import GuitarMeasure, GuitarNoteEvent, GuitarProjectIR, GuitarTrackIR, IRFingering, IRTempoEvent, IRTimeSignatureEvent, PerformanceTiming, ScoreTiming
from fretpilot.performance import build_performance_plan


def test_neutral_plan_keeps_source_values():
    event = GuitarNoteEvent(
        "n1", 0, 64,
        ScoreTiming(0.0, 0.5, 1, 0.0),
        PerformanceTiming(0.03, 0.55, 80),
        IRFingering(2, 5),
    )
    project = GuitarProjectIR(
        "p", "fixture.mid",
        [IRTempoEvent(0.0, 120.0)],
        [IRTimeSignatureEvent(0.0, 4, 4)],
        [GuitarTrackIR(
            "g1", "Guitar", None, "riff", [40, 45, 50, 55, 59, 64], 24,
            [GuitarMeasure(1, 0.0, 4.0, 4, 4, [event])],
            {"performance": {
                "timing_looseness": 1.0,
                "velocity_variation": 1.0,
                "note_overlap": 1.0,
                "accent_strength": 1.0,
            }},
        )],
    )
    note = build_performance_plan(project).notes[0]
    assert note.target_start_beat == 0.03
    assert note.target_duration_beats == 0.55
    assert note.target_velocity == 80
    assert note.reasons == []
