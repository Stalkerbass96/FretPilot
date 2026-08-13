from __future__ import annotations

import pytest

from fretpilot.virtual_instruments import (
    AdapterEvidence,
    ArticulationCapability,
    ControlAction,
    VirtualGuitarInstrumentProfile,
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
