from pathlib import Path

from fretpilot.exporters.pdf_score import export_score_pdf
from fretpilot.exporters.pdf_score.density_renderer import (
    _density_warnings,
    _track_system_chunks,
)
from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
    IRFingering,
    IRTempoEvent,
    IRTimeSignatureEvent,
    PerformanceTiming,
    ScoreTiming,
)


def _event(index: int, measure_start: float, start: float, duration: float):
    absolute = measure_start + start
    return GuitarNoteEvent(
        id=f"n-{measure_start}-{index}",
        source_note_index=int(measure_start * 100) + index,
        pitch=60 + (index % 8),
        score=ScoreTiming(
            start_beat=absolute,
            duration_beats=duration,
            measure_number=int(measure_start / 4) + 1,
            beat_in_measure=start,
        ),
        performance=PerformanceTiming(
            source_start_beat=absolute,
            source_duration_beats=duration,
            velocity=90,
        ),
        fingering=IRFingering(string=1 + (index % 6), fret=index % 12),
    )


def _measure(number: int, step: float, count: int):
    start = (number - 1) * 4.0
    return GuitarMeasure(
        number=number,
        start_beat=start,
        duration_beats=4.0,
        numerator=4,
        denominator=4,
        events=[_event(index, start, index * step, step) for index in range(count)],
    )


def _project(measures):
    return GuitarProjectIR(
        title="Density PDF",
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
                measures=list(measures),
            )
        ],
    )


def test_dense_sixteenth_measures_use_fewer_measures_per_system():
    track = _project([_measure(index + 1, 0.25, 16) for index in range(4)]).tracks[0]
    chunks = _track_system_chunks(
        track,
        max_measures_per_system=4,
        available_width=720.0,
    )
    assert [[item.number for item in chunk] for chunk in chunks] == [[1, 2, 3], [4]]


def test_mixed_extreme_measure_is_not_compressed_below_its_equal_share():
    track = _project(
        [
            _measure(1, 0.5, 8),
            _measure(2, 0.125, 32),
            _measure(3, 0.5, 8),
        ]
    ).tracks[0]
    chunks = _track_system_chunks(
        track,
        max_measures_per_system=4,
        available_width=720.0,
    )
    assert [[item.number for item in chunk] for chunk in chunks] == [[1], [2], [3]]


def test_overfull_single_measure_produces_explicit_density_warning():
    track = _project([_measure(1, 0.03125, 128)]).tracks[0]
    warnings = _density_warnings(track, available_width=720.0)
    assert len(warnings) == 1
    assert "Measure 1" in warnings[0]
    assert "horizontally compressed" in warnings[0]


def test_public_pdf_export_uses_density_renderer_without_breaking_output(tmp_path: Path):
    project = _project([_measure(index + 1, 0.25, 16) for index in range(4)])
    output = tmp_path / "dense.pdf"
    result = export_score_pdf(
        project,
        output,
        measures_per_system=4,
        systems_per_page=5,
    )
    assert result.track_count == 1
    assert result.measure_count == 4
    assert result.warnings == []
    assert output.read_bytes().startswith(b"%PDF")
    assert output.stat().st_size > 1000
