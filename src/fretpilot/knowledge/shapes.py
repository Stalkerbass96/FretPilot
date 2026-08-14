"""Reusable, tuning-scoped fretboard shape prototypes."""

from __future__ import annotations

from dataclasses import dataclass

from fretpilot.knowledge.models import KnowledgeEntry
from fretpilot.knowledge.registry import get_builtin_knowledge_registry


@dataclass(frozen=True, slots=True)
class ShapeNote:
    string_offset: int
    fret_offset: int
    interval_semitones: int
    function: str


@dataclass(frozen=True, slots=True)
class GuitarShapePrototype:
    shape_id: str
    label: str
    coordinate_system: str
    notes: tuple[ShapeNote, ...]
    tuning_families: tuple[str, ...]
    knowledge_id: str
    knowledge_version: str
    status: str


def _shape_from_entry(entry: KnowledgeEntry) -> GuitarShapePrototype:
    payload = entry.payload
    coordinate_system = str(payload["coordinate_system"])
    if coordinate_system != "relative_string_fret":
        raise ValueError(f"Unsupported shape coordinate system {coordinate_system!r}.")
    notes = tuple(ShapeNote(**item) for item in payload["notes"])
    if not notes:
        raise ValueError("A guitar shape must contain at least one note.")
    return GuitarShapePrototype(
        shape_id=str(payload["shape_id"]),
        label=str(payload["label"]),
        coordinate_system=coordinate_system,
        notes=notes,
        tuning_families=tuple(payload.get("tuning_families", ())),
        knowledge_id=entry.knowledge_id,
        knowledge_version=entry.knowledge_version,
        status=entry.status,
    )


def list_guitar_shapes() -> tuple[GuitarShapePrototype, ...]:
    registry = get_builtin_knowledge_registry()
    return tuple(
        _shape_from_entry(entry)
        for entry in registry.query(domain="guitar_playing", kind="shape_prototype")
    )


def get_guitar_shape(shape_id: str) -> GuitarShapePrototype | None:
    return next(
        (shape for shape in list_guitar_shapes() if shape.shape_id == shape_id),
        None,
    )
