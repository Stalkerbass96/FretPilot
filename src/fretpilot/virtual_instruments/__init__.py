"""Virtual-guitar adapter knowledge and capability models."""

from fretpilot.virtual_instruments.models import (
    AdapterEvidence,
    ArticulationCapability,
    ControlAction,
    InstrumentControlCapability,
    VelocityLayer,
    VirtualGuitarInstrumentProfile,
    VirtualInstrumentKnowledgeSnapshot,
)
from fretpilot.virtual_instruments.registry import (
    BUILTIN_VIRTUAL_INSTRUMENT_SNAPSHOT_VERSION,
    VirtualInstrumentRegistry,
    get_builtin_virtual_instrument_registry,
    load_virtual_instrument_snapshot,
)

__all__ = [
    "AdapterEvidence",
    "ArticulationCapability",
    "BUILTIN_VIRTUAL_INSTRUMENT_SNAPSHOT_VERSION",
    "ControlAction",
    "InstrumentControlCapability",
    "VelocityLayer",
    "VirtualGuitarInstrumentProfile",
    "VirtualInstrumentKnowledgeSnapshot",
    "VirtualInstrumentRegistry",
    "get_builtin_virtual_instrument_registry",
    "load_virtual_instrument_snapshot",
]
