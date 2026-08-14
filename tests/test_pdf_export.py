from pathlib import Path

from fretpilot.exporters.pdf_score import export_score_pdf
from fretpilot.exporters.pdf_score.renderer import (
    _TechniquePlacement,
    _duration_label,
    _harmony_label_map,
    _layout_technique_labels,
    _measure_for_voice,
)
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


def test_duration_labels_never_round_unknown_values_to_standard_notes() -> None:
    assert _duration_label(0.5) == "1/8"
    assert _duration_label(1 / 3) == "8T"
    assert _duration_label(0.4) == "0.4b"
    assert _duration_label(2.5) == "2.5b"


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
    assert result.maximum_voice_count == 1
    assert destination.read_bytes().startswith(b"%PDF")
    assert destination.stat().st_size > 1000


def test_pdf_keeps_two_voices_in_independent_rhythm_lanes(tmp_path: Path) -> None:
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
    voice_one = _measure_for_voice(measure, 1)
    voice_two = _measure_for_voice(measure, 2)

    assert [event.id for event in voice_one.events] == ["voice-1"]
    assert [event.id for event in voice_two.events] == ["voice-2"]

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
    assert destination.stat().st_size > 1000
