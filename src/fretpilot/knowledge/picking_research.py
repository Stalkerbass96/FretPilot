"""Picking-family priors distilled from cited educational sources."""

PICKING_RESEARCH = {
    "alternate": {
        "fast_single_note_bias": 1.25,
        "fluid_scale_run_bias": 1.25,
    },
    "downstroke": {
        "tight_repeated_rhythm_bias": 1.50,
        "short_attack_bias": 1.20,
    },
    "tremolo": {
        "rapid_repeated_pitch_bias": 1.60,
    },
    "sweep": {
        "adjacent_string_arpeggio": 1.70,
        "shape_reuse": 1.45,
    },
    "hybrid": {
        "bass_treble_separation": 1.25,
        "string_skip_bias": 1.20,
    },
    "source_ids": ("fender-picking-styles",),
}
