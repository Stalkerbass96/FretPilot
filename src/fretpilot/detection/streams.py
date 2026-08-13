"""Resolve raw MIDI tracks/channels/programs into logical instrument streams."""

from __future__ import annotations

from collections import defaultdict

from fretpilot.detection.models import InstrumentStream
from fretpilot.midi.gm import program_family, program_name
from fretpilot.midi.models import NormalizedTimeline


def resolve_instrument_streams(timeline: NormalizedTimeline) -> list[InstrumentStream]:
    """Split notes by physical track, channel, and active program.

    A MIDI type-0 file often contains one physical track with many channels.
    Conversely, type-1 files may have one instrument per physical track. This
    resolver normalizes both cases into the same logical representation.
    """

    streams: list[InstrumentStream] = []

    for track in timeline.tracks:
        grouped = defaultdict(list)
        for note in track.notes:
            grouped[(note.channel, note.program)].append(note)

        for (channel, program), notes in sorted(
            grouped.items(),
            key=lambda item: (item[0][0], -1 if item[0][1] is None else item[0][1]),
        ):
            program_token = "unknown" if program is None else str(program)
            stream_id = f"t{track.index}:ch{channel}:p{program_token}"
            streams.append(
                InstrumentStream(
                    stream_id=stream_id,
                    source_track_index=track.index,
                    source_track_name=track.name,
                    channel=channel,
                    program=program,
                    program_name=program_name(program) if program is not None else None,
                    program_family=(
                        program_family(program) if program is not None else None
                    ),
                    instrument_name=track.instrument_name,
                    notes=sorted(
                        notes,
                        key=lambda note: (note.start_tick, note.pitch, note.channel),
                    ),
                )
            )

    return streams
