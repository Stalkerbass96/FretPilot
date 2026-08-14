"""Metal guitar priors distilled from cited educational sources."""

METAL_PRIORS = {
    "shape_reuse": 1.50,
    "hand_position_stability": 1.40,
    "palm_mute": 1.60,
    "staccato": 1.35,
    "power_chord_bias": 1.45,
    "downpicking_bias": 1.35,
    "note_overlap": 0.70,
    "timing_looseness": 0.65,
    "source_ids": ("fender-palm-mute", "fender-picking-styles"),
}
