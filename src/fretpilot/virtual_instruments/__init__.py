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
    VirtualGuitarInstrumentProfile,
)
from fretpilot.virtual_instruments.negotiation import (
    CapabilityResolution,
    negotiate_intent,
    negotiate_intents,
)
from fretpilot.virtual_instruments.registry import get_profile, list_profiles

__all__ = [
    "AMPLE_GUITAR_SC_V4_PROFILE",
    "AdapterEvidence",
    "ArticulationCapability",
    "CapabilityReport",
    "CapabilityRequirement",
    "CapabilityResolution",
    "ControlAction",
    "VirtualGuitarInstrumentProfile",
    "build_capability_report",
    "get_profile",
    "list_profiles",
    "negotiate_intent",
    "negotiate_intents",
]
