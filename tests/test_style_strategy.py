from fretpilot.analysis.style_inference import infer_style_from_features
from fretpilot.knowledge.context_strategy import apply_style_scores_to_context
from fretpilot.knowledge.playing_contexts import compose_playing_context


def _features(**overrides):
    values = {
        "monophonic_onset_ratio": 0.7,
        "chord_onset_ratio": 0.2,
        "repeated_pitch_ratio": 0.18,
        "low_register_ratio": 0.65,
        "short_note_ratio": 0.7,
        "adjacent_interval_within_octave_ratio": 0.9,
        "mean_onset_polyphony": 1.3,
        "pitch_range_semitones": 18,
    }
    values.update(overrides)
    return values


def test_driven_low_riff_prefers_metal_over_jazz():
    result = infer_style_from_features(_features(), program=30)
    assert result.style_scores["metal"] > result.style_scores["jazz"]
    assert result.style_scores["metal"] >= 0.7


def test_rock_strategy_changes_riff_fingering_preferences():
    context = compose_playing_context({"riff": 0.8})
    before = context.fingering.shape_reuse

    strategy = apply_style_scores_to_context(context, {"rock": 0.8})

    assert context.fingering.shape_reuse > before
    assert strategy.styles["rock"] == 0.8
    assert "strategy:rock" in context.source_profiles
