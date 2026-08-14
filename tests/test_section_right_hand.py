from fretpilot.analysis import analyze_guitar_track_by_sections
from fretpilot.analysis.section_contexts import SectionContextAnalysis
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def _fixture():
    notes = [
        NormalizedNote(0, "Guitar", 0, 40, 90, i * 120, 96, i * 0.25, 0.2, 29)
        for i in range(4)
    ]
    track = NormalizedTrack(0, "Guitar", notes)
    section = SectionContextAnalysis(
        "s1", "guitar", 1, 1, 0.0, 1.0, [],
        compose_playing_context({"riff": 1.0, "metal": 1.0}),
    )
    return track, section


def test_section_analysis_has_right_hand_plan():
    track, section = _fixture()
    result = analyze_guitar_track_by_sections(track, [section])
    assert result.picking is not None
    assert [item.direction for item in result.picking.decisions] == ["down"] * 4


def test_section_override_is_used_by_right_hand_plan():
    track, section = _fixture()
    result = analyze_guitar_track_by_sections(
        track,
        [section],
        context_overrides={"s1": compose_playing_context({})},
    )
    assert result.picking is not None
    assert result.picking.decisions == []
