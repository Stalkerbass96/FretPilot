"""MIDI import and normalization for FretPilot."""

from __future__ import annotations

from collections import defaultdict, deque
from io import BytesIO
from pathlib import Path

import mido
from mido.messages.specs import SPEC_BY_STATUS
from mido.midifiles.meta import KeySignatureError

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


def _read_variable_int(data: bytearray, offset: int, end: int) -> tuple[int, int]:
    value = 0
    while offset < end:
        byte = data[offset]
        offset += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, offset
    raise OSError("Unexpected end of MIDI variable-length integer.")


def _sanitize_invalid_key_signatures(
    source: Path,
) -> tuple[bytes, list[Diagnostic]]:
    """Replace invalid key-signature payloads before Mido decodes the file.

    Key signatures are descriptive metadata and are not consumed by the V0.1
    engine. Some DAWs export out-of-range values that otherwise make Mido abort
    before any notes can be recovered. Replacing only those invalid two-byte
    payloads with C major preserves event length/timing and lets normalization
    continue with an explicit diagnostic.
    """

    data = bytearray(source.read_bytes())
    diagnostics: list[Diagnostic] = []
    if len(data) < 14 or data[:4] != b"MThd":
        return bytes(data), diagnostics

    header_length = int.from_bytes(data[4:8], "big")
    chunk_offset = 8 + header_length
    track_index = 0
    while chunk_offset + 8 <= len(data):
        chunk_type = bytes(data[chunk_offset : chunk_offset + 4])
        chunk_length = int.from_bytes(
            data[chunk_offset + 4 : chunk_offset + 8],
            "big",
        )
        chunk_start = chunk_offset + 8
        chunk_end = chunk_start + chunk_length
        if chunk_end > len(data):
            raise OSError("MIDI chunk extends beyond the end of the file.")
        if chunk_type != b"MTrk":
            chunk_offset = chunk_end
            continue

        offset = chunk_start
        absolute_tick = 0
        running_status: int | None = None
        while offset < chunk_end:
            delta, offset = _read_variable_int(data, offset, chunk_end)
            absolute_tick += delta
            if offset >= chunk_end:
                raise OSError("MIDI track ends before an event status byte.")

            status = data[offset]
            if status < 0x80:
                if running_status is None:
                    raise OSError("MIDI running status has no preceding status byte.")
                status = running_status
                first_data_consumed = True
                offset += 1
            else:
                offset += 1
                first_data_consumed = False
                if status != 0xFF:
                    running_status = status

            if status == 0xFF:
                if offset >= chunk_end:
                    raise OSError("MIDI track ends before a meta-event type.")
                meta_type = data[offset]
                offset += 1
                length, offset = _read_variable_int(data, offset, chunk_end)
                payload_start = offset
                payload_end = payload_start + length
                if payload_end > chunk_end:
                    raise OSError("MIDI meta event extends beyond its track.")
                if meta_type == 0x59 and length >= 2:
                    sharps = int.from_bytes(
                        data[payload_start : payload_start + 1],
                        "big",
                        signed=True,
                    )
                    mode = data[payload_start + 1]
                    if not -7 <= sharps <= 7 or mode not in (0, 1):
                        data[payload_start] = 0
                        data[payload_start + 1] = 0
                        diagnostics.append(
                            Diagnostic(
                                level="warning",
                                code="invalid_key_signature",
                                message=(
                                    "Ignored invalid MIDI key signature "
                                    f"({sharps} sharps/flats, mode {mode}); "
                                    "note data was preserved."
                                ),
                                track_index=track_index,
                                tick=absolute_tick,
                            )
                        )
                offset = payload_end
                continue

            if status in (0xF0, 0xF7):
                length, offset = _read_variable_int(data, offset, chunk_end)
                offset += length
                if offset > chunk_end:
                    raise OSError("MIDI SysEx event extends beyond its track.")
                continue

            try:
                message_data_length = int(SPEC_BY_STATUS[status]["length"]) - 1
            except KeyError as exc:
                raise OSError(f"Undefined MIDI status byte 0x{status:02x}.") from exc
            remaining = message_data_length - int(first_data_consumed)
            offset += remaining
            if offset > chunk_end:
                raise OSError("MIDI channel event extends beyond its track.")

        track_index += 1
        chunk_offset = chunk_end

    return bytes(data), diagnostics


def _load_mido_file(source: Path) -> tuple[mido.MidiFile, list[Diagnostic]]:
    try:
        return mido.MidiFile(source), []
    except KeySignatureError:
        sanitized, diagnostics = _sanitize_invalid_key_signatures(source)
        if not diagnostics:
            raise
        return mido.MidiFile(file=BytesIO(sanitized)), diagnostics


def load_midi(path: str | Path) -> NormalizedTimeline:
    """Read a Standard MIDI File and return FretPilot's normalized timeline.

    This stage does not quantize or repair anything. It preserves physical
    tracks, channels, program changes, source ticks, and derived beat values.
    Later layers resolve these raw structures into logical instrument streams.
    """

    source = Path(path)
    midi, diagnostics = _load_mido_file(source)
    ticks_per_beat = midi.ticks_per_beat

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
