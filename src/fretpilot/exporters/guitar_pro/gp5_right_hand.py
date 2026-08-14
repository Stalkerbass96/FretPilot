"""GP5 enrichment wrapper for picking, fretting digits, and pitch curves."""

from pathlib import Path

import guitarpro as gp

from fretpilot.exporters.guitar_pro.gp5 import (
    GP5ExportResult,
    _apply_linked_effects,
    _configure_song,
    _populate_measure,
)
from fretpilot.guitar.fretting_digits import assign_digit_locations
from fretpilot.ir.models import GuitarMeasure, GuitarProjectIR


_GP_FRETTING_DIGITS = {
    1: gp.Fingering.index,
    2: gp.Fingering.middle,
    3: gp.Fingering.annular,
    4: gp.Fingering.little,
}


def _stroke_value_for_spread(spread_beats: float) -> int:
    values = (4, 8, 16, 32, 64, 128)
    return min(values, key=lambda value: abs((4.0 / value) - spread_beats))


def _apply_right_hand(ir_measure: GuitarMeasure, gp_measure: gp.Measure) -> None:
    grouped = {}
    for event in ir_measure.events:
        if event.right_hand is None or event.score.tie_in:
            continue
        grouped.setdefault(round(event.score.start_beat, 9), []).append(event)

    for beat in gp_measure.voices[0].beats:
        if beat.status != gp.BeatStatus.normal or beat.start is None:
            continue
        start = ir_measure.start_beat + (
            beat.start - gp_measure.start
        ) / gp.Duration.quarterTime
        events = grouped.get(round(start, 9), [])
        if not events:
            continue
        intent = events[0].right_hand
        if intent is None:
            continue
        direction = (
            gp.BeatStrokeDirection.down
            if intent.direction == "down"
            else gp.BeatStrokeDirection.up
        )
        if intent.technique == "rolled_strum" and len(events) >= 2:
            starts = [event.performance.source_start_beat for event in events]
            spread = max(starts) - min(starts)
            if spread > 1e-6:
                beat.effect.stroke.direction = direction
                beat.effect.stroke.value = _stroke_value_for_spread(spread)
                beat.effect.pickStroke = gp.BeatStrokeDirection.none
                continue
        beat.effect.pickStroke = direction


def _fretting_digit_map(project: GuitarProjectIR) -> dict[int, int]:
    events_by_source = {}
    for measure in project.tracks[0].measures:
        for event in measure.events:
            if not event.score.tie_in:
                events_by_source.setdefault(event.source_note_index, event)

    persisted = {
        source_index: event.fingering.fretting_digit
        for source_index, event in events_by_source.items()
        if event.fingering.fretting_digit is not None
    }
    if len(persisted) == len(events_by_source):
        return persisted

    source_indices = sorted(events_by_source)
    entries = []
    for source_index in source_indices:
        event = events_by_source[source_index]
        entries.append(
            (
                round(event.performance.source_start_beat * 1_000_000),
                event.pitch,
                event.fingering.string,
                event.fingering.fret,
            )
        )
    digits = assign_digit_locations(entries)
    result = {
        source_index: digit
        for source_index, digit in zip(source_indices, digits, strict=True)
        if digit is not None
    }
    result.update(persisted)
    return result


def _apply_fretting_digits(
    ir_measure: GuitarMeasure,
    gp_measure: gp.Measure,
    digits: dict[int, int],
) -> None:
    for beat in gp_measure.voices[0].beats:
        if beat.status != gp.BeatStatus.normal or beat.start is None:
            continue
        start = ir_measure.start_beat + (
            beat.start - gp_measure.start
        ) / gp.Duration.quarterTime
        events = [
            event
            for event in ir_measure.events
            if not event.score.tie_in
            and abs(event.score.start_beat - start) <= 1e-8
        ]
        for event in events:
            digit = digits.get(event.source_note_index)
            if digit is None:
                continue
            gp_note = next(
                (
                    note
                    for note in beat.notes
                    if note.string == event.fingering.string
                    and note.value == event.fingering.fret
                ),
                None,
            )
            if gp_note is not None:
                gp_note.effect.leftHandFinger = _GP_FRETTING_DIGITS[digit]


def _apply_pitch_raises(events, note_lookup, warnings) -> None:
    for event in events:
        if event.score.tie_in:
            continue
        for articulation in event.articulations:
            if articulation.type != "pitch_raise" or not articulation.parameters:
                continue
            note = note_lookup.get(event.id)
            if note is None:
                warnings.append(f"Skipped pitch raise on {event.id}: note was not exported.")
                continue

            semitones = float(articulation.parameters.get("semitones", 0.0))
            value = max(1, min(12, round(semitones)))
            if abs(semitones - value) > 0.26:
                warnings.append(
                    f"Omitted non-integer pitch raise on {event.id}: {semitones:.3f} semitones cannot be represented faithfully by the current GP5 adapter; exact intent remains in Guitar IR."
                )
                continue

            peak = max(
                1,
                min(12, round(float(articulation.parameters.get("peak_position", 0.5)) * 12)),
            )
            returned = float(
                articulation.parameters.get("returned_to_center", 0.0)
            ) >= 0.5
            points = [gp.BendPoint(position=0, value=0)]
            points.append(gp.BendPoint(position=peak, value=value))

            if returned:
                release = min(
                    12,
                    max(
                        peak + 1 if peak < 12 else 12,
                        round(float(articulation.parameters.get("return_position", 1.0)) * 12),
                    ),
                )
                points.append(gp.BendPoint(position=release, value=0))
                if release < 12:
                    points.append(gp.BendPoint(position=12, value=0))
                effect_type = gp.BendType.bendRelease
            else:
                if peak < 12:
                    points.append(gp.BendPoint(position=12, value=value))
                effect_type = gp.BendType.bend

            note.effect.bend = gp.BendEffect(
                type=effect_type,
                value=value,
                points=points,
            )


def export_gp5(project: GuitarProjectIR, output: str | Path) -> GP5ExportResult:
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    song = _configure_song(project)
    ir_track = project.tracks[0]
    gp_track = song.tracks[0]
    note_lookup: dict[str, gp.Note] = {}
    warnings: list[str] = []
    note_count = 0
    fretting_digits = _fretting_digit_map(project)

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
        _apply_right_hand(ir_measure, gp_measure)
        _apply_fretting_digits(ir_measure, gp_measure, fretting_digits)
        note_count += exported
        warnings.extend(measure_warnings)

    all_events = [event for measure in ir_track.measures for event in measure.events]
    _apply_linked_effects(all_events, note_lookup, warnings)
    _apply_pitch_raises(all_events, note_lookup, warnings)
    gp.write(song, destination, version=(5, 1, 0))
    return GP5ExportResult(
        path=str(destination),
        measure_count=len(ir_track.measures),
        note_count=note_count,
        warnings=warnings,
    )
