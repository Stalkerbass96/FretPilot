"""Contracts returned by the prototype conversion pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from fretpilot.knowledge import BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION


@dataclass(slots=True)
class PrototypeOutputStatus:
    path: str | None
    status: str
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(slots=True)
class PrototypeStreamResult:
    stream_id: str
    directory: str
    analysis: PrototypeOutputStatus
    rewrite: PrototypeOutputStatus
    guitar_ir: PrototypeOutputStatus
    pdf: PrototypeOutputStatus
    gp5: PrototypeOutputStatus
    ample_sc_midi: PrototypeOutputStatus
    performance_plan: PrototypeOutputStatus
    vi_capabilities: PrototypeOutputStatus
    report: PrototypeOutputStatus

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PrototypeManifest:
    source: str
    output_directory: str
    stream_results: list[PrototypeStreamResult]
    selected_stream_ids: list[str]
    knowledge_snapshot_version: str = BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION
    format_version: str = "0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
