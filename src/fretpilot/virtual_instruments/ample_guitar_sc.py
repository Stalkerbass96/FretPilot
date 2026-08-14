"""Provider-neutral Ample Guitar SC 4.x knowledge snapshot.

This module migrates the control facts already used by the regression-covered
legacy Ample exporter into ``VirtualGuitarInstrumentProfile``.  It does not
change the legacy renderer and it does not claim that repository-derived facts
are official vendor documentation.
"""

from __future__ import annotations

from fretpilot.virtual_instruments.models import (
    AdapterEvidence,
    ArticulationCapability,
    ControlAction,
    VirtualGuitarInstrumentProfile,
)


_EVIDENCE = (
    AdapterEvidence(
        source_type="repository_regression",
        reference="src/fretpilot/exporters/ample_guitar/profiles.py",
        status="verified",
        notes=(
            "Values migrated from the current versioned legacy profile and kept "
            "identical so VI-002 does not alter MIDI behavior."
        ),
    ),
    AdapterEvidence(
        source_type="repository_regression",
        reference="src/fretpilot/exporters/ample_guitar/renderer.py",
        status="verified",
        notes=(
            "Capability mappings mirror the currently tested legacy scheduling "
            "logic; this is internal evidence, not an official-vendor citation."
        ),
    ),
)


def _keyswitch(note: int, *, timing: str = "preroll") -> ControlAction:
    return ControlAction(
        kind="keyswitch_note",
        target=note,
        value=100,
        timing=timing,
        duration_ticks=12,
    )


def _overlap() -> ControlAction:
    return ControlAction(
        kind="note_overlap_ticks",
        target="source_to_destination",
        value=30,
        timing="linked_transition",
    )


def _reset_sustain() -> ControlAction:
    return _keyswitch(24, timing="after_event")


AMPLE_GUITAR_SC_V4_PROFILE = VirtualGuitarInstrumentProfile(
    profile_id="ample-guitar-sc-v4",
    vendor="Ample Sound",
    product="Ample Guitar SC",
    version_family="4.x",
    profile_schema_version="0.1",
    playable_min=38,
    playable_max=86,
    capabilities=(
        ArticulationCapability(
            intent="sustain",
            support="native",
            actions=(_keyswitch(24, timing="initial_state"),),
            notes="Legacy renderer establishes Sustain at tick zero.",
        ),
        ArticulationCapability(
            intent="hammer_on",
            support="native",
            actions=(_keyswitch(29), _overlap()),
            notes="Shares the legacy Hammer/Pull control state.",
        ),
        ArticulationCapability(
            intent="pull_off",
            support="native",
            actions=(_keyswitch(29), _overlap()),
            notes="Shares the legacy Hammer/Pull control state.",
        ),
        ArticulationCapability(
            intent="slide",
            support="native",
            actions=(_keyswitch(28), _overlap()),
            notes="Legacy linked slide path uses the Legato Slide control.",
        ),
        ArticulationCapability(
            intent="natural_harmonic",
            support="native",
            actions=(_keyswitch(25), _reset_sustain()),
        ),
        ArticulationCapability(
            intent="palm_mute",
            support="native",
            actions=(_keyswitch(26), _reset_sustain()),
        ),
        ArticulationCapability(
            intent="slide_in",
            support="native",
            actions=(_keyswitch(27), _reset_sustain()),
        ),
        ArticulationCapability(
            intent="slide_out",
            support="native",
            actions=(_keyswitch(27), _reset_sustain()),
        ),
        ArticulationCapability(
            intent="let_ring",
            support="native",
            actions=(),
            notes=(
                "Legacy renderer realizes let-ring through the preserved source "
                "performance duration rather than a separate control event."
            ),
        ),
        ArticulationCapability(
            intent="vibrato",
            support="unsupported",
            notes="Preserved in Guitar IR but not rendered by the legacy SC MIDI adapter.",
        ),
        ArticulationCapability(
            intent="pitch_raise",
            support="unsupported",
            notes="The legacy SC MIDI adapter does not currently render pitch-raise curves.",
        ),
    ),
    supports_string_forcing=False,
    supports_position_forcing=False,
    supports_per_note_pitch_expression=False,
    pitch_bend_range_semitones=None,
    default_note_channel=0,
    timing_parameters={
        "keyswitch_velocity": 100,
        "note_off_velocity": 64,
        "keyswitch_length_ticks": 12,
        "legato_overlap_ticks": 30,
        "keyswitch_preroll_ticks": 30,
    },
    limitations=(
        "Legacy adapter does not render vibrato.",
        "Legacy adapter does not render canonical pitch_raise curves.",
        "No string-forcing or position-forcing control is represented in the migrated baseline.",
        "Generic PerformancePlan intents are not yet consumed by the legacy adapter.",
    ),
    evidence=_EVIDENCE,
    maturity="legacy-compatible-baseline",
)
