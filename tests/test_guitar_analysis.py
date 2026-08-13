from __future__ import annotations

from fretpilot.analysis import analyze_guitar_track
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def test_analysis_combines_rhythm_fingering_and_articulation() -> None:
    onsets = [0.02, 0.49, 1.01]
    pitches = [64, 66, 71]
    durations = [0.47, 0.50, 1.50]

    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Lead Guitar",
            channel=0,
            pitch=pitch,
            velocity=90,
            start_tick=round(onsets[index] * 480),
            duration_ticks=round(durations[index] * 480),
            start_beat=onsets[index],
            duration_beats=durations[index],
        )
        for index, pitch in enumerate(pitches)
    ]
    track = NormalizedTrack(index=0, name="Lead Guitar", notes=notes)

    analysis = analyze_guitar_track(track)

    assert analysis.rhythm.selected_grid.name == "eighth"
    assert all(note.playable for note in analysis.fingering.notes)
    assert any(
        decision.technique == "hammer_on"
        for decision in analysis.articulations.decisions
    )
    assert any(
        decision.technique == "slide"
        for decision in analysis.articulations.decisions
    )
    assert any(
        decision.technique == "vibrato"
        for decision in analysis.articulations.decisions
    )
