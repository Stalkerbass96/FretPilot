"""Minimal Guitar IR to Guitar Pro 5 exporter.

The V0 exporter intentionally supports a narrow, testable subset: one guitar
track, up to two notation voices, monophonic notes or same-onset chords with
equal durations inside each voice, rests, ties, standard string/fret data, and
a few basic note effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import guitarpro as gp

from fretpilot.exporters.guitar_pro.markers import section_marker_titles
from fretpilot.ir.models import GuitarMeasure, GuitarNoteEvent, GuitarProjectIR


class UnsupportedGuitarIR(ValueError):
    """Raised when the current GP5 prototype cannot represent an IR pattern."""


@dataclass(slots=True)
class GP5ExportResult:
    path: str
    measure_count: int
    note_count: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "measure_count": self.measure_count,
            "note_count": self.note_count,
            "warnings": self.warnings,
        }


def _duration_candidates() -> list[gp.Duration]:
    candidates: dict[int, tuple[int, gp.Duration]] = {}
    for value in (
        gp.Duration.whole,
        gp.Duration.half,
        gp.Duration.quarter,
        gp.Duration.eighth,
        gp.Duration.sixteenth,
        gp.Duration.thirtySecond,
        gp.Duration.sixtyFourth,
    ):
        for dotted in (False, True):
            for enters, times in ((1, 1), (3, 2)):
                duration = gp.Duration(
                    value=value,
                    isDotted=dotted,
                    tuplet=gp.Tuplet(enters=enters, times=times),
                )
                complexity = (2 if enters != times else 0) + (1 if dotted else 0)
                existing = candidates.get(duration.time)
                if existing is None or complexity < existing[0]:
                    candidates[duration.time] = (complexity, duration)
    return [
        item[1]
        for item in sorted(
            candidates.values(),
            key=lambda item: (-item[1].time, item[0], item[1].value),
        )
    ]


_DURATION_CANDIDATES = _duration_candidates()


@lru_cache(maxsize=512)
def _split_duration_ticks(total_ticks: int) -> tuple[gp.Duration, ...]:
    if total_ticks <= 0:
        raise UnsupportedGuitarIR("GP5 duration must be positive.")

    try:
        return (gp.Duration.fromTime(total_ticks),)
    except (ValueError, OverflowError):
        pass

    best: list[gp.Duration] | None = None

    def search(remaining: int, chosen: list[gp.Duration]) -> None:
        nonlocal best
        if remaining == 0:
            if best is None or len(chosen) < len(best):
                best = list(chosen)
            return
        if best is not None and len(chosen) >= len(best):
            return

        for candidate in _DURATION_CANDIDATES:
            if candidate.time > remaining:
                continue
            chosen.append(candidate)
            search(remaining - candidate.time, chosen)
            chosen.pop()

    search(total_ticks, [])
    if best is None:
        raise UnsupportedGuitarIR(
            f"Duration {total_ticks} GP ticks cannot be represented by the V0 exporter."
        )
    return tuple(best)


def _beats_to_gp_ticks(beats: float) -> int:
    return int(round(beats * gp.Duration.quarterTime))


def _make_rest_beats(
    voice: gp.Voice,
    *,
    absolute_start: int,
    duration_ticks: int,
) -> list[gp.Beat]:
    beats: list[gp.Beat] = []
    cursor = absolute_start
    for duration in _split_duration_ticks(duration_ticks):
        beat = gp.Beat(
            voice,
            duration=duration,
            start=cursor,
            status=gp.BeatStatus.rest,
        )
        beats.append(beat)
        cursor += duration.time
    return beats


def _group_measure_events(
    measure: GuitarMeasure,
    *,
    voice_number: int,
) -> list[tuple[float, list[GuitarNoteEvent]]]:
    grouped: dict[float, list[GuitarNoteEvent]] = {}
    for event in measure.events:
        if event.score.voice == voice_number:
            grouped.setdefault(event.score.start_beat, []).append(event)
    return sorted(grouped.items(), key=lambda item: item[0])


def _has_articulation(event: GuitarNoteEvent, articulation_type: str) -> bool:
    return any(
        articulation.type == articulation_type
        for articulation in event.articulations
    )


def _apply_direct_effects(
    event: GuitarNoteEvent,
    note: gp.Note,
    *,
    allow_let_ring: bool,
) -> None:
    for articulation in event.articulations:
        if articulation.type == "vibrato":
            note.effect.vibrato = True
        elif articulation.type == "let_ring" and allow_let_ring:
            note.effect.letRing = True
        elif articulation.type == "palm_mute":
            note.effect.palmMute = True
        elif articulation.type == "staccato":
            note.effect.staccato = True


def _populate_voice(
    ir_measure: GuitarMeasure,
    gp_measure: gp.Measure,
    *,
    voice_number: int,
    note_lookup: dict[str, gp.Note],
) -> tuple[int, list[str]]:
    warnings: list[str] = []
    if voice_number not in {1, 2}:
        raise UnsupportedGuitarIR("The GP5 exporter supports voices 1 and 2 only.")
    voice = gp_measure.voices[voice_number - 1]
    voice.beats.clear()
    grouped_events = _group_measure_events(
        ir_measure,
        voice_number=voice_number,
    )
    if not grouped_events and voice_number == 2:
        return 0, warnings

    measure_start = gp_measure.start
    cursor = measure_start
    note_count = 0

    for absolute_start_beat, events in grouped_events:
        start_in_measure = absolute_start_beat - ir_measure.start_beat
        start_tick = measure_start + _beats_to_gp_ticks(start_in_measure)
        if start_tick < cursor:
            raise UnsupportedGuitarIR(
                "Overlapping note groups require multiple voices, which the V0 GP5 "
                "exporter cannot further split "
                f"(measure {ir_measure.number}, voice {voice_number})."
            )

        if start_tick > cursor:
            rests = _make_rest_beats(
                voice,
                absolute_start=cursor,
                duration_ticks=start_tick - cursor,
            )
            voice.beats.extend(rests)
            cursor = start_tick

        durations = {
            _beats_to_gp_ticks(event.score.duration_beats) for event in events
        }
        if len(durations) != 1:
            raise UnsupportedGuitarIR(
                "Same-onset chord notes must have equal score durations in the V0 "
                f"GP5 exporter (measure {ir_measure.number}, voice {voice_number})."
            )
        total_duration = durations.pop()
        segments = _split_duration_ticks(total_duration)

        playable_strings = [
            event.fingering.string
            for event in events
            if event.fingering.string is not None
        ]
        if len(playable_strings) != len(set(playable_strings)):
            raise UnsupportedGuitarIR(
                "Same-onset chord notes must use distinct strings; duplicate "
                f"string assignment in measure {ir_measure.number}, beat "
                f"{start_in_measure:g}, voice {voice_number}."
            )

        partial_chord_let_ring = (
            len(events) > 1
            and any(_has_articulation(event, "let_ring") for event in events)
            and not all(_has_articulation(event, "let_ring") for event in events)
        )
        if partial_chord_let_ring:
            warnings.append(
                "Omitted partial let-ring marking from a chord at measure "
                f"{ir_measure.number}, beat {start_in_measure:g}; the intent remains "
                "in Guitar IR and source performance timing."
            )

        for segment_index, duration in enumerate(segments):
            beat = gp.Beat(
                voice,
                duration=duration,
                start=cursor,
                status=gp.BeatStatus.normal,
            )
            voice.beats.append(beat)

            for event in events:
                if event.fingering.string is None or event.fingering.fret is None:
                    raise UnsupportedGuitarIR(
                        f"Event {event.id} has no playable string/fret assignment."
                    )

                continuation = event.score.tie_in or segment_index > 0
                note = gp.Note(
                    beat,
                    value=event.fingering.fret,
                    velocity=max(1, min(127, event.performance.velocity)),
                    string=event.fingering.string,
                    type=gp.NoteType.tie if continuation else gp.NoteType.normal,
                )
                if segment_index == 0:
                    _apply_direct_effects(
                        event,
                        note,
                        allow_let_ring=not partial_chord_let_ring,
                    )
                    note_lookup[event.id] = note
                beat.notes.append(note)
                note_count += 1

            cursor += duration.time

    measure_end = gp_measure.end
    if cursor < measure_end:
        voice.beats.extend(
            _make_rest_beats(
                voice,
                absolute_start=cursor,
                duration_ticks=measure_end - cursor,
            )
        )
    elif cursor > measure_end:
        raise UnsupportedGuitarIR(
            f"Events overflow measure {ir_measure.number} by {cursor - measure_end} GP ticks."
        )

    return note_count, warnings


def _populate_measure(
    ir_measure: GuitarMeasure,
    gp_measure: gp.Measure,
    *,
    note_lookup: dict[str, gp.Note],
) -> tuple[int, list[str]]:
    note_count = 0
    warnings: list[str] = []
    present_voices = {event.score.voice for event in ir_measure.events}
    unsupported = sorted(present_voices - {1, 2})
    if unsupported:
        raise UnsupportedGuitarIR(
            f"Measure {ir_measure.number} uses unsupported voices: {unsupported}."
        )
    for voice_number in (1, 2):
        exported, voice_warnings = _populate_voice(
            ir_measure,
            gp_measure,
            voice_number=voice_number,
            note_lookup=note_lookup,
        )
        note_count += exported
        warnings.extend(voice_warnings)
    return note_count, warnings


def _apply_linked_effects(
    events: Iterable[GuitarNoteEvent],
    note_lookup: dict[str, gp.Note],
    warnings: list[str],
) -> None:
    for event in events:
        for articulation in event.articulations:
            if articulation.type not in {"hammer_on", "pull_off", "slide"}:
                continue
            if not articulation.source_note_id:
                warnings.append(
                    f"Skipped {articulation.type} on {event.id}: no source note ID."
                )
                continue
            source_note = note_lookup.get(articulation.source_note_id)
            if source_note is None:
                warnings.append(
                    f"Skipped {articulation.type} on {event.id}: source note "
                    f"{articulation.source_note_id} was not exported."
                )
                continue
            if articulation.type in {"hammer_on", "pull_off"}:
                source_note.effect.hammer = True
            elif articulation.type == "slide":
                source_note.effect.slides.append(gp.SlideType.shiftSlideTo)


def _configure_song(project: GuitarProjectIR) -> gp.Song:
    if len(project.tracks) != 1:
        raise UnsupportedGuitarIR("The V0 GP5 exporter supports exactly one guitar track.")

    ir_track = project.tracks[0]
    if not ir_track.measures:
        raise UnsupportedGuitarIR("The Guitar IR contains no measures.")

    song = gp.Song()
    song.title = project.title
    if project.tempo_map:
        song.tempo = max(1, int(round(project.tempo_map[0].bpm)))
    song.tempoName = "FretPilot"

    while len(song.measureHeaders) < len(ir_track.measures):
        song.newMeasure()

    if len(song.measureHeaders) > len(ir_track.measures):
        song.measureHeaders = song.measureHeaders[: len(ir_track.measures)]
        for track in song.tracks:
            track.measures = track.measures[: len(ir_track.measures)]

    track = song.tracks[0]
    track.name = ir_track.name[:40] or "FretPilot Guitar"
    track.fretCount = ir_track.fret_count
    track.strings = [
        gp.GuitarString(number=index + 1, value=pitch)
        for index, pitch in enumerate(reversed(ir_track.tuning))
    ]

    marker_titles = section_marker_titles(ir_track.section_contexts)
    start = gp.Duration.quarterTime
    for ir_measure, header in zip(
        ir_track.measures,
        song.measureHeaders,
        strict=True,
    ):
        header.number = ir_measure.number
        header.start = start
        header.timeSignature = gp.TimeSignature(
            numerator=ir_measure.numerator,
            denominator=gp.Duration(value=ir_measure.denominator),
        )
        marker_title = marker_titles.get(ir_measure.number)
        if marker_title:
            header.marker = gp.Marker(title=marker_title)
        start = header.end

    return song


def export_gp5(project: GuitarProjectIR, output: str | Path) -> GP5ExportResult:
    """Write the supported Guitar IR subset as a Guitar Pro 5.1 file."""

    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)

    song = _configure_song(project)
    ir_track = project.tracks[0]
    gp_track = song.tracks[0]
    note_lookup: dict[str, gp.Note] = {}
    warnings: list[str] = []
    note_count = 0

    for ir_measure, gp_measure in zip(
        ir_track.measures,
        gp_track.measures,
        strict=True,
    ):
        exported, measure_warnings = _populate_measure(
            ir_measure,
            gp_measure,
            note_lookup=note_lookup,
        )
        note_count += exported
        warnings.extend(measure_warnings)

    all_events = [
        event
        for measure in ir_track.measures
        for event in measure.events
    ]
    _apply_linked_effects(all_events, note_lookup, warnings)

    gp.write(song, destination, version=(5, 1, 0))
    return GP5ExportResult(
        path=str(destination),
        measure_count=len(ir_track.measures),
        note_count=note_count,
        warnings=warnings,
    )
