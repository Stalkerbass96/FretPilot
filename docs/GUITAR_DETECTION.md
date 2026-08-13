# FretPilot Guitar Detection

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

FretPilot resolves notes by:

```text
physical_track + channel + active_program
```

Example stream ID:

```text
t0:ch2:p27
```

Internal channels and programs are zero-based. User-facing channel numbers are
one-based.

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

The current rules are placeholders for a growing knowledge base. Future profile
features may include:

- phrase segmentation
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
```

The report ranks logical streams rather than physical tracks.

## Next implementation steps

1. Add `--stream-id` to analysis commands so rhythm/fingering/articulation run on
   a selected logical stream instead of a physical track.
2. Add section-level segmentation because one stream may change role between
   verse, chorus, solo, and breakdown.
3. Build a labeled regression corpus with correct instrument and role labels.
4. Calibrate thresholds and profile rules using precision/recall measurements.
5. Add chord-shape and strumming-timing features before trusting rhythm-guitar
   style labels.
