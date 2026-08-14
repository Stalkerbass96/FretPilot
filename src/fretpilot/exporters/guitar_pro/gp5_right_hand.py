"""GP5 enrichment wrapper for right-hand direction and pitch curves."""

from pathlib import Path

import guitarpro as gp

from fretpilot.exporters.guitar_pro.gp5 import (
    GP5ExportResult,
    _apply_linked_effects,
    _configure_song,
    _populate_measure,
)
from fretpilot.ir.models import GuitarMeasure, GuitarProjectIR


def _apply_right_hand(ir_measure: GuitarMeasure, gp_measure: gp.Measure) -> None:
    intents = {
        round(event.score.start_beat, 9): event.right_hand
        for event in ir_measure.events
        if event.right_hand is not None and not event.score.tie_in
    }
    for beat in gp_measure.voices[0].beats:
        if beat.status != gp.BeatStatus.normal or beat.start is None:
            continue
        start = ir_measure.start_beat + (
            beat.start - gp_measure.start
        ) / gp.Duration.quarterTime
        intent = intents.get(round(start, 9))
        if intent is None:
            continue
        beat.effect.pickStroke = (
            gp.BeatStrokeDirection.down
            if intent.direction == "down"
            else gp.BeatStrokeDirection.up
        )


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
                    f"Rounded pitch raise on {event.id} from {semitones:.3f} to {value} semitones for GP5."
                )
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
