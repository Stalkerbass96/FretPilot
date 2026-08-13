"""Ample Guitar performance-MIDI adapters."""

from fretpilot.exporters.ample_guitar.profiles import (
    AMPLE_GUITAR_SC_V4,
    AmpleGuitarProfile,
    get_profile,
)
from fretpilot.exporters.ample_guitar.renderer import (
    AmpleExportResult,
    export_ample_sc_midi,
)

__all__ = [
    "AMPLE_GUITAR_SC_V4",
    "AmpleExportResult",
    "AmpleGuitarProfile",
    "export_ample_sc_midi",
    "get_profile",
]
