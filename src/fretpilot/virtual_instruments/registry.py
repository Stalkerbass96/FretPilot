"""Deterministic registry for approved virtual-guitar instrument profiles.

Runtime profile discovery is intentionally local and versioned.  The registry
must never crawl vendor pages or silently ingest candidate knowledge.
"""

from __future__ import annotations

from fretpilot.virtual_instruments.ample_guitar_sc import AMPLE_GUITAR_SC_V4_PROFILE
from fretpilot.virtual_instruments.models import VirtualGuitarInstrumentProfile


_PROFILES: tuple[VirtualGuitarInstrumentProfile, ...] = (
    AMPLE_GUITAR_SC_V4_PROFILE,
)
_PROFILE_BY_ID = {profile.profile_id: profile for profile in _PROFILES}

if len(_PROFILE_BY_ID) != len(_PROFILES):
    raise RuntimeError("Virtual instrument profile ids must be unique.")


def list_profiles() -> tuple[VirtualGuitarInstrumentProfile, ...]:
    """Return the immutable approved runtime profile snapshot."""

    return _PROFILES


def get_profile(profile_id: str) -> VirtualGuitarInstrumentProfile:
    """Resolve one approved target profile by stable id."""

    try:
        return _PROFILE_BY_ID[profile_id]
    except KeyError as exc:
        available = ", ".join(sorted(_PROFILE_BY_ID))
        raise ValueError(
            f"Unknown virtual-guitar profile {profile_id!r}; available: {available}."
        ) from exc
