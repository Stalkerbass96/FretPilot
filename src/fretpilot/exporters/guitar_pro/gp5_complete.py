from pathlib import Path

import guitarpro as gp

from fretpilot.exporters.guitar_pro.gp5_harmony import (
    apply_harmony_labels,
    harmony_label_map,
)
from fretpilot.exporters.guitar_pro.gp5_right_hand import export_gp5 as _export_base
from fretpilot.ir.models import GuitarProjectIR


def export_gp5(project: GuitarProjectIR, output: str | Path):
    result = _export_base(project, output)
    labels = harmony_label_map(project)
    if not labels:
        return result

    song = gp.parse(result.path)
    ir_track = project.tracks[0]
    gp_track = song.tracks[0]
    for ir_measure, gp_measure in zip(
        ir_track.measures,
        gp_track.measures,
        strict=True,
    ):
        apply_harmony_labels(ir_measure, gp_measure, labels)

    gp.write(song, result.path, version=(5, 1, 0))
    return result
