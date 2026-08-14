"""Pinned snapshot loading and read-only knowledge lookup."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
import json
from pathlib import Path
from typing import Iterable, Mapping

from fretpilot.knowledge.models import KnowledgeEntry, KnowledgeSnapshot


BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION = "2026.08.1"
BUILTIN_KNOWLEDGE_RESOURCE = "assets/knowledge-2026.08.1.json"
SUPPORTED_KNOWLEDGE_SCHEMA_VERSION = "1"


class KnowledgeRegistry:
    """Query one explicit knowledge snapshot without mutating it at runtime."""

    def __init__(self, snapshot: KnowledgeSnapshot) -> None:
        self.snapshot = snapshot
        self._by_id = {entry.knowledge_id: entry for entry in snapshot.entries}

    def get(self, knowledge_id: str) -> KnowledgeEntry | None:
        return self._by_id.get(knowledge_id)

    def query(
        self,
        *,
        domain: str | None = None,
        kind: str | None = None,
        statuses: Iterable[str] | None = None,
        scope: Mapping[str, str] | None = None,
    ) -> list[KnowledgeEntry]:
        allowed_statuses = set(statuses) if statuses is not None else None
        result: list[KnowledgeEntry] = []
        for entry in self.snapshot.entries:
            if domain is not None and entry.domain != domain:
                continue
            if kind is not None and entry.kind != kind:
                continue
            if allowed_statuses is not None and entry.status not in allowed_statuses:
                continue
            if scope and any(
                value not in entry.scope.get(key, ())
                for key, value in scope.items()
            ):
                continue
            result.append(entry)
        return result


def load_knowledge_snapshot(path: str | Path) -> KnowledgeSnapshot:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    snapshot = KnowledgeSnapshot.from_dict(payload)
    if snapshot.schema_version != SUPPORTED_KNOWLEDGE_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported knowledge schema {snapshot.schema_version!r}; "
            f"expected {SUPPORTED_KNOWLEDGE_SCHEMA_VERSION!r}."
        )
    return snapshot


@lru_cache(maxsize=1)
def get_builtin_knowledge_registry() -> KnowledgeRegistry:
    resource = files("fretpilot.knowledge").joinpath(BUILTIN_KNOWLEDGE_RESOURCE)
    payload = json.loads(resource.read_text(encoding="utf-8"))
    snapshot = KnowledgeSnapshot.from_dict(payload)
    if snapshot.schema_version != SUPPORTED_KNOWLEDGE_SCHEMA_VERSION:
        raise ValueError(
            "Built-in knowledge asset uses an unsupported schema version."
        )
    if snapshot.snapshot_version != BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION:
        raise ValueError(
            "Built-in knowledge asset version does not match the runtime pin."
        )
    if snapshot.status != "approved":
        raise ValueError("The built-in runtime knowledge snapshot must be approved.")
    return KnowledgeRegistry(snapshot)
