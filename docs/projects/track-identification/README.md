# Track Identification Project

**Project status:** Active backlog, V0 baseline implemented  
**Scope:** MIDI instrument-stream resolution, guitar identity classification, and guitar behavior/role classification  
**Primary code:** `src/fretpilot/detection/`, `src/fretpilot/knowledge/`, and MIDI metadata support in `src/fretpilot/midi/`

This folder is the canonical project hub for the detailed track-identification feature. Future AI agents should start here instead of reconstructing decisions from commit history or chat transcripts.

## Problem statement

A MIDI file may represent instruments in several incompatible ways:

- one physical track per instrument;
- one physical track containing many MIDI channels;
- multiple channels inside one named track;
- program changes inside a channel;
- correct, missing, generic, or incorrect instrument metadata.

FretPilot must find guitar material without assuming that a physical Track equals one instrument or that metadata is always correct.

## Product outcome

Given a MIDI file, FretPilot should return an explainable ranked list of logical instrument streams:

```text
MIDI file
  ↓
Preserve physical track, channel, active program and source timing
  ↓
Resolve InstrumentStream objects
  ↓
Layer 1 — track-name evidence
Layer 2 — channel/program/instrument-name evidence
Layer 3 — note-behavior and guitar-plausibility evidence
  ↓
Guitar probability, confidence, decision, reasons and raw metrics
  ↓
Layer 4 — section-level guitar behavior profiles
```

Layers 1–3 answer:

> Is this stream probably six-string guitar material?

Layer 4 answers:

> Within the selected guitar stream, does this musical region resemble solo, riff, strumming, breakdown, jazz comping, or another maintained behavior profile?

The two questions must remain separate.

## Current user flow

```bash
fretpilot tracks song.mid -o tracks.json
fretpilot analyze song.mid --stream-id t0:ch2:p27 -o analysis.json
```

When exactly one high-confidence guitar stream exists, downstream commands may select it automatically. When several likely guitar streams exist, the user must choose a `stream_id`.

## Canonical documents

- [`STATUS.md`](STATUS.md) — current implementation inventory, known limitations, and code map.
- [`BACKLOG.md`](BACKLOG.md) — prioritized task IDs with acceptance criteria.
- [`TEST_PLAN.md`](TEST_PLAN.md) — fixtures, regression cases, metrics, and quality gates.
- [`../../GUITAR_DETECTION.md`](../../GUITAR_DETECTION.md) — algorithm details and current scoring semantics.
- [`../../ROADMAP.md`](../../ROADMAP.md) — relationship to the overall FretPilot roadmap.
- [`../../../AGENTS.md`](../../../AGENTS.md) — mandatory AI/contributor workflow.

## Stable concepts and names

### Physical MIDI track

The track container as stored in the Standard MIDI File. It is retained for provenance but is not assumed to be a single instrument.

### InstrumentStream

A logical note stream currently resolved by:

```text
physical_track + MIDI_channel + active_program
```

Example internal ID:

```text
t0:ch2:p27
```

Internal track, channel, and program values are zero-based. User-facing channel labels are one-based.

### Guitar identity candidate

An `InstrumentStream` plus Layers 1–3 evidence, final guitar probability, confidence, decision, and reasons.

Current decisions:

```text
likely_guitar
possible_guitar
unlikely_guitar
```

### Guitar behavior profile

A Layer-4 role, technique, or style-behavior label. Current experimental vocabulary:

```text
solo
riff
strumming
breakdown
jazz_comping
```

These profiles currently score an entire stream. The intended architecture is section/phrase-level classification.

## Architecture boundaries

The module owns:

- MIDI metadata interpretation for instrument identity;
- logical stream resolution;
- explainable Layers 1–3 guitar classification;
- feature extraction used by guitar identity and behavior profiles;
- versioned Layer-4 behavior vocabulary and rules;
- ranked candidate output and selection policy.

The module does not own:

- score quantization or note-duration repair;
- final string/fret optimization;
- articulation rendering;
- Guitar Pro export;
- Ample Guitar keyswitch mapping;
- audio-to-MIDI transcription.

## Definition of done for this project

The module is no longer considered experimental when all of the following are true:

1. A licensed or synthetic labeled corpus covers Type 0, Type 1, correct metadata, missing metadata, misleading metadata, bass, drums, keyboard false positives, and multiple guitar parts.
2. Evaluation produces repeatable precision, recall, F1, confusion matrices, and per-source error reports.
3. Layers 1–3 are configurable and calibrated without hidden magic numbers spread across the codebase.
4. Chord and polyphonic feasibility uses actual guitar voicing constraints rather than only onset note count.
5. Alternate tunings and extended-range configurations are represented explicitly.
6. Program changes used as articulations do not accidentally fragment one musical stream.
7. Layer 4 operates on sections/phrases and can label changing behavior within one stream.
8. Every decision remains explainable and the user can override stream selection.

## Immediate next step

Start with the first uncompleted P0 task in [`BACKLOG.md`](BACKLOG.md). Do not expand the behavior vocabulary before the evaluation harness and section-boundary representation exist.
