from __future__ import annotations

import pytest

from fretpilot.virtual_instruments import (
    BUILTIN_VIRTUAL_INSTRUMENT_SNAPSHOT_VERSION,
    AdapterEvidence,
    ArticulationCapability,
    ControlAction,
    VirtualGuitarInstrumentProfile,
    get_builtin_virtual_instrument_registry,
)


def test_profile_can_represent_keyswitch_and_overlap_requirements() -> None:
    profile = VirtualGuitarInstrumentProfile(
        profile_id="example-guitar-v1",
        vendor="Example",
        product="Example Guitar",
        version_family="1.x",
        profile_schema_version="0.1",
        playable_min=40,
        playable_max=88,
        capabilities=(
            ArticulationCapability(
                intent="hammer_on",
                support="native",
                actions=(
                    ControlAction(kind="keyswitch", target=29, timing="preroll"),
                    ControlAction(kind="note_overlap", value=30, timing="between_notes"),
                ),
            ),
        ),
        timing_parameters={"keyswitch_preroll_ticks": 30},
        evidence=(
            AdapterEvidence(
                source_type="official_manual",
                reference="example manual v1",
                status="official",
            ),
        ),
    )

    hammer_on = profile.capability("hammer_on")
    assert hammer_on is not None
    assert hammer_on.support == "native"
    assert [action.kind for action in hammer_on.actions] == ["keyswitch", "note_overlap"]
    assert profile.to_dict()["profile_id"] == "example-guitar-v1"


def test_requires_fallback_must_name_fallback_intent() -> None:
    with pytest.raises(ValueError, match="fallback_intent"):
        ArticulationCapability(intent="bend", support="requires_fallback")


def test_profile_rejects_invalid_playable_range() -> None:
    with pytest.raises(ValueError, match="playable_min"):
        VirtualGuitarInstrumentProfile(
            profile_id="broken",
            vendor="Example",
            product="Broken",
            version_family="1.x",
            profile_schema_version="0.1",
            playable_min=90,
            playable_max=40,
        )


def test_builtin_registry_contains_documented_ample_metal_eclipse_profile() -> None:
    registry = get_builtin_virtual_instrument_registry()

    assert registry.snapshot.snapshot_version == (
        BUILTIN_VIRTUAL_INSTRUMENT_SNAPSHOT_VERSION
    )
    profile = registry.require("ample-metal-eclipse-v4.1")

    assert profile.vendor == "Ample Sound"
    assert profile.product == "Ample Metal Eclipse"
    assert profile.version_family == "4.1"
    assert profile.playable_min == 36  # Ample C1, stored as an unambiguous MIDI note.
    assert profile.playable_max == 84  # Ample C5.
    assert profile.default_tuning == (40, 45, 50, 55, 59, 64)
    assert profile.maturity == "official_documented"
    assert profile.verification_status == "plugin_unverified"


def test_eclipse_profile_preserves_articulation_and_velocity_facts() -> None:
    profile = get_builtin_virtual_instrument_registry().require(
        "ample-metal-eclipse-v4.1"
    )

    hammer_on = profile.capability("hammer_on")
    assert hammer_on is not None
    assert hammer_on.support == "native"
    assert [action.kind for action in hammer_on.actions] == [
        "keyswitch",
        "note_overlap",
        "automatic_reset",
    ]
    assert hammer_on.actions[0].target == 29  # Ample F0.
    assert hammer_on.actions[0].display_label == "F0"
    assert hammer_on.actions[1].value == "required"

    tap = profile.capability("tap")
    pinch = profile.capability("pinch_harmonic")
    assert tap is not None and tap.actions[0].target == 30
    assert pinch is not None and pinch.actions[0].target == 31

    assert [
        (layer.minimum, layer.maximum, layer.result)
        for layer in profile.velocity_layers
        if layer.context == "sustain"
    ] == [
        (1, 15, "full_mute"),
        (16, 31, "three_quarter_mute"),
        (32, 63, "half_mute"),
        (64, 126, "sustain"),
        (127, 127, "pop_or_pinch_harmonic"),
    ]


def test_eclipse_profile_exposes_non_articulation_control_families() -> None:
    profile = get_builtin_virtual_instrument_registry().require(
        "ample-metal-eclipse-v4.1"
    )

    string_assignment = profile.control("string_assignment")
    position_assignment = profile.control("position_assignment")
    auto_legato = profile.control("auto_legato")

    assert string_assignment is not None
    assert string_assignment.category == "fretboard"
    assert string_assignment.actions[0].target == "18-23"
    assert position_assignment is not None
    assert position_assignment.actions[0].target == 32
    assert auto_legato is not None
    assert {action.value for action in auto_legato.actions} == {
        "auto_hammer_pull",
        "auto_legato_slide",
    }


def test_virtual_instrument_registry_filters_provider_neutrally() -> None:
    registry = get_builtin_virtual_instrument_registry()

    assert [profile.profile_id for profile in registry.list(vendor="Ample Sound")] == [
        "ample-metal-eclipse-v4.1"
    ]
    with pytest.raises(ValueError, match="available: ample-metal-eclipse-v4.1"):
        registry.require("missing-profile")
