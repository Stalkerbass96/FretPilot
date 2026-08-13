"""Canonical data structures produced by FretPilot's MIDI import layer.

The importer intentionally preserves raw MIDI ticks while also exposing musical
beat values. Later rhythm-repair stages should never need to guess what the
original file contained.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TempoEvent:
    tick: int
    beat: float
    bpm: float


@dataclass(slots=True)
class TimeSignatureEvent:
    tick: int
    beat: float
    numerator: int
    denominator: int


@dataclass(slots=True)
class NormalizedNote:
    track_index: int
    track_name: str
    channel: int
    pitch: int
    velocity: int
    start_tick: int
    duration_ticks: int
    start_beat: float
    duration_beats: float

    @property
    def end_tick(self) -> int:
        return self.start_tick + self.duration_ticks

    @property
    def end_beat(self) -> float:
        return self.start_beat + self.duration_beats


@dataclass(slots=True)
class NormalizedTrack:
    index: int
    name: str
    notes: list[NormalizedNote] = field(default_factory=list)


@dataclass(slots=True)
class Diagnostic:
    level: str
    code: str
    message: str
    track_index: int | None = None
    tick: int | None = None


@dataclass(slots=True)
class NormalizedTimeline:
    source: str
    midi_type: int
    ticks_per_beat: int
    tempo_events: list[TempoEvent]
    time_signature_events: list[TimeSignatureEvent]
    tracks: list[NormalizedTrack]
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def note_count(self) -> int:
        return sum(len(track.notes) for track in self.tracks)

    @property
    def duration_beats(self) -> float:
        end_beats = [
            note.end_beat
            for track in self.tracks
            for note in track.notes
        ]
        return max(end_beats, default=0.0)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["summary"] = {
            "track_count": len(self.tracks),
            "note_count": self.note_count,
            "duration_beats": self.duration_beats,
        }
        return payload

    @classmethod
    def source_name(cls, path: str | Path) -> str:
        return str(Path(path))
