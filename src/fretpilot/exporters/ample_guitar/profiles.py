"""Versioned virtual-instrument profiles for Ample Guitar output.

Raw MIDI note numbers are stored explicitly to avoid octave-label ambiguity
between DAWs. Ample's documentation labels the common electric-guitar
keyswitches C0 through F#0; in the convention used by the product range this is
MIDI notes 24 through 30, while standard guitar low E remains MIDI note 40.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AmpleGuitarProfile:
    profile_id: str
    product: str
    version_family: str
    keyswitches: dict[str, int]
    playable_min: int
    playable_max: int
    note_channel: int = 0
    keyswitch_velocity: int = 100
    note_off_velocity: int = 64
    keyswitch_length_ticks: int = 12
    legato_overlap_ticks: int = 30
    keyswitch_preroll_ticks: int = 30
    supported_articulations: frozenset[str] = field(default_factory=frozenset)


AMPLE_GUITAR_SC_V4 = AmpleGuitarProfile(
    profile_id="ample-guitar-sc-v4",
    product="Ample Guitar SC",
    version_family="4.x",
    keyswitches={
        "sustain": 24,          # C0 in Ample's displayed octave convention
        "natural_harmonic": 25,  # C#0
        "palm_mute": 26,       # D0
        "slide_in_out": 27,    # D#0
        "legato_slide": 28,    # E0
        "hammer_pull": 29,     # F0
        "slide_guitar": 30,    # F#0
    },
    # Standard-tuned FretPilot V0 notes fall inside this product range. The
    # profile leaves room for Ample's documented drop-D lower extension.
    playable_min=38,
    playable_max=86,
    supported_articulations=frozenset(
        {
            "hammer_on",
            "pull_off",
            "slide",
            "natural_harmonic",
            "palm_mute",
            "slide_in",
            "slide_out",
            "let_ring",
        }
    ),
)


PROFILES = {
    AMPLE_GUITAR_SC_V4.profile_id: AMPLE_GUITAR_SC_V4,
}


def get_profile(profile_id: str) -> AmpleGuitarProfile:
    try:
        return PROFILES[profile_id]
    except KeyError as exc:
        available = ", ".join(sorted(PROFILES))
        raise ValueError(
            f"Unknown Ample Guitar profile {profile_id!r}; available: {available}."
        ) from exc
