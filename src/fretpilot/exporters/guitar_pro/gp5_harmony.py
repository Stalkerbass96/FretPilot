import guitarpro as gp

from fretpilot.ir.models import GuitarMeasure, GuitarProjectIR


def harmony_label_map(project: GuitarProjectIR) -> dict[float, str]:
    if not project.tracks:
        return {}
    track = project.tracks[0]
    events = [
        event
        for measure in track.measures
        for event in measure.events
        if not event.score.tie_in
    ]
    labels: dict[float, str] = {}
    for region in track.harmony_regions:
        source_indices = set(region.source_note_indices)
        anchor = next(
            (
                event
                for event in events
                if event.source_note_index in source_indices
            ),
            None,
        )
        if anchor is not None:
            labels.setdefault(round(anchor.score.start_beat, 9), region.symbol)
    return labels


def apply_harmony_labels(
    ir_measure: GuitarMeasure,
    gp_measure: gp.Measure,
    labels: dict[float, str],
) -> None:
    for beat in gp_measure.voices[0].beats:
        if beat.status != gp.BeatStatus.normal or beat.start is None:
            continue
        start = ir_measure.start_beat + (
            beat.start - gp_measure.start
        ) / gp.Duration.quarterTime
        label = labels.get(round(start, 9))
        if label is not None and not beat.text:
            beat.text = label
