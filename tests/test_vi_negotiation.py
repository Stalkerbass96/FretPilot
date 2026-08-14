import pytest

from fretpilot.virtual_instruments.ample_guitar_sc import AMPLE_GUITAR_SC_V4_PROFILE
from fretpilot.virtual_instruments.models import (
    ArticulationCapability,
    ControlAction,
    VirtualGuitarInstrumentProfile,
)
from fretpilot.virtual_instruments.negotiation import (
    negotiate_intent,
    negotiate_intents,
)


def test_native_ample_intent_returns_declared_actions_without_midi_rendering():
    result = negotiate_intent(AMPLE_GUITAR_SC_V4_PROFILE, "hammer_on")
    assert result.support == "native"
    assert result.supported is True
    assert result.resolved_intent == "hammer_on"
    assert result.fallback_chain == ("hammer_on",)
    assert [item.kind for item in result.actions] == [
        "keyswitch_note",
        "note_overlap_ticks",
    ]
    assert result.actions[0].target == 29


def test_explicitly_unsupported_ample_intent_stays_explicit():
    result = negotiate_intent(AMPLE_GUITAR_SC_V4_PROFILE, "vibrato")
    assert result.support == "unsupported"
    assert result.supported is False
    assert result.resolved_intent == "vibrato"
    assert result.actions == ()


def test_undeclared_intent_is_not_silently_treated_as_supported():
    result = negotiate_intent(AMPLE_GUITAR_SC_V4_PROFILE, "pick_down")
    assert result.support == "unsupported"
    assert result.resolved_intent is None
    assert result.actions == ()
    assert "declares no capability" in result.notes


def _fallback_profile(*capabilities):
    return VirtualGuitarInstrumentProfile(
        profile_id="fixture",
        vendor="Fixture",
        product="Fixture Guitar",
        version_family="1.x",
        profile_schema_version="0.1",
        playable_min=40,
        playable_max=88,
        capabilities=tuple(capabilities),
    )


def test_requires_fallback_is_reported_as_approximated_when_target_is_native():
    profile = _fallback_profile(
        ArticulationCapability(
            intent="special",
            support="requires_fallback",
            fallback_intent="sustain",
        ),
        ArticulationCapability(
            intent="sustain",
            support="native",
            actions=(ControlAction(kind="keyswitch_note", target=24),),
        ),
    )
    result = negotiate_intent(profile, "special")
    assert result.support == "approximated"
    assert result.resolved_intent == "sustain"
    assert result.fallback_chain == ("special", "sustain")
    assert result.actions[0].target == 24


def test_fallback_chain_that_ends_unsupported_remains_unsupported():
    profile = _fallback_profile(
        ArticulationCapability(
            intent="special",
            support="requires_fallback",
            fallback_intent="basic",
        ),
        ArticulationCapability(intent="basic", support="unsupported"),
    )
    result = negotiate_intent(profile, "special")
    assert result.support == "unsupported"
    assert result.resolved_intent == "basic"
    assert result.fallback_chain == ("special", "basic")


def test_fallback_cycle_is_rejected_instead_of_looping():
    profile = _fallback_profile(
        ArticulationCapability(
            intent="a",
            support="requires_fallback",
            fallback_intent="b",
        ),
        ArticulationCapability(
            intent="b",
            support="requires_fallback",
            fallback_intent="a",
        ),
    )
    with pytest.raises(ValueError, match="fallback cycle"):
        negotiate_intent(profile, "a")


def test_batch_negotiation_preserves_caller_order_and_duplicates():
    results = negotiate_intents(
        AMPLE_GUITAR_SC_V4_PROFILE,
        ["palm_mute", "vibrato", "palm_mute"],
    )
    assert [item.requested_intent for item in results] == [
        "palm_mute",
        "vibrato",
        "palm_mute",
    ]
