# FretPilot

**AI-assisted MIDI-to-guitar notation and performance engine.**

FretPilot turns raw or imperfect MIDI into guitar-aware musical data that is both **readable by humans** and **playable by virtual guitar instruments**.

The first product target is:

- Input: MIDI extracted/generated from Suno, other AI music tools, DAWs, or transcription tools
- Instrument: 6-string standard-tuned guitar
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
3. **Instrument-aware by design.** Notes become strings, frets, positions, techniques, and phrases—not just MIDI pitches.
4. **One canonical intermediate representation.** Exporters and instrument adapters depend on the FretPilot IR rather than on each other.
5. **Start narrow.** V0.1 focuses on monophonic guitar lead/riff material and Ample Guitar before expanding further.

## Current runnable vertical slice

The repository now implements:

```text
MIDI file
→ NormalizedTimeline
→ rhythm-grid scoring + onset repair suggestions
→ phrase-level guitar fingering
→ basic articulation planning
→ JSON analysis
```

The MIDI importer preserves original source ticks and durations. Repair decisions are stored separately so future score cleanup never destroys the original performance timing.

Current deterministic articulation vocabulary includes:

- hammer-on
- pull-off
- slide
- vibrato

Plugin-specific Ample Guitar keyswitches are intentionally **not** stored in this layer.

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

For a multi-track MIDI file, select a zero-based track index:

```bash
fretpilot analyze song.mid --track 2
```

The analysis JSON contains:

- candidate notation-grid scores and selected grid
- source and suggested note-on positions
- per-note rhythm confidence
- standard-guitar string/fret assignments
- fingering diagnostics for impossible pitches
- generic guitar articulation decisions and confidence

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
├── tests/
└── .github/workflows/ci.yml
```

## Status

Early V0.1 implementation. The first deterministic analysis vertical slice is runnable. The next core milestone is notation-quality **duration spelling, ties, phrase segmentation, and measure coordinates**, followed by the Guitar IR builder and GP5 export.

See [`docs/PRODUCT.md`](docs/PRODUCT.md) for the product specification and [`docs/ROADMAP.md`](docs/ROADMAP.md) for detailed milestones.
