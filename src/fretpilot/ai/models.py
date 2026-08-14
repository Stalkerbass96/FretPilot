"""Provider-neutral contracts for optional AI musical advice."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class AIProviderIdentity:
    provider_id: str
    model: str
    endpoint_origin: str


@dataclass(frozen=True, slots=True)
class ShadowRewritePolicy:
    midi_fidelity: float
    allowed_operations: tuple[str, ...]
    max_delete_count: int
    max_transpose_count: int
    max_pitch_shift: int
    max_context_notes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ShadowRewriteRequest:
    source_label: str
    stream: dict[str, Any]
    musical_features: dict[str, Any]
    policy: ShadowRewritePolicy
    notes: tuple[dict[str, Any], ...]
    deterministic_changes: tuple[dict[str, Any], ...]
    knowledge_snapshot_version: str
    context_truncated: bool = False
    format_version: str = "0.1"

    @property
    def request_id(self) -> str:
        payload = json.dumps(
            self.to_provider_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"shadow-{sha256(payload).hexdigest()[:16]}"

    def to_provider_payload(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "source_label": self.source_label,
            "stream": self.stream,
            "musical_features": self.musical_features,
            "policy": self.policy.to_dict(),
            "notes": list(self.notes),
            "deterministic_changes": list(self.deterministic_changes),
            "knowledge_snapshot_version": self.knowledge_snapshot_version,
            "context_truncated": self.context_truncated,
        }


@dataclass(frozen=True, slots=True)
class RewriteProposalDecision:
    source_note_index: int
    operation: str
    confidence: float
    reason: str
    target_pitch: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RejectedRewriteDecision:
    raw: dict[str, Any]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"raw": self.raw, "errors": list(self.errors)}


@dataclass(slots=True)
class ShadowRewriteReport:
    request: ShadowRewriteRequest
    provider: AIProviderIdentity
    summary: str
    accepted_decisions: list[RewriteProposalDecision] = field(default_factory=list)
    rejected_decisions: list[RejectedRewriteDecision] = field(default_factory=list)
    mode: str = "shadow"
    applied: bool = False
    format_version: str = "0.1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "mode": self.mode,
            "applied": self.applied,
            "request_id": self.request.request_id,
            "provider": asdict(self.provider),
            "source_label": self.request.source_label,
            "stream_id": self.request.stream["stream_id"],
            "context": {
                "note_count": len(self.request.notes),
                "truncated": self.request.context_truncated,
                "knowledge_snapshot_version": (
                    self.request.knowledge_snapshot_version
                ),
            },
            "policy": self.request.policy.to_dict(),
            "summary": self.summary,
            "accepted_decisions": [
                item.to_dict() for item in self.accepted_decisions
            ],
            "rejected_decisions": [
                item.to_dict() for item in self.rejected_decisions
            ],
        }
