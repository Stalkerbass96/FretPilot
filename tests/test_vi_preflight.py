import pytest

from fretpilot.virtual_instruments.capability_report import (
    CapabilityReport,
    CapabilityRequirement,
)
from fretpilot.virtual_instruments.negotiation import CapabilityResolution
from fretpilot.virtual_instruments.preflight import evaluate_capability_report


def _report() -> CapabilityReport:
    return CapabilityReport(
        profile_id="fixture",
        requirements=(
            CapabilityRequirement(
                intent="native",
                source="articulation",
                occurrences=2,
                resolution=CapabilityResolution(
                    requested_intent="native",
                    resolved_intent="native",
                    support="native",
                ),
            ),
            CapabilityRequirement(
                intent="approx",
                source="articulation",
                occurrences=1,
                resolution=CapabilityResolution(
                    requested_intent="approx",
                    resolved_intent="fallback",
                    support="approximated",
                    fallback_chain=("approx", "fallback"),
                ),
            ),
            CapabilityRequirement(
                intent="missing",
                source="right_hand",
                occurrences=3,
                resolution=CapabilityResolution(
                    requested_intent="missing",
                    resolved_intent=None,
                    support="unsupported",
                ),
            ),
        ),
    )


def test_report_only_never_changes_render_decision_or_warnings():
    result = evaluate_capability_report(_report(), mode="report_only")
    assert result.can_render is True
    assert result.warnings == ()
    assert result.errors == ()


def test_warn_surfaces_approximated_and_unsupported_without_blocking():
    result = evaluate_capability_report(_report(), mode="warn")
    assert result.can_render is True
    assert len(result.warnings) == 2
    assert result.errors == ()
    assert any("approx" in item and "approximated" in item for item in result.warnings)
    assert any("missing" in item and "unsupported" in item for item in result.warnings)


def test_strict_blocks_only_unsupported_and_keeps_approximation_as_warning():
    result = evaluate_capability_report(_report(), mode="strict")
    assert result.can_render is False
    assert len(result.warnings) == 1
    assert "approx" in result.warnings[0]
    assert len(result.errors) == 1
    assert "missing" in result.errors[0]


def test_unknown_preflight_mode_is_rejected():
    with pytest.raises(ValueError, match="Unknown capability policy"):
        evaluate_capability_report(_report(), mode="invalid")  # type: ignore[arg-type]
