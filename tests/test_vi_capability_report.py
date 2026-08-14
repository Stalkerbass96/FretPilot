from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
    IRArticulation,
    IRFingering,
    IRRightHandIntent,
    IRTempoEvent,
    IRTimeSignatureEvent,
    PerformanceTiming,
    ScoreTiming,
)
from fretpilot.performance.models import GuitarPerformancePlan, PerformanceNoteIntent
from fretpilot.virtual_instruments.ample_guitar_sc import AMPLE_GUITAR_SC_V4_PROFILE
from fretpilot.virtual_instruments.capability_report import build_capability_report


def _event(*, event_id: str, start: float, tie_in: bool = False) -> GuitarNoteEvent:
    return GuitarNoteEvent(
        id=event_id,
        source_note_index=0,
        pitch=64,
        score=ScoreTiming(
            start_beat=start,
            duration_beats=0.5,
            measure_number=1,
            beat_in_measure=start,
            tie_in=tie_in,
        ),
        performance=PerformanceTiming(
            source_start_beat=0.0,
            source_duration_beats=1.0,
            velocity=90,
        ),
        fingering=IRFingering(string=1, fret=0),
        articulations=[
            IRArticulation(
                type="hammer_on",
                confidence=0.9,
                reason="fixture",
            )
        ],
        right_hand=IRRightHandIntent(
            motion="pick",
            direction="down",
            confidence=0.9,
            reason="fixture",
            technique="tremolo",
        ),
    )


def _project() -> GuitarProjectIR:
    return GuitarProjectIR(
        title="VI report",
        source="fixture.mid",
        tempo_map=[IRTempoEvent(beat=0.0, bpm=120.0)],
        time_signatures=[IRTimeSignatureEvent(beat=0.0, numerator=4, denominator=4)],
        tracks=[
            GuitarTrackIR(
                id="guitar-1",
                name="Guitar",
                source_stream_id="t0:ch0:p29",
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
                        events=[
                            _event(event_id="n-0", start=0.0),
                            _event(event_id="n-0-tie", start=0.5, tie_in=True),
                        ],
                    )
                ],
            )
        ],
    )


def _performance_plan() -> GuitarPerformancePlan:
    return GuitarPerformancePlan(
        source="fixture.mid",
        track_id="guitar-1",
        source_stream_id="t0:ch0:p29",
        notes=[
            PerformanceNoteIntent(
                source_note_index=0,
                pitch=64,
                section_id=None,
                source_start_beat=0.0,
                source_duration_beats=1.0,
                source_velocity=90,
                target_start_beat=0.02,
                target_duration_beats=1.0,
                target_velocity=96,
                timing_offset_beats=0.02,
                duration_delta_beats=0.0,
                velocity_delta=6,
                metric_accent=0.5,
                reasons=["fixture"],
            )
        ],
    )


def _requirements(report):
    return {(item.source, item.intent): item for item in report.requirements}


def test_report_resolves_actual_ir_and_performance_requirements_against_ample():
    report = build_capability_report(
        _project(),
        AMPLE_GUITAR_SC_V4_PROFILE,
        performance_plan=_performance_plan(),
    )
    items = _requirements(report)

    assert items[("articulation", "hammer_on")].occurrences == 1
    assert items[("articulation", "hammer_on")].resolution.support == "native"

    assert items[("right_hand", "pick_down")].occurrences == 1
    assert items[("right_hand", "pick_down")].resolution.support == "unsupported"
    assert items[("right_hand", "tremolo")].occurrences == 1
    assert items[("right_hand", "tremolo")].resolution.support == "unsupported"

    assert items[("performance_plan", "performance_timing_adjustment")].occurrences == 1
    assert items[("performance_plan", "performance_timing_adjustment")].resolution.support == "unsupported"
    assert items[("performance_plan", "performance_velocity_adjustment")].occurrences == 1
    assert items[("performance_plan", "performance_velocity_adjustment")].resolution.support == "unsupported"
    assert ("performance_plan", "performance_duration_adjustment") not in items

    assert report.native_count == 1
    assert report.approximated_count == 0
    assert report.unsupported_count == 4


def test_tied_score_fragments_do_not_double_count_canonical_requirements():
    report = build_capability_report(_project(), AMPLE_GUITAR_SC_V4_PROFILE)
    items = _requirements(report)
    assert items[("articulation", "hammer_on")].occurrences == 1
    assert items[("right_hand", "pick_down")].occurrences == 1
    assert items[("right_hand", "tremolo")].occurrences == 1


def test_omitting_performance_plan_adds_no_performance_requirements():
    report = build_capability_report(_project(), AMPLE_GUITAR_SC_V4_PROFILE)
    assert all(item.source != "performance_plan" for item in report.requirements)


def test_report_to_dict_contains_explicit_support_summary():
    payload = build_capability_report(
        _project(),
        AMPLE_GUITAR_SC_V4_PROFILE,
        performance_plan=_performance_plan(),
    ).to_dict()
    assert payload["profile_id"] == "ample-guitar-sc-v4"
    assert payload["summary"] == {
        "native_occurrences": 1,
        "approximated_occurrences": 0,
        "unsupported_occurrences": 4,
    }
