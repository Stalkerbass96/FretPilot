from __future__ import annotations

from fretpilot.detection.models import BehaviorProfileMatch
from fretpilot.knowledge import (
    BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION,
    compose_playing_context,
    context_from_behavior_matches,
    match_behavior_profiles,
)


def _match(profile_id: str, score: float) -> BehaviorProfileMatch:
    return BehaviorProfileMatch(
        profile_id=profile_id,
        label=profile_id,
        score=score,
        status="strong" if score >= 0.75 else "possible",
    )


def test_role_and_style_are_composed_instead_of_flattened() -> None:
    context = compose_playing_context({"solo": 0.9, "metal": 0.8})
    assert context.role_scores == {"solo": 0.9}
    assert context.style_scores == {"metal": 0.8}
    assert context.source_profiles == ["solo", "metal"]
    assert context.knowledge_version == BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION
    assert context.knowledge_entry_ids == ["gk.profile.solo", "gk.profile.metal"]
    assert context.articulation.vibrato > 1.0
    assert context.fingering.low_register_bias > 1.0


def test_breakdown_behavior_maps_to_metal_riff_context() -> None:
    context = context_from_behavior_matches([_match("breakdown", 0.82)])
    assert context.role_scores["riff"] == 0.82
    assert context.style_scores["metal"] == 0.82
    assert context.articulation.palm_mute > 1.0
    assert context.fingering.shape_reuse > 1.0


def test_jazz_comping_maps_to_style_plus_role() -> None:
    context = context_from_behavior_matches([_match("jazz_comping", 0.76)])
    assert context.role_scores["strumming"] == 0.76
    assert context.style_scores["jazz"] == 0.76
    assert context.fingering.compact_chord_voicing > 1.0


def test_explicit_style_can_be_combined_with_detected_solo() -> None:
    context = context_from_behavior_matches(
        [_match("solo", 0.88)],
        explicit_styles={"metal": 0.95},
    )
    assert context.role_scores["solo"] == 0.88
    assert context.style_scores["metal"] == 0.95
    assert set(context.source_profiles) == {"solo", "metal"}


def test_broken_chord_texture_matches_arpeggio_profile() -> None:
    matches = match_behavior_profiles({
        "monophonic_onset_ratio": 0.73,
        "chord_onset_ratio": 0.27,
        "mean_onset_polyphony": 1.27,
        "adjacent_interval_within_octave_ratio": 0.80,
        "repeated_pitch_ratio": 0.0,
        "short_note_ratio": 0.32,
        "pitch_range_semitones": 39,
        "max_onset_polyphony": 3,
        "low_register_ratio": 0.35,
    })
    arpeggio = next(item for item in matches if item.profile_id == "arpeggio")
    assert arpeggio.score == 1.0
    assert arpeggio.status == "strong"
