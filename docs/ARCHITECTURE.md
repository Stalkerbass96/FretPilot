# FretPilot Architecture

## Architectural goal

FretPilot converts imperfect symbolic MIDI into guitar-aware notation and performance data while remaining independent of any single LLM, score format, or virtual instrument.

The current architecture is:

```text
Input Foundation
      ↓
Instrument Intelligence
      ↓
Musical / Guitar Intelligence
      ↓
Canonical Guitar IR
      ↓
Output Adapters
```

Long-term evolution adds a separate offline Learning Plane. See [`LONG_TERM_ARCHITECTURE.md`](LONG_TERM_ARCHITECTURE.md).

---

## Current executable pipeline

```text
.mid
 ↓
MIDI parser
 ↓
NormalizedTimeline
 ↓
InstrumentStream resolver
 ↓
Layered guitar candidate detection
 ↓
Selected InstrumentStream
 ↓
Rhythm analysis / notation repair
 ↓
Fingering optimizer
 ↓
Articulation planner
 ↓
GuitarTrackAnalysis
 ↓
Guitar IR
 ├── PDF/TAB preview
 ├── GP5 exporter
 └── Ample Guitar SC MIDI renderer
```

The prototype also supports batch packaging for likely guitar streams.

---

## Module boundaries

### `midi`

**Implemented.** Owns source truth and MIDI normalization.

Responsibilities include:

- Standard MIDI parsing;
- PPQ/tick preservation;
- tempo/time-signature maps;
- track/channel/program metadata;
- note pairing and diagnostics;
- source timing retained without musical quantization.

Invariant:

> MIDI import preserves what the source contained. Musical repair happens later.

### `detection`

**Implemented V0, long-term evolvable.**

Responsibilities include:

- resolving logical `InstrumentStream` objects from physical Track/Channel/Program information;
- three-layer guitar identity evidence;
- candidate ranking and explicit ambiguity handling;
- behavior features for the experimental Layer-4 knowledge library.

Detailed work lives under `projects/track-identification/` (`TI-*`).

### `analysis`

**Implemented orchestration, future musical-context owner.**

Current responsibility:

- combine rhythm, fingering, and articulation results.

Long-term responsibilities include:

- measure/phrase/section context;
- motif/repetition;
- harmony;
- role/style/technique-family inference;
- shared region context consumed by downstream modules.

### `rhythm`

**Implemented V0/V0.1 notation repair.**

Responsibilities include:

- onset grid analysis;
- straight/triplet candidate families;
- duration spelling;
- measure-aware score timing;
- rests/ties via Guitar IR construction;
- preserving source/performance timing separately from score timing.

Invariant:

> Score timing and performance timing are different representations.

Future work includes section-dependent grids, swing, richer tuplets, and true multi-voice notation.

### `guitar`

**Implemented V0/V0.2 fingering engine.**

Responsibilities include:

- tuning/fretboard model;
- pitch → legal string/fret candidates;
- hard physical feasibility;
- phrase-level fingering optimization;
- simultaneous-chord distinct-string solving;
- movable riff/arpeggio shape repair.

Hard playability is deterministic. Which valid path is most guitarist-like is a long-term evolvable ranking problem.

### `knowledge`

**Implemented initial versioned knowledge layer.**

Current components include:

- behavior profiles (`solo`, `riff`, `strumming`, `breakdown`, `jazz_comping`);
- composable `PlayingContext` dimensions;
- role/style/technique profiles;
- fingering, articulation, and performance preferences.

Important distinction:

```text
role: solo/riff/strumming/comping
style: metal/rock/jazz/blues/...
technique family: legato/arpeggio/sweep/fingerstyle/...
```

These dimensions compose instead of being flattened into one genre label.

Detailed work lives under `projects/guitar-playing-knowledge/` (`GK-*`).

### `articulation`

**Implemented conservative V0.**

Current generic techniques include:

- hammer-on;
- pull-off;
- slide;
- vibrato.

The module stores musical intent, not plugin keyswitches.

Future work includes bends, palm mute, picking/stroke direction, harmonics, tapping, and style/phrase-aware priors.

### Canonical Guitar IR

**Implemented schema/builder.**

Guitar IR is the contract between musical reasoning and output adapters. It carries:

- score timing;
- preserved source/performance timing;
- measure/event coordinates;
- string/fret assignment;
- generic articulation intent;
- ties/let-ring transformations;
- confidence/warnings/change records.

Invariant:

> Output-specific plugin mappings do not belong in Guitar IR.

### `exporters/guitar_pro`

**Implemented GP5 prototype.**

Current support includes rests, duration decomposition, string/fret mapping, ties, basic techniques, GP5 writing, and automated parse-back validation.

Remaining quality work includes visual review, richer two-voice notation, and difficult chord/let-ring cases.

### PDF/TAB renderer

**Implemented prototype review renderer.**

PDF exists so users can inspect output without Guitar Pro. Its notation quality remains under active development and should converge toward musician-readable TAB rather than debug visualization.

### `exporters/ample_guitar`

**Implemented Ample Guitar SC 4.x prototype adapter.**

Owns plugin-specific details such as:

- keyswitches;
- note overlaps;
- articulation mappings;
- plugin/version-specific conventions.

The renderer consumes Guitar IR/source performance data; it must not redefine musical intent.

### `ai`

**Optional/future by design.**

Possible responsibilities:

- structured ambiguous-choice ranking;
- phrase/style advisor;
- provider abstraction;
- retrieval/context assistance.

The deterministic engine must remain functional with AI disabled.

---

## Runtime vs Learning

Runtime processing uses deterministic code plus an approved/versioned knowledge state.

Future self-evolution happens offline:

```text
eligible sources / corrections / golden material
→ provenance + quality + deduplication
→ feature extraction / training
→ candidate knowledge
→ evaluation
→ approved snapshot
→ Runtime
```

Runtime must never silently modify production knowledge while processing a user request.

See:

- [`LONG_TERM_ARCHITECTURE.md`](LONG_TERM_ARCHITECTURE.md)
- [`projects/system-evolution/README.md`](projects/system-evolution/README.md)
- [`projects/guitar-playing-knowledge/LEARNING_PIPELINE.md`](projects/guitar-playing-knowledge/LEARNING_PIPELINE.md)

---

## Determinism and reproducibility

A long-term result should be attributable to a version tuple including:

```text
source fingerprint
engine version
configuration version
Guitar IR schema version
knowledge snapshot version
optional provider/model version
```

AI/learned components rank or advise. Hard guitar constraints and output validation remain deterministic.

---

## Explainability

Transformations should be able to expose:

- confidence;
- reason/code;
- source value;
- transformed value;
- section/context identity;
- knowledge/model version where relevant.

This supports a product-facing "What FretPilot changed" review workflow rather than hiding algorithmic decisions.

---

## Task ownership

Use stable project task prefixes:

```text
PV-*  prototype/output validation
TI-*  instrument/track identification
GK-*  guitar-playing/style/learning knowledge
SE-*  cross-project evolution infrastructure
```

Do not duplicate work across project backlogs. The specialized backlog remains authoritative for module-specific algorithms.