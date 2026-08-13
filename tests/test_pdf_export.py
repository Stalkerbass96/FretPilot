from pathlib import Path

import pytest

from fretpilot.exporters.pdf_score import export_score_pdf
from fretpilot.exporters.pdf_score.renderer import (
    _TechniquePlacement,
    _group_rhythm_events,
    _layout_technique_labels,
    _rhythm_mark,
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
    assert result.maximum_voice_count == 1
    assert destination.read_bytes().startswith(b"%PDF")
    assert destination.stat().st_size > 1000


def test_pdf_keeps_two_voices_in_independent_rhythm_rows(tmp_path: Path) -> None:
    events = [
        GuitarNoteEvent(
            id="voice-1",
            source_note_index=0,
            pitch=64,
            score=ScoreTiming(
                start_beat=0.0,
                duration_beats=1.0,
                measure_number=1,
                beat_in_measure=0.0,
                voice=1,
            ),
            performance=PerformanceTiming(0.0, 1.0, 90),
            fingering=IRFingering(string=1, fret=0),
        ),
        GuitarNoteEvent(
            id="voice-2",
            source_note_index=1,
            pitch=59,
            score=ScoreTiming(
                start_beat=0.0,
                duration_beats=2.0,
                measure_number=1,
                beat_in_measure=0.0,
                voice=2,
            ),
            performance=PerformanceTiming(0.0, 2.0, 90),
            fingering=IRFingering(string=2, fret=0),
        ),
    ]
    measure = GuitarMeasure(
        number=1,
        start_beat=0.0,
        duration_beats=4.0,
        numerator=4,
        denominator=4,
        events=events,
    )
    grouped = _group_rhythm_events(measure)

    assert list(grouped) == [1, 2]
    assert grouped[1][0][1][0].score.duration_beats == 1.0
    assert grouped[2][0][1][0].score.duration_beats == 2.0

    project = GuitarProjectIR(
        title="Two Voice PDF",
        source="test.mid",
        tempo_map=[IRTempoEvent(beat=0.0, bpm=120.0)],
        time_signatures=[IRTimeSignatureEvent(0.0, 4, 4)],
        tracks=[
            GuitarTrackIR(
                id="guitar-1",
                name="Guitar",
                source_stream_id="t0:ch0:p27",
                role="lead",
                tuning=[40, 45, 50, 55, 59, 64],
                fret_count=24,
                measures=[measure],
            )
        ],
    )
    destination = tmp_path / "two-voice.pdf"
    result = export_score_pdf(project, destination)

    assert result.maximum_voice_count == 2
    assert destination.read_bytes().startswith(b"%PDF")

    project.tracks[0].measures = [
        GuitarMeasure(
            number=number,
            start_beat=0.0,
            duration_beats=4.0,
            numerator=4,
            denominator=4,
            events=events[:1] if number <= 8 else events,
        )
        for number in range(1, 17)
    ]
    mixed_layout = export_score_pdf(project, tmp_path / "mixed-voices.pdf")

    # Two single-voice systems followed by two taller V1/V2 systems require a
    # second score page; otherwise the last downward V2 stems enter the footer.
    assert mixed_layout.page_count == 3


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


def test_technique_labels_use_lanes_and_condense_repeated_collisions() -> None:
    draws, condensed = _layout_technique_labels(
        [
            _TechniquePlacement(x=10.0, text="let ring", width=18.0),
            _TechniquePlacement(x=18.0, text="let ring", width=18.0),
            _TechniquePlacement(x=18.0, text="H", width=4.0),
            _TechniquePlacement(x=24.0, text="P", width=4.0),
        ],
        base_y=100.0,
    )

    assert condensed == 1
    assert [(draw.text, draw.y) for draw in draws] == [
        ("let ring", 100.0),
        ("H", 106.5),
        ("P", 100.0),
    ]
