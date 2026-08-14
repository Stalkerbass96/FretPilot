from pathlib import Path

import mido

from fretpilot.entrypoint import main


def test_standard_prototype_command_writes_performance_sidecars(tmp_path: Path):
    midi_path = tmp_path / "riff.mid"
    midi = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name="Guitar", time=0))
    track.append(mido.Message("program_change", channel=0, program=29, time=0))
    for index in range(16):
        track.append(mido.Message("note_on", channel=0, note=40, velocity=95, time=0 if index == 0 else 24))
        track.append(mido.Message("note_off", channel=0, note=40, velocity=0, time=96))
    midi.tracks.append(track)
    midi.save(midi_path)

    output = tmp_path / "out"
    assert main(["prototype", str(midi_path), "-o", str(output)]) == 0
    assert (output / "manifest.json").exists()
    assert (output / "performance-plans.json").exists()
    sidecars = list(output.glob("**/*.performance-plan.json"))
    assert sidecars
