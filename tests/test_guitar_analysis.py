from __future__ import annotations

from fretpilot.analysis import analyze_guitar_track
from fretpilot.knowledge import compose_playing_context
from fretpilot.midi.models import NormalizedNote, NormalizedTrack


def _track(
    pitches: list[int],
    *,
    onsets: list[float] | None = None,
    durations: list[float] | None = None,
) -> NormalizedTrack:
    active_onsets = onsets or [index * 0.5 for index in range(len(pitches))]
    active_durations = durations or [0.5] * len(pitches)
    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Lead Guitar",
            channel=0,
            pitch=pitch,
            velocity=90,
            start_tick=round(active_onsets[index] * 480),
            duration_ticks=round(active_durations[index] * 480),
            start_beat=active_onsets[index],
            duration_beats=active_durations[index],
        )
        for index, pitch in enumerate(pitches)
    ]
    return NormalizedTrack(index=0, name="Lead Guitar", notes=notes)


def test_analysis_combines_rhythm_fingering_and_articulation() -> None:
    track = _track(
        [64, 66, 71],
        onsets=[0.02, 0.49, 1.01],
        durations=[0.47, 0.50, 1.50],
    )

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


def test_analysis_threads_explicit_playing_context_into_fingering() -> None:
    track = _track([64, 66, 67, 69])
    context = compose_playing_context({"solo": 1.0})

    analysis = analyze_guitar_track(track, playing_context=context)

    assert analysis.playing_context is context
    assert analysis.to_dict()["playing_context"]["role_scores"] == {"solo": 1.0}
    assert [(note.string, note.fret) for note in analysis.fingering.notes] == [
        (2, 5),
        (2, 7),
        (2, 8),
        (2, 10),
    ]
