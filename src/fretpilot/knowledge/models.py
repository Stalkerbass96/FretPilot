"""Shared contracts for versioned FretPilot knowledge assets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


VALID_KNOWLEDGE_STATUSES = frozenset(
    {"candidate", "evaluated", "approved", "deprecated"}
)


@dataclass(frozen=True, slots=True)
class KnowledgeProvenance:
    """Where one knowledge item came from and how it may be used."""

    source_type: str = "hand_authored"
    reference: str | None = None
    license: str | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class KnowledgeEvaluation:
    """Evaluation identity attached to a knowledge item."""

    benchmark_version: str | None = None
    status: str = "untested"
    notes: str = ""


@dataclass(frozen=True, slots=True)
class KnowledgeEntry:
    """One independently identifiable piece of versioned knowledge."""

    knowledge_id: str
    domain: str
    kind: str
    schema_version: str
    knowledge_version: str
    status: str
    payload: Mapping[str, Any]
    scope: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    provenance: KnowledgeProvenance = KnowledgeProvenance()
    evaluation: KnowledgeEvaluation = KnowledgeEvaluation()

    def __post_init__(self) -> None:
        if not self.knowledge_id:
            raise ValueError("knowledge_id cannot be empty.")
        if not self.domain or not self.kind:
            raise ValueError("knowledge domain and kind cannot be empty.")
        if self.status not in VALID_KNOWLEDGE_STATUSES:
            raise ValueError(
                f"Unsupported knowledge status {self.status!r}; "
                f"expected one of {sorted(VALID_KNOWLEDGE_STATUSES)}."
            )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> KnowledgeEntry:
        scope = {
            str(key): tuple(str(item) for item in values)
            for key, values in dict(data.get("scope", {})).items()
        }
        return cls(
            knowledge_id=str(data["knowledge_id"]),
            domain=str(data["domain"]),
            kind=str(data["kind"]),
            schema_version=str(data["schema_version"]),
            knowledge_version=str(data["knowledge_version"]),
            status=str(data["status"]),
            payload=dict(data.get("payload", {})),
            scope=scope,
            provenance=KnowledgeProvenance(**dict(data.get("provenance", {}))),
            evaluation=KnowledgeEvaluation(**dict(data.get("evaluation", {}))),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class KnowledgeSnapshot:
    """A pinned collection of knowledge entries used by one runtime build."""

    snapshot_version: str
    schema_version: str
    status: str
    entries: tuple[KnowledgeEntry, ...]

    def __post_init__(self) -> None:
        if self.status not in VALID_KNOWLEDGE_STATUSES:
            raise ValueError(
                f"Unsupported knowledge status {self.status!r}; "
                f"expected one of {sorted(VALID_KNOWLEDGE_STATUSES)}."
            )
        identifiers = [entry.knowledge_id for entry in self.entries]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique within one snapshot.")
        mismatched = [
            entry.knowledge_id
            for entry in self.entries
            if entry.knowledge_version != self.snapshot_version
        ]
        if mismatched:
            raise ValueError(
                "knowledge entries must match their snapshot version: "
                + ", ".join(mismatched)
            )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> KnowledgeSnapshot:
        return cls(
            snapshot_version=str(data["snapshot_version"]),
            schema_version=str(data["schema_version"]),
            status=str(data["status"]),
            entries=tuple(
                KnowledgeEntry.from_dict(item)
                for item in data.get("entries", [])
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
