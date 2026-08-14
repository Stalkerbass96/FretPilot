from fretpilot.analysis.section_contexts import SectionContextAnalysis
from fretpilot.guitar import optimize_fingering
from fretpilot.guitar.fretting_digits import assign_fretting_digits
from fretpilot.harmony import plan_harmony, plan_harmony_by_sections
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def _track():
    pitches = [49, 56, 63]
    return NormalizedTrack(
        index=0,
        name="Guitar",
        notes=[
            NormalizedNote(
                track_index=0,
                track_name="Guitar",
                channel=0,
                pitch=pitch,
                velocity=90,
                start_tick=index * 240,
                duration_ticks=240,
                start_beat=index * 0.5,
                duration_beats=0.5,
                program=27,
            )
            for index, pitch in enumerate(pitches)
        ],
    )


def _section(section_id, start, end):
    return SectionContextAnalysis(
        section_id=section_id,
        stream_id="guitar",
        start_measure=1,
        end_measure=1,
        start_beat=start,
        end_beat=end,
        behavior_profiles=[],
        playing_context=compose_playing_context({}),
    )


def test_section_boundary_prevents_cross_boundary_chord_label():
    track = _track()
    fingering = assign_fretting_digits(track, optimize_fingering(track))
    assert [item.symbol for item in plan_harmony(track, fingering).decisions] == ["C#sus2"]

    split = plan_harmony_by_sections(
        track,
        fingering,
        [_section("s1", 0.0, 0.75), _section("s2", 0.75, 2.0)],
    )
    assert split.decisions == []


def test_same_section_allows_arpeggio_harmony_label():
    track = _track()
    fingering = assign_fretting_digits(track, optimize_fingering(track))
    plan = plan_harmony_by_sections(
        track,
        fingering,
        [_section("s1", 0.0, 2.0)],
    )
    assert [item.symbol for item in plan.decisions] == ["C#sus2"]
    assert plan.decisions[0].note_indices == (0, 1, 2)
