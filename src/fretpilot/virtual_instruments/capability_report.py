"""Read-only capability reports for canonical guitar/performance intent.

The report inventories musical requirements already present in Guitar IR and an
optional Generic PerformancePlan, then resolves each requirement against one
approved virtual-instrument profile. It never emits target MIDI/control events
and never mutates canonical source data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fretpilot.ir.models import GuitarProjectIR
from fretpilot.performance.models import GuitarPerformancePlan
from fretpilot.virtual_instruments.models import VirtualGuitarInstrumentProfile
from fretpilot.virtual_instruments.negotiation import (
    CapabilityResolution,
    negotiate_intent,
)


_EPSILON = 1e-9


@dataclass(frozen=True, slots=True)
class CapabilityRequirement:
    """One aggregated canonical requirement and its target resolution."""

    intent: str
    source: str
    occurrences: int
    resolution: CapabilityResolution


@dataclass(frozen=True, slots=True)
class CapabilityReport:
    """Deterministic target-support snapshot for one project/profile pair."""

    profile_id: str
    requirements: tuple[CapabilityRequirement, ...]

    @property
    def native_count(self) -> int:
        return sum(item.occurrences for item in self.requirements if item.resolution.support == "native")

    @property
    def approximated_count(self) -> int:
        return sum(item.occurrences for item in self.requirements if item.resolution.support == "approximated")

    @property
    def unsupported_count(self) -> int:
        return sum(item.occurrences for item in self.requirements if item.resolution.support == "unsupported")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["summary"] = {
            "native_occurrences": self.native_count,
            "approximated_occurrences": self.approximated_count,
            "unsupported_occurrences": self.unsupported_count,
        }
        return payload


def _increment(counts: dict[tuple[str, str], int], source: str, intent: str) -> None:
    key = (source, intent)
    counts[key] = counts.get(key, 0) + 1


def _collect_ir_requirements(
    project: GuitarProjectIR,
    counts: dict[tuple[str, str], int],
) -> None:
    seen_articulations: set[tuple[int, str, str | None]] = set()
    seen_right_hand: set[tuple[int, str, str, str | None]] = set()

    for track in project.tracks:
        for measure in track.measures:
            for event in measure.events:
                for articulation in event.articulations:
                    key = (
                        event.source_note_index,
                        articulation.type,
                        articulation.source_note_id,
                    )
                    if key in seen_articulations:
                        continue
                    seen_articulations.add(key)
                    _increment(counts, "articulation", articulation.type)

                right_hand = event.right_hand
                if right_hand is None:
                    continue
                key = (
                    event.source_note_index,
                    right_hand.motion,
                    right_hand.direction,
                    right_hand.technique,
                )
                if key in seen_right_hand:
                    continue
                seen_right_hand.add(key)

                if right_hand.motion in {"pick", "strum"} and right_hand.direction in {"down", "up"}:
                    _increment(
                        counts,
                        "right_hand",
                        f"{right_hand.motion}_{right_hand.direction}",
                    )
                if right_hand.technique:
                    _increment(counts, "right_hand", right_hand.technique)


def _collect_performance_requirements(
    performance_plan: GuitarPerformancePlan | None,
    counts: dict[tuple[str, str], int],
) -> None:
    if performance_plan is None:
        return

    for note in performance_plan.notes:
        if abs(float(note.timing_offset_beats)) > _EPSILON:
            _increment(counts, "performance_plan", "performance_timing_adjustment")
        if abs(float(note.duration_delta_beats)) > _EPSILON:
            _increment(counts, "performance_plan", "performance_duration_adjustment")
        if int(note.velocity_delta) != 0:
            _increment(counts, "performance_plan", "performance_velocity_adjustment")


def build_capability_report(
    project: GuitarProjectIR,
    profile: VirtualGuitarInstrumentProfile,
    *,
    performance_plan: GuitarPerformancePlan | None = None,
) -> CapabilityReport:
    """Inventory actual canonical intents and resolve target support explicitly."""

    counts: dict[tuple[str, str], int] = {}
    _collect_ir_requirements(project, counts)
    _collect_performance_requirements(performance_plan, counts)

    requirements = tuple(
        CapabilityRequirement(
            intent=intent,
            source=source,
            occurrences=occurrences,
            resolution=negotiate_intent(profile, intent),
        )
        for (source, intent), occurrences in sorted(counts.items())
    )
    return CapabilityReport(
        profile_id=profile.profile_id,
        requirements=requirements,
    )
