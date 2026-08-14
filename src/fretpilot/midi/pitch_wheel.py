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
