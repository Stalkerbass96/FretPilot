from __future__ import annotations

import json
from pathlib import Path

from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)
from fretpilot.prototype import generate_prototype_package


def _note(
    *,
    channel: int,
    program: int,
    pitch: int,
    start_beat: float,
) -> NormalizedNote:
    ticks_per_beat = 480
    return NormalizedNote(
        track_index=0,
        track_name="Arrangement",
        channel=channel,
        pitch=pitch,
        velocity=90,
        start_tick=round(start_beat * ticks_per_beat),
        duration_ticks=240,
        start_beat=start_beat,
        duration_beats=0.5,
        program=program,
    )


def test_all_likely_guitars_receive_complete_output_packages(tmp_path: Path) -> None:
    notes = []
    for index, pitch in enumerate([64, 66, 67, 69, 67, 66, 64, 64]):
        notes.append(
            _note(
                channel=0,
                program=27,
                pitch=pitch,
                start_beat=index * 0.5,
            )
        )
    for index, pitch in enumerate([52, 52, 55, 57, 55, 52, 50, 52]):
        notes.append(
            _note(
                channel=1,
                program=29,
                pitch=pitch,
                start_beat=index * 0.5,
            )
        )

    timeline = NormalizedTimeline(
        source="multi-guitar.mid",
        midi_type=0,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(tick=0, beat=0.0, bpm=120.0)],
        time_signature_events=[
            TimeSignatureEvent(
                tick=0,
                beat=0.0,
                numerator=4,
                denominator=4,
            )
        ],
        tracks=[
            NormalizedTrack(
                index=0,
                name="Arrangement",
                notes=sorted(notes, key=lambda item: (item.start_tick, item.channel)),
            )
        ],
    )

    output = tmp_path / "prototype"
    manifest = generate_prototype_package(
        timeline,
        output,
        all_likely_guitars=True,
    )

    assert len(manifest.selected_stream_ids) == 2
    assert (output / "manifest.json").exists()

    for result in manifest.stream_results:
        assert result.analysis.status == "success"
        assert result.rewrite.status == "success"
        assert result.guitar_ir.status == "success"
        assert result.pdf.status == "success"
        assert result.gp5.status == "success"
        assert result.ample_sc_midi.status == "success"
        assert result.report.status == "success"
        assert result.analysis.path and Path(result.analysis.path).exists()
        assert result.rewrite.path and Path(result.rewrite.path).exists()
        assert result.guitar_ir.path and Path(result.guitar_ir.path).exists()
        assert result.pdf.path and Path(result.pdf.path).exists()
        assert result.gp5.path and Path(result.gp5.path).exists()
        assert result.ample_sc_midi.path and Path(result.ample_sc_midi.path).exists()
        assert result.report.path and Path(result.report.path).exists()

        analysis_payload = json.loads(Path(result.analysis.path).read_text(encoding="utf-8"))
        rewrite_payload = json.loads(Path(result.rewrite.path).read_text(encoding="utf-8"))
        report_payload = json.loads(Path(result.report.path).read_text(encoding="utf-8"))
        assert analysis_payload["section_contexts"]
        assert rewrite_payload["midi_fidelity"] == 0.35
        assert rewrite_payload["original_note_count"] == 8
        assert report_payload["sections"]["count"] >= 1
        assert report_payload["sections"]["items"]
        assert report_payload["note_rewrite"]["midi_fidelity"] == 0.35
        assert report_payload["fingering"]["hand_position_plan"]["sections"]
        assert report_payload["guitar_ir"]["voice_counts"]["1"] > 0
        assert report_payload["outputs"]["pdf"]["status"] == "success"
