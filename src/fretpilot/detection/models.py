"""Data models for layered instrument and guitar-behavior detection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from fretpilot.midi.models import NormalizedNote, NormalizedTrack


@dataclass(slots=True)
class InstrumentStream:
    """Logical musical stream resolved from a physical track/channel/program."""

    stream_id: str
    source_track_index: int
    source_track_name: str
    channel: int
    program: int | None
    program_name: str | None
    program_family: str | None
    instrument_name: str | None
    notes: list[NormalizedNote] = field(default_factory=list)

    @property
    def display_channel(self) -> int:
        return self.channel + 1

    @property
    def is_drum_channel(self) -> bool:
        # General MIDI percussion uses zero-based channel 9 (display channel 10).
        return self.channel == 9

    def as_track(self) -> NormalizedTrack:
        """Expose the stream to existing rhythm/fingering engines."""

        label_parts = [self.source_track_name, f"CH{self.display_channel}"]
        if self.program_name:
            label_parts.append(self.program_name)
        return NormalizedTrack(
            index=self.source_track_index,
            name=" · ".join(label_parts),
            notes=self.notes,
            instrument_name=self.instrument_name,
        )


@dataclass(slots=True)
class BehaviorFeatures:
    note_count: int
    pitch_min: int | None
    pitch_max: int | None
    pitch_range_semitones: int
    playable_pitch_ratio: float
    onset_count: int
    max_onset_polyphony: int
    mean_onset_polyphony: float
    monophonic_onset_ratio: float
    chord_onset_ratio: float
    adjacent_interval_within_octave_ratio: float
    repeated_pitch_ratio: float
    low_register_ratio: float
    short_note_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DetectionLayerResult:
    layer: str
    score: float
    status: str
    reasons: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BehaviorProfileMatch:
    profile_id: str
    label: str
    score: float
    status: str
    matched_features: list[str] = field(default_factory=list)
    missing_features: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GuitarStreamCandidate:
    stream: InstrumentStream
    guitar_probability: float
    confidence: float
    decision: str
    layers: list[DetectionLayerResult]
    behavior_profiles: list[BehaviorProfileMatch] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["stream"]["display_channel"] = self.stream.display_channel
        payload["stream"]["is_drum_channel"] = self.stream.is_drum_channel
        return payload


@dataclass(slots=True)
class GuitarDetectionReport:
    source: str
    physical_track_count: int
    stream_count: int
    candidates: list[GuitarStreamCandidate]

    @property
    def recommended_stream_ids(self) -> list[str]:
        return [
            candidate.stream.stream_id
            for candidate in self.candidates
            if candidate.decision == "likely_guitar"
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "physical_track_count": self.physical_track_count,
            "stream_count": self.stream_count,
            "recommended_stream_ids": self.recommended_stream_ids,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }
