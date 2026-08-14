from fretpilot.exporters.ample_guitar.profiles import AMPLE_GUITAR_SC_V4 as LEGACY
from fretpilot.virtual_instruments.ample_guitar_sc import AMPLE_GUITAR_SC_V4_PROFILE


def _keyswitch_note(intent: str) -> int:
    capability = AMPLE_GUITAR_SC_V4_PROFILE.capability(intent)
    assert capability is not None
    action = next(item for item in capability.actions if item.kind == "keyswitch_note")
    assert isinstance(action.target, int)
    return action.target


def test_generic_profile_preserves_legacy_identity_range_and_channel():
    profile = AMPLE_GUITAR_SC_V4_PROFILE
    assert profile.profile_id == LEGACY.profile_id
    assert profile.product == LEGACY.product
    assert profile.version_family == LEGACY.version_family
    assert profile.playable_min == LEGACY.playable_min
    assert profile.playable_max == LEGACY.playable_max
    assert profile.default_note_channel == LEGACY.note_channel


def test_generic_profile_preserves_legacy_timing_parameters():
    timing = AMPLE_GUITAR_SC_V4_PROFILE.timing_parameters
    assert timing["keyswitch_velocity"] == LEGACY.keyswitch_velocity
    assert timing["note_off_velocity"] == LEGACY.note_off_velocity
    assert timing["keyswitch_length_ticks"] == LEGACY.keyswitch_length_ticks
    assert timing["legato_overlap_ticks"] == LEGACY.legato_overlap_ticks
    assert timing["keyswitch_preroll_ticks"] == LEGACY.keyswitch_preroll_ticks


def test_generic_capabilities_preserve_all_current_legacy_keyswitch_notes():
    assert _keyswitch_note("sustain") == LEGACY.keyswitches["sustain"]
    assert _keyswitch_note("natural_harmonic") == LEGACY.keyswitches["natural_harmonic"]
    assert _keyswitch_note("palm_mute") == LEGACY.keyswitches["palm_mute"]
    assert _keyswitch_note("slide_in") == LEGACY.keyswitches["slide_in_out"]
    assert _keyswitch_note("slide_out") == LEGACY.keyswitches["slide_in_out"]
    assert _keyswitch_note("slide") == LEGACY.keyswitches["legato_slide"]
    assert _keyswitch_note("hammer_on") == LEGACY.keyswitches["hammer_pull"]
    assert _keyswitch_note("pull_off") == LEGACY.keyswitches["hammer_pull"]


def test_linked_legato_capabilities_preserve_overlap_requirement():
    for intent in ("hammer_on", "pull_off", "slide"):
        capability = AMPLE_GUITAR_SC_V4_PROFILE.capability(intent)
        assert capability is not None
        overlap = next(item for item in capability.actions if item.kind == "note_overlap_ticks")
        assert overlap.value == LEGACY.legato_overlap_ticks


def test_persistent_single_note_states_reset_to_legacy_sustain_keyswitch():
    for intent in ("natural_harmonic", "palm_mute", "slide_in", "slide_out"):
        capability = AMPLE_GUITAR_SC_V4_PROFILE.capability(intent)
        assert capability is not None
        reset = next(
            item
            for item in capability.actions
            if item.kind == "keyswitch_note" and item.timing == "after_event"
        )
        assert reset.target == LEGACY.keyswitches["sustain"]


def test_currently_unrendered_intents_are_explicitly_unsupported():
    assert AMPLE_GUITAR_SC_V4_PROFILE.capability("vibrato").support == "unsupported"
    assert AMPLE_GUITAR_SC_V4_PROFILE.capability("pitch_raise").support == "unsupported"


def test_migration_evidence_does_not_claim_official_vendor_provenance():
    assert AMPLE_GUITAR_SC_V4_PROFILE.evidence
    assert all(item.source_type == "repository_regression" for item in AMPLE_GUITAR_SC_V4_PROFILE.evidence)
    assert all(item.status == "verified" for item in AMPLE_GUITAR_SC_V4_PROFILE.evidence)
