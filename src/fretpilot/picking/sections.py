from fretpilot.guitar.models import FingeredNote, FingeringResult
from fretpilot.midi.models import NormalizedTrack
from .models import PickingDecision, PickingPlan
from .planner import plan_picking


def plan_picking_by_sections(track, fingering, sections, overrides=None):
    decisions = []
    for section in sections:
        ids = [
            i for i, note in enumerate(track.notes)
            if section.start_beat - 1e-9 <= note.start_beat < section.end_beat - 1e-9
        ]
        if not ids:
            continue
        notes = [track.notes[i] for i in ids]
        sub = NormalizedTrack(track.index, track.name, notes, track.instrument_name)
        local = FingeringResult(
            track.index, track.name, fingering.tuning, fingering.max_fret,
            [
                FingeredNote(
                    j, notes[j].pitch, notes[j].start_beat, notes[j].duration_beats,
                    fingering.notes[i].string, fingering.notes[i].fret,
                    fingering.notes[i].local_cost,
                )
                for j, i in enumerate(ids)
            ],
        )
        context = overrides.get(section.section_id, section.playing_context) if overrides else section.playing_context
        for item in plan_picking(sub, local, context=context).decisions:
            decisions.append(
                PickingDecision(
                    tuple(ids[i] for i in item.note_indices),
                    item.start_beat,
                    item.motion,
                    item.direction,
                    item.confidence,
                    item.reason,
                    item.technique,
                )
            )
    return PickingPlan(track.index, track.name, decisions)
