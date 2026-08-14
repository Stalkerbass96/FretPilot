import json
from pathlib import Path

import mido

from fretpilot.cli import main as cli_main
from fretpilot.entrypoint import main


def test_console_entrypoint_uses_the_cli_implementation():
    assert main is cli_main


def test_standard_prototype_command_writes_performance_and_vi_sidecars(tmp_path: Path):
    midi_path = tmp_path / "riff.mid"
    midi = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name="Guitar", time=0))
    track.append(mido.Message("program_change", channel=0, program=29, time=0))
    for index in range(16):
        track.append(
            mido.Message(
                "note_on",
                channel=0,
                note=40,
                velocity=95,
                time=0 if index == 0 else 24,
            )
        )
        track.append(
            mido.Message(
                "note_off",
                channel=0,
                note=40,
                velocity=0,
                time=96,
            )
        )
    midi.tracks.append(track)
    midi.save(midi_path)

    output = tmp_path / "out"
    assert main(["prototype", str(midi_path), "-o", str(output)]) == 0
    assert (output / "manifest.json").exists()

    performance_index = output / "performance-plans.json"
    assert performance_index.exists()
    performance_payload = json.loads(performance_index.read_text(encoding="utf-8"))
    assert performance_payload["performance_plans"]
    assert performance_payload["performance_plans"][0]["status"] == "success"
    assert list(output.glob("**/*.performance-plan.json"))

    capability_index = output / "vi-capabilities.json"
    assert capability_index.exists()
    capability_index_payload = json.loads(
        capability_index.read_text(encoding="utf-8")
    )
    assert capability_index_payload["profile_id"] == "ample-guitar-sc-v4"
    assert capability_index_payload["capability_reports"]
    capability_entry = capability_index_payload["capability_reports"][0]
    assert capability_entry["status"] == "success"
    assert capability_entry["profile_id"] == "ample-guitar-sc-v4"
    assert capability_entry["performance_plan_included"] is True

    capability_sidecars = list(output.glob("**/*.vi-capabilities.json"))
    assert capability_sidecars
    capability_payload = json.loads(
        capability_sidecars[0].read_text(encoding="utf-8")
    )
    assert capability_payload["profile_id"] == "ample-guitar-sc-v4"
    assert "requirements" in capability_payload
    assert set(capability_payload["summary"]) == {
        "native_occurrences",
        "approximated_occurrences",
        "unsupported_occurrences",
    }
