from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
    IRFingering,
    IRRightHandIntent,
    PerformanceTiming,
    ScoreTiming,
)
from fretpilot.ir.serde import project_from_dict


def test_project_dict_round_trip_keeps_guitar_metadata():
    event = GuitarNoteEvent(
        "n1", 0, 64,
        ScoreTiming(0.0, 0.5, 1, 0.0),
        PerformanceTiming(0.0, 0.5, 90),
        IRFingering(2, 5, 3),
        right_hand=IRRightHandIntent(
            "pick", "down", 0.9, "fixture", "sweep"
        ),
    )
    project = GuitarProjectIR(
        "song", "song.mid", [], [],
        [GuitarTrackIR(
            "g1", "Guitar", "s1", "riff", [40, 45, 50, 55, 59, 64], 24,
            [GuitarMeasure(1, 0.0, 4.0, 4, 4, [event])],
            section_contexts=[{"section_id": "s1"}],
            hand_positions=[{"section_id": "s1", "min_fret": 5}],
        )],
    )
    restored = project_from_dict(project.to_dict())
    assert restored.to_dict() == project.to_dict()
    restored_event = restored.tracks[0].measures[0].events[0]
    assert restored_event.fingering.fretting_digit == 3
    assert restored_event.right_hand.technique == "sweep"
