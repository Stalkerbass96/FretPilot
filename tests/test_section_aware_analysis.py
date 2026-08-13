from __future__ import annotations

from fretpilot.analysis import (
    SectionContextAnalysis,
    analyze_guitar_stream_section_aware,
    analyze_guitar_track_by_sections,
)
from fretpilot.detection.models import InstrumentStream
from fretpilot.ir import build_guitar_ir
from fretpilot.knowledge.playing_contexts import (
    ArticulationPreferences,
    FingeringPreferences,
    PlayingContext,
)
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)


def _note(pitch: int, start_beat: float, duration: float = 0.5) -> NormalizedNote:
    return NormalizedNote(
        track_index=0,
        track_name="Guitar",
        channel=0,
        pitch=pitch,
        velocity=90,
        start_tick=round(start_beat * 480),
        duration_ticks=round(duration * 480),
        start_beat=start_beat,
        duration_beats=duration,
        program=27,
    )


def _timeline(track: NormalizedTrack) -> NormalizedTimeline:
    return NormalizedTimeline(
        source="section-aware.mid",
        midi_type=1,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(tick=0, beat=0.0, bpm=120.0)],
        time_signature_events=[
            TimeSignatureEvent(tick=0, beat=0.0, numerator=4, denominator=4)
        ],
        tracks=[track],
    )


def _context_section(
    section_id: str,
    start_beat: float,
    end_beat: float,
    context: PlayingContext,
    *,
    boundary_strength: float = 0.0,
    boundary_reason: str = "test_boundary",
) -> SectionContextAnalysis:
    return SectionContextAnalysis(
        section_id=section_id,
        stream_id="t0:ch0:p27",
        start_measure=int(start_beat // 4) + 1,
        end_measure=int((end_beat - 1e-9) // 4) + 1,
        start_beat=start_beat,
        end_beat=end_beat,
        behavior_profiles=[],
        playing_context=context,
        boundary_strength=boundary_strength,
        boundary_reason=boundary_reason,
    )


def test_section_contexts_drive_different_valid_fingering_and_articulation() -> None:
    track = NormalizedTrack(
        index=0,
        name="Guitar",
        notes=[
            _note(64, 0.0),
            _note(66, 0.5),
            _note(64, 4.0),
            _note(66, 4.5),
        ],
    )
    open_context = PlayingContext(
        fingering=FingeringPreferences(open_string_usage=1.0),
        articulation=ArticulationPreferences(hammer_pull=0.50),
    )
    closed_context = PlayingContext(
        fingering=FingeringPreferences(open_string_usage=0.0),
        articulation=ArticulationPreferences(hammer_pull=1.25),
    )
    sections = [
        _context_section("section-001", 0.0, 4.0, open_context),
        _context_section("section-002", 4.0, 8.0, closed_context),
    ]

    analysis = analyze_guitar_track_by_sections(track, sections)

    assert [(item.string, item.fret) for item in analysis.fingering.notes] == [
        (1, 0),
        (1, 2),
        (2, 5),
        (2, 7),
    ]
    hammer_ons = [
        item for item in analysis.articulations.decisions if item.technique == "hammer_on"
    ]
    assert [(item.source_note_index, item.note_index) for item in hammer_ons] == [
        (0, 1),
        (2, 3),
    ]
    assert hammer_ons[0].confidence < hammer_ons[1].confidence
    assert [item.note_index for item in analysis.fingering.notes] == [0, 1, 2, 3]


def test_auto_section_analysis_round_trips_global_indices_into_guitar_ir() -> None:
    notes: list[NormalizedNote] = []

    # Bars 1-2: low repeated riff.
    for step in range(16):
        notes.append(_note(40 if step % 4 else 43, step * 0.5))

    # Bars 3-4: chord rhythm with a very different onset/polyphony profile.
    for step in range(8):
        onset = 8.0 + step
        for pitch in (52, 59, 64):
            notes.append(_note(pitch, onset, 0.75))

    track = NormalizedTrack(index=0, name="Guitar", notes=notes)
    timeline = _timeline(track)
    stream = InstrumentStream(
        stream_id="t0:ch0:p27",
        source_track_index=0,
        source_track_name="Guitar",
        channel=0,
        program=27,
        program_name="Electric Guitar (clean)",
        program_family="guitar",
        instrument_name=None,
        notes=notes,
    )

    analysis = analyze_guitar_stream_section_aware(
        timeline,
        stream,
        window_measures=2,
        change_threshold=0.20,
    )

    assert len(analysis.section_contexts) == 2
    assert len(analysis.fingering.notes) == len(notes)
    assert [item.note_index for item in analysis.fingering.notes] == list(range(len(notes)))
    assert all(
        0 <= item.note_index < len(notes)
        and (
            item.source_note_index is None
            or 0 <= item.source_note_index < len(notes)
        )
        for item in analysis.articulations.decisions
    )

    project = build_guitar_ir(
        timeline,
        stream.as_track(),
        analysis,
        source_stream_id=stream.stream_id,
    )
    events = [
        event
        for measure in project.tracks[0].measures
        for event in measure.events
    ]
    assert {event.source_note_index for event in events} == set(range(len(notes)))
    assert all(event.fingering.playable for event in events)


def test_weak_boundary_carries_hand_position_but_strong_boundary_resets() -> None:
    track = NormalizedTrack(
        index=0,
        name="Lead Guitar",
        notes=[
            # Avoiding the open E string puts section 1 around frets 5-7.
            _note(64, 3.0),
            _note(66, 3.5),
            # Independently these prefer frets 1-3; a weak boundary should keep
            # their alternative frets 6-8 near the previous hand position.
            _note(65, 4.0),
            _note(67, 4.5),
        ],
    )
    positioned = PlayingContext(
        fingering=FingeringPreferences(open_string_usage=0.0)
    )
    neutral = PlayingContext()

    weak = analyze_guitar_track_by_sections(
        track,
        [
            _context_section("section-001", 0.0, 4.0, positioned),
            _context_section(
                "section-002",
                4.0,
                8.0,
                neutral,
                boundary_strength=0.20,
                boundary_reason="similar_lead_phrase",
            ),
        ],
    )
    strong = analyze_guitar_track_by_sections(
        track,
        [
            _context_section("section-001", 0.0, 4.0, positioned),
            _context_section(
                "section-002",
                4.0,
                8.0,
                neutral,
                boundary_strength=0.90,
                boundary_reason="role_change",
            ),
        ],
    )

    assert [item.fret for item in weak.fingering.notes[2:]] == [6, 8]
    assert [item.fret for item in strong.fingering.notes[2:]] == [1, 3]

    weak_transition = weak.hand_position_plan.transitions[0]
    assert weak_transition.action == "carry"
    assert weak_transition.shift_distance <= 2.0
    assert weak_transition.reason == "similar_lead_phrase"

    strong_transition = strong.hand_position_plan.transitions[0]
    assert strong_transition.action == "reset"
    assert strong_transition.shift_distance >= 3.0
    assert strong_transition.reason == "role_change"


def test_hand_position_plan_is_persisted_in_guitar_ir() -> None:
    track = NormalizedTrack(
        index=0,
        name="Lead Guitar",
        notes=[_note(64, 0.0), _note(66, 0.5), _note(65, 4.0), _note(67, 4.5)],
    )
    sections = [
        _context_section("section-001", 0.0, 4.0, PlayingContext()),
        _context_section(
            "section-002",
            4.0,
            8.0,
            PlayingContext(),
            boundary_strength=0.20,
        ),
    ]
    analysis = analyze_guitar_track_by_sections(track, sections)

    project = build_guitar_ir(_timeline(track), track, analysis)

    plan = project.tracks[0].hand_position_plan
    assert plan is not None
    assert len(plan["sections"]) == 2
    assert len(plan["transitions"]) == 1
    assert plan["transitions"][0]["from_section_id"] == "section-001"
    assert plan["transitions"][0]["to_section_id"] == "section-002"
