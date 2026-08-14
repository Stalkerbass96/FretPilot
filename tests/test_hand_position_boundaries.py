from fretpilot.analysis import analyze_guitar_track_by_sections
from fretpilot.analysis.section_contexts import SectionContextAnalysis
from fretpilot.knowledge.playing_contexts import FingeringPreferences, PlayingContext
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def _note(pitch, beat):
    return NormalizedNote(0, "Guitar", 0, pitch, 90, round(beat * 480), 240, beat, 0.5, 27)


def _section(section_id, start, end, context, strength):
    return SectionContextAnalysis(
        section_id=section_id,
        stream_id="guitar",
        start_measure=int(start // 4) + 1,
        end_measure=int((end - 1e-9) // 4) + 1,
        start_beat=start,
        end_beat=end,
        behavior_profiles=[],
        playing_context=context,
        boundary_strength=strength,
        boundary_reason="fixture",
    )


def _analyze(second_boundary_strength):
    track = NormalizedTrack(
        0,
        "Guitar",
        [_note(64, 0.0), _note(66, 0.5), _note(66, 4.0), _note(67, 4.5)],
    )
    closed = PlayingContext(fingering=FingeringPreferences(open_string_usage=0.0))
    open_friendly = PlayingContext(fingering=FingeringPreferences(open_string_usage=1.0))
    sections = [
        _section("s1", 0.0, 4.0, closed, 0.0),
        _section("s2", 4.0, 8.0, open_friendly, second_boundary_strength),
    ]
    return analyze_guitar_track_by_sections(track, sections)


def test_weak_boundary_carries_real_fingering_position():
    result = _analyze(0.5)
    assert [(n.string, n.fret) for n in result.fingering.notes[:2]] == [(2, 5), (2, 7)]
    assert [(n.string, n.fret) for n in result.fingering.notes[2:]] == [(2, 7), (2, 8)]
    assert result.hand_positions[1].carried_from_previous is True
    assert result.hand_positions[1].transition_reason == "carry_across_weak_section_boundary"


def test_strong_boundary_allows_local_position_reset():
    result = _analyze(2.0)
    assert [(n.string, n.fret) for n in result.fingering.notes[2:]] == [(1, 2), (1, 3)]
    assert result.hand_positions[1].carried_from_previous is False
    assert result.hand_positions[1].transition_reason == "reset_at_strong_section_boundary"
