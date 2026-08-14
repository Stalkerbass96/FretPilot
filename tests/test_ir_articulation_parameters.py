from fretpilot.analysis import analyze_guitar_track
from fretpilot.articulation.models import ArticulationDecision
from fretpilot.ir import build_guitar_ir
from fretpilot.midi.models import NormalizedNote, NormalizedTimeline, NormalizedTrack, TempoEvent, TimeSignatureEvent


def test_builder_preserves_articulation_parameters():
    note = NormalizedNote(0, "Guitar", 0, 64, 90, 0, 480, 0.0, 1.0, 29)
    track = NormalizedTrack(0, "Guitar", [note])
    timeline = NormalizedTimeline(
        "fixture.mid", 1, 480,
        [TempoEvent(0, 0.0, 120.0)],
        [TimeSignatureEvent(0, 0.0, 4, 4)],
        [track],
    )
    analysis = analyze_guitar_track(track)
    analysis.articulations.decisions.append(
        ArticulationDecision(
            note_index=0,
            technique="pitch_raise",
            confidence=0.9,
            reason="fixture",
            parameters={"semitones": 1.0, "peak_position": 0.25},
        )
    )
    project = build_guitar_ir(timeline, track, analysis)
    articulation = next(
        item for item in project.tracks[0].measures[0].events[0].articulations
        if item.type == "pitch_raise"
    )
    assert articulation.parameters == {"semitones": 1.0, "peak_position": 0.25}
