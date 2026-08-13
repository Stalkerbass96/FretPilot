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
Output / Virtual-Instrument Adapters
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
 └── Performance intent
       ↓
   Ample Guitar SC profile/renderer
       ↓
   Ample-compatible MIDI
```

The prototype also supports batch packaging for likely guitar streams.

The Ample path is the first implementation of a broader virtual-guitar adapter architecture. The generic provider-neutral profile model now lives in `src/fretpilot/virtual_instruments/`; migration of the working Ample profile is intentionally deferred so the prototype remains stable.

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

**Implemented initial versioned guitar-playing knowledge layer.**

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

This module describes guitarist behavior and musical preferences. It must not contain vendor-specific virtual-instrument controls.

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

### `virtual_instruments`

**Generic schema foundation implemented; product migration pending.**

This module owns provider-neutral knowledge models that describe how a target virtual-guitar instrument can realize canonical performance intent.

Current model types include:

- `VirtualGuitarInstrumentProfile`;
- `ArticulationCapability`;
- `ControlAction`;
- `AdapterEvidence`.

Long-term responsibilities include:

- product/version identity;
- playable range and capabilities;
- native / approximated / unsupported intent negotiation;
- keyswitch/CC/velocity/program/pitch-bend binding descriptions;
- string/position forcing capability;
- timing/legato overlap requirements;
- state/latch/reset semantics;
- evidence/provenance and verification maturity.

Important distinction:

```text
Guitar Playing Knowledge
= what a real guitarist is likely to do

Virtual Guitar Instrument Knowledge
= how a specific software instrument must be controlled
```

Detailed work lives under `projects/virtual-guitar-instruments/` (`VI-*`).

### `exporters/guitar_pro`

**Implemented GP5 prototype.**

Current support includes rests, duration decomposition, string/fret mapping, ties, basic techniques, GP5 writing, and automated parse-back validation.

Remaining quality work includes visual review, richer two-voice notation, and difficult chord/let-ring cases.

### PDF/TAB renderer

**Implemented prototype review renderer.**

PDF exists so users can inspect output without Guitar Pro. Its notation quality remains under active development and should converge toward musician-readable TAB rather than debug visualization.

### `exporters/ample_guitar`

**Implemented Ample Guitar SC 4.x prototype adapter.**

Owns current product-specific details such as:

- keyswitches;
- note overlaps;
- articulation mappings;
- plugin/version-specific conventions.

The renderer consumes Guitar IR/source performance data; it must not redefine musical intent.

Current Ample static profile data remains in this package until `VI-002` migrates it to the generic virtual-instrument profile contract. Existing behavior should remain green during that migration.

Future virtual-guitar products should be added through `VI-*` rather than by copying Ample assumptions into shared code.

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

Runtime processing uses deterministic code plus approved/versioned knowledge states and target-instrument profiles.

Future self-evolution happens offline:

```text
eligible sources / corrections / golden material / adapter evidence
→ provenance + quality + deduplication/verification
→ feature extraction / training / capability extraction
→ candidate knowledge or adapter profile
→ evaluation / conformance tests
→ approved snapshot/profile
→ Runtime
```

Runtime must never silently modify production knowledge or product mappings while processing a user request.

See:

- [`LONG_TERM_ARCHITECTURE.md`](LONG_TERM_ARCHITECTURE.md)
- [`projects/system-evolution/README.md`](projects/system-evolution/README.md)
- [`projects/guitar-playing-knowledge/LEARNING_PIPELINE.md`](projects/guitar-playing-knowledge/LEARNING_PIPELINE.md)
- [`projects/virtual-guitar-instruments/README.md`](projects/virtual-guitar-instruments/README.md)