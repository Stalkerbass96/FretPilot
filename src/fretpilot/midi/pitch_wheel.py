from pathlib import Path

import mido

from fretpilot.midi.models import PitchWheelEvent, PitchWheelRangeEvent
from fretpilot.midi.parser import load_midi as _load_base_midi


def load_midi(path: str | Path):
    timeline = _load_base_midi(path)
    midi = mido.MidiFile(path)
    wheel_events = []
    range_events = []

    for track_index, track in enumerate(midi.tracks):
        tick = 0
        rpn_msb: dict[int, int | None] = {}
        rpn_lsb: dict[int, int | None] = {}
        range_semitones: dict[int, int] = {}
        range_cents: dict[int, int] = {}

        for message in track:
            tick += int(message.time)
            if message.is_meta:
                continue

            channel = int(getattr(message, "channel", 0))
            if message.type == "pitchwheel":
                wheel_events.append(
                    PitchWheelEvent(
                        track_index=track_index,
                        channel=channel,
                        tick=tick,
                        beat=tick / timeline.ticks_per_beat,
                        value=int(message.pitch),
                    )
                )
                continue

            if message.type != "control_change":
                continue

            control = int(message.control)
            value = int(message.value)
            if control == 101:
                rpn_msb[channel] = value
            elif control == 100:
                rpn_lsb[channel] = value
            elif control in {6, 38} and rpn_msb.get(channel) == 0 and rpn_lsb.get(channel) == 0:
                if control == 6:
                    range_semitones[channel] = value
                else:
                    range_cents[channel] = value
                if channel in range_semitones:
                    event = PitchWheelRangeEvent(
                        track_index=track_index,
                        channel=channel,
                        tick=tick,
                        beat=tick / timeline.ticks_per_beat,
                        semitones=range_semitones[channel],
                        cents=range_cents.get(channel, 0),
                    )
                    if not range_events or range_events[-1] != event:
                        range_events.append(event)

    timeline.pitch_wheel_events = sorted(
        wheel_events,
        key=lambda item: (item.tick, item.track_index, item.channel),
    )
    timeline.pitch_wheel_range_events = sorted(
        range_events,
        key=lambda item: (item.tick, item.track_index, item.channel),
    )
    return timeline


def extract_monophonic_pitch_raises(timeline, stream):
    """Return explicit positive wheel gestures only when source evidence is unambiguous."""

    wheels = [
        event for event in timeline.pitch_wheel_events
        if event.track_index == stream.source_track_index
        and event.channel == stream.channel
    ]
    ranges = [
        event for event in timeline.pitch_wheel_range_events
        if event.track_index == stream.source_track_index
        and event.channel == stream.channel
    ]
    if not wheels or not ranges:
        return []

    results = []
    for note_index, note in enumerate(stream.notes):
        events = [
            event for event in wheels
            if note.start_tick <= event.tick <= note.end_tick
        ]
        positive = [event for event in events if event.value > 0]
        if not positive:
            continue
        peak = max(positive, key=lambda event: event.value)
        active_count = sum(
            other.start_tick <= peak.tick < other.end_tick
            for other in stream.notes
        )
        if active_count != 1:
            continue
        active_ranges = [event for event in ranges if event.tick <= peak.tick]
        if not active_ranges:
            continue
        wheel_range = active_ranges[-1]
        total_range = wheel_range.semitones + wheel_range.cents / 100.0
        if total_range <= 0:
            continue
        semitones = peak.value / 8192.0 * total_range
        if semitones < 0.25:
            continue

        center_events = [
            event for event in events
            if event.tick >= peak.tick and abs(event.value) <= 64
        ]
        return_event = center_events[0] if center_events else None
        duration_ticks = max(1, note.duration_ticks)
        peak_position = max(
            0.0,
            min(1.0, (peak.tick - note.start_tick) / duration_ticks),
        )
        return_position = (
            max(
                peak_position,
                min(1.0, (return_event.tick - note.start_tick) / duration_ticks),
            )
            if return_event is not None
            else 1.0
        )
        results.append(
            {
                "note_index": note_index,
                "semitones": round(semitones, 6),
                "peak_wheel": float(peak.value),
                "range_semitones": round(total_range, 6),
                "peak_position": round(peak_position, 6),
                "return_position": round(return_position, 6),
                "returned_to_center": return_event is not None,
            }
        )
    return results
