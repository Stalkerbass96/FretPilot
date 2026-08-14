"""Shared contracts for versioned FretPilot knowledge assets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


VALID_KNOWLEDGE_STATUSES = frozenset(
    {"candidate", "evaluated", "approved", "deprecated"}
)


@dataclass(slots=True)
class BehaviorProfileMatch:
    """One explainable match against a guitar-behavior knowledge profile."""

    profile_id: str
    label: str
    score: float
    status: str
    matched_features: list[str] = field(default_factory=list)
    missing_features: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class KnowledgeSource:
    """One reusable source record referenced by any number of entries."""

    source_id: str
    source_type: str
    title: str
    creator: str | None = None
    reference: str | None = None
    license: str | None = None
    allowed_uses: tuple[str, ...] = ()
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> KnowledgeSource:
        return cls(
            source_id=str(data["source_id"]),
            source_type=str(data["source_type"]),
            title=str(data["title"]),
            creator=(str(data["creator"]) if data.get("creator") else None),
            reference=(str(data["reference"]) if data.get("reference") else None),
            license=(str(data["license"]) if data.get("license") else None),
            allowed_uses=tuple(str(item) for item in data.get("allowed_uses", ())),
            notes=str(data.get("notes", "")),
        )


@dataclass(frozen=True, slots=True)
class KnowledgeProvenance:
    """Where one knowledge item came from and how it may be used."""

    source_type: str = "hand_authored"
    reference: str | None = None
    license: str | None = None
    notes: str = ""
    source_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> KnowledgeProvenance:
        return cls(
            source_type=str(data.get("source_type", "hand_authored")),
            reference=(str(data["reference"]) if data.get("reference") else None),
            license=(str(data["license"]) if data.get("license") else None),
            notes=str(data.get("notes", "")),
            source_ids=tuple(str(item) for item in data.get("source_ids", ())),
        )


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
            provenance=KnowledgeProvenance.from_dict(
                dict(data.get("provenance", {}))
            ),
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
    sources: tuple[KnowledgeSource, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in VALID_KNOWLEDGE_STATUSES:
            raise ValueError(
                f"Unsupported knowledge status {self.status!r}; "
                f"expected one of {sorted(VALID_KNOWLEDGE_STATUSES)}."
            )
        identifiers = [entry.knowledge_id for entry in self.entries]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique within one snapshot.")
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("knowledge source IDs must be unique within one snapshot.")
        unknown_source_ids = sorted(
            {
                source_id
                for entry in self.entries
                for source_id in entry.provenance.source_ids
                if source_id not in source_ids
            }
        )
        if unknown_source_ids:
            raise ValueError(
                "knowledge entries reference unknown sources: "
                + ", ".join(unknown_source_ids)
            )
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
            sources=tuple(
                KnowledgeSource.from_dict(item)
                for item in data.get("sources", [])
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
