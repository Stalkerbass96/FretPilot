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
→ selected stream
→ rhythm-grid scoring + onset repair suggestions
→ phrase-level guitar fingering
→ basic articulation planning
→ measure-aware Guitar IR
→ JSON output with source timing, score timing, ties and change log
```

The MIDI importer preserves original source ticks and durations. Guitar IR stores source/performance timing separately from repaired score timing, so score cleanup does not destroy the original musical performance.

### Guitar detection layers

1. Track-name keyword evidence
2. Channel/program/instrument metadata
3. MIDI note behavior and standard-guitar plausibility
4. Separate experimental behavior library: solo, riff, strumming, breakdown, and jazz comping

The first three layers answer whether a stream is probably guitar. The fourth layer describes the guitar behavior and does not override instrument identity. Track identification remains an incremental project and is documented separately.

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

Analyze one selected logical stream:

```bash
fretpilot rhythm song.mid --stream-id t0:ch2:p27
fretpilot fingering song.mid --stream-id t0:ch2:p27
fretpilot analyze song.mid --stream-id t0:ch2:p27 -o analysis.json
```

Build canonical measure-aware Guitar IR:

```bash
fretpilot build-ir song.mid \
  --stream-id t0:ch2:p27 \
  -o guitar-ir.json
```

Current Guitar IR V0.1 includes:

- schema version
- tempo and time-signature maps
- measures and beat-in-measure coordinates
- score onset and duration
- original source onset, duration, and velocity
- string/fret assignments
- generic articulations
- ties for notes crossing measure boundaries
- rhythm transformation/change log

When exactly one high-confidence guitar stream exists, downstream commands can select it automatically. When multiple likely guitar streams exist, FretPilot stops and asks for an explicit `--stream-id` instead of silently choosing the wrong guitar part.

A legacy physical-track selector remains available:

```bash
fretpilot build-ir song.mid --track 2 -o guitar-ir.json
```

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
├── AGENTS.md
├── README.md
├── pyproject.toml
├── docs/
│   ├── README.md
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   ├── GUITAR_DETECTION.md
│   ├── MUSIC_IR.md
│   ├── ROADMAP.md
│   └── projects/
│       └── track-identification/
├── src/fretpilot/
│   ├── midi/
│   ├── detection/
│   ├── knowledge/
│   ├── analysis/
│   ├── rhythm/
│   ├── guitar/
│   ├── articulation/
│   ├── ir/
│   ├── ai/
│   └── exporters/
│       ├── guitar_pro/
│       └── ample_guitar/
├── tests/
└── .github/workflows/ci.yml
```

## Development documentation

- [`AGENTS.md`](AGENTS.md) — mandatory starting point for AI agents and contributors.
- [`docs/README.md`](docs/README.md) — documentation index.
- [`docs/projects/track-identification/README.md`](docs/projects/track-identification/README.md) — track-identification project hub.
- [`docs/MUSIC_IR.md`](docs/MUSIC_IR.md) — canonical score/performance representation.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — prototype and product milestones.

## Status

Early V0.1 implementation. Instrument-stream detection, deterministic guitar analysis, and measure-aware Guitar IR generation are runnable. Track identification will continue to improve incrementally, but the main prototype path now advances toward a minimal GP5 exporter, followed by an Ample Guitar performance-MIDI adapter.
