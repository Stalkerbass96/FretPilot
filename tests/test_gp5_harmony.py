from pathlib import Path

import guitarpro as gp

from fretpilot.analysis import analyze_guitar_track
from fretpilot.exporters.guitar_pro import export_gp5
from fretpilot.ir import build_guitar_ir
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)


def test_message_in_a_bottle_harmony_labels_reach_gp5(tmp_path: Path):
    pitches = [
        49, 56, 63,
        45, 52, 59,
        47, 54, 61,
        42, 49, 56, 57,
    ]
    notes = [
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
    ]
    track = NormalizedTrack(0, "Guitar", notes)
    timeline = NormalizedTimeline(
        source="message.mid",
        midi_type=1,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(0, 0.0, 151.0)],
        time_signature_events=[TimeSignatureEvent(0, 0.0, 4, 4)],
        tracks=[track],
    )

    analysis = analyze_guitar_track(track)
    assert [item.symbol for item in analysis.harmony.decisions] == [
        "C#sus2", "Asus2", "Bsus2", "F#sus2",
    ]
    project = build_guitar_ir(timeline, track, analysis)
    assert [item.symbol for item in project.tracks[0].harmony_regions] == [
        "C#sus2", "Asus2", "Bsus2", "F#sus2",
    ]

    output = tmp_path / "message.gp5"
    export_gp5(project, output)
    parsed = gp.parse(output)
    labels = [
        beat.text
        for measure in parsed.tracks[0].measures
        for beat in measure.voices[0].beats
        if beat.text
    ]
    assert labels == ["C#sus2", "Asus2", "Bsus2", "F#sus2"]
