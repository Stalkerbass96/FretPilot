from fretpilot.analysis import analyze_guitar_track_by_sections
from fretpilot.analysis.section_contexts import SectionContextAnalysis
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def test_section_analysis_has_right_hand_plan():
    notes = [NormalizedNote(0, "Guitar", 0, 40, 90, i * 120, 96, i * 0.25, 0.2, 29) for i in range(4)]
    track = NormalizedTrack(0, "Guitar", notes)
    section = SectionContextAnalysis(
        "s1", "guitar", 1, 1, 0.0, 1.0, [],
        compose_playing_context({"riff": 1.0, "metal": 1.0}),
    )
    result = analyze_guitar_track_by_sections(track, [section])
    assert result.picking is not None
    assert [item.direction for item in result.picking.decisions] == ["down"] * 4
