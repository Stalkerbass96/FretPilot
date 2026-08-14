"""Public Ample renderer handoff from generic VI knowledge to legacy scheduling.

The scheduling implementation intentionally remains in ``renderer.py``.  This
wrapper only chooses/normalizes profile data so VI-002 can move static target
truth into the provider-neutral profile without changing MIDI event behavior.
"""

from __future__ import annotations

from pathlib import Path

from fretpilot.exporters.ample_guitar.profile_view import normalize_renderer_profile
from fretpilot.exporters.ample_guitar.profiles import AmpleGuitarProfile
from fretpilot.exporters.ample_guitar.renderer import (
    AmpleExportResult,
    export_ample_sc_midi as _export_legacy_ample_sc_midi,
)
from fretpilot.ir.models import GuitarProjectIR
from fretpilot.virtual_instruments.ample_guitar_sc import AMPLE_GUITAR_SC_V4_PROFILE
from fretpilot.virtual_instruments.models import VirtualGuitarInstrumentProfile


def export_ample_sc_midi(
    project: GuitarProjectIR,
    output: str | Path,
    *,
    profile: AmpleGuitarProfile | VirtualGuitarInstrumentProfile | None = None,
    ticks_per_beat: int = 480,
) -> AmpleExportResult:
    """Render Ample MIDI using generic profile truth and legacy scheduling.

    ``None`` selects the approved generic ``ample-guitar-sc-v4`` profile.
    Explicit legacy ``AmpleGuitarProfile`` values remain accepted for backward
    compatibility, while callers may also pass a generic profile directly.
    """

    selected = AMPLE_GUITAR_SC_V4_PROFILE if profile is None else profile
    renderer_profile = normalize_renderer_profile(selected)
    return _export_legacy_ample_sc_midi(
        project,
        output,
        profile=renderer_profile,
        ticks_per_beat=ticks_per_beat,
    )
