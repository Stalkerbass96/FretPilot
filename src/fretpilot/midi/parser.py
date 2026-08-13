"""MIDI import and normalization for FretPilot."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path

import mido

from fretpilot.midi.gm import program_family, program_name
from fretpilot.midi.models import (
    Diagnostic,
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    ProgramEvent,
    TempoEvent,
    TimeSignatureEvent,
)

DEFAULT_TEMPO_US_PER_BEAT = 500_000  # MIDI default: 120 BPM
DEFAULT_TIME_SIGNATURE = (4, 4)


def _beat(tick: int, ticks_per_beat: int) -> float:
    return tick / ticks_per_beat


def load_midi(path: str | Path) -> NormalizedTimeline:
    """Read a Standard MIDI File and return FretPilot's normalized timeline.

    This stage does not quantize or repair anything. It preserves physical
    tracks, channels, program changes, source ticks, and derived beat values.
    Later layers resolve these raw structures into logical instrument streams.
    """

    source = Path(path)
    midi = mido.MidiFile(source)
    ticks_per_beat = midi.ticks_per_beat

    diagnostics: list[Diagnostic] = []
    tempo_events: list[TempoEvent] = []
    time_signature_events: list[TimeSignatureEvent] = []
    program_events: list[ProgramEvent] = []
    normalized_tracks: list[NormalizedTrack] = []

    if midi.type == 2:
        diagnostics.append(
            Diagnostic(
                level="warning",
                code="midi_type_2",
                message=(
                    "MIDI type 2 contains asynchronous track sequences. "
                    "FretPilot V0.1 treats track tick positions independently."
                ),
            )
        )

    for track_index, track in enumerate(midi.tracks):
        absolute_tick = 0
        track_name = f"Track {track_index + 1}"
        instrument_name: str | None = None
        current_program: dict[int, int] = {}
        open_notes: dict[
            tuple[int, int],
            deque[tuple[int, int, int | None]],
        ] = defaultdict(deque)
        notes: list[NormalizedNote] = []

        # Obtain final descriptive metadata before constructing notes.
        for message in track:
            if message.type == "track_name" and message.name.strip():
                track_name = message.name.strip()
            elif message.type == "instrument_name" and message.name.strip():
                instrument_name = message.name.strip()

        for message in track:
            absolute_tick += int(message.time)

            if message.type == "set_tempo":
                tempo_events.append(
                    TempoEvent(
                        tick=absolute_tick,
                        beat=_beat(absolute_tick, ticks_per_beat),
                        bpm=round(float(mido.tempo2bpm(message.tempo)), 6),
                    )
                )
                continue

            if message.type == "time_signature":
                time_signature_events.append(
                    TimeSignatureEvent(
                        tick=absolute_tick,
                        beat=_beat(absolute_tick, ticks_per_beat),
                        numerator=int(message.numerator),
                        denominator=int(message.denominator),
                    )
                )
                continue

            if message.type == "program_change":
                program = int(message.program)
                channel = int(message.channel)
                current_program[channel] = program
                program_events.append(
                    ProgramEvent(
                        track_index=track_index,
                        channel=channel,
                        tick=absolute_tick,
                        beat=_beat(absolute_tick, ticks_per_beat),
                        program=program,
                        program_name=program_name(program),
                        family=program_family(program),
                    )
                )
                continue

            if message.is_meta:
                continue

            if message.type == "note_on" and message.velocity > 0:
                channel = int(message.channel)
                open_notes[(channel, int(message.note))].append(
                    (
                        absolute_tick,
                        int(message.velocity),
                        current_program.get(channel),
                    )
                )
                continue

            is_note_end = message.type == "note_off" or (
                message.type == "note_on" and message.velocity == 0
            )
            if not is_note_end:
                continue

            channel = int(message.channel)
            pitch = int(message.note)
            key = (channel, pitch)
            if not open_notes[key]:
                diagnostics.append(
                    Diagnostic(
                        level="warning",
                        code="unmatched_note_off",
                        message=(
                            f"Note-off for MIDI note {pitch} has no matching note-on."
                        ),
                        track_index=track_index,
                        tick=absolute_tick,
                    )
                )
                continue

            start_tick, velocity, program = open_notes[key].popleft()
            duration_ticks = max(0, absolute_tick - start_tick)
            if duration_ticks == 0:
                diagnostics.append(
                    Diagnostic(
                        level="warning",
                        code="zero_length_note",
                        message=f"MIDI note {pitch} has zero duration.",
                        track_index=track_index,
                        tick=start_tick,
                    )
                )

            notes.append(
                NormalizedNote(
                    track_index=track_index,
                    track_name=track_name,
                    channel=channel,
                    pitch=pitch,
                    velocity=velocity,
                    start_tick=start_tick,
                    duration_ticks=duration_ticks,
                    start_beat=_beat(start_tick, ticks_per_beat),
                    duration_beats=_beat(duration_ticks, ticks_per_beat),
                    program=program,
                )
            )

        for (channel, pitch), pending in open_notes.items():
            for start_tick, _velocity, _program in pending:
                diagnostics.append(
                    Diagnostic(
                        level="warning",
                        code="unclosed_note",
                        message=(
                            f"MIDI note {pitch} on channel {channel} has no "
                            "matching note-off."
                        ),
                        track_index=track_index,
                        tick=start_tick,
                    )
                )

        notes.sort(key=lambda note: (note.start_tick, note.pitch, note.channel))
        normalized_tracks.append(
            NormalizedTrack(
                index=track_index,
                name=track_name,
                notes=notes,
                instrument_name=instrument_name,
            )
        )

    tempo_events.sort(key=lambda event: event.tick)
    time_signature_events.sort(key=lambda event: event.tick)
    program_events.sort(key=lambda event: (event.tick, event.track_index, event.channel))

    if not tempo_events or tempo_events[0].tick > 0:
        tempo_events.insert(
            0,
            TempoEvent(
                tick=0,
                beat=0.0,
                bpm=round(float(mido.tempo2bpm(DEFAULT_TEMPO_US_PER_BEAT)), 6),
            ),
        )
        diagnostics.append(
            Diagnostic(
                level="info",
                code="default_tempo",
                message="No tempo was defined at beat 0; MIDI default 120 BPM is used.",
                tick=0,
            )
        )

    if not time_signature_events or time_signature_events[0].tick > 0:
        numerator, denominator = DEFAULT_TIME_SIGNATURE
        time_signature_events.insert(
            0,
            TimeSignatureEvent(
                tick=0,
                beat=0.0,
                numerator=numerator,
                denominator=denominator,
            ),
        )
        diagnostics.append(
            Diagnostic(
                level="info",
                code="default_time_signature",
                message="No time signature was defined at beat 0; 4/4 is assumed.",
                tick=0,
            )
        )

    return NormalizedTimeline(
        source=NormalizedTimeline.source_name(source),
        midi_type=int(midi.type),
        ticks_per_beat=int(ticks_per_beat),
        tempo_events=tempo_events,
        time_signature_events=time_signature_events,
        tracks=normalized_tracks,
        program_events=program_events,
        diagnostics=diagnostics,
    )
