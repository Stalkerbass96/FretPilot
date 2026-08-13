"""Rock/pop guitar priors distilled from cited educational sources."""

ROCK_POP_PRIORS = {
    "rhythm": {
        "shape_reuse": 1.30,
        "power_chord_bias": 1.30,
        "rhythmic_pattern_reuse": 1.25,
        "open_string_usage": 1.00,
    },
    "arpeggio": {
        "adjacent_string_arpeggio": 1.40,
        "shape_reuse": 1.45,
        "let_ring": 1.25,
    },
    "lead": {
        "same_string_legato": 1.20,
        "bend": 1.30,
        "vibrato": 1.30,
        "slide": 1.20,
    },
    "source_ids": ("fender-picking-styles", "fender-blues-scale"),
}
