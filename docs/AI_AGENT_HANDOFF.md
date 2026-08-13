# FretPilot AI Agent Handoff

> Last consolidated: 2026-08-13
>
> Purpose: let a new AI agent understand the current product, architecture, task ownership, and safe next steps in roughly 10 minutes without reconstructing historical chat context.

## 1. Product in one paragraph

FretPilot converts imperfect or AI-generated MIDI into **guitar-aware notation** and **virtual-guitar performance data**. The engine must preserve source MIDI truth, infer/select guitar streams, repair notation timing, choose guitarist-like string/fret paths, plan generic guitar articulations, build a canonical Guitar IR, then render score/performance outputs. The current prototype targets PDF/TAB + GP5 for score review and Ample Guitar SC MIDI for performance. Long term, both guitar-playing knowledge and virtual-instrument adapter knowledge are versioned/evolvable assets.

## 2. Current runtime pipeline

```text
MIDI
  ↓
NormalizedTimeline
  ↓
InstrumentStream resolution
  ↓
Layers 1–3 guitar identity evidence
  ↓
selected guitar stream
  ↓
rhythm / notation repair
  ↓
fingering + guitar-shape planning
  ↓
articulation planning
  ↓
GuitarTrackAnalysis
  ↓
Canonical Guitar IR
  ├── PDF/TAB preview
  ├── GP5
  └── performance adapter
         └── Ample Guitar SC 4.x today
```

## 3. What exists now

Before changing code, verify against `docs/ROADMAP.md` and tests, but the current baseline includes:

- Standard MIDI Type 0 / Type 1 parsing;
- preservation of Track / Channel / Program / original ticks;
- logical `InstrumentStream` resolution;
- explainable three-layer guitar candidate ranking;
- rhythm grid analysis and basic notation-duration repair;
- measure coordinates and cross-measure ties;
- standard six-string fretboard candidate generation;
- phrase-level fingering baseline;
- movable riff/arpeggio shape repair baseline;
- simultaneous chord distinct-string solving;
- hammer-on / pull-off / slide / vibrato inference;
- canonical Guitar IR v0.1;
- PDF/TAB review renderer (still not musician-quality engraving);
- GP5 exporter with automated write/parse round-trip validation;
- Ample Guitar SC 4.x MIDI renderer;
- initial composable `PlayingContext` knowledge model;
- generic `VirtualGuitarInstrumentProfile` schema skeleton;
- batch prototype packaging for likely guitar streams.

## 4. Current product priority

Do **not** block Prototype 0.1 on perfect track identification, internet learning, every guitar style, or every virtual instrument.

Near-term order:

1. **Readable score/TAB output and real-song review** (`PV-*`).
2. **Thread PlayingContext into fingering/articulation** (`GK-002`, `GK-003`, `GK-004`).
3. **Phrase/Section context** so role/style can change over time (`GK-010/011`, coordinated with `TI-040/041`).
4. **Review/correction records** so human feedback becomes future evaluation data (`SE-020/021`, `TI-052`).
5. **Keep Track identification improving incrementally** (`TI-*`) without making it the prototype blocker.
6. **Generalize Ample into the virtual-instrument adapter architecture** (`VI-002` onward) after preserving current Ample behavior.
7. Build larger offline learning/self-evolution infrastructure only after useful real evaluation data exists.

## 5. Task ownership

Use the existing task family instead of inventing duplicate work.

```text
PV-*  prototype/output validation and immediate user-facing quality
TI-*  InstrumentStream / guitar-track identification
GK-*  guitarist-like playing knowledge, role/style/phrase, fingering learning
VI-*  virtual-guitar product knowledge, adapter capabilities, compatibility
SE-*  cross-project reproducibility, feedback, evaluation, snapshot governance
```

Canonical backlogs:

```text
docs/ROADMAP.md

docs/projects/track-identification/BACKLOG.md
docs/projects/guitar-playing-knowledge/BACKLOG.md
docs/projects/virtual-guitar-instruments/BACKLOG.md
docs/projects/system-evolution/BACKLOG.md
```

## 6. The four long-term knowledge assets

### A. Instrument / Track knowledge (`TI-*`)

Answers:

> Which logical stream is guitar, and how confident are we?

Evidence may include metadata, program/channel information, note behavior, guitar feasibility, chord/strum behavior, and later learned classification.

### B. Guitar Playing Knowledge (`GK-*`)

Answers:

> If this is guitar, how would a real guitarist most likely play it?

Includes:

- string/fret ranking;
- hand position and shift planning;
- shape/voicing memory;
- left-hand fingering;
- role/style-conditioned choices;
- articulation priors;
- performance feel.

Important dimensions remain composable:

```text
role: solo / riff / strumming / comping / ...
style: metal / rock / jazz / blues / ...
technique family: legato / arpeggio / sweep / fingerstyle / ...
```

Do not flatten these into one label.

### C. Virtual Guitar Instrument Knowledge (`VI-*`)

Answers:

> How must a particular software guitar be controlled to realize canonical guitar intent?

Examples:

- keyswitch / CC / program mappings;
- latch/reset state semantics;
- legato overlap and preroll;
- bend/vibrato capability;
- string/position forcing;
- picking/strumming controls;
- product/version limitations.

Critical boundary:

```text
GK = how a guitarist plays
VI = how a plugin is controlled
```

Never change canonical guitar intent just because one plugin cannot express it. Use capability negotiation, approximation, fallback, or warnings.

### D. Evaluation / Learning knowledge (`SE-*` + specialized projects)

Answers:

> Did a new heuristic, knowledge profile, model, or adapter mapping actually improve the system?

Includes golden reviews, labeled fixtures, user corrections, benchmark identity, source provenance, candidate-vs-production comparison, and knowledge/profile promotion.

## 7. Stable engine vs evolvable intelligence

### Keep deterministic / schema-versioned

- raw MIDI parsing and preservation;
- physical fretboard constraints;
- impossible fingering rejection;
- Guitar IR contracts;
- file-format correctness;
- target control protocol facts once verified;
- output validation.

### Allowed to evolve with evidence/data

- guitar identity ranking;
- phrase/section boundaries;
- role/style inference;
- fingering ranking among physically valid candidates;
- shape selection;
- articulation ranking;
- timing/velocity/strum feel;
- expressive virtual-instrument calibration.

Learned systems **rank valid alternatives**. They do not bypass hard constraints.

## 8. Runtime Plane vs Learning Plane

Runtime must be reproducible and must not silently learn from arbitrary web pages.

```text
Runtime Plane
source + engine/config + approved knowledge/profile versions
→ deterministic/validated result
```

Future learning happens offline:

```text
eligible/permissioned sources + user corrections + golden reviews
→ provenance/license gate
→ quality + normalization + deduplication
→ feature extraction / training
→ candidate knowledge/profile
→ offline evaluation / shadow comparison
→ approval
→ versioned production snapshot/profile
```

Public availability is not automatically permission to crawl, store, redistribute, or train on content. Preserve provenance and permitted use.

## 9. Canonical boundaries that must not be violated

1. A physical MIDI Track is not necessarily one instrument.
2. Always preserve source Track, Channel, Program, ticks, and original note timing.
3. Track/instrument metadata is evidence, not absolute truth.
4. Layers 1–3 decide likely guitar identity; Layer 4 / PlayingContext describes behavior/style.
5. Guitar Playing Knowledge is a soft prior; fretboard physics is a hard constraint.
6. Product-specific keyswitch/CC data must not enter Guitar IR or guitar-playing knowledge.
7. Score timing and performance timing are separate representations.
8. Multiple likely guitar streams must not be silently collapsed into one.
9. Unsupported target capabilities must be reported explicitly.
10. Runtime uses pinned/approved knowledge and instrument profiles; new learning does not silently mutate production behavior.

## 10. First files to inspect by task

### Score / PDF / notation

```text
src/fretpilot/ir/
src/fretpilot/rhythm/
src/fretpilot/exporters/
docs/MUSIC_IR.md
docs/ROADMAP.md
```

### Fingering / style / guitar behavior

```text
src/fretpilot/guitar/
src/fretpilot/knowledge/
src/fretpilot/articulation/
docs/projects/guitar-playing-knowledge/
```

### Track identification

```text
src/fretpilot/midi/
src/fretpilot/detection/
docs/projects/track-identification/
```

### Virtual guitar adapters

```text
src/fretpilot/virtual_instruments/
src/fretpilot/exporters/ample_guitar/
docs/projects/virtual-guitar-instruments/
```

### Self-evolution / evaluation

```text
docs/LONG_TERM_ARCHITECTURE.md
docs/projects/system-evolution/
docs/projects/guitar-playing-knowledge/LEARNING_PIPELINE.md
```

## 11. Required agent workflow

For any nontrivial change:

1. Read this handoff plus the specialized project README/backlog.
2. Pick an existing stable task ID where possible.
3. Inspect current implementation and relevant tests; do not trust docs alone.
4. Preserve current public behavior unless the task intentionally changes it.
5. Add/update regression tests before changing scoring, fingering, knowledge, or adapter mappings.
6. Run the full test suite / CI.
7. Update the narrowest relevant STATUS/BACKLOG/algorithm doc.
8. Record evidence for claims such as "more accurate", "more guitarist-like", or "verified plugin behavior".

## 12. Recommended next-agent starting point

If no more specific user request exists, start with the smallest high-value task that improves the current prototype rather than expanding the long-term learning system.

Preferred candidates:

```text
PV: improve musician-readable PDF/TAB using existing Guitar IR
GK-002: thread PlayingContext through analysis without changing neutral output
GK-003: make fingering costs knowledge-aware while preserving golden regressions
VI-002: migrate Ample static knowledge to the generic profile schema without changing render output
```

Do not start broad crawling/training infrastructure until review/correction/evaluation data is mature enough to measure improvement.
