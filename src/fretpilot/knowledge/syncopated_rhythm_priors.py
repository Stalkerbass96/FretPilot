"""Priors for syncopated chordal rhythm guitar."""

SYNCOPATED_RHYTHM_PRIORS = {
    "voicing_continuity": 1.35,
    "compact_chord_voicing": 1.30,
    "syncopation_preservation": 1.45,
    "accent_strength": 1.30,
    "short_release_bias": 1.35,
    "muted_attack_bias": 1.25,
    "source_ids": ("fender-rnb-soul",),
}
