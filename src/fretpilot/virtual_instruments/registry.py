"""Deterministic registry for approved virtual-guitar instrument profiles.

Runtime profile discovery is intentionally local and versioned.  The registry
must never crawl vendor pages or silently ingest candidate knowledge.
"""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
import json
from pathlib import Path
from typing import Iterable

from fretpilot.virtual_instruments.ample_guitar_sc import AMPLE_GUITAR_SC_V4_PROFILE
from fretpilot.virtual_instruments.models import (
    VirtualGuitarInstrumentProfile,
    VirtualInstrumentKnowledgeSnapshot,
)


BUILTIN_VIRTUAL_INSTRUMENT_SNAPSHOT_VERSION = "2026.08.0"
BUILTIN_VIRTUAL_INSTRUMENT_RESOURCE = "assets/virtual-instruments-2026.08.0.json"
SUPPORTED_VIRTUAL_INSTRUMENT_SCHEMA_VERSION = "1"


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


class VirtualInstrumentRegistry:
    """Read-only review catalog over one explicit knowledge snapshot.

    This catalog may contain officially documented but plugin-unverified product
    profiles. It is deliberately separate from ``get_profile``/``list_profiles``,
    which expose only profiles approved for production rendering.
    """

    def __init__(self, snapshot: VirtualInstrumentKnowledgeSnapshot) -> None:
        self.snapshot = snapshot
        self._by_id = {profile.profile_id: profile for profile in snapshot.profiles}

    def get(self, profile_id: str) -> VirtualGuitarInstrumentProfile | None:
        return self._by_id.get(profile_id)

    def require(self, profile_id: str) -> VirtualGuitarInstrumentProfile:
        profile = self.get(profile_id)
        if profile is None:
            available = ", ".join(sorted(self._by_id))
            raise ValueError(
                f"Unknown virtual-instrument profile {profile_id!r}; "
                f"available: {available}."
            )
        return profile

    def list(
        self,
        *,
        vendor: str | None = None,
        product: str | None = None,
        maturities: Iterable[str] | None = None,
    ) -> list[VirtualGuitarInstrumentProfile]:
        allowed_maturities = set(maturities) if maturities is not None else None
        return [
            profile
            for profile in self.snapshot.profiles
            if (vendor is None or profile.vendor == vendor)
            and (product is None or profile.product == product)
            and (
                allowed_maturities is None
                or profile.maturity in allowed_maturities
            )
        ]


def _validate_snapshot_schema(snapshot: VirtualInstrumentKnowledgeSnapshot) -> None:
    if snapshot.schema_version != SUPPORTED_VIRTUAL_INSTRUMENT_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported virtual-instrument schema {snapshot.schema_version!r}; "
            f"expected {SUPPORTED_VIRTUAL_INSTRUMENT_SCHEMA_VERSION!r}."
        )


def load_virtual_instrument_snapshot(
    path: str | Path,
) -> VirtualInstrumentKnowledgeSnapshot:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    snapshot = VirtualInstrumentKnowledgeSnapshot.from_dict(payload)
    _validate_snapshot_schema(snapshot)
    return snapshot


@lru_cache(maxsize=1)
def get_builtin_virtual_instrument_registry() -> VirtualInstrumentRegistry:
    resource = files("fretpilot.virtual_instruments").joinpath(
        BUILTIN_VIRTUAL_INSTRUMENT_RESOURCE
    )
    payload = json.loads(resource.read_text(encoding="utf-8"))
    snapshot = VirtualInstrumentKnowledgeSnapshot.from_dict(payload)
    _validate_snapshot_schema(snapshot)
    if snapshot.snapshot_version != BUILTIN_VIRTUAL_INSTRUMENT_SNAPSHOT_VERSION:
        raise ValueError(
            "Built-in virtual-instrument asset version does not match the runtime pin."
        )
    if snapshot.status != "approved":
        raise ValueError(
            "The built-in virtual-instrument knowledge snapshot must be approved."
        )
    return VirtualInstrumentRegistry(snapshot)
