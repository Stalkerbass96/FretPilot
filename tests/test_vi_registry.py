import pytest

from fretpilot.virtual_instruments.ample_guitar_sc import AMPLE_GUITAR_SC_V4_PROFILE
from fretpilot.virtual_instruments.registry import get_profile, list_profiles


def test_registry_contains_migrated_ample_profile_once():
    profiles = list_profiles()
    assert [item.profile_id for item in profiles] == ["ample-guitar-sc-v4"]
    assert profiles[0] is AMPLE_GUITAR_SC_V4_PROFILE


def test_registry_resolves_stable_profile_id():
    assert get_profile("ample-guitar-sc-v4") is AMPLE_GUITAR_SC_V4_PROFILE


def test_registry_rejects_unknown_profile_with_available_ids():
    with pytest.raises(ValueError) as exc_info:
        get_profile("missing-guitar")
    message = str(exc_info.value)
    assert "missing-guitar" in message
    assert "ample-guitar-sc-v4" in message


def test_registry_snapshot_is_immutable_tuple():
    assert isinstance(list_profiles(), tuple)
