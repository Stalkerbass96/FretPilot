"""Compile approved VI capabilities into a deterministic target control plan.

This is a shadow planning layer: it resolves canonical Guitar IR articulations
through provider-neutral capability negotiation and schedules generic
``ControlAction`` records, but it does not emit MIDI.  The plan can therefore be
compared against a legacy adapter before replacing any proven scheduling code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fretpilot.ir.models import GuitarNoteEvent, GuitarProjectIR
from fretpilot.virtual_instruments.models import (
    ControlAction,
    VirtualGuitarInstrumentProfile,
)
from fretpilot.virtual_instruments.negotiation import negotiate_intent


@dataclass(frozen=True, slots=True)
class ScheduledControlAction:
    tick: int
    source_event_id: str | None
    requested_intent: str
    resolved_intent: str
    action: ControlAction


@dataclass(frozen=True, slots=True)
class NoteEndExtension:
    source_event_id: str
    minimum_end_tick: int
    requested_intent: str


@dataclass(slots=True)
class VirtualInstrumentControlPlan:
    profile_id: str
    ticks_per_beat: int
    timeline_offset_ticks: int
    controls: list[ScheduledControlAction] = field(default_factory=list)
    note_end_extensions: list[NoteEndExtension] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _timing_int(profile: VirtualGuitarInstrumentProfile, key: str) -> int:
    value = profile.timing_parameters.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"Profile {profile.profile_id!r} timing parameter {key!r} must be numeric."
        )
    integer = int(value)
    if abs(float(value) - integer) > 1e-9:
        raise ValueError(
            f"Profile {profile.profile_id!r} timing parameter {key!r} must be integer-valued."
        )
    return integer


def _flatten_events(project: GuitarProjectIR) -> list[GuitarNoteEvent]:
    if not project.tracks:
        return []
    return [event for measure in project.tracks[0].measures for event in measure.events]


def _event_ticks(
    event: GuitarNoteEvent,
    *,
    ticks_per_beat: int,
    timeline_offset_ticks: int,
) -> tuple[int, int]:
    start = round(event.performance.source_start_beat * ticks_per_beat) + timeline_offset_ticks
    duration = max(1, round(event.performance.source_duration_beats * ticks_per_beat))
    return start, start + duration


def _initial_controls(
    profile: VirtualGuitarInstrumentProfile,
) -> list[ScheduledControlAction]:
    controls: list[ScheduledControlAction] = []
    for capability in profile.capabilities:
        if capability.support not in {"native", "approximated"}:
            continue
        for action in capability.actions:
            if action.timing != "initial_state":
                continue
            controls.append(
                ScheduledControlAction(
                    tick=0,
                    source_event_id=None,
                    requested_intent=capability.intent,
                    resolved_intent=capability.intent,
                    action=action,
                )
            )
    return controls


def build_control_plan(
    project: GuitarProjectIR,
    profile: VirtualGuitarInstrumentProfile,
    *,
    ticks_per_beat: int = 480,
) -> VirtualInstrumentControlPlan:
    """Compile supported articulation capabilities into a generic control plan."""

    if ticks_per_beat <= 0:
        raise ValueError("ticks_per_beat must be positive")

    preroll = _timing_int(profile, "keyswitch_preroll_ticks")
    configured_overlap = _timing_int(profile, "legato_overlap_ticks")
    timeline_offset = max(0, preroll, configured_overlap)
    plan = VirtualInstrumentControlPlan(
        profile_id=profile.profile_id,
        ticks_per_beat=ticks_per_beat,
        timeline_offset_ticks=timeline_offset,
        controls=_initial_controls(profile),
    )

    events = _flatten_events(project)
    by_id = {event.id: event for event in events}
    start_ticks: dict[str, int] = {}
    end_ticks: dict[str, int] = {}
    for event in events:
        start, end = _event_ticks(
            event,
            ticks_per_beat=ticks_per_beat,
            timeline_offset_ticks=timeline_offset,
        )
        start_ticks[event.id] = start
        end_ticks[event.id] = end

    resolved_items: list[tuple[GuitarNoteEvent, object, object, GuitarNoteEvent | None]] = []
    for event in events:
        for articulation in event.articulations:
            resolution = negotiate_intent(profile, articulation.type)
            if not resolution.supported or resolution.resolved_intent is None:
                plan.warnings.append(
                    f"Skipped unsupported target intent {articulation.type!r} on {event.id}."
                )
                continue
            has_linked_action = any(
                action.kind == "note_overlap_ticks" or action.timing == "linked_transition"
                for action in resolution.actions
            )
            source_event = None
            if has_linked_action:
                if articulation.source_note_id is None:
                    plan.warnings.append(
                        f"Skipped linked target intent {articulation.type!r} on {event.id}: source note id is missing."
                    )
                    continue
                source_event = by_id.get(articulation.source_note_id)
                if source_event is None:
                    plan.warnings.append(
                        f"Skipped linked target intent {articulation.type!r} on {event.id}: source note {articulation.source_note_id!r} was not exported."
                    )
                    continue
            resolved_items.append((event, articulation, resolution, source_event))

    # First apply linked note-end extensions. The legacy renderer performs these
    # before scheduling momentary reset controls, so later after-event actions
    # must see the extended end tick when the same note participates in both.
    for event, articulation, resolution, source_event in resolved_items:
        if source_event is None:
            continue
        for action in resolution.actions:
            if action.kind != "note_overlap_ticks":
                continue
            if isinstance(action.value, bool) or not isinstance(action.value, (int, float)):
                raise ValueError(
                    f"Profile {profile.profile_id!r} note_overlap_ticks value must be numeric."
                )
            overlap = int(action.value)
            minimum_end = start_ticks[event.id] + overlap
            end_ticks[source_event.id] = max(end_ticks[source_event.id], minimum_end)
            plan.note_end_extensions.append(
                NoteEndExtension(
                    source_event_id=source_event.id,
                    minimum_end_tick=minimum_end,
                    requested_intent=articulation.type,
                )
            )

    # Then schedule control actions using the effective note ends above.
    for event, articulation, resolution, source_event in resolved_items:
        linked = source_event is not None
        anchor = source_event if linked else event
        for action in resolution.actions:
            if action.kind == "note_overlap_ticks":
                continue
            if action.timing == "initial_state":
                continue
            if action.timing == "preroll":
                tick = max(0, start_ticks[anchor.id] - preroll)
            elif action.timing == "after_event":
                tick = max(start_ticks[event.id], end_ticks[event.id])
            elif action.timing in {"immediate", "on_event"}:
                tick = start_ticks[event.id]
            else:
                plan.warnings.append(
                    f"Skipped unsupported ControlAction timing {action.timing!r} for {articulation.type!r} on {event.id}."
                )
                continue
            plan.controls.append(
                ScheduledControlAction(
                    tick=tick,
                    source_event_id=event.id,
                    requested_intent=articulation.type,
                    resolved_intent=resolution.resolved_intent,
                    action=action,
                )
            )

    plan.controls.sort(
        key=lambda item: (
            item.tick,
            item.source_event_id or "",
            item.requested_intent,
            item.action.kind,
            str(item.action.target),
        )
    )
    plan.note_end_extensions.sort(
        key=lambda item: (item.source_event_id, item.minimum_end_tick, item.requested_intent)
    )
    return plan
