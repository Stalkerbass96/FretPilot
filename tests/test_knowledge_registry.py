from __future__ import annotations

import json
from pathlib import Path

import pytest

from fretpilot.knowledge import (
    BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION,
    KnowledgeEntry,
    get_builtin_knowledge_registry,
    get_guitar_shape,
    load_knowledge_snapshot,
)


def test_builtin_snapshot_exposes_versioned_playing_profiles() -> None:
    registry = get_builtin_knowledge_registry()
    entries = registry.query(domain="guitar_playing", kind="playing_profile")

    assert registry.snapshot.snapshot_version == BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION
    assert registry.snapshot.status == "approved"
    assert {entry.payload["profile_id"] for entry in entries} == {
        "solo",
        "riff",
        "strumming",
        "metal",
        "jazz",
        "rock_arpeggio",
    }
    assert all(entry.provenance.source_type == "hand_authored" for entry in entries)
    assert all(entry.status == "approved" for entry in entries)


def test_shape_library_contains_relative_reusable_prototypes() -> None:
    power_chord = get_guitar_shape("power_chord")
    octave = get_guitar_shape("octave")
    sus2 = get_guitar_shape("sus2_arpeggio")
    triad = get_guitar_shape("triad_inversion")

    assert power_chord is not None
    assert octave is not None
    assert sus2 is not None
    assert triad is not None
    assert power_chord.coordinate_system == "relative_string_fret"
    assert [note.interval_semitones for note in power_chord.notes] == [0, 7, 12]
    assert power_chord.status == "candidate"


def test_total_rock_guitar_candidate_covers_every_lesson() -> None:
    registry = get_builtin_knowledge_registry()
    entries = [
        entry
        for entry in registry.query(domain="guitar_playing")
        if entry.provenance.source_type == "user_provided_reference"
    ]

    assert len(entries) == 71
    assert {entry.kind for entry in entries} == {
        "execution_rule",
        "harmonic_context",
        "phrase_pattern",
        "rhythm_rule",
        "shape_family",
    }
    assert all(entry.status == "candidate" for entry in entries)
    assert all(entry.evaluation.status == "untested" for entry in entries)
    assert all(entry.provenance.license for entry in entries)

    covered_lessons = {
        lesson
        for entry in entries
        for section in entry.payload["source_sections"]
        for lesson in range(1, 23)
        if section.startswith(f"Lesson {lesson} ")
    }
    assert covered_lessons == set(range(1, 23))


def test_reference_candidates_do_not_change_approved_runtime_profiles() -> None:
    registry = get_builtin_knowledge_registry()

    approved_profiles = registry.query(
        domain="guitar_playing",
        kind="playing_profile",
        statuses={"approved"},
    )

    assert {entry.payload["profile_id"] for entry in approved_profiles} == {
        "solo",
        "riff",
        "strumming",
        "metal",
        "jazz",
        "rock_arpeggio",
    }


def test_registry_filters_entries_by_scope() -> None:
    registry = get_builtin_knowledge_registry()

    riff_entries = registry.query(
        domain="guitar_playing",
        kind="playing_profile",
        scope={"roles": "riff"},
    )

    assert [entry.payload["profile_id"] for entry in riff_entries] == ["riff"]


def test_knowledge_entry_rejects_unknown_lifecycle_status() -> None:
    with pytest.raises(ValueError, match="knowledge status"):
        KnowledgeEntry(
            knowledge_id="broken",
            domain="guitar_playing",
            kind="playing_profile",
            schema_version="1",
            knowledge_version="1",
            status="latest",
            payload={},
        )


def test_loader_rejects_an_incompatible_snapshot_schema(tmp_path: Path) -> None:
    path = tmp_path / "incompatible.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "999",
                "snapshot_version": "future",
                "status": "candidate",
                "entries": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported knowledge schema"):
        load_knowledge_snapshot(path)
