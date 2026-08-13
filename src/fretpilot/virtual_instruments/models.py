"""Provider-neutral knowledge models for virtual guitar instruments.

These models describe *how a target virtual instrument is controlled*. They do
not describe how a real guitarist should play, and vendor-specific control data
must never leak back into canonical Guitar IR or Guitar Playing Knowledge.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_SUPPORT_LEVELS = frozenset({"native", "approximated", "unsupported", "requires_fallback"})
VALID_EVIDENCE_STATUS = frozenset({"candidate", "verified", "official"})


@dataclass(frozen=True, slots=True)
class AdapterEvidence:
    """Provenance for one piece of adapter/product knowledge."""

    source_type: str
    reference: str
    status: str = "candidate"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.status not in VALID_EVIDENCE_STATUS:
            raise ValueError(
                f"Unsupported evidence status {self.status!r}; "
                f"expected one of {sorted(VALID_EVIDENCE_STATUS)}."
            )


@dataclass(frozen=True, slots=True)
class ControlAction:
    """One target-specific control action used to realize musical intent.

    Examples include a keyswitch note, CC value, velocity range, note-overlap
    requirement, pitch-bend setup, or a product-specific state transition.
    ``target`` and ``value`` remain generic because different control types use
    different MIDI/control payloads.
    """

    kind: str
    target: int | str | None = None
    value: int | float | str | None = None
    timing: str = "at_event"
    duration_ticks: int | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class ArticulationCapability:
    """How one canonical Guitar IR intent maps to a target instrument."""

    intent: str
    support: str
    actions: tuple[ControlAction, ...] = ()
    fallback_intent: str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if self.support not in VALID_SUPPORT_LEVELS:
            raise ValueError(
                f"Unsupported capability level {self.support!r}; "
                f"expected one of {sorted(VALID_SUPPORT_LEVELS)}."
            )
        if self.support == "unsupported" and self.actions:
            raise ValueError("Unsupported capabilities cannot declare control actions.")
        if self.support == "requires_fallback" and not self.fallback_intent:
            raise ValueError("requires_fallback capabilities must name fallback_intent.")


@dataclass(frozen=True, slots=True)
class VirtualGuitarInstrumentProfile:
    """Versioned knowledge profile for one virtual-guitar product family."""

    profile_id: str
    vendor: str
    product: str
    version_family: str
    profile_schema_version: str
    playable_min: int
    playable_max: int
    capabilities: tuple[ArticulationCapability, ...] = ()
    supports_string_forcing: bool = False
    supports_position_forcing: bool = False
    supports_per_note_pitch_expression: bool = False
    pitch_bend_range_semitones: float | None = None
    default_note_channel: int = 0
    timing_parameters: dict[str, int | float] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()
    evidence: tuple[AdapterEvidence, ...] = ()
    maturity: str = "experimental"

    def __post_init__(self) -> None:
        if self.playable_min > self.playable_max:
            raise ValueError("playable_min cannot exceed playable_max.")
        if not 0 <= self.default_note_channel <= 15:
            raise ValueError("default_note_channel must be a zero-based MIDI channel 0..15.")
        intents = [capability.intent for capability in self.capabilities]
        if len(intents) != len(set(intents)):
            raise ValueError("capability intents must be unique within one profile.")

    def capability(self, intent: str) -> ArticulationCapability | None:
        for capability in self.capabilities:
            if capability.intent == intent:
                return capability
        return None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
