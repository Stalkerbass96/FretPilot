# FretPilot AI Contributor Guide

This file is the mandatory entry point for Codex, AI agents, and new contributors.

## Start here

Read these in order before making a nontrivial change:

1. [`docs/AI_AGENT_HANDOFF.md`](docs/AI_AGENT_HANDOFF.md) — **authoritative current state, task map, architecture boundaries, and recommended next work**.
2. [`docs/ROADMAP.md`](docs/ROADMAP.md) — current prototype milestone and product priority.
3. Read the specialized project docs only for the task family you are changing.

Do not reconstruct architecture or priorities from old chat history when these repository documents already define them.

## Task families

```text
PV-*  prototype/output validation and immediate user-facing quality
TI-*  InstrumentStream / guitar-track identification
GK-*  guitarist-like playing knowledge, style, phrasing, and learning
VI-*  virtual-guitar product knowledge, capabilities, adapters, compatibility
SE-*  cross-project reproducibility, evaluation, feedback, and evolution governance
```

Canonical project docs:

```text
docs/projects/track-identification/          TI-*
docs/projects/guitar-playing-knowledge/      GK-*
docs/projects/virtual-guitar-instruments/    VI-*
docs/projects/system-evolution/              SE-*
```

`PV-*` prototype work is tracked in `docs/ROADMAP.md`.

## Module-specific reading

### Track identification (`TI-*`)

Read:

```text
docs/projects/track-identification/README.md
docs/projects/track-identification/STATUS.md
docs/projects/track-identification/BACKLOG.md
docs/projects/track-identification/TEST_PLAN.md
docs/GUITAR_DETECTION.md
```

Inspect:

```text
src/fretpilot/midi/
src/fretpilot/detection/
```

### Guitar playing knowledge / fingering / articulation (`GK-*`)

Read:

```text
docs/projects/guitar-playing-knowledge/README.md
docs/projects/guitar-playing-knowledge/BACKLOG.md
docs/projects/guitar-playing-knowledge/LEARNING_PIPELINE.md
```

Inspect:

```text
src/fretpilot/knowledge/
src/fretpilot/guitar/
src/fretpilot/articulation/
src/fretpilot/analysis/
```

Current section-aware execution path is centered on:

```text
src/fretpilot/analysis/sections.py
src/fretpilot/analysis/section_contexts.py
src/fretpilot/analysis/section_aware.py
src/fretpilot/guitar/fingering.py
src/fretpilot/articulation/planner.py
```

### Virtual guitar instruments (`VI-*`)

Read:

```text
docs/projects/virtual-guitar-instruments/README.md
docs/projects/virtual-guitar-instruments/BACKLOG.md
```

Inspect:

```text
src/fretpilot/virtual_instruments/
src/fretpilot/exporters/ample_guitar/
src/fretpilot/ir/
```

Critical distinction:

```text
GK = how a real guitarist would likely play
VI = how a target software instrument must be controlled
```

Never push plugin limitations upstream into canonical guitar intent.

### System evolution (`SE-*`)

Read:

```text
docs/LONG_TERM_ARCHITECTURE.md
docs/projects/system-evolution/README.md
docs/projects/system-evolution/BACKLOG.md
```

Use `SE-*` only for shared infrastructure/governance. Do not duplicate work already owned by `TI-*`, `GK-*`, or `VI-*`.

## Non-negotiable design rules

- A physical MIDI Track is not necessarily one instrument.
- Preserve source Track, Channel, Program, ticks, original note timing, and stable source-note identity.
- Resolve logical `InstrumentStream` objects before guitar analysis.
- Track names and General MIDI programs are evidence, not absolute truth.
- Layers 1–3 estimate guitar identity; Layer 4 / `PlayingContext` describes behavior/style.
- `role`, `style`, and `technique family` are separate, composable dimensions.
- Guitar Playing Knowledge is a soft prior; physical fretboard/playability constraints are hard constraints.
- Learned/AI systems rank or advise among valid alternatives; they do not bypass deterministic physical/file constraints.
- Section-local processing must remap results back to stream-wide `source_note_index` correctly.
- Score timing and performance timing remain separate representations.
- Canonical Guitar IR is versioned and independent of output adapters.
- Product-specific keyswitch/CC/state mappings never belong in Guitar IR or Guitar Playing Knowledge.
- Unsupported target-instrument capabilities must be reported, approximated explicitly, or preserved for another target; do not silently discard material intent.
- Multiple likely guitar streams must not be silently collapsed into one.
- Runtime uses approved/pinned musical knowledge and adapter profiles. Newly discovered data must not silently mutate production behavior.
- Publicly visible tablature or vendor material is not automatically licensed for crawling, storage, redistribution, or training.

## Required workflow

For a nontrivial task:

1. Read `docs/AI_AGENT_HANDOFF.md` and the relevant specialized backlog.
2. Reuse an existing stable task ID where possible.
3. Inspect current implementation and tests; repository docs describe intent but code/tests are the final implementation truth.
4. Add/update regression tests before changing scoring, fingering, knowledge, or adapter mappings.
5. Preserve backward-compatible public output unless the selected task explicitly changes the schema.
6. Run the full test suite / CI.
7. Update the narrowest relevant backlog/status/algorithm document.
8. Record evidence before claiming improved accuracy, more guitarist-like behavior, or verified plugin behavior.

Learning/promotion always follows a controlled path:

```text
eligible evidence/data
→ provenance/license/verification gate
→ candidate knowledge/profile/model
→ evaluation/conformance/shadow comparison
→ approval
→ versioned production state
```

Runtime must not learn directly from arbitrary web pages while processing a user's song.

## Default priority when the user has not specified a task

Use `docs/AI_AGENT_HANDOFF.md` as the source of truth. Current preferred work is:

```text
PV-002  musician-readable PDF/TAB
GK-013  explicit hand-position state / cross-section continuity
GK-005  generic Performance Plan consuming PerformancePreferences
VI-002  migrate Ample product facts to the generic VI profile
```

Prefer improving the existing prototype over expanding distant crawling/training infrastructure.
