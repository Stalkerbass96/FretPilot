from pathlib import Path

import mido
import pytest

from fretpilot.exporters.ample_guitar import export_ample_sc_midi
from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
    IRFingering,
    IRRightHandIntent,
    IRTempoEvent,
    IRTimeSignatureEvent,
    PerformanceTiming,
    ScoreTiming,
)


def _project() -> GuitarProjectIR:
    event = GuitarNoteEvent(
        id="n0",
        source_note_index=0,
        pitch=64,
        score=ScoreTiming(
            start_beat=0.0,
            duration_beats=1.0,
            measure_number=1,
            beat_in_measure=0.0,
        ),
        performance=PerformanceTiming(
            source_start_beat=0.0,
            source_duration_beats=1.0,
            velocity=90,
        ),
        fingering=IRFingering(string=1, fret=0),
        right_hand=IRRightHandIntent(
            motion="pick",
            direction="down",
            confidence=0.9,
            reason="fixture",
        ),
    )
    return GuitarProjectIR(
        title="Capability preflight",
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
                        events=[event],
                    )
                ],
            )
        ],
    )


def _signature(path: Path):
    midi = mido.MidiFile(path)
    result = []
    for track_index, track in enumerate(midi.tracks):
        absolute = 0
        for message in track:
            absolute += message.time
            payload = message.dict()
            payload.pop("time", None)
            result.append((track_index, absolute, payload))
    return result


def test_report_only_preserves_legacy_output_and_warnings(tmp_path: Path):
    output = tmp_path / "report-only.mid"
    result = export_ample_sc_midi(
        _project(),
        output,
        capability_mode="report_only",
    )
    assert result.warnings == []
    assert output.exists()


def test_warn_surfaces_unsupported_intent_without_changing_midi(tmp_path: Path):
    report_only_path = tmp_path / "report-only.mid"
    warn_path = tmp_path / "warn.mid"
    export_ample_sc_midi(_project(), report_only_path, capability_mode="report_only")
    result = export_ample_sc_midi(_project(), warn_path, capability_mode="warn")

    assert any("'pick_down'" in warning for warning in result.warnings)
    assert any("unsupported" in warning for warning in result.warnings)
    assert _signature(warn_path) == _signature(report_only_path)


def test_strict_blocks_before_target_midi_is_written(tmp_path: Path):
    output = tmp_path / "strict.mid"
    with pytest.raises(ValueError, match="pick_down"):
        export_ample_sc_midi(_project(), output, capability_mode="strict")
    assert not output.exists()
