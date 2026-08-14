from pathlib import Path

import mido

from fretpilot.exporters.ample_guitar import export_ample_sc_midi
from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
    IRArticulation,
    IRFingering,
    IRTempoEvent,
    IRTimeSignatureEvent,
    PerformanceTiming,
    ScoreTiming,
)
from fretpilot.virtual_instruments.ample_guitar_sc import AMPLE_GUITAR_SC_V4_PROFILE
from fretpilot.virtual_instruments.control_plan import build_control_plan


def _event(index, pitch, start, articulation=None):
    return GuitarNoteEvent(
        id=f"n{index}",
        source_note_index=index,
        pitch=pitch,
        score=ScoreTiming(
            start_beat=start,
            duration_beats=0.5,
            measure_number=1,
            beat_in_measure=start,
        ),
        performance=PerformanceTiming(
            source_start_beat=start,
            source_duration_beats=0.5,
            velocity=90,
        ),
        fingering=IRFingering(string=1 + (index % 6), fret=5 + index),
        articulations=[] if articulation is None else [articulation],
    )


def _project():
    events = [
        _event(0, 64, 0.0),
        _event(
            1,
            66,
            0.5,
            IRArticulation(
                type="hammer_on",
                confidence=0.9,
                reason="fixture",
                source_note_id="n0",
            ),
        ),
        _event(
            2,
            67,
            1.0,
            IRArticulation(
                type="slide",
                confidence=0.9,
                reason="fixture",
                source_note_id="n1",
            ),
        ),
        _event(
            3,
            69,
            1.5,
            IRArticulation(type="natural_harmonic", confidence=0.9, reason="fixture"),
        ),
        _event(
            4,
            70,
            2.0,
            IRArticulation(type="palm_mute", confidence=0.9, reason="fixture"),
        ),
        _event(
            5,
            71,
            2.5,
            IRArticulation(type="slide_in", confidence=0.9, reason="fixture"),
        ),
        _event(
            6,
            72,
            3.0,
            IRArticulation(type="slide_out", confidence=0.9, reason="fixture"),
        ),
    ]
    return GuitarProjectIR(
        title="VI shadow parity",
        source="fixture.mid",
        tempo_map=[IRTempoEvent(beat=0.0, bpm=120.0)],
        time_signatures=[IRTimeSignatureEvent(beat=0.0, numerator=4, denominator=4)],
        tracks=[
            GuitarTrackIR(
                id="guitar-1",
                name="Guitar",
                source_stream_id=None,
                role="riff",
                tuning=[40, 45, 50, 55, 59, 64],
                fret_count=24,
                measures=[
                    GuitarMeasure(
                        number=1,
                        start_beat=0.0,
                        duration_beats=4.0,
                        numerator=4,
                        denominator=4,
                        events=events,
                    )
                ],
            )
        ],
    )


def _planned_keyswitch_signature(plan):
    result = []
    for item in plan.controls:
        action = item.action
        if action.kind != "keyswitch_note":
            continue
        assert isinstance(action.target, int)
        velocity = int(action.value) if action.value is not None else 100
        release_velocity = int(action.release_value) if action.release_value is not None else 0
        duration = int(action.duration_ticks or 0)
        result.append((item.tick, "note_on", action.target, velocity))
        result.append((item.tick + duration, "note_off", action.target, release_velocity))
    return sorted(result)


def _rendered_keyswitch_signature(path: Path):
    midi = mido.MidiFile(path)
    result = []
    for track in midi.tracks:
        absolute = 0
        for message in track:
            absolute += message.time
            if message.type not in {"note_on", "note_off"}:
                continue
            if message.note >= AMPLE_GUITAR_SC_V4_PROFILE.playable_min:
                continue
            result.append((absolute, message.type, message.note, message.velocity))
    return sorted(result)


def _rendered_note_off_ticks(path: Path):
    midi = mido.MidiFile(path)
    result = {}
    for track in midi.tracks:
        absolute = 0
        for message in track:
            absolute += message.time
            if message.type == "note_off" and message.note >= AMPLE_GUITAR_SC_V4_PROFILE.playable_min:
                result[message.note] = absolute
    return result


def test_generic_control_plan_matches_legacy_keyswitch_ticks_and_values(tmp_path: Path):
    project = _project()
    plan = build_control_plan(project, AMPLE_GUITAR_SC_V4_PROFILE)
    output = tmp_path / "legacy.mid"
    export_ample_sc_midi(project, output)

    assert plan.timeline_offset_ticks == 30
    assert plan.warnings == []
    assert _planned_keyswitch_signature(plan) == _rendered_keyswitch_signature(output)

    sustain_reset_ticks = [
        item.tick
        for item in plan.controls
        if item.source_event_id in {"n3", "n4", "n5", "n6"}
        and item.action.kind == "keyswitch_note"
        and item.action.target == 24
    ]
    assert sustain_reset_ticks == [991, 1231, 1471, 1711]


def test_generic_control_plan_matches_legacy_legato_note_extensions(tmp_path: Path):
    project = _project()
    plan = build_control_plan(project, AMPLE_GUITAR_SC_V4_PROFILE)
    output = tmp_path / "legacy.mid"
    export_ample_sc_midi(project, output)

    extensions = {
        item.source_event_id: item.minimum_end_tick
        for item in plan.note_end_extensions
    }
    assert extensions == {"n0": 300, "n1": 540}

    rendered_offs = _rendered_note_off_ticks(output)
    assert rendered_offs[64] == extensions["n0"]
    assert rendered_offs[66] == extensions["n1"]
