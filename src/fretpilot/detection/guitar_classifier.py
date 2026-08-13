"""Explainable multi-layer guitar stream classification.

Layer 1: track-name keywords.
Layer 2: channel/program/instrument metadata.
Layer 3: MIDI note behavior and physical guitar plausibility.
Layer 4: optional behavior profile matching (solo/riff/strumming/etc.).
"""

from __future__ import annotations

from collections import defaultdict
from statistics import mean

from fretpilot.detection.models import (
    BehaviorFeatures,
    DetectionLayerResult,
    GuitarDetectionReport,
    GuitarStreamCandidate,
    InstrumentStream,
)
from fretpilot.detection.streams import resolve_instrument_streams
from fretpilot.guitar.instrument import candidate_positions
from fretpilot.knowledge.guitar_behaviors import match_behavior_profiles
from fretpilot.midi.models import NormalizedTimeline

GUITAR_KEYWORDS = (
    "guitar",
    "gtr",
    "guitarra",
    "gitara",
    "吉他",
)

NON_GUITAR_KEYWORDS = (
    "bass",
    "drum",
    "percussion",
    "piano",
    "organ",
    "synth",
    "violin",
    "strings",
    "vocal",
    "voice",
    "harmonica",
    "sax",
    "trumpet",
)


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _keyword_score(text: str | None, *, source: str) -> DetectionLayerResult:
    if not text:
        return DetectionLayerResult(
            layer=source,
            score=0.5,
            status="unknown",
            reasons=[f"No {source.replace('_', ' ')} metadata was provided."],
        )

    lowered = text.casefold()

    # "Bass Guitar" contains the word guitar but should not be treated as the
    # six-string guitar target in V0.1.
    if "bass guitar" in lowered or "bass" in lowered:
        return DetectionLayerResult(
            layer=source,
            score=0.05,
            status="negative",
            reasons=[f"{source} contains bass-related wording: {text!r}."],
        )

    matched_guitar = [keyword for keyword in GUITAR_KEYWORDS if keyword in lowered]
    if matched_guitar:
        return DetectionLayerResult(
            layer=source,
            score=0.95,
            status="positive",
            reasons=[
                f"{source} contains guitar keyword {matched_guitar[0]!r}: {text!r}."
            ],
        )

    matched_other = [keyword for keyword in NON_GUITAR_KEYWORDS if keyword in lowered]
    if matched_other:
        return DetectionLayerResult(
            layer=source,
            score=0.15,
            status="negative",
            reasons=[
                f"{source} names another instrument ({matched_other[0]!r}): {text!r}."
            ],
        )

    return DetectionLayerResult(
        layer=source,
        score=0.5,
        status="unknown",
        reasons=[f"{source} has no decisive instrument keyword: {text!r}."],
    )


def _layer1_track_name(stream: InstrumentStream) -> DetectionLayerResult:
    result = _keyword_score(stream.source_track_name, source="track_name")
    result.layer = "layer_1_track_keywords"
    return result


def _layer2_channel_metadata(stream: InstrumentStream) -> DetectionLayerResult:
    if stream.is_drum_channel:
        return DetectionLayerResult(
            layer="layer_2_channel_metadata",
            score=0.0,
            status="negative",
            reasons=["General MIDI channel 10 is reserved for percussion."],
            metrics={"display_channel": stream.display_channel},
        )

    scores: list[float] = []
    reasons: list[str] = []

    if stream.program_family == "guitar":
        scores.append(0.95)
        reasons.append(
            f"Program {stream.program + 1} is {stream.program_name}."
            if stream.program is not None
            else "Program belongs to the guitar family."
        )
    elif stream.program_family == "bass":
        scores.append(0.05)
        reasons.append(
            f"Program {stream.program + 1} is a bass program ({stream.program_name})."
            if stream.program is not None
            else "Program belongs to the bass family."
        )
    elif stream.program_family is not None:
        scores.append(0.15)
        reasons.append(
            f"Program family is {stream.program_family}, not guitar "
            f"({stream.program_name})."
        )

    if stream.instrument_name:
        instrument_result = _keyword_score(
            stream.instrument_name,
            source="instrument_name",
        )
        scores.append(instrument_result.score)
        reasons.extend(instrument_result.reasons)

    if not scores:
        return DetectionLayerResult(
            layer="layer_2_channel_metadata",
            score=0.5,
            status="unknown",
            reasons=["No program change or instrument-name evidence was available."],
            metrics={"display_channel": stream.display_channel},
        )

    score = mean(scores)
    status = "positive" if score >= 0.75 else "negative" if score <= 0.25 else "mixed"
    return DetectionLayerResult(
        layer="layer_2_channel_metadata",
        score=round(score, 6),
        status=status,
        reasons=reasons,
        metrics={
            "display_channel": stream.display_channel,
            "program": stream.program,
            "program_name": stream.program_name,
            "program_family": stream.program_family,
            "instrument_name": stream.instrument_name,
        },
    )


def extract_behavior_features(stream: InstrumentStream) -> BehaviorFeatures:
    notes = stream.notes
    if not notes:
        return BehaviorFeatures(
            note_count=0,
            pitch_min=None,
            pitch_max=None,
            pitch_range_semitones=0,
            playable_pitch_ratio=0.0,
            onset_count=0,
            max_onset_polyphony=0,
            mean_onset_polyphony=0.0,
            monophonic_onset_ratio=0.0,
            chord_onset_ratio=0.0,
            adjacent_interval_within_octave_ratio=0.0,
            repeated_pitch_ratio=0.0,
            low_register_ratio=0.0,
            short_note_ratio=0.0,
        )

    pitches = [note.pitch for note in notes]
    playable_count = sum(bool(candidate_positions(pitch)) for pitch in pitches)

    onset_groups: dict[int, list[int]] = defaultdict(list)
    for note in notes:
        onset_groups[note.start_tick].append(note.pitch)

    onset_sizes = [len(group) for group in onset_groups.values()]
    onset_count = len(onset_sizes)

    ordered = sorted(notes, key=lambda note: (note.start_tick, note.pitch))
    intervals = [
        abs(current.pitch - previous.pitch)
        for previous, current in zip(ordered, ordered[1:])
        if current.start_tick > previous.start_tick
    ]

    return BehaviorFeatures(
        note_count=len(notes),
        pitch_min=min(pitches),
        pitch_max=max(pitches),
        pitch_range_semitones=max(pitches) - min(pitches),
        playable_pitch_ratio=playable_count / len(notes),
        onset_count=onset_count,
        max_onset_polyphony=max(onset_sizes, default=0),
        mean_onset_polyphony=mean(onset_sizes) if onset_sizes else 0.0,
        monophonic_onset_ratio=(
            sum(size == 1 for size in onset_sizes) / onset_count if onset_count else 0.0
        ),
        chord_onset_ratio=(
            sum(2 <= size <= 6 for size in onset_sizes) / onset_count
            if onset_count
            else 0.0
        ),
        adjacent_interval_within_octave_ratio=(
            sum(interval <= 12 for interval in intervals) / len(intervals)
            if intervals
            else 1.0
        ),
        repeated_pitch_ratio=(
            sum(interval == 0 for interval in intervals) / len(intervals)
            if intervals
            else 0.0
        ),
        low_register_ratio=sum(pitch <= 52 for pitch in pitches) / len(pitches),
        short_note_ratio=(
            sum(note.duration_beats <= 0.5 for note in notes) / len(notes)
        ),
    )


def _layer3_note_behavior(stream: InstrumentStream) -> DetectionLayerResult:
    features = extract_behavior_features(stream)
    metrics = features.to_dict()

    if stream.is_drum_channel:
        return DetectionLayerResult(
            layer="layer_3_note_behavior",
            score=0.0,
            status="negative",
            reasons=["Percussion-channel notes are not evaluated as pitched guitar behavior."],
            metrics=metrics,
        )

    if not stream.notes:
        return DetectionLayerResult(
            layer="layer_3_note_behavior",
            score=0.0,
            status="negative",
            reasons=["The stream contains no completed notes."],
            metrics=metrics,
        )

    pitch_min = features.pitch_min if features.pitch_min is not None else 0
    pitch_max = features.pitch_max if features.pitch_max is not None else 0
    range_overflow = (
        max(0, 40 - pitch_min)
        + max(0, pitch_max - 88)
        + max(0, features.pitch_range_semitones - 48)
    )
    range_score = _bounded(1.0 - range_overflow / 48.0)

    if features.max_onset_polyphony <= 6:
        polyphony_score = 1.0
    elif features.max_onset_polyphony <= 8:
        polyphony_score = 0.55
    else:
        polyphony_score = 0.10

    structure_score = _bounded(
        features.monophonic_onset_ratio + features.chord_onset_ratio
    )

    score = (
        0.40 * features.playable_pitch_ratio
        + 0.15 * range_score
        + 0.20 * polyphony_score
        + 0.15 * features.adjacent_interval_within_octave_ratio
        + 0.10 * structure_score
    )
    score = _bounded(score)

    reasons = [
        f"{features.playable_pitch_ratio:.1%} of pitches fit standard six-string guitar (0–24 frets).",
        f"Maximum simultaneous onset size is {features.max_onset_polyphony} notes.",
        (
            f"{features.adjacent_interval_within_octave_ratio:.1%} of adjacent "
            "movements stay within one octave."
        ),
    ]
    if features.max_onset_polyphony > 6:
        reasons.append("Some onsets exceed the six-note physical string limit.")
    if features.playable_pitch_ratio < 0.80:
        reasons.append("A substantial portion of pitches falls outside the target guitar range.")

    status = "positive" if score >= 0.75 else "mixed" if score >= 0.50 else "negative"
    return DetectionLayerResult(
        layer="layer_3_note_behavior",
        score=round(score, 6),
        status=status,
        reasons=reasons,
        metrics=metrics,
    )


def classify_guitar_stream(stream: InstrumentStream) -> GuitarStreamCandidate:
    layers = [
        _layer1_track_name(stream),
        _layer2_channel_metadata(stream),
        _layer3_note_behavior(stream),
    ]

    probability = (
        0.30 * layers[0].score
        + 0.35 * layers[1].score
        + 0.35 * layers[2].score
    )
    probability = round(_bounded(probability), 6)

    if probability >= 0.75:
        decision = "likely_guitar"
    elif probability >= 0.62:
        decision = "possible_guitar"
    else:
        decision = "unlikely_guitar"

    decisive_metadata_layers = sum(
        layer.status in {"positive", "negative"} for layer in layers[:2]
    )
    confidence = _bounded(
        0.35
        + 0.15 * decisive_metadata_layers
        + 0.70 * abs(probability - 0.5)
    )

    features = layers[2].metrics
    profile_matches = match_behavior_profiles(features)

    return GuitarStreamCandidate(
        stream=stream,
        guitar_probability=probability,
        confidence=round(confidence, 6),
        decision=decision,
        layers=layers,
        behavior_profiles=profile_matches,
    )


def classify_timeline(timeline: NormalizedTimeline) -> GuitarDetectionReport:
    streams = resolve_instrument_streams(timeline)
    candidates = [classify_guitar_stream(stream) for stream in streams]
    candidates.sort(
        key=lambda candidate: (
            candidate.guitar_probability,
            len(candidate.stream.notes),
        ),
        reverse=True,
    )
    return GuitarDetectionReport(
        source=timeline.source,
        physical_track_count=len(timeline.tracks),
        stream_count=len(streams),
        candidates=candidates,
    )
