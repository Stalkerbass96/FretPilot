"""Virtual-guitar adapter knowledge and capability models."""

from fretpilot.virtual_instruments.ample_guitar_sc import AMPLE_GUITAR_SC_V4_PROFILE
from fretpilot.virtual_instruments.capability_report import (
    CapabilityReport,
    CapabilityRequirement,
    build_capability_report,
)
from fretpilot.virtual_instruments.models import (
    AdapterEvidence,
    ArticulationCapability,
    ControlAction,
    InstrumentControlCapability,
    VelocityLayer,
    VirtualGuitarInstrumentProfile,
    VirtualInstrumentKnowledgeSnapshot,
)
from fretpilot.virtual_instruments.negotiation import (
    CapabilityResolution,
    negotiate_intent,
    negotiate_intents,
)
from fretpilot.virtual_instruments.registry import (
    BUILTIN_VIRTUAL_INSTRUMENT_SNAPSHOT_VERSION,
    VirtualInstrumentRegistry,
    get_builtin_virtual_instrument_registry,
    get_profile,
    list_profiles,
    load_virtual_instrument_snapshot,
)

__all__ = [
    "AMPLE_GUITAR_SC_V4_PROFILE",
    "AdapterEvidence",
    "ArticulationCapability",
    "BUILTIN_VIRTUAL_INSTRUMENT_SNAPSHOT_VERSION",
    "CapabilityReport",
    "CapabilityRequirement",
    "CapabilityResolution",
    "ControlAction",
    "InstrumentControlCapability",
    "VelocityLayer",
    "VirtualGuitarInstrumentProfile",
    "VirtualInstrumentKnowledgeSnapshot",
    "VirtualInstrumentRegistry",
    "build_capability_report",
    "get_profile",
    "get_builtin_virtual_instrument_registry",
    "list_profiles",
    "load_virtual_instrument_snapshot",
    "negotiate_intent",
    "negotiate_intents",
]
