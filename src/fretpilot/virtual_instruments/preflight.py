"""Explicit policy for applying capability reports before target rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fretpilot.virtual_instruments.capability_report import CapabilityReport


CapabilityPolicyMode = Literal["report_only", "warn", "strict"]


@dataclass(frozen=True, slots=True)
class RenderCapabilityPreflight:
    profile_id: str
    mode: CapabilityPolicyMode
    can_render: bool
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def _message(source: str, intent: str, occurrences: int, support: str) -> str:
    return (
        f"Target capability {intent!r} from {source} occurs {occurrences} time(s) "
        f"and resolves as {support}."
    )


def evaluate_capability_report(
    report: CapabilityReport,
    *,
    mode: CapabilityPolicyMode = "report_only",
) -> RenderCapabilityPreflight:
    """Turn target support diagnostics into an explicit render policy decision.

    ``report_only`` preserves legacy behavior and emits no render warnings.
    ``warn`` allows rendering while surfacing approximated/unsupported intent.
    ``strict`` still allows approximations with warnings, but blocks rendering
    when any actually requested intent is unsupported.
    """

    if mode not in {"report_only", "warn", "strict"}:
        raise ValueError(f"Unknown capability policy mode {mode!r}.")

    if mode == "report_only":
        return RenderCapabilityPreflight(
            profile_id=report.profile_id,
            mode=mode,
            can_render=True,
        )

    warnings: list[str] = []
    errors: list[str] = []
    for item in report.requirements:
        support = item.resolution.support
        if support == "native":
            continue
        message = _message(item.source, item.intent, item.occurrences, support)
        if mode == "strict" and support == "unsupported":
            errors.append(message)
        else:
            warnings.append(message)

    return RenderCapabilityPreflight(
        profile_id=report.profile_id,
        mode=mode,
        can_render=not errors,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
