# FretPilot Architecture

## Architectural goal

FretPilot should remain independent of any single LLM, score format, or virtual instrument.

The system is divided into four layers:

```text
Input Layer
  ↓
Musical Intelligence Layer
  ↓
Canonical Guitar IR
  ↓
Output Adapters
```

## Modules

### `midi`
Reads MIDI and produces normalized note/timing events.

Responsibilities:
- SMF parsing
- PPQ/tick conversion
- note event normalization
- tempo/time-signature maps
- track selection
- malformed note repair

### `analysis`
Adds musical context without changing the source notes.

Responsibilities may include:
- beat strength
- measure boundaries
- phrase segmentation
- key/scale estimation
- motif/repetition detection
- role inference

### `rhythm`
Converts expressive/raw timing into symbolic score rhythm.

Responsibilities:
- candidate grid generation
- quantization scoring
- triplet/swing ambiguity handling
- tie generation
- note-duration cleanup
- confidence scoring

Important: original performance timing is retained separately.

### `guitar`
Transforms pitches into physically meaningful guitar positions.

Responsibilities:
- tuning model
- pitch → string/fret candidates
- playability validation
- phrase-level fingering optimization
- position continuity
- hand-movement cost functions

### `articulation`
Plans guitar technique after fingering candidates are known.

Responsibilities:
- hammer-on / pull-off
- slide
- vibrato
- palm mute
- harmonics
- future bend/tapping support

Technique generation must never violate physical constraints.

### `ai`
Optional external reasoning providers.

Responsibilities:
- provider abstraction
- structured prompt building
- structured response validation
- phrase/style classification
- ranking ambiguous musical alternatives

The rest of the engine must function without this module.

### `exporters/guitar_pro`
Converts canonical Guitar IR to Guitar Pro-compatible notation.

Initial target: GP5.

### `exporters/ample_guitar`
Converts canonical Guitar IR + performance information into Ample Guitar-oriented MIDI events.

This layer owns plugin-specific details such as:
- keyswitches
- required overlaps
- articulation-specific velocity/control conventions

No Ample-specific event should leak into the canonical Guitar IR.

## Processing pipeline

```text
.mid
 ↓
MidiDocument
 ↓
NormalizedTimeline
 ↓
AnalyzedTimeline
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
- configuration
- model/provider version (if AI is enabled)

FretPilot should be able to reproduce the same result.

AI-assisted choices must be serialized into structured decisions and validated. The pipeline should support an `ai_enabled=false` mode for testing and deterministic fallback.

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
  "reason": "nearest_16th_with_phrase_consistency"
}
```

This will later power the user-facing "what FretPilot changed" review panel.
