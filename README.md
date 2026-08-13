# FretPilot

**AI-assisted MIDI-to-guitar notation and performance engine.**

FretPilot turns raw or imperfect MIDI into guitar-aware musical data that is both **readable by humans** and **playable by virtual guitar instruments**.

The first product target is:

- Input: MIDI extracted/generated from Suno, other AI music tools, DAWs, or transcription tools
- Instrument: 6-string standard-tuned guitar
- Score output: Guitar Pro 5 (`.gp5`)
- Performance output: Ample Guitar SC 4.x MIDI
- Core capabilities: stream detection, rhythm repair, guitar fingering, articulation planning, score rendering, and performance rendering

## Product pipeline

```text
Raw MIDI
   ↓
MIDI normalization
   ↓
Physical track + channel + program stream resolution
   ↓
Layered guitar detection
   ↓
Rhythm analysis / repair
   ↓
Guitar fingering optimization
   ↓
Articulation planning
   ↓
Canonical Guitar IR
   ├──→ Guitar Pro 5 exporter
   └──→ Ample Guitar SC performance-MIDI renderer
```

FretPilot deliberately separates **score timing** from **source/performance timing**. A score can use clean note lengths and rests while Ample playback retains ringing notes, overlaps, velocity, and legato timing.

## Design principles

1. **Deterministic engine first.** Timing, validation, fingering constraints, file I/O, and instrument mappings do not depend on an LLM.
2. **AI is an advisor, not the source of truth.** A model may later rank ambiguous musical choices, but deterministic validation remains mandatory.
3. **Metadata is evidence, not truth.** Track names and MIDI programs contribute to guitar detection but are checked against note behavior.
4. **Instrument-aware by design.** Notes become strings, frets, techniques, phrases, score events, and performance events.
5. **One canonical IR.** Guitar Pro and Ample adapters both consume Guitar IR instead of depending on each other.
6. **Start narrow.** V0.1 focuses on standard six-string lead, riff, and arpeggio material.

## Current runnable vertical slice

```text
MIDI file
→ NormalizedTimeline
→ InstrumentStream resolution
→ three-layer guitar candidate ranking
→ selected stream
→ rhythm-grid analysis
→ guitar fingering
→ articulation planning
→ measure-aware Guitar IR
├──→ GP5 export + parse-back test
└──→ Ample Guitar SC MIDI + event-order test
```

Current score cleanup also recognizes a common guitar-MIDI pattern: an arpeggio note may continue ringing after the next pick attack. FretPilot shortens the **written** duration, adds `let_ring`, and preserves the original sustained duration in performance timing.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Inspect normalized MIDI:

```bash
fretpilot inspect song.mid
```

Rank logical guitar streams:

```bash
fretpilot tracks song.mid -o tracks.json
```

Analyze a selected stream:

```bash
fretpilot analyze song.mid \
  --stream-id t0:ch2:p27 \
  -o analysis.json
```

Build Guitar IR:

```bash
fretpilot build-ir song.mid \
  --stream-id t0:ch2:p27 \
  -o guitar-ir.json
```

Export Guitar Pro 5.1:

```bash
fretpilot export-gp5 song.mid \
  --stream-id t0:ch2:p27 \
  -o song.gp5
```

Export Ample Guitar SC 4.x performance MIDI:

```bash
fretpilot export-ample-sc song.mid \
  --stream-id t0:ch2:p27 \
  -o song-ample-sc.mid
```

Each file-export command prints a JSON report with output statistics and warnings.

## Guitar IR V0.1

Current IR includes:

- schema version
- tempo and time-signature maps
- measures and beat-in-measure coordinates
- repaired score onset and duration
- original source onset, duration, and velocity
- string/fret assignments
- generic articulations
- cross-measure ties
- `let_ring` intent for ringing overlaps
- transformation/change log

## GP5 prototype

Currently supported:

- one guitar track and one notation voice
- monophonic phrases
- same-onset chords with equal written duration
- generated rests for silent gaps
- straight, dotted, and triplet duration decomposition supported by PyGuitarPro
- string/fret assignments
- ties
- let ring
- vibrato
- hammer-on / pull-off
- shift slide

The exporter raises an explicit error when a stream requires unsupported independent voices or contains a pattern the current subset cannot represent. It does not silently produce a misleading score.

## Ample Guitar SC prototype

Profile:

```text
ample-guitar-sc-v4
```

Currently rendered:

- Sustain state
- original note timing and velocity
- original ringing overlaps
- Hammer-On / Pull-Off keyswitch and required note overlap
- Legato Slide keyswitch and required note overlap
- Natural Harmonic, Palm Mute, and Slide In/Out when those intents appear in Guitar IR
- tempo and time-signature maps

Vibrato and bends remain in Guitar IR but are not yet rendered by the SC V0 adapter; the export report emits warnings instead.

See [`docs/AMPLE_GUITAR_SC.md`](docs/AMPLE_GUITAR_SC.md) for the raw MIDI mapping and timing rules.

## Track detection

Detection currently uses:

1. Track-name keywords
2. Channel, program, and instrument metadata
3. MIDI note behavior and guitar plausibility
4. A separate experimental behavior library for solo, riff, strumming, breakdown, and jazz comping

Track recognition will be improved incrementally and is not blocking the prototype output pipeline. The dedicated backlog is in [`docs/projects/track-identification/`](docs/projects/track-identification/).

When exactly one high-confidence guitar stream exists, downstream commands may select it automatically. When several likely guitars exist, FretPilot requires an explicit `--stream-id`.

## Tests

```bash
pytest
```

GitHub Actions verifies, among other cases:

- Type-0 channel/program stream separation
- layered guitar detection
- rhythm and fingering behavior
- cross-measure ties
- articulation links across tied fragments
- ringing-overlap → let-ring score conversion
- GP5 write-and-parse round trip
- Ample HP keyswitch timing and source/destination overlap

## Repository layout

```text
FretPilot/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── docs/
│   ├── README.md
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   ├── GUITAR_DETECTION.md
│   ├── MUSIC_IR.md
│   ├── AMPLE_GUITAR_SC.md
│   ├── ROADMAP.md
│   └── projects/track-identification/
├── src/fretpilot/
│   ├── midi/
│   ├── detection/
│   ├── knowledge/
│   ├── analysis/
│   ├── rhythm/
│   ├── guitar/
│   ├── articulation/
│   ├── ir/
│   └── exporters/
│       ├── guitar_pro/
│       └── ample_guitar/
├── tests/
└── .github/workflows/ci.yml
```

## Status

FretPilot is an early V0.1 prototype with both target output paths implemented: a limited, round-trip-tested GP5 exporter and a first Ample Guitar SC 4.x performance-MIDI renderer. The next quality milestone is real DAW/Guitar Pro listening and visual inspection, followed by chord-duration normalization, true two-voice notation, vibrato/bend rendering, and broader real-world regression samples.
