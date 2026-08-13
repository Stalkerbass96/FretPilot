# FretPilot

**AI-assisted MIDI-to-guitar notation and performance engine.**

FretPilot turns raw or imperfect MIDI into guitar-aware musical data that is both **readable by humans** and **playable by virtual guitar instruments**.

The first product target is:

- Input: MIDI extracted/generated from Suno, other AI music tools, DAWs, or transcription tools
- Instrument: 6-string standard-tuned guitar
- Score target: Guitar Pro-compatible output (initial target: GP5)
- Performance target: Ample Guitar-compatible MIDI
- Core capabilities: instrument-stream detection, rhythm repair, guitar fingering, articulation planning, and performance rendering

## Product idea

Raw MIDI describes pitches and timing, but it usually does not reliably describe which stream is guitar or how a guitarist would actually play it. FretPilot adds that missing instrument intelligence.

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
   ├──→ Score rendering → Guitar Pro
   └──→ Performance rendering → Ample Guitar MIDI
```

FretPilot deliberately separates **score data** from **performance data**. A readable score and a convincing virtual-instrument performance are related, but they are not the same representation.

## Design principles

1. **Deterministic engine first.** Timing, validation, fingering constraints, file I/O, and instrument mappings must not depend on an LLM.
2. **AI is an advisor, not the source of truth.** LLMs may help resolve musical ambiguity, infer phrasing/style, or rank articulation candidates.
3. **Metadata is evidence, not truth.** Track names and MIDI programs contribute to instrument detection but are checked against note behavior.
4. **Instrument-aware by design.** Notes become strings, frets, positions, techniques, and phrases—not just MIDI pitches.
5. **One canonical intermediate representation.** Exporters and instrument adapters depend on the FretPilot IR rather than on each other.
6. **Start narrow.** V0.1 focuses on guitar lead/riff material and Ample Guitar before expanding further.

## Current runnable vertical slice

The repository now implements:

```text
MIDI file
→ NormalizedTimeline with program metadata
→ InstrumentStream resolution
→ three-layer guitar candidate ranking
→ experimental guitar behavior profiles
→ rhythm-grid scoring + onset repair suggestions
→ phrase-level guitar fingering
→ basic articulation planning
→ JSON analysis
```

The MIDI importer preserves original source ticks and durations. Repair decisions are stored separately so future score cleanup never destroys the original performance timing.

### Guitar detection layers

1. Track-name keyword evidence
2. Channel/program/instrument metadata
3. MIDI note behavior and standard-guitar plausibility
4. Separate experimental behavior library: solo, riff, strumming, breakdown, and jazz comping

The first three layers answer whether a stream is probably guitar. The fourth layer describes the guitar behavior and does not override instrument identity.

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

Resolve physical tracks/channels and rank guitar candidates:

```bash
fretpilot tracks song.mid
fretpilot tracks song.mid -o tracks.json
```

Analyze likely notation rhythm:

```bash
fretpilot rhythm song.mid
```

Optimize guitar string/fret positions:

```bash
fretpilot fingering song.mid
```

Run the current end-to-end guitar intelligence stack:

```bash
fretpilot analyze song.mid -o analysis.json
```

`tracks` already works on logical instrument streams. The older `rhythm`, `fingering`, and `analyze` commands still select physical tracks; adding `--stream-id` is the next integration step.

Current deterministic articulation vocabulary includes:

- hammer-on
- pull-off
- slide
- vibrato

Plugin-specific Ample Guitar keyswitches are intentionally **not** stored in this layer.

Run tests:

```bash
pytest
```

GitHub Actions also runs the test suite on pushes to `main` and pull requests.

## Repository layout

```text
FretPilot/
├── README.md
├── pyproject.toml
├── docs/
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   ├── GUITAR_DETECTION.md
│   ├── MUSIC_IR.md
│   └── ROADMAP.md
├── src/fretpilot/
│   ├── midi/
│   ├── detection/
│   ├── knowledge/
│   ├── analysis/
│   ├── rhythm/
│   ├── guitar/
│   ├── articulation/
│   ├── ai/
│   └── exporters/
│       ├── guitar_pro/
│       └── ample_guitar/
├── tests/
└── .github/workflows/ci.yml
```

## Status

Early V0.1 implementation. Layered instrument-stream detection and the first deterministic guitar-analysis vertical slice are runnable. The next core milestone is to route a selected `InstrumentStream` through rhythm, fingering, and articulation analysis, then add phrase/section segmentation before expanding the behavior library.

See [`docs/PRODUCT.md`](docs/PRODUCT.md), [`docs/GUITAR_DETECTION.md`](docs/GUITAR_DETECTION.md), and [`docs/ROADMAP.md`](docs/ROADMAP.md) for the current product and architecture definitions.
