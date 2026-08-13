"""Provider-neutral knowledge models for virtual guitar instruments.

These models describe *how a target virtual instrument is controlled*. They do
not describe how a real guitarist should play, and vendor-specific control data
must never leak back into canonical Guitar IR or Guitar Playing Knowledge.

Raw MIDI numbers are canonical in this layer. ``display_label`` may retain a
vendor's octave label (for example Ample ``C0``), which is useful to a human but
is not safe enough to drive rendering by itself.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


VALID_SUPPORT_LEVELS = frozenset({"native", "approximated", "unsupported", "requires_fallback"})
VALID_EVIDENCE_STATUS = frozenset({"candidate", "verified", "official"})
VALID_SNAPSHOT_STATUSES = frozenset({"candidate", "approved", "deprecated"})


@dataclass(frozen=True, slots=True)
class AdapterEvidence:
    """Provenance for one piece of adapter/product knowledge."""

    source_type: str
    reference: str
    status: str = "candidate"
    notes: str = ""
    evidence_id: str = ""
    document_version: str = ""
    retrieved_on: str = ""
    verified_on: str = ""

    def __post_init__(self) -> None:
        if self.status not in VALID_EVIDENCE_STATUS:
            raise ValueError(
                f"Unsupported evidence status {self.status!r}; "
                f"expected one of {sorted(VALID_EVIDENCE_STATUS)}."
            )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AdapterEvidence:
        return cls(**dict(data))


@dataclass(frozen=True, slots=True)
class ControlAction:
    """One target-specific control action used to realize musical intent."""

    kind: str
    target: int | str | None = None
    value: int | float | str | None = None
    timing: str = "at_event"
    duration_ticks: int | None = None
    notes: str = ""
    display_label: str = ""
    state: str = ""
    conditions: Mapping[str, str | int | float] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ControlAction:
        return cls(**dict(data))


@dataclass(frozen=True, slots=True)
class ArticulationCapability:
    """How one canonical Guitar IR intent maps to a target instrument."""

    intent: str
    support: str
    actions: tuple[ControlAction, ...] = ()
    fallback_intent: str | None = None
    notes: str = ""
    playable_min: int | None = None
    playable_max: int | None = None
    evidence_ids: tuple[str, ...] = ()

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
        if (
            self.playable_min is not None
            and self.playable_max is not None
            and self.playable_min > self.playable_max
        ):
            raise ValueError("articulation playable_min cannot exceed playable_max.")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ArticulationCapability:
        payload = dict(data)
        payload["actions"] = tuple(
            ControlAction.from_dict(item) for item in payload.get("actions", ())
        )
        payload["evidence_ids"] = tuple(payload.get("evidence_ids", ()))
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class InstrumentControlCapability:
    """A non-articulation control family such as string or position forcing."""

    capability_id: str
    category: str
    support: str
    actions: tuple[ControlAction, ...] = ()
    notes: str = ""
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.support not in VALID_SUPPORT_LEVELS:
            raise ValueError(
                f"Unsupported capability level {self.support!r}; "
                f"expected one of {sorted(VALID_SUPPORT_LEVELS)}."
            )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> InstrumentControlCapability:
        payload = dict(data)
        payload["actions"] = tuple(
            ControlAction.from_dict(item) for item in payload.get("actions", ())
        )
        payload["evidence_ids"] = tuple(payload.get("evidence_ids", ()))
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class VelocityLayer:
    """A documented velocity interval and its product-specific result."""

    context: str
    minimum: int
    maximum: int
    result: str
    notes: str = ""
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 1 <= self.minimum <= self.maximum <= 127:
            raise ValueError("velocity layer must fit within MIDI velocity 1..127.")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VelocityLayer:
        payload = dict(data)
        payload["evidence_ids"] = tuple(payload.get("evidence_ids", ()))
        return cls(**payload)


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
    supports_string_forcing: bool | None = None
    supports_position_forcing: bool | None = None
    supports_per_note_pitch_expression: bool | None = None
    pitch_bend_range_semitones: float | None = None
    default_note_channel: int = 0
    timing_parameters: Mapping[str, int | float] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()
    evidence: tuple[AdapterEvidence, ...] = ()
    maturity: str = "experimental"
    profile_version: str = "1"
    knowledge_version: str = ""
    verification_status: str = "unverified"
    instrument_model: str = ""
    instrument_type: str = "guitar"
    pickup_configuration: str = ""
    default_tuning: tuple[int, ...] = ()
    tuning_down_semitones_per_string: int | None = None
    sample_modes: tuple[str, ...] = ()
    supported_formats: tuple[str, ...] = ()
    controls: tuple[InstrumentControlCapability, ...] = ()
    velocity_layers: tuple[VelocityLayer, ...] = ()

    def __post_init__(self) -> None:
        if self.playable_min > self.playable_max:
            raise ValueError("playable_min cannot exceed playable_max.")
        if not 0 <= self.default_note_channel <= 15:
            raise ValueError("default_note_channel must be a zero-based MIDI channel 0..15.")
        intents = [capability.intent for capability in self.capabilities]
        if len(intents) != len(set(intents)):
            raise ValueError("capability intents must be unique within one profile.")
        control_ids = [control.capability_id for control in self.controls]
        if len(control_ids) != len(set(control_ids)):
            raise ValueError("control capability IDs must be unique within one profile.")
        evidence_ids = {item.evidence_id for item in self.evidence if item.evidence_id}
        referenced_ids = {
            evidence_id
            for capability in (*self.capabilities, *self.controls, *self.velocity_layers)
            for evidence_id in capability.evidence_ids
        }
        missing = sorted(referenced_ids - evidence_ids)
        if missing:
            raise ValueError("unknown evidence IDs: " + ", ".join(missing))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VirtualGuitarInstrumentProfile:
        payload = dict(data)
        payload["capabilities"] = tuple(
            ArticulationCapability.from_dict(item)
            for item in payload.get("capabilities", ())
        )
        payload["controls"] = tuple(
            InstrumentControlCapability.from_dict(item)
            for item in payload.get("controls", ())
        )
        payload["velocity_layers"] = tuple(
            VelocityLayer.from_dict(item)
            for item in payload.get("velocity_layers", ())
        )
        payload["evidence"] = tuple(
            AdapterEvidence.from_dict(item) for item in payload.get("evidence", ())
        )
        for key in (
            "limitations",
            "default_tuning",
            "sample_modes",
            "supported_formats",
        ):
            payload[key] = tuple(payload.get(key, ()))
        return cls(**payload)

    def capability(self, intent: str) -> ArticulationCapability | None:
        for capability in self.capabilities:
            if capability.intent == intent:
                return capability
        return None

    def control(self, capability_id: str) -> InstrumentControlCapability | None:
        for control in self.controls:
            if control.capability_id == capability_id:
                return control
        return None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VirtualInstrumentKnowledgeSnapshot:
    """An immutable, release-pinned collection of instrument profiles."""

    snapshot_version: str
    schema_version: str
    status: str
    profiles: tuple[VirtualGuitarInstrumentProfile, ...]

    def __post_init__(self) -> None:
        if self.status not in VALID_SNAPSHOT_STATUSES:
            raise ValueError(f"Unsupported virtual-instrument snapshot status {self.status!r}.")
        profile_ids = [profile.profile_id for profile in self.profiles]
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("profile IDs must be unique within one snapshot.")
        mismatched = [
            profile.profile_id
            for profile in self.profiles
            if profile.knowledge_version != self.snapshot_version
        ]
        if mismatched:
            raise ValueError(
                "profile knowledge versions must match their snapshot: "
                + ", ".join(mismatched)
            )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VirtualInstrumentKnowledgeSnapshot:
        return cls(
            snapshot_version=str(data["snapshot_version"]),
            schema_version=str(data["schema_version"]),
            status=str(data["status"]),
            profiles=tuple(
                VirtualGuitarInstrumentProfile.from_dict(item)
                for item in data.get("profiles", ())
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
