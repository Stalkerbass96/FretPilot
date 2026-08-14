from pathlib import Path

from fretpilot.exporters.pdf_score import export_score_pdf
from fretpilot.exporters.pdf_score.renderer import _harmony_label_map
from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
    IRFingering,
    IRHarmonyRegion,
    IRTempoEvent,
    IRTimeSignatureEvent,
    PerformanceTiming,
    ScoreTiming,
)


def test_export_score_pdf_writes_reviewable_pdf(tmp_path: Path) -> None:
    event = GuitarNoteEvent(
        id="n-1",
        source_note_index=0,
        pitch=64,
        score=ScoreTiming(
            start_beat=0.0,
            duration_beats=1.0,
            measure_number=1,
            beat_in_measure=0.0,
        ),
        performance=PerformanceTiming(
            source_start_beat=0.01,
            source_duration_beats=0.98,
            velocity=90,
        ),
        fingering=IRFingering(string=1, fret=0),
    )
    track = GuitarTrackIR(
        id="guitar-1",
        name="Lead Guitar",
        source_stream_id="t0:ch0:p27",
        role="lead",
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
        harmony_regions=[
            IRHarmonyRegion(
                start_beat=0.01,
                symbol="C#sus2",
                root_pitch_class=1,
                quality="sus2",
                confidence=0.9,
                source_note_indices=[0],
                reason="fixture",
            )
        ],
    )
    project = GuitarProjectIR(
        title="PDF Test",
        source="test.mid",
        tempo_map=[IRTempoEvent(beat=0.0, bpm=120.0)],
        time_signatures=[
            IRTimeSignatureEvent(beat=0.0, numerator=4, denominator=4)
        ],
        tracks=[track],
    )

    assert _harmony_label_map(track) == {0.0: "C#sus2"}

    destination = tmp_path / "score.pdf"
    result = export_score_pdf(project, destination)

    assert result.page_count == 2
    assert result.track_count == 1
    assert result.note_count == 1
    assert destination.read_bytes().startswith(b"%PDF")
    assert destination.stat().st_size > 1000
