from __future__ import annotations

from fretpilot.midi.models import NormalizedNote, NormalizedTrack
from fretpilot.rhythm import analyze_track_rhythm


def _track_with_onsets(onsets: list[float]) -> NormalizedTrack:
    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Lead Guitar",
            channel=0,
            pitch=60 + index,
            velocity=90,
            start_tick=round(onset * 480),
            duration_ticks=120,
            start_beat=onset,
            duration_beats=0.25,
        )
        for index, onset in enumerate(onsets)
    ]
    return NormalizedTrack(index=0, name="Lead Guitar", notes=notes)


def test_humanized_eighth_notes_choose_eighth_grid() -> None:
    track = _track_with_onsets([0.02, 0.49, 1.01, 1.51])

    analysis = analyze_track_rhythm(track)

    assert analysis.selected_grid.name == "eighth"
    assert analysis.suggestions[0].target_start_beat == 0.0
    assert analysis.suggestions[1].target_start_beat == 0.5
    assert analysis.suggestions[2].target_start_beat == 1.0
    assert analysis.suggestions[3].target_start_beat == 1.5
    assert all(suggestion.confidence > 0.9 for suggestion in analysis.suggestions)


def test_triplet_phrase_prefers_triplet_grid() -> None:
    track = _track_with_onsets([0.01, 0.34, 0.67, 1.0, 1.34])

    analysis = analyze_track_rhythm(track)

    assert analysis.selected_grid.name == "eighth_triplet"
    assert analysis.selected_grid.family == "triplet"
    assert analysis.grid_scores[0].profile.name == "eighth_triplet"


def test_finer_grid_does_not_win_when_coarser_grid_fits() -> None:
    track = _track_with_onsets([0.0, 0.5, 1.0, 1.5])

    analysis = analyze_track_rhythm(track)

    assert analysis.selected_grid.name == "eighth"
    sixteenth = next(
        score for score in analysis.grid_scores if score.profile.name == "sixteenth"
    )
    eighth = next(
        score for score in analysis.grid_scores if score.profile.name == "eighth"
    )
    assert eighth.mean_absolute_error_beats == sixteenth.mean_absolute_error_beats
    assert eighth.objective < sixteenth.objective
