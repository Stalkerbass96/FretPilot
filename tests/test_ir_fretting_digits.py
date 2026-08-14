from fretpilot.analysis import analyze_guitar_track
from fretpilot.ir import build_guitar_ir
from fretpilot.knowledge import FingeringPreferences, PlayingContext
from fretpilot.midi.models import NormalizedNote, NormalizedTimeline, NormalizedTrack, TempoEvent, TimeSignatureEvent


def test_guitar_ir_persists_final_fretting_digits():
    notes = [
        NormalizedNote(0, "Guitar", 0, pitch, 90, i * 240, 240, i * 0.5, 0.5, 27)
        for i, pitch in enumerate([64, 66, 67])
    ]
    track = NormalizedTrack(0, "Guitar", notes)
    timeline = NormalizedTimeline(
        "fixture.mid", 1, 480,
        [TempoEvent(0, 0.0, 120.0)],
        [TimeSignatureEvent(0, 0.0, 4, 4)],
        [track],
    )
    context = PlayingContext(
        fingering=FingeringPreferences(open_string_usage=0.0)
    )
    analysis = analyze_guitar_track(track, playing_context=context)
    project = build_guitar_ir(timeline, track, analysis)
    events = project.tracks[0].measures[0].events

    assert [(event.fingering.string, event.fingering.fret) for event in events] == [
        (2, 5), (2, 7), (2, 8),
    ]
    assert [event.fingering.fretting_digit for event in events] == [1, 3, 4]
