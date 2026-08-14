from pathlib import Path

import mido

from fretpilot.exporters.ample_guitar import export_ample_sc_midi
from fretpilot.exporters.ample_guitar.profile_view import renderer_profile_from_generic
from fretpilot.exporters.ample_guitar.profiles import AMPLE_GUITAR_SC_V4 as LEGACY
from fretpilot.exporters.ample_guitar.renderer import (
    export_ample_sc_midi as export_legacy_ample_sc_midi,
)
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


def _event(
    index: int,
    *,
    pitch: int,
    start: float,
    articulation: IRArticulation | None = None,
) -> GuitarNoteEvent:
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
            velocity=80 + index,
        ),
        fingering=IRFingering(string=1 + (index % 6), fret=5 + index),
        articulations=[] if articulation is None else [articulation],
    )


def _project() -> GuitarProjectIR:
    events = [
        _event(0, pitch=64, start=0.0),
        _event(
            1,
            pitch=66,
            start=0.5,
            articulation=IRArticulation(
                type="hammer_on",
                confidence=0.95,
                reason="fixture",
                source_note_id="n0",
            ),
        ),
        _event(
            2,
            pitch=67,
            start=1.0,
            articulation=IRArticulation(
                type="slide",
                confidence=0.95,
                reason="fixture",
                source_note_id="n1",
            ),
        ),
        _event(
            3,
            pitch=69,
            start=1.5,
            articulation=IRArticulation(
                type="natural_harmonic",
                confidence=0.95,
                reason="fixture",
            ),
        ),
        _event(
            4,
            pitch=70,
            start=2.0,
            articulation=IRArticulation(
                type="palm_mute",
                confidence=0.95,
                reason="fixture",
            ),
        ),
        _event(
            5,
            pitch=71,
            start=2.5,
            articulation=IRArticulation(
                type="slide_in",
                confidence=0.95,
                reason="fixture",
            ),
        ),
        _event(
            6,
            pitch=72,
            start=3.0,
            articulation=IRArticulation(
                type="slide_out",
                confidence=0.95,
                reason="fixture",
            ),
        ),
        _event(
            7,
            pitch=74,
            start=3.5,
            articulation=IRArticulation(
                type="let_ring",
                confidence=0.95,
                reason="fixture",
            ),
        ),
    ]
    return GuitarProjectIR(
        title="Ample Generic Handoff",
        source="fixture.mid",
        tempo_map=[IRTempoEvent(beat=0.0, bpm=120.0)],
        time_signatures=[IRTimeSignatureEvent(beat=0.0, numerator=4, denominator=4)],
        tracks=[
            GuitarTrackIR(
                id="guitar-1",
                name="Guitar",
                source_stream_id="fixture",
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


def _midi_signature(path: Path):
    midi = mido.MidiFile(path)
    signature = []
    for track_index, track in enumerate(midi.tracks):
        absolute_tick = 0
        for message in track:
            absolute_tick += message.time
            payload = message.dict()
            payload.pop("time", None)
            signature.append((track_index, absolute_tick, payload))
    return signature


def test_generic_renderer_view_matches_all_legacy_fields_used_by_scheduler():
    view = renderer_profile_from_generic(AMPLE_GUITAR_SC_V4_PROFILE)
    assert view.profile_id == LEGACY.profile_id
    assert view.product == LEGACY.product
    assert view.version_family == LEGACY.version_family
    assert view.playable_min == LEGACY.playable_min
    assert view.playable_max == LEGACY.playable_max
    assert view.note_channel == LEGACY.note_channel
    assert view.keyswitch_velocity == LEGACY.keyswitch_velocity
    assert view.note_off_velocity == LEGACY.note_off_velocity
    assert view.keyswitch_length_ticks == LEGACY.keyswitch_length_ticks
    assert view.legato_overlap_ticks == LEGACY.legato_overlap_ticks
    assert view.keyswitch_preroll_ticks == LEGACY.keyswitch_preroll_ticks
    assert view.keyswitches == {
        "sustain": LEGACY.keyswitches["sustain"],
        "natural_harmonic": LEGACY.keyswitches["natural_harmonic"],
        "palm_mute": LEGACY.keyswitches["palm_mute"],
        "slide_in_out": LEGACY.keyswitches["slide_in_out"],
        "legato_slide": LEGACY.keyswitches["legato_slide"],
        "hammer_pull": LEGACY.keyswitches["hammer_pull"],
    }


def test_default_generic_profile_handoff_is_semantically_identical_to_legacy_renderer(tmp_path: Path):
    project = _project()
    generic_path = tmp_path / "generic.mid"
    legacy_path = tmp_path / "legacy.mid"

    generic_report = export_ample_sc_midi(project, generic_path)
    legacy_report = export_legacy_ample_sc_midi(
        project,
        legacy_path,
        profile=LEGACY,
    )

    assert generic_report.profile_id == legacy_report.profile_id == LEGACY.profile_id
    assert generic_report.source_note_count == legacy_report.source_note_count
    assert generic_report.keyswitch_count == legacy_report.keyswitch_count
    assert generic_report.warnings == legacy_report.warnings
    assert _midi_signature(generic_path) == _midi_signature(legacy_path)


def test_public_renderer_still_accepts_explicit_legacy_profile_override(tmp_path: Path):
    project = _project()
    default_path = tmp_path / "default.mid"
    explicit_legacy_path = tmp_path / "explicit-legacy.mid"

    export_ample_sc_midi(project, default_path)
    export_ample_sc_midi(project, explicit_legacy_path, profile=LEGACY)

    assert _midi_signature(default_path) == _midi_signature(explicit_legacy_path)


def test_public_renderer_accepts_explicit_generic_profile(tmp_path: Path):
    project = _project()
    default_path = tmp_path / "default.mid"
    explicit_generic_path = tmp_path / "explicit-generic.mid"

    export_ample_sc_midi(project, default_path)
    export_ample_sc_midi(
        project,
        explicit_generic_path,
        profile=AMPLE_GUITAR_SC_V4_PROFILE,
    )

    assert _midi_signature(default_path) == _midi_signature(explicit_generic_path)
