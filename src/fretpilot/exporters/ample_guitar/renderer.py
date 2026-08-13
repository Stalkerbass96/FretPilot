"""Render Guitar IR as performance MIDI for Ample Guitar."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import mido

from fretpilot.exporters.ample_guitar.profiles import (
    AMPLE_GUITAR_SC_V4,
    AmpleGuitarProfile,
)
from fretpilot.ir.models import GuitarNoteEvent, GuitarProjectIR, IRArticulation


@dataclass(slots=True)
class AmpleExportResult:
    path: str
    profile_id: str
    source_note_count: int
    keyswitch_count: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "profile_id": self.profile_id,
            "source_note_count": self.source_note_count,
            "keyswitch_count": self.keyswitch_count,
            "warnings": self.warnings,
        }


@dataclass(slots=True)
class _SourceNote:
    source_note_index: int
    pitch: int
    start_tick: int
    end_tick: int
    velocity: int
    articulations: list[IRArticulation] = field(default_factory=list)


def _beat_to_tick(beat: float, ticks_per_beat: int) -> int:
    return int(round(beat * ticks_per_beat))


def _collect_source_notes(
    project: GuitarProjectIR,
    ticks_per_beat: int,
    timeline_offset: int,
) -> tuple[dict[int, _SourceNote], dict[str, int]]:
    source_notes: dict[int, _SourceNote] = {}
    event_id_to_source: dict[str, int] = {}

    for track in project.tracks:
        for measure in track.measures:
            for event in measure.events:
                event_id_to_source[event.id] = event.source_note_index
                existing = source_notes.get(event.source_note_index)
                if existing is None:
                    start_tick = (
                        _beat_to_tick(
                            event.performance.source_start_beat,
                            ticks_per_beat,
                        )
                        + timeline_offset
                    )
                    duration_tick = max(
                        1,
                        _beat_to_tick(
                            event.performance.source_duration_beats,
                            ticks_per_beat,
                        ),
                    )
                    existing = _SourceNote(
                        source_note_index=event.source_note_index,
                        pitch=event.pitch,
                        start_tick=start_tick,
                        end_tick=start_tick + duration_tick,
                        velocity=max(1, min(127, event.performance.velocity)),
                    )
                    source_notes[event.source_note_index] = existing

                # Articulations live on the first score fragment. Tied fragments
                # repeat performance timing but do not create duplicate MIDI notes.
                known = {
                    (
                        item.type,
                        item.source_note_id,
                        round(item.confidence, 6),
                    )
                    for item in existing.articulations
                }
                for articulation in event.articulations:
                    key = (
                        articulation.type,
                        articulation.source_note_id,
                        round(articulation.confidence, 6),
                    )
                    if key not in known:
                        existing.articulations.append(articulation)
                        known.add(key)

    return source_notes, event_id_to_source


def _add_keyswitch(
    events: list[tuple[int, int, mido.Message]],
    emitted: set[tuple[int, int]],
    *,
    tick: int,
    note: int,
    profile: AmpleGuitarProfile,
) -> bool:
    key = (tick, note)
    if key in emitted:
        return False
    emitted.add(key)
    events.append(
        (
            tick,
            0,
            mido.Message(
                "note_on",
                channel=profile.note_channel,
                note=note,
                velocity=profile.keyswitch_velocity,
                time=0,
            ),
        )
    )
    events.append(
        (
            tick + profile.keyswitch_length_ticks,
            1,
            mido.Message(
                "note_off",
                channel=profile.note_channel,
                note=note,
                velocity=0,
                time=0,
            ),
        )
    )
    return True


def _schedule_articulations(
    source_notes: dict[int, _SourceNote],
    event_id_to_source: dict[str, int],
    profile: AmpleGuitarProfile,
    events: list[tuple[int, int, mido.Message]],
    warnings: list[str],
) -> int:
    emitted: set[tuple[int, int]] = set()
    keyswitch_count = 0

    # Establish a known default state at the beginning of the file.
    if _add_keyswitch(
        events,
        emitted,
        tick=0,
        note=profile.keyswitches["sustain"],
        profile=profile,
    ):
        keyswitch_count += 1

    for destination in source_notes.values():
        for articulation in destination.articulations:
            technique_key: str | None = None
            source: _SourceNote | None = None

            if articulation.type in {"hammer_on", "pull_off"}:
                technique_key = "hammer_pull"
            elif articulation.type == "slide":
                technique_key = "legato_slide"
            elif articulation.type == "natural_harmonic":
                technique_key = "natural_harmonic"
            elif articulation.type == "palm_mute":
                technique_key = "palm_mute"
            elif articulation.type in {"slide_in", "slide_out"}:
                technique_key = "slide_in_out"
            elif articulation.type == "let_ring":
                # The source performance duration already contains the ring.
                continue
            elif articulation.type == "vibrato":
                warnings.append(
                    f"Vibrato on source note {destination.source_note_index} is "
                    "preserved in Guitar IR but is not rendered by the SC V0 MIDI adapter."
                )
                continue
            else:
                warnings.append(
                    f"Unsupported Ample articulation {articulation.type!r} on "
                    f"source note {destination.source_note_index}."
                )
                continue

            if articulation.source_note_id:
                source_index = event_id_to_source.get(articulation.source_note_id)
                if source_index is None:
                    warnings.append(
                        f"Cannot resolve articulation source {articulation.source_note_id!r} "
                        f"for note {destination.source_note_index}."
                    )
                    continue
                source = source_notes[source_index]

            if technique_key in {"hammer_pull", "legato_slide"}:
                if source is None:
                    warnings.append(
                        f"Linked articulation {articulation.type!r} on note "
                        f"{destination.source_note_index} has no source note."
                    )
                    continue
                # Ample requires the two legato notes to overlap. Preserve the
                # original performance duration when already long enough and
                # extend only the source note-off when necessary.
                source.end_tick = max(
                    source.end_tick,
                    destination.start_tick + profile.legato_overlap_ticks,
                )
                trigger_reference = source.start_tick
            else:
                trigger_reference = destination.start_tick

            trigger_tick = max(
                0,
                trigger_reference - profile.keyswitch_preroll_ticks,
            )
            if _add_keyswitch(
                events,
                emitted,
                tick=trigger_tick,
                note=profile.keyswitches[technique_key],
                profile=profile,
            ):
                keyswitch_count += 1

            # Persistent single-note articulations return to sustain after the
            # destination note. Ample's HP/LS modes auto-return when the target
            # note ends, so they do not need an explicit reset.
            if technique_key in {
                "natural_harmonic",
                "palm_mute",
                "slide_in_out",
            }:
                if _add_keyswitch(
                    events,
                    emitted,
                    tick=destination.end_tick + 1,
                    note=profile.keyswitches["sustain"],
                    profile=profile,
                ):
                    keyswitch_count += 1

    return keyswitch_count


def _write_absolute_events(
    track: mido.MidiTrack,
    events: list[tuple[int, int, mido.Message | mido.MetaMessage]],
) -> None:
    previous_tick = 0
    for absolute_tick, _priority, message in sorted(
        events,
        key=lambda item: (item[0], item[1]),
    ):
        delta = max(0, absolute_tick - previous_tick)
        track.append(message.copy(time=delta))
        previous_tick = absolute_tick


def export_ample_sc_midi(
    project: GuitarProjectIR,
    output: str | Path,
    *,
    profile: AmpleGuitarProfile = AMPLE_GUITAR_SC_V4,
    ticks_per_beat: int = 480,
) -> AmpleExportResult:
    """Render source performance timing with Ample Guitar SC keyswitches."""

    if len(project.tracks) != 1:
        raise ValueError("The V0 Ample renderer supports exactly one guitar track.")

    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    timeline_offset = profile.keyswitch_preroll_ticks
    source_notes, event_id_to_source = _collect_source_notes(
        project,
        ticks_per_beat,
        timeline_offset,
    )

    warnings: list[str] = []
    performance_events: list[tuple[int, int, mido.Message]] = []
    keyswitch_count = _schedule_articulations(
        source_notes,
        event_id_to_source,
        profile,
        performance_events,
        warnings,
    )

    for note in sorted(
        source_notes.values(),
        key=lambda item: (item.start_tick, item.pitch, item.source_note_index),
    ):
        if not profile.playable_min <= note.pitch <= profile.playable_max:
            warnings.append(
                f"MIDI note {note.pitch} is outside the configured {profile.product} "
                f"range {profile.playable_min}-{profile.playable_max}."
            )
        performance_events.append(
            (
                note.start_tick,
                2,
                mido.Message(
                    "note_on",
                    channel=profile.note_channel,
                    note=note.pitch,
                    velocity=note.velocity,
                    time=0,
                ),
            )
        )
        performance_events.append(
            (
                max(note.start_tick + 1, note.end_tick),
                3,
                mido.Message(
                    "note_off",
                    channel=profile.note_channel,
                    note=note.pitch,
                    velocity=profile.note_off_velocity,
                    time=0,
                ),
            )
        )

    midi = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)
    meta_track = mido.MidiTrack()
    performance_track = mido.MidiTrack()
    midi.tracks.extend([meta_track, performance_track])

    meta_track.append(mido.MetaMessage("track_name", name="FretPilot Tempo", time=0))
    meta_events: list[tuple[int, int, mido.MetaMessage]] = []
    for event in project.tempo_map:
        meta_events.append(
            (
                _beat_to_tick(event.beat, ticks_per_beat),
                0,
                mido.MetaMessage(
                    "set_tempo",
                    tempo=mido.bpm2tempo(event.bpm),
                    time=0,
                ),
            )
        )
    for event in project.time_signatures:
        meta_events.append(
            (
                _beat_to_tick(event.beat, ticks_per_beat),
                1,
                mido.MetaMessage(
                    "time_signature",
                    numerator=event.numerator,
                    denominator=event.denominator,
                    time=0,
                ),
            )
        )
    _write_absolute_events(meta_track, meta_events)

    performance_track.append(
        mido.MetaMessage(
            "track_name",
            name=f"FretPilot · {profile.product}",
            time=0,
        )
    )
    _write_absolute_events(performance_track, performance_events)
    midi.save(destination)

    return AmpleExportResult(
        path=str(destination),
        profile_id=profile.profile_id,
        source_note_count=len(source_notes),
        keyswitch_count=keyswitch_count,
        warnings=warnings,
    )
