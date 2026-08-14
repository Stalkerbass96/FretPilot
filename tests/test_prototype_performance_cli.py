import json
from pathlib import Path

from fretpilot.midi.models import NormalizedNote, NormalizedTimeline, NormalizedTrack, TempoEvent, TimeSignatureEvent
from fretpilot.prototype_performance_cli import generate_prototype_with_performance


def test_prototype_performance_command_writes_sidecar(tmp_path: Path):
    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Guitar",
            channel=0,
            pitch=40,
            velocity=95,
            start_tick=i * 120,
            duration_ticks=96,
            start_beat=i * 0.25,
            duration_beats=0.2,
            program=29,
        )
        for i in range(16)
    ]
    timeline = NormalizedTimeline(
        source="riff.mid",
        midi_type=1,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(0, 0.0, 120.0)],
        time_signature_events=[TimeSignatureEvent(0, 0.0, 4, 4)],
        tracks=[NormalizedTrack(0, "Guitar", notes)],
    )

    manifest, sidecars, index = generate_prototype_with_performance(
        timeline,
        tmp_path / "out",
    )

    assert manifest.stream_results[0].guitar_ir.status == "success"
    assert sidecars[0]["status"] == "success"
    sidecar_path = Path(sidecars[0]["path"])
    assert sidecar_path.exists()
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert payload["notes"]
    assert payload["sections"]
    assert index.exists()
