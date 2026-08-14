"""GP5 wrapper that adds generic right-hand direction to exported beats."""

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

    all_events = [
        event for measure in ir_track.measures for event in measure.events
    ]
    _apply_linked_effects(all_events, note_lookup, warnings)
    gp.write(song, destination, version=(5, 1, 0))
    return GP5ExportResult(
        path=str(destination),
        measure_count=len(ir_track.measures),
        note_count=note_count,
        warnings=warnings,
    )
