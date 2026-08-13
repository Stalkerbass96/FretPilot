# FretPilot Architecture

## Architectural goal

FretPilot should remain independent of any single LLM, score format, or virtual instrument.

The system is divided into four conceptual layers:

```text
Input Layer
  ↓
Musical / Instrument Intelligence
  ↓
Canonical Guitar IR
  ↓
Output Adapters
```

The implementation is intentionally incremental. The current V0 vertical slice reaches the intelligence layer and emits JSON analysis; the canonical IR builder and output adapters come next.

## Current executable pipeline

```text
.mid
 ↓
load_midi()
 ↓
NormalizedTimeline
 ↓
analyze_track_rhythm()
 ↓
RhythmAnalysis
 ↓
optimize_fingering()
 ↓
FingeringResult
 ↓
plan_articulations()
 ↓
ArticulationPlan
 ↓
analyze_guitar_track()
 ↓
GuitarTrackAnalysis JSON
```

Command-line entry points:

```text
fretpilot inspect
fretpilot rhythm
fretpilot fingering
fretpilot analyze
```

## Modules

### `midi`

**Implemented V0.** Reads Standard MIDI Files and produces normalized note/timing events.

Current responsibilities:
- SMF parsing through Mido
- PPQ/tick conversion
- note-on/note-off normalization
- tempo map
- time-signature map
- track names
- default MIDI tempo/time-signature handling
- malformed/unclosed note diagnostics
- preservation of original ticks alongside beat coordinates

Important invariant:

> MIDI import never performs musical quantization.

The source representation must remain available after every later repair step.

### `analysis`

**Implemented as orchestration; musical-context features remain future work.**

Current responsibility:
- compose rhythm, fingering, and articulation analysis into one guitar-track result

Future responsibilities:
- beat strength
- measure boundaries
- phrase segmentation
- key/scale estimation
- motif/repetition detection
- role/style inference

### `rhythm`

**Onset-repair V0 implemented.** Converts expressive/raw timing into symbolic-score candidates without mutating source MIDI.

Current responsibilities:
- candidate notation grids
- straight vs triplet grid families
- grid scoring from note-on timing error
- complexity penalty so unnecessarily fine grids do not always win
- suggested note-on locations
- per-note confidence
- source/target timing deltas

Next responsibilities:
- note-duration spelling
- rests and ties
- phrase-level grid changes
- measure-aware constraints
- swing interpretation
- mixed tuplets

Important invariant:

> Score timing and performance timing are different data.

### `guitar`

**Monophonic lead/riff V0 implemented.** Transforms MIDI pitches into physically meaningful guitar positions.

Current responsibilities:
- standard six-string tuning: E2 A2 D3 G3 B3 E4
- pitch → all legal string/fret candidates
- configurable maximum fret
- impossible-pitch diagnostics
- phrase-level dynamic-programming optimization
- lead-oriented string-continuity cost model

The cost model currently favors modest same-string movement enough to preserve useful hammer-on, pull-off, and slide opportunities. A future rhythm/chord-guitar mode should use different weights and simultaneous-string constraints.

### `articulation`

**Conservative V0 implemented.** Plans generic guitar techniques after fingering is known.

Current techniques:
- hammer-on
- pull-off
- slide
- vibrato

Current rules consider:
- same-string physical validity
- semitone interval
- note connectivity
- inter-onset time
- sustained notes / phrase endings

Future techniques/context:
- explicit picking/stroke direction
- legato slide distinction
- palm mute
- natural/artificial harmonics
- bends
- tapping
- style/phrase-aware density control

Important invariant:

> This module stores musical intent, never Ample-specific keyswitch numbers.

### `ai`

**Not implemented yet by design.** Optional external reasoning providers.

Future responsibilities:
- provider abstraction
- structured prompt/context building
- strict response schemas
- phrase/style classification
- ranking ambiguous rhythm/fingering/articulation alternatives
- deterministic validation and fallback

The rest of the engine must function with AI completely disabled.

### Canonical Guitar IR

**Schema direction defined; builder not implemented yet.**

See `docs/MUSIC_IR.md`.

The IR is the contract between FretPilot's musical reasoning and every output adapter. It will combine:
- clean score timing
- preserved performance timing
- fingering
- generic articulation intent
- confidence
- explainable transformation records

### `exporters/guitar_pro`

**Not implemented yet.** Converts canonical Guitar IR to Guitar Pro-compatible notation.

Initial target: GP5.

### `exporters/ample_guitar`

**Not implemented yet.** Converts canonical Guitar IR + performance information into Ample Guitar-oriented MIDI events.

This layer will own plugin-specific details such as:
- keyswitches
- required note overlaps
- articulation-specific velocity/control conventions
- plugin/version-specific mapping tables

No Ample-specific event may leak into canonical Guitar IR.

## Target full pipeline

```text
.mid
 ↓
NormalizedTimeline
 ↓
Measure + Phrase Analysis
 ↓
RhythmPlan
 ↓
FingeringPlan
 ↓
ArticulationPlan
 ↓
GuitarIR
 ├── ScoreRenderer → GP5
 └── PerformanceRenderer → Ample MIDI
```

## Determinism

Given identical:
- source MIDI
- FretPilot configuration
- engine version
- provider/model version if AI is enabled

FretPilot should be able to reproduce the same result.

AI-assisted choices must be serialized into structured decisions and validated. The pipeline must support an `ai_enabled=false` mode for testing and deterministic fallback.

## Confidence and explainability

Each transformation should be capable of attaching:
- confidence
- reason/code
- original value
- transformed value

Example:

```json
{
  "type": "rhythm_repair",
  "measure": 12,
  "original_start_beats": 2.487,
  "score_start_beats": 2.5,
  "confidence": 0.96,
  "reason": "phrase_consistent_16th_quantization"
}
```

This becomes the foundation of a user-facing **What FretPilot changed** review panel rather than hiding AI/algorithm decisions from the musician.

## Testing strategy

The repository has unit tests for:
- MIDI normalization/defaults/diagnostics
- straight and triplet rhythm-grid selection
- guitar position generation
- phrase-level fingering
- unplayable pitches
- hammer-on / pull-off / slide / vibrato rules
- composed guitar analysis

GitHub Actions runs the test suite on pushes to `main` and pull requests.
