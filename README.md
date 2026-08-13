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
6. **Start narrow.** V0.1 focuses on standard six-string lead, riff, arpeggio, and simple chord material.

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

Current score cleanup recognizes two common guitar-MIDI patterns:

- arpeggio notes that continue ringing after the next pick attack;
- notes struck together as a chord but released at different times.

FretPilot shortens only the **written** duration where needed, records `let_ring` intent and a change log, and preserves original sustained durations for Ample playback.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### One-command prototype package

For every likely guitar stream:

```bash
fretpilot prototype song.mid \
  --all-likely-guitars \
  -o output/
```

For one explicit stream:

```bash
fretpilot prototype song.mid \
  --stream-id t0:ch2:p27 \
  -o output/
```

The package contains one directory per stream:

```text
output/
├── manifest.json
├── t0_ch2_p27/
│   ├── t0_ch2_p27.analysis.json
│   ├── t0_ch2_p27.rewrite.json
│   ├── t0_ch2_p27.guitar-ir.json
│   ├── t0_ch2_p27.gp5
│   ├── t0_ch2_p27.ample-sc.mid
│   └── t0_ch2_p27.report.json
└── ...
```

If GP5 cannot represent a stream yet, the package still keeps the analysis, Guitar IR, Ample MIDI, and report. The manifest records the unsupported output instead of failing the whole batch.

### Individual commands

Inspect and rank streams:

```bash
fretpilot inspect song.mid
fretpilot tracks song.mid -o tracks.json
```

Analyze and build Guitar IR:

```bash
fretpilot analyze song.mid --stream-id t0:ch2:p27 -o analysis.json
fretpilot build-ir song.mid --stream-id t0:ch2:p27 -o guitar-ir.json
```

Score and performance output commands use an adjustable MIDI-fidelity
continuum. `1` preserves source notes exactly; `0` permits the most
confidence-gated rewriting. The default is `0.35`, favoring a reasonable,
playable guitar result:

```bash
fretpilot prototype song.mid \
  --stream-id t0:ch2:p27 \
  --midi-fidelity 0.35 \
  -o output/
```

Rewriting currently covers high-confidence guitar-range/octave repairs, exact
duplicates, isolated short spike notes, and strongly evidenced missing repeated
pulses. Every change is recorded in `*.rewrite.json`; synthetic notes receive
an explicit origin and a stable identity after the original source-note range.

Export individual files:

```bash
fretpilot export-gp5 song.mid \
  --stream-id t0:ch2:p27 \
  -o song.gp5

fretpilot export-ample-sc song.mid \
  --stream-id t0:ch2:p27 \
  -o song-ample-sc.mid
```

## Processing report

Each prototype stream report contains:

- stream and detection evidence;
- guitar probability and confidence;
- selected rhythm grid;
- MIDI-fidelity setting and note-rewrite counts;
- low-confidence rhythm notes;
- unplayable fingering notes;
- articulation counts;
- per-section entry/exit hand state and explainable cross-section shifts;
- Guitar IR transformation counts;
- let-ring conversions;
- GP5 and Ample output status;
- warnings and whether manual review is required.

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
- `let_ring` intent
- transformation/change log

## GP5 prototype

Currently supported:

- one guitar track and up to two notation voices
- monophonic phrases
- same-onset chords with normalized equal written duration
- generated rests for silent gaps
- straight, dotted, and triplet duration decomposition
- string/fret assignments
- ties
- single-note let ring
- vibrato
- hammer-on / pull-off
- shift slide

The builder promotes a high-confidence unequal chord release to voice 2 when
the sustained string is not rearticulated and the second voice is available.
Other ringing material keeps the established let-ring normalization path. The
exporter raises an explicit error for polyphony that still exceeds two safe
voices; unsafe partial chord let-ring remains in Guitar IR/performance timing
and is reported when GP5 must omit the marking.

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

See [`docs/AMPLE_GUITAR_SC.md`](docs/AMPLE_GUITAR_SC.md) for raw MIDI mapping and timing rules.

## Track detection

Detection currently uses:

1. Track-name keywords
2. Channel, program, and instrument metadata
3. MIDI note behavior and guitar plausibility
4. A separate experimental behavior library for solo, riff, strumming, breakdown, and jazz comping

Track recognition will improve incrementally and is not blocking the output prototype. The dedicated backlog is in [`docs/projects/track-identification/`](docs/projects/track-identification/).

When exactly one high-confidence guitar stream exists, downstream commands may select it automatically. When several likely guitars exist, FretPilot requires an explicit `--stream-id` or `--all-likely-guitars`.

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
- ringing-overlap and unequal-chord normalization
- GP5 write-and-parse round trip
- safe GP5 downgrade for partial chord let ring
- Ample HP keyswitch timing and source/destination overlap
- complete multi-guitar prototype package generation

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
│   ├── prototype.py
│   └── exporters/
│       ├── guitar_pro/
│       └── ample_guitar/
├── tests/
└── .github/workflows/ci.yml
```

## Status

FretPilot is an early V0.1 prototype with both target output paths and a one-command multi-guitar package workflow implemented. The next milestone is hands-on validation: open generated GP5 files in Guitar Pro, play generated MIDI through Ample Guitar SC, record measure-level issues, then prioritize richer voice separation/PDF engraving, bend/vibrato rendering, and a simple upload/download interface.
