# FretPilot

**AI-assisted MIDI-to-guitar notation and performance engine.**

FretPilot turns raw or imperfect MIDI into guitar-aware musical data that is both **readable by humans** and **playable by virtual guitar instruments**.

The first product target is:

- Input: MIDI extracted/generated from Suno, other AI music tools, DAWs, or transcription tools
- Instrument: 6-string guitar
- Score target: Guitar Pro-compatible output (initial target: GP5)
- Performance target: Ample Guitar-compatible MIDI
- Core capabilities: rhythm repair, guitar fingering, articulation planning, and performance rendering

## Product idea

Raw MIDI describes pitches and timing, but it usually does not describe how a guitarist would actually play the music. FretPilot adds that missing instrument intelligence.

```text
Raw MIDI
   ↓
MIDI normalization
   ↓
Musical structure analysis
   ↓
Rhythm repair
   ↓
Guitar fingering optimization
   ↓
Articulation planning
   ↓
Canonical Guitar IR
   ├──→ Score rendering → Guitar Pro
   └──→ Performance rendering → Ample Guitar MIDI
```

FretPilot deliberately separates **score data** from **performance data**. A readable score and a convincing virtual-instrument performance are related, but they are not the same representation.

## Design principles

1. **Deterministic engine first.** Timing, validation, fingering constraints, file I/O, and instrument mappings must not depend on an LLM.
2. **AI is an advisor, not the source of truth.** LLMs may help resolve musical ambiguity, infer phrasing/style, or rank articulation candidates.
3. **Instrument-aware by design.** Notes become strings, frets, positions, techniques, and phrases—not just MIDI pitches.
4. **One canonical intermediate representation.** Exporters and instrument adapters depend on the FretPilot IR rather than on each other.
5. **Start narrow.** V0.1 focuses on guitar and Ample Guitar before expanding to other instruments or plugins.

## Current runnable milestone

The first executable layer is now implemented:

```text
MIDI file → lossless timing normalization → NormalizedTimeline → JSON
```

The importer preserves source tick positions and durations. It does **not** quantize notes during import. Rhythm repair is a separate stage so FretPilot can always compare a repaired phrase with the original performance timing.

### Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Inspect a MIDI file:

```bash
fretpilot inspect song.mid
```

Write the normalized representation to JSON:

```bash
fretpilot inspect song.mid -o song.json
```

The JSON contains:

- MIDI type and PPQ/ticks-per-beat
- tempo map
- time-signature map
- tracks and track names
- note pitch, velocity, channel
- original start/duration in ticks
- derived start/duration in beats
- diagnostics for malformed or ambiguous MIDI events

Run tests:

```bash
pytest
```

## Repository layout

```text
FretPilot/
├── README.md
├── docs/
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   ├── MUSIC_IR.md
│   └── ROADMAP.md
├── src/fretpilot/
│   ├── midi/
│   ├── analysis/
│   ├── rhythm/
│   ├── guitar/
│   ├── articulation/
│   ├── ai/
│   └── exporters/
│       ├── guitar_pro/
│       └── ample_guitar/
└── tests/
```

## Status

Early V0.1 implementation. MIDI normalization and inspection are runnable; rhythm repair is the next engine layer.

See [`docs/PRODUCT.md`](docs/PRODUCT.md) for the product specification and [`docs/ROADMAP.md`](docs/ROADMAP.md) for milestones.
