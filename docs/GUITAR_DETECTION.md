# FretPilot Guitar Detection

> Project tracking: [`projects/track-identification/README.md`](projects/track-identification/README.md)  
> Implementation status: [`projects/track-identification/STATUS.md`](projects/track-identification/STATUS.md)  
> Prioritized tasks: [`projects/track-identification/BACKLOG.md`](projects/track-identification/BACKLOG.md)  
> Evaluation requirements: [`projects/track-identification/TEST_PLAN.md`](projects/track-identification/TEST_PLAN.md)

This document defines the current algorithm semantics. The project documents above distinguish completed work from future work and should be updated alongside implementation changes.

## Goal

FretPilot must not blindly trust a MIDI track name or General MIDI program.
Those fields are useful evidence, but generated, exported, and hand-edited MIDI
files frequently contain missing or incorrect metadata.

The detector therefore uses four explainable layers.

```text
Physical MIDI tracks
        +
MIDI channels / program changes
        ↓
InstrumentStream resolver
        ↓
Layer 1: Track keyword evidence
Layer 2: Channel/program evidence
Layer 3: MIDI note-behavior evidence
        ↓
Guitar probability + confidence + reasons
        ↓
Layer 4: Guitar behavior/style profile library
```

Layers 1–3 answer **is this probably guitar?**

Layer 4 answers **what kind of guitar behavior does it resemble?**

These questions must remain separate.

## Instrument streams

A physical MIDI track is not necessarily an instrument. Type-0 MIDI commonly
stores a full arrangement in one track and separates instruments by channel.
Type-1 MIDI often uses separate physical tracks, but may still contain multiple
channels or program changes.

FretPilot currently resolves notes by:

```text
physical_track + channel + active_program
```

Example stream ID:

```text
t0:ch2:p27
```

Internal channels and programs are zero-based. User-facing channel numbers are
one-based.

Current caveat: some sources may use program changes as articulation controls.
The raw event timeline is preserved, but the resolver does not yet distinguish
articulation program changes from true instrument changes.

## Layer 1 — Track keyword evidence

Strong positive examples:

- `Guitar`
- `Lead Guitar`
- `Rhythm Gtr`
- `Clean Guitar`
- localized guitar words maintained by the keyword dictionary

Negative examples:

- `Bass Guitar`
- `Drums`
- `Piano`
- `Organ`
- `Harmonica`

Track naming is strong evidence, not truth. A track named `Guitar` can still be
assigned a conflicting program or contain non-guitar behavior.

## Layer 2 — Channel/program evidence

Inputs:

- MIDI channel
- General MIDI program change
- optional MIDI `instrument_name`
- future vendor-specific metadata

General MIDI guitar programs 25–32 (one-based display numbering) strongly
support guitar classification. Bass programs reduce the six-string guitar
probability. Display channel 10 is treated as percussion under General MIDI.

Program metadata is also non-authoritative. Some exporters use a piano program
for all tracks, and some generated MIDI assigns plausible but incorrect sounds.

## Layer 3 — MIDI note behavior

Current deterministic features:

- proportion of pitches playable on standard six-string guitar, frets 0–24
- pitch range and range overflow
- maximum notes at one onset
- monophonic onset ratio
- guitar-sized chord-onset ratio
- proportion of adjacent movements within one octave
- repeated-pitch ratio
- low-register ratio
- short-note ratio

Current V0 score is deliberately conservative and explainable. It is not a
trained instrument classifier.

Important limitations:

- piano and synth parts can be completely guitar-playable
- arpeggiated keyboard parts may resemble guitar
- strummed MIDI may stagger chord notes instead of sharing one onset
- alternate tunings, capos, seven/eight-string guitars, and pitch bends are not
  yet represented
- physical chord feasibility requires a later voicing solver, not only a
  six-note count

## Combining Layers 1–3

Current weights:

```text
30% track keywords
35% channel/program metadata
35% note behavior
```

Thresholds:

```text
>= 0.75  likely_guitar
>= 0.62  possible_guitar
<  0.62  unlikely_guitar
```

These are starting calibration values. They must be evaluated against a labeled
MIDI corpus and changed through tests, not intuition alone.

Every result includes:

- final guitar probability
- confidence
- per-layer score and status
- human-readable reasons
- raw behavior metrics

The UI should auto-select only high-confidence candidates and always allow the
user to override the choice.

## Layer 4 — Guitar behavior knowledge library

The initial versioned library is stored in:

```text
src/fretpilot/knowledge/guitar_behaviors.py
```

Initial experimental profiles:

- Solo / Lead
- Riff
- Strumming / Chord Rhythm
- Breakdown / Heavy Low Riff
- Jazz Comping

The current implementation scores whole-stream summary features. This is a
baseline only. The intended design is to segment the stream into musical
sections or phrases and classify each time-bounded region independently.

Future profile features may include:

- phrase and section segmentation
- repeated-pattern similarity
- strum-direction timing signatures
- chord-shape feasibility
- power-chord detection
- palm-mute likelihood
- syncopation and accent maps
- bend/slide/legato density
- tonal center and scale vocabulary
- chord extensions and voice leading
- genre/style priors

The library should be versioned and auditable. A future learned model may rank
profiles, but its output should still map to this canonical vocabulary.

## CLI

```bash
fretpilot tracks song.mid
fretpilot tracks song.mid -o tracks.json
fretpilot analyze song.mid --stream-id t0:ch2:p27
```

The report ranks logical streams rather than physical tracks. Downstream rhythm,
fingering, and articulation analysis can consume a selected `InstrumentStream`.

## Development priorities

The canonical prioritized list is maintained in
[`projects/track-identification/BACKLOG.md`](projects/track-identification/BACKLOG.md).
The immediate order is:

1. define a licensed/synthetic labeled fixture manifest;
2. implement repeatable precision/recall/F1 evaluation;
3. centralize weights, thresholds, aliases, and assumptions in configuration;
4. harden stream resolution and physical chord feasibility;
5. define section/phrase results and baseline segmentation;
6. calibrate the Layer-4 behavior library on labeled regions.

Do not add production accuracy claims or continually tune heuristics against one
song before the evaluation harness exists.
