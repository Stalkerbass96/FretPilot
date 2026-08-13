from pathlib import Path

import pytest

from fretpilot.exporters.pdf_score import export_score_pdf
from fretpilot.exporters.pdf_score.renderer import _rhythm_mark
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
    project = GuitarProjectIR(
        title="PDF Test",
        source="test.mid",
        tempo_map=[IRTempoEvent(beat=0.0, bpm=120.0)],
        time_signatures=[
            IRTimeSignatureEvent(beat=0.0, numerator=4, denominator=4)
        ],
        tracks=[
            GuitarTrackIR(
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
            )
        ],
    )

    destination = tmp_path / "score.pdf"
    result = export_score_pdf(project, destination)

    assert result.page_count == 2
    assert result.track_count == 1
    assert result.note_count == 1
    assert destination.read_bytes().startswith(b"%PDF")
    assert destination.stat().st_size > 1000


@pytest.mark.parametrize(
    ("duration", "stem", "filled", "beams", "dotted", "tuplet"),
    [
        (4.0, False, False, 0, False, None),
        (2.0, True, False, 0, False, None),
        (1.0, True, True, 0, False, None),
        (0.75, True, True, 1, True, None),
        (0.5, True, True, 1, False, None),
        (1 / 3, True, True, 1, False, 3),
        (0.25, True, True, 2, False, None),
        (0.125, True, True, 3, False, None),
    ],
)
def test_rhythm_mark_maps_written_durations(
    duration: float,
    stem: bool,
    filled: bool,
    beams: int,
    dotted: bool,
    tuplet: int | None,
) -> None:
    mark = _rhythm_mark(duration)

    assert mark.stem is stem
    assert mark.filled is filled
    assert mark.beam_count == beams
    assert mark.dotted is dotted
    assert mark.tuplet == tuplet
