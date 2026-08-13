# Ample Guitar SC Performance MIDI Adapter

## Scope

This document defines FretPilot's first virtual-instrument adapter:

```text
Guitar IR
→ Ample Guitar SC 4.x performance MIDI
```

The adapter is intentionally separate from score notation and guitar detection.
It consumes canonical Guitar IR and renders original source/performance timing,
keyswitches, and the note overlaps required by Ample's legato engine.

Implementation:

```text
src/fretpilot/exporters/ample_guitar/profiles.py
src/fretpilot/exporters/ample_guitar/renderer.py
```

CLI:

```bash
fretpilot export-ample-sc song.mid \
  --stream-id t0:ch2:p27 \
  -o song-ample-sc.mid
```

## Target profile

```text
profile_id: ample-guitar-sc-v4
product: Ample Guitar SC
version family: 4.x
```

Ample Guitar SC is the first supported product because it represents the
initial electric-guitar use case and uses the common Ample electric-guitar
articulation layout.

## Raw MIDI keyswitch mapping

FretPilot stores raw MIDI note numbers so DAW octave-label differences cannot
change the meaning of a profile.

| Musical intent | Ample label | MIDI note |
|---|---:|---:|
| Sustain | C0 | 24 |
| Natural harmonic | C#0 | 25 |
| Palm mute | D0 | 26 |
| Slide in / slide out | D#0 | 27 |
| Legato slide | E0 | 28 |
| Hammer-on / pull-off | F0 | 29 |
| Slide guitar | F#0 | 30 |

The labels follow Ample's displayed octave convention. FretPilot's standard
six-string low E remains raw MIDI note 40.

## Timing strategy

### Source performance timing

The renderer uses:

```text
performance.source_start_beat
performance.source_duration_beats
velocity
```

It does not use quantized score durations for playback. This is especially
important for arpeggios: score notes may be shortened and marked `let_ring`,
while the Ample MIDI retains the original overlap.

### Initial preroll

All musical notes receive a small positive timeline offset. This provides room
for an articulation keyswitch before a note that originally starts at beat 0.

Current profile defaults:

```text
PPQ: 480
keyswitch preroll: 30 ticks
keyswitch note length: 12 ticks
legato overlap: 30 ticks
```

### Hammer-on and pull-off

For `hammer_on` and `pull_off`:

1. send raw MIDI note 29 before the source note;
2. retain the source and destination notes;
3. extend the source note-off when needed so the notes overlap by at least the
   configured legato-overlap amount.

### Legato slide

Generic Guitar IR `slide` currently maps to Ample's legato-slide keyswitch:

```text
E0 / MIDI note 28
```

The renderer applies the same overlap rule as hammer-on/pull-off.

### Let ring

`let_ring` does not emit a keyswitch. The source performance duration already
contains the ringing overlap. The GP5 score and Ample MIDI intentionally differ
here:

```text
GP5: readable shortened note + let-ring marking
Ample MIDI: original sustained duration
```

## Current support

Rendered:

- Sustain state
- Hammer-on
- Pull-off
- Legato slide
- Natural harmonic, when present in Guitar IR
- Palm mute, when present in Guitar IR
- Slide in / slide out, when present in Guitar IR
- Original note velocity and duration
- Tempo and time-signature maps

Retained in Guitar IR but not yet rendered:

- Vibrato
- Bend curves
- Pick direction
- Velocity shaping by musical accent
- Capo/string-forcing control
- Pinch harmonic
- Slide speed control

Unsupported items produce warnings in the export report instead of silently
pretending that they were rendered.

## Output structure

The generated Standard MIDI File is Type 1:

```text
Track 0: tempo and time signatures
Track 1: Ample keyswitches and guitar notes
```

The export report contains:

```json
{
  "path": "song-ample-sc.mid",
  "profile_id": "ample-guitar-sc-v4",
  "source_note_count": 128,
  "keyswitch_count": 14,
  "warnings": []
}
```

## Verification

Automated tests parse the generated MIDI back through Mido and verify:

- Sustain and HP keyswitch presence;
- keyswitch timing before source notes;
- original relative note timing;
- required source/destination overlap for HP legato;
- one output note per source-note index even when Guitar IR has tied fragments.

Manual acceptance still required:

1. load the MIDI into a DAW;
2. route it to Ample Guitar SC 4.x;
3. disable conflicting DAW transpose/octave settings;
4. verify HP and LS triggering by ear and in the plugin keyboard display;
5. document any product/version-specific differences before changing the
   canonical Guitar IR.

## Official references

- Ample Sound Guitar tutorial: articulation and Poly Legato keyswitch table.
- Ample Guitar SC product page: product/version and available sampled
  articulations.

The external product documentation is the source of truth for keyswitch
semantics. FretPilot profiles must be versioned when a product mapping changes.
