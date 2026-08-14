"""Thin compatibility view from generic VI knowledge to the legacy Ample renderer.

The legacy renderer expects a small attribute-oriented profile.  This module
constructs that view from ``VirtualGuitarInstrumentProfile`` without changing
render scheduling or placing product controls into canonical Guitar IR.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from fretpilot.exporters.ample_guitar.profiles import AmpleGuitarProfile
from fretpilot.virtual_instruments.models import VirtualGuitarInstrumentProfile


@runtime_checkable
class AmpleRendererProfile(Protocol):
    profile_id: str
    product: str
    version_family: str
    keyswitches: dict[str, int]
    playable_min: int
    playable_max: int
    note_channel: int
    keyswitch_velocity: int
    note_off_velocity: int
    keyswitch_length_ticks: int
    legato_overlap_ticks: int
    keyswitch_preroll_ticks: int


@dataclass(frozen=True, slots=True)
class GenericAmpleRendererProfile:
    """Legacy-renderer-compatible immutable projection of generic profile data."""

    profile_id: str
    product: str
    version_family: str
    keyswitches: dict[str, int]
    playable_min: int
    playable_max: int
    note_channel: int
    keyswitch_velocity: int
    note_off_velocity: int
    keyswitch_length_ticks: int
    legato_overlap_ticks: int
    keyswitch_preroll_ticks: int


def _required_timing_int(
    profile: VirtualGuitarInstrumentProfile,
    key: str,
) -> int:
    try:
        value = profile.timing_parameters[key]
    except KeyError as exc:
        raise ValueError(
            f"Virtual-instrument profile {profile.profile_id!r} is missing "
            f"required Ample renderer timing parameter {key!r}."
        ) from exc
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"Virtual-instrument profile {profile.profile_id!r} timing parameter "
            f"{key!r} must be numeric."
        )
    integer = int(value)
    if abs(float(value) - integer) > 1e-9:
        raise ValueError(
            f"Virtual-instrument profile {profile.profile_id!r} timing parameter "
            f"{key!r} must be an integer tick/value for the legacy renderer."
        )
    return integer


def _keyswitch(
    profile: VirtualGuitarInstrumentProfile,
    intent: str,
) -> int:
    capability = profile.capability(intent)
    if capability is None or capability.support not in {"native", "approximated"}:
        raise ValueError(
            f"Virtual-instrument profile {profile.profile_id!r} does not provide "
            f"a supported {intent!r} capability required by the legacy Ample renderer."
        )
    actions = [
        action
        for action in capability.actions
        if action.kind == "keyswitch_note" and action.timing != "after_event"
    ]
    if len(actions) != 1 or not isinstance(actions[0].target, int):
        raise ValueError(
            f"Virtual-instrument profile {profile.profile_id!r} must provide exactly "
            f"one primary integer keyswitch_note action for {intent!r}."
        )
    return actions[0].target


def renderer_profile_from_generic(
    profile: VirtualGuitarInstrumentProfile,
) -> GenericAmpleRendererProfile:
    """Project approved generic profile facts into the legacy renderer contract."""

    slide_in = _keyswitch(profile, "slide_in")
    slide_out = _keyswitch(profile, "slide_out")
    if slide_in != slide_out:
        raise ValueError(
            f"Virtual-instrument profile {profile.profile_id!r} cannot be represented "
            "by the legacy Ample slide-in/out shared-control contract."
        )

    hammer_on = _keyswitch(profile, "hammer_on")
    pull_off = _keyswitch(profile, "pull_off")
    if hammer_on != pull_off:
        raise ValueError(
            f"Virtual-instrument profile {profile.profile_id!r} cannot be represented "
            "by the legacy Ample shared hammer/pull control contract."
        )

    return GenericAmpleRendererProfile(
        profile_id=profile.profile_id,
        product=profile.product,
        version_family=profile.version_family,
        keyswitches={
            "sustain": _keyswitch(profile, "sustain"),
            "natural_harmonic": _keyswitch(profile, "natural_harmonic"),
            "palm_mute": _keyswitch(profile, "palm_mute"),
            "slide_in_out": slide_in,
            "legato_slide": _keyswitch(profile, "slide"),
            "hammer_pull": hammer_on,
        },
        playable_min=profile.playable_min,
        playable_max=profile.playable_max,
        note_channel=profile.default_note_channel,
        keyswitch_velocity=_required_timing_int(profile, "keyswitch_velocity"),
        note_off_velocity=_required_timing_int(profile, "note_off_velocity"),
        keyswitch_length_ticks=_required_timing_int(profile, "keyswitch_length_ticks"),
        legato_overlap_ticks=_required_timing_int(profile, "legato_overlap_ticks"),
        keyswitch_preroll_ticks=_required_timing_int(profile, "keyswitch_preroll_ticks"),
    )


def normalize_renderer_profile(
    profile: AmpleGuitarProfile | VirtualGuitarInstrumentProfile,
) -> AmpleRendererProfile:
    """Preserve legacy overrides while allowing generic profile input explicitly."""

    if isinstance(profile, AmpleGuitarProfile):
        return profile
    if isinstance(profile, VirtualGuitarInstrumentProfile):
        return renderer_profile_from_generic(profile)
    raise TypeError(
        "profile must be an AmpleGuitarProfile or VirtualGuitarInstrumentProfile"
    )
