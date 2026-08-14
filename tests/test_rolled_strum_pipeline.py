from pathlib import Path

import guitarpro as gp

from fretpilot.analysis import analyze_guitar_track_by_sections
from fretpilot.analysis.section_contexts import SectionContextAnalysis
from fretpilot.exporters.guitar_pro import export_gp5
from fretpilot.ir import build_guitar_ir
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)


def test_rolled_strum_survives_analysis_ir_and_gp5(tmp_path: Path):
    starts = [0.0, 0.02, 0.04]
    pitches = [45, 52, 59]
    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Guitar",
            channel=0,
            pitch=pitch,
            velocity=90,
            start_tick=round(starts[i] * 480),
            duration_ticks=384,
            start_beat=starts[i],
            duration_beats=0.8,
            program=27,
        )
        for i, pitch in enumerate(pitches)
    ]
    track = NormalizedTrack(0, "Guitar", notes)
    timeline = NormalizedTimeline(
        source="rolled.mid",
        midi_type=1,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(0, 0.0, 120.0)],
        time_signature_events=[TimeSignatureEvent(0, 0.0, 4, 4)],
        tracks=[track],
    )
    section = SectionContextAnalysis(
        section_id="s1",
        stream_id="guitar",
        start_measure=1,
        end_measure=1,
        start_beat=0.0,
        end_beat=4.0,
        behavior_profiles=[],
        playing_context=compose_playing_context({}),
    )

    analysis = analyze_guitar_track_by_sections(track, [section])
    decision = next(item for item in analysis.picking.decisions if item.technique == "rolled_strum")
    assert decision.note_indices == (0, 1, 2)
    assert decision.direction == "down"

    project = build_guitar_ir(timeline, track, analysis)
    events = project.tracks[0].measures[0].events
    assert len({event.score.start_beat for event in events}) == 1
    assert all(event.right_hand.technique == "rolled_strum" for event in events)

    output = tmp_path / "rolled.gp5"
    export_gp5(project, output)
    beat = next(
        beat
        for beat in gp.parse(output).tracks[0].measures[0].voices[0].beats
        if beat.notes
    )
    assert beat.effect.stroke.direction == gp.BeatStrokeDirection.down
    assert beat.effect.pickStroke == gp.BeatStrokeDirection.none
