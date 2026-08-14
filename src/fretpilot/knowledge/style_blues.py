"""Evidence-backed blues guitar priors."""

from __future__ import annotations

BLUES_STYLE_KNOWLEDGE = {
    "version": "0.1",
    "lead": {
        "shape_reuse": 1.35,
        "same_string_legato": 1.20,
        "bend": 1.55,
        "vibrato": 1.50,
        "slide": 1.25,
        "timing_looseness": 1.15,
        "strategy": "movable_blues_positions_with_expressive_articulation",
    },
    "rhythm": {
        "compact_two_string_shapes": 1.30,
        "shape_reuse": 1.35,
        "rhythmic_pattern_reuse": 1.35,
        "strategy": "repeated_compact_shuffle_shapes",
    },
    "source_ids": ("fender-blues-scale", "bontempi-rich-tab-2024"),
}
