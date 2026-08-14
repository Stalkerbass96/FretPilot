"""Jazz guitar voicing priors distilled from cited research."""

JAZZ_VOICING_PRIORS = {
    "voice_leading_weight": 1.6,
    "previous_voicing_context": True,
    "moveable_voicing_family_bias": 1.45,
    "open_string_usage": 0.6,
    "source_ids": ("kunjara-drop2-2025", "dhooge-chord-context-2024"),
}
