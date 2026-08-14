"""Deterministic validation for untrusted LLM rewrite proposals."""

from __future__ import annotations

from typing import Any

from fretpilot.ai.models import (
    RejectedRewriteDecision,
    RewriteProposalDecision,
    ShadowRewriteRequest,
)
from fretpilot.ai.providers.base import AIProviderError
from fretpilot.guitar.instrument import candidate_positions


def _integer(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def validate_rewrite_proposal(
    request: ShadowRewriteRequest,
    payload: dict[str, Any],
    *,
    max_fret: int = 24,
) -> tuple[str, list[RewriteProposalDecision], list[RejectedRewriteDecision]]:
    summary = payload.get("summary", "")
    decisions = payload.get("decisions")
    if not isinstance(summary, str) or not isinstance(decisions, list):
        raise AIProviderError(
            "LLM proposal must contain a string summary and a decisions array."
        )
    if len(decisions) > 128:
        raise AIProviderError("LLM proposal contains too many decisions.")

    source_notes = {
        int(item["source_note_index"]): item for item in request.notes
    }
    accepted: list[RewriteProposalDecision] = []
    rejected: list[RejectedRewriteDecision] = []
    seen_indices: set[int] = set()
    operation_counts = {"delete": 0, "transpose": 0}
    operation_limits = {
        "delete": request.policy.max_delete_count,
        "transpose": request.policy.max_transpose_count,
    }

    for item in decisions:
        raw = item if isinstance(item, dict) else {"value": item}
        errors: list[str] = []
        source_index = _integer(raw.get("source_note_index"))
        operation = raw.get("operation")
        confidence = raw.get("confidence")
        reason = raw.get("reason")
        target_pitch = _integer(raw.get("target_pitch"))

        if source_index is None or source_index not in source_notes:
            errors.append("source_note_index is not present in the bounded context")
        elif source_index in seen_indices:
            errors.append("source_note_index appears more than once")
        if operation not in request.policy.allowed_operations:
            errors.append("operation is not allowed by the fidelity policy")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            errors.append("confidence must be numeric")
        elif not 0.0 <= float(confidence) <= 1.0:
            errors.append("confidence must be between 0 and 1")
        if not isinstance(reason, str) or not reason.strip():
            errors.append("reason must be a non-empty string")
        elif len(reason) > 500:
            errors.append("reason exceeds 500 characters")

        if operation == "transpose":
            if target_pitch is None:
                errors.append("transpose requires an integer target_pitch")
            elif source_index in source_notes:
                source_pitch = int(source_notes[source_index]["pitch"])
                if abs(target_pitch - source_pitch) > request.policy.max_pitch_shift:
                    errors.append("target_pitch exceeds the allowed pitch shift")
                if not candidate_positions(target_pitch, max_fret=max_fret):
                    errors.append("target_pitch is outside the configured fretboard")
        elif target_pitch is not None:
            errors.append("target_pitch is only valid for transpose")

        if operation in operation_counts:
            if operation_counts[operation] >= operation_limits[operation]:
                errors.append(f"{operation} budget is exhausted")

        if errors:
            rejected.append(RejectedRewriteDecision(raw=raw, errors=tuple(errors)))
            continue

        assert source_index is not None
        assert operation in operation_counts
        assert isinstance(reason, str)
        assert isinstance(confidence, (int, float))
        seen_indices.add(source_index)
        operation_counts[operation] += 1
        accepted.append(
            RewriteProposalDecision(
                source_note_index=source_index,
                operation=operation,
                target_pitch=target_pitch,
                confidence=round(float(confidence), 6),
                reason=reason.strip(),
            )
        )

    return summary.strip()[:2000], accepted, rejected
