"""Virtual-guitar adapter knowledge and capability models."""

from fretpilot.virtual_instruments.ample_guitar_sc import AMPLE_GUITAR_SC_V4_PROFILE
from fretpilot.virtual_instruments.models import (
    AdapterEvidence,
    ArticulationCapability,
    ControlAction,
    VirtualGuitarInstrumentProfile,
)

__all__ = [
    "AMPLE_GUITAR_SC_V4_PROFILE",
    "AdapterEvidence",
    "ArticulationCapability",
    "ControlAction",
    "VirtualGuitarInstrumentProfile",
]
