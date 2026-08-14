"""Public Ample renderer handoff from generic VI knowledge to legacy scheduling.

The scheduling implementation intentionally remains in ``renderer.py``. This
wrapper chooses/normalizes profile data and runs provider-neutral capability
preflight without changing the legacy MIDI event algorithm.
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
from fretpilot.virtual_instruments.capability_report import build_capability_report
from fretpilot.virtual_instruments.models import VirtualGuitarInstrumentProfile
from fretpilot.virtual_instruments.preflight import (
    CapabilityPolicyMode,
    evaluate_capability_report,
)
from fretpilot.virtual_instruments.registry import get_profile


def _generic_profile_for_preflight(
    selected: AmpleGuitarProfile | VirtualGuitarInstrumentProfile,
    *,
    capability_mode: CapabilityPolicyMode,
) -> VirtualGuitarInstrumentProfile | None:
    if isinstance(selected, VirtualGuitarInstrumentProfile):
        return selected
    if capability_mode == "report_only":
        return None
    try:
        return get_profile(selected.profile_id)
    except ValueError as exc:
        raise ValueError(
            "Capability policy 'warn'/'strict' requires an approved generic "
            f"profile matching legacy profile id {selected.profile_id!r}."
        ) from exc


def export_ample_sc_midi(
    project: GuitarProjectIR,
    output: str | Path,
    *,
    profile: AmpleGuitarProfile | VirtualGuitarInstrumentProfile | None = None,
    ticks_per_beat: int = 480,
    capability_mode: CapabilityPolicyMode = "report_only",
) -> AmpleExportResult:
    """Render Ample MIDI using generic profile truth and legacy scheduling.

    ``None`` selects the approved generic ``ample-guitar-sc-v4`` profile.
    Explicit legacy ``AmpleGuitarProfile`` values remain accepted for backward
    compatibility, while callers may also pass a generic profile directly.

    Capability policy is deliberately explicit:

    - ``report_only`` negotiates the default generic target before rendering but
      preserves legacy warnings/output behavior;
    - ``warn`` renders and appends approximated/unsupported capability warnings;
    - ``strict`` blocks before legacy scheduling when requested intent is
      unsupported.
    """

    selected = AMPLE_GUITAR_SC_V4_PROFILE if profile is None else profile
    generic_profile = _generic_profile_for_preflight(
        selected,
        capability_mode=capability_mode,
    )
    preflight = None
    if generic_profile is not None:
        capability_report = build_capability_report(project, generic_profile)
        preflight = evaluate_capability_report(
            capability_report,
            mode=capability_mode,
        )
        if not preflight.can_render:
            details = "; ".join(preflight.errors)
            raise ValueError(
                f"Target capability preflight blocked profile {generic_profile.profile_id!r}: {details}"
            )

    renderer_profile = normalize_renderer_profile(selected)
    result = _export_legacy_ample_sc_midi(
        project,
        output,
        profile=renderer_profile,
        ticks_per_beat=ticks_per_beat,
    )
    if preflight is not None and preflight.warnings:
        result.warnings.extend(preflight.warnings)
    return result
