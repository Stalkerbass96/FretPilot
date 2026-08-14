from fretpilot.guitar.models import FingeredNote, FingeringResult
from fretpilot.harmony.models import HarmonyDecision, HarmonyPlan
from fretpilot.harmony.planner import plan_harmony
from fretpilot.midi.models import NormalizedTrack


def plan_harmony_by_sections(track, fingering, sections):
    decisions = []
    for section in sections:
        indices = [
            index for index, note in enumerate(track.notes)
            if section.start_beat - 1e-9 <= note.start_beat < section.end_beat - 1e-9
        ]
        if not indices:
            continue
        notes = [track.notes[index] for index in indices]
        local_track = NormalizedTrack(track.index, track.name, notes, track.instrument_name)
        local_fingering = FingeringResult(
            track_index=track.index,
            track_name=track.name,
            tuning=fingering.tuning,
            max_fret=fingering.max_fret,
            notes=[
                FingeredNote(
                    note_index=local_index,
                    pitch=notes[local_index].pitch,
                    start_beat=notes[local_index].start_beat,
                    duration_beats=notes[local_index].duration_beats,
                    string=fingering.notes[global_index].string,
                    fret=fingering.notes[global_index].fret,
                    local_cost=fingering.notes[global_index].local_cost,
                    fretting_digit=fingering.notes[global_index].fretting_digit,
                )
                for local_index, global_index in enumerate(indices)
            ],
        )
        local_plan = plan_harmony(local_track, local_fingering)
        for item in local_plan.decisions:
            decisions.append(
                HarmonyDecision(
                    note_indices=tuple(indices[index] for index in item.note_indices),
                    start_beat=item.start_beat,
                    symbol=item.symbol,
                    root_pitch_class=item.root_pitch_class,
                    quality=item.quality,
                    confidence=item.confidence,
                    reason=item.reason,
                )
            )
    return HarmonyPlan(
        track_index=track.index,
        track_name=track.name,
        decisions=sorted(
            decisions,
            key=lambda item: (item.start_beat, item.note_indices[0]),
        ),
    )
