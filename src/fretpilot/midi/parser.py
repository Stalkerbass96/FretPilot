"""MIDI import and normalization for FretPilot."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path

import mido

from fretpilot.midi.models import (
    Diagnostic,
    NormalizedNote,
    NormalizedTimeline,
    NormalizedTrack,
    TempoEvent,
    TimeSignatureEvent,
)

DEFAULT_TEMPO_US_PER_BEAT = 500_000  # MIDI default: 120 BPM
DEFAULT_TIME_SIGNATURE = (4, 4)


def _beat(tick: int, ticks_per_beat: int) -> float:
    return tick / ticks_per_beat


def load_midi(path: str | Path) -> NormalizedTimeline:
    """Read a Standard MIDI File and return FretPilot's normalized timeline.

    This stage does not quantize or "repair" anything. It preserves the source
    timing exactly in ticks and derives beat positions from PPQ. Musical repair
    belongs to the later rhythm engine.
    """

    source = Path(path)
    midi = mido.MidiFile(source)
    ticks_per_beat = midi.ticks_per_beat

    diagnostics: list[Diagnostic] = []
    tempo_events: list[TempoEvent] = []
    time_signature_events: list[TimeSignatureEvent] = []
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
        open_notes: dict[tuple[int, int], deque[tuple[int, int]]] = defaultdict(deque)
        notes: list[NormalizedNote] = []

        # First pass obtains the track name so notes created earlier in the
        # event stream still get the final human-readable name.
        for message in track:
            if message.type == "track_name" and message.name.strip():
                track_name = message.name.strip()
                break

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

            if message.is_meta:
                continue

            if message.type == "note_on" and message.velocity > 0:
                open_notes[(message.channel, message.note)].append(
                    (absolute_tick, int(message.velocity))
                )
                continue

            is_note_end = message.type == "note_off" or (
                message.type == "note_on" and message.velocity == 0
            )
            if not is_note_end:
                continue

            key = (message.channel, message.note)
            if not open_notes[key]:
                diagnostics.append(
                    Diagnostic(
                        level="warning",
                        code="unmatched_note_off",
                        message=(
                            f"Note-off for MIDI note {message.note} has no matching "
                            "note-on."
                        ),
                        track_index=track_index,
                        tick=absolute_tick,
                    )
                )
                continue

            start_tick, velocity = open_notes[key].popleft()
            duration_ticks = max(0, absolute_tick - start_tick)
            if duration_ticks == 0:
                diagnostics.append(
                    Diagnostic(
                        level="warning",
                        code="zero_length_note",
                        message=f"MIDI note {message.note} has zero duration.",
                        track_index=track_index,
                        tick=start_tick,
                    )
                )

            notes.append(
                NormalizedNote(
                    track_index=track_index,
                    track_name=track_name,
                    channel=int(message.channel),
                    pitch=int(message.note),
                    velocity=velocity,
                    start_tick=start_tick,
                    duration_ticks=duration_ticks,
                    start_beat=_beat(start_tick, ticks_per_beat),
                    duration_beats=_beat(duration_ticks, ticks_per_beat),
                )
            )

        for (channel, pitch), pending in open_notes.items():
            for start_tick, _velocity in pending:
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
            NormalizedTrack(index=track_index, name=track_name, notes=notes)
        )

    tempo_events.sort(key=lambda event: event.tick)
    time_signature_events.sort(key=lambda event: event.tick)

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
        diagnostics=diagnostics,
    )
