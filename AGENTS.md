# FretPilot AI Contributor Guide

This file is the entry point for AI agents and new contributors.

## Before changing code

Read these project-wide documents first:

1. [`README.md`](README.md) — product summary and runnable commands.
2. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — current executable architecture and module boundaries.
3. [`docs/LONG_TERM_ARCHITECTURE.md`](docs/LONG_TERM_ARCHITECTURE.md) — stable vs evolvable modules, Runtime/Learning planes, and long-term knowledge architecture.
4. [`docs/ROADMAP.md`](docs/ROADMAP.md) — current prototype/product priority.

Then read the specialized project documentation for the module you are changing.

### Track identification work (`TI-*`)

1. [`docs/projects/track-identification/README.md`](docs/projects/track-identification/README.md)
2. [`docs/projects/track-identification/STATUS.md`](docs/projects/track-identification/STATUS.md)
3. [`docs/projects/track-identification/BACKLOG.md`](docs/projects/track-identification/BACKLOG.md)
4. [`docs/projects/track-identification/TEST_PLAN.md`](docs/projects/track-identification/TEST_PLAN.md)
5. [`docs/GUITAR_DETECTION.md`](docs/GUITAR_DETECTION.md)

Then inspect:

```text
src/fretpilot/midi/
src/fretpilot/detection/
tests/test_midi_parser.py
tests/test_guitar_detection.py
```

### Guitar-playing knowledge / fingering / articulation work (`GK-*`)

Before changing `knowledge`, `guitar/fingering.py`, articulation behavior, or style-aware performance decisions, read:

1. [`docs/projects/guitar-playing-knowledge/README.md`](docs/projects/guitar-playing-knowledge/README.md)
2. [`docs/projects/guitar-playing-knowledge/BACKLOG.md`](docs/projects/guitar-playing-knowledge/BACKLOG.md)
3. [`docs/projects/guitar-playing-knowledge/LEARNING_PIPELINE.md`](docs/projects/guitar-playing-knowledge/LEARNING_PIPELINE.md)

Then inspect:

```text
src/fretpilot/knowledge/
src/fretpilot/guitar/
src/fretpilot/articulation/
src/fretpilot/analysis/
tests/test_playing_knowledge.py
tests/test_guitar_fingering.py
tests/test_articulation_planner.py
```

### Cross-project self-evolution infrastructure (`SE-*`)

Use `SE-*` only when work crosses specialized module boundaries. Read:

1. [`docs/projects/system-evolution/README.md`](docs/projects/system-evolution/README.md)
2. [`docs/projects/system-evolution/BACKLOG.md`](docs/projects/system-evolution/BACKLOG.md)
3. [`docs/LONG_TERM_ARCHITECTURE.md`](docs/LONG_TERM_ARCHITECTURE.md)

Examples include runtime reproducibility manifests, knowledge snapshot pinning, shared evaluation identity, cross-module correction envelopes, shadow comparison, and model/knowledge compatibility metadata.

Do **not** create an `SE-*` task if the work clearly belongs to an existing `TI-*` or `GK-*` task.

## Task prefixes

```text
PV-*  prototype/output validation and near-term user-facing quality
TI-*  instrument-stream and guitar-track identification
GK-*  guitar-playing/style/phrase knowledge and learning
SE-*  cross-project system-evolution infrastructure and governance
```

## Non-negotiable design rules

- A physical MIDI track is not necessarily an instrument.
- Preserve physical track, MIDI channel, active program, source ticks, and original notes.
- Resolve logical `InstrumentStream` objects before guitar analysis.
- Layers 1–3 answer whether a stream is probably guitar.
- Layer 4 answers what guitar behavior a region resembles; it must not override instrument identity.
- `role`, `style`, and `technique family` are separate dimensions and may be composed (for example `solo + metal`).
- Guitar-playing knowledge is a soft prior. Physical fretboard/playability constraints remain hard constraints.
- Learned/AI systems rank or advise among valid alternatives; they do not bypass deterministic physical/file constraints.
- Do not scatter genre-specific magic numbers across fingering, articulation, and exporters; add or update a versioned knowledge profile instead.
- Track names and General MIDI programs are evidence, not absolute truth.
- Classification must remain explainable: expose per-layer scores, reasons, and raw metrics.
- Do not silently auto-select when multiple likely guitar streams exist.
- Do not let plugin-specific Ample Guitar mappings leak into detection or canonical musical intent.
- Do not introduce an LLM dependency into deterministic import, stream resolution, baseline classification, hard fretboard validation, or file-format validation.
- Canonical Guitar IR must remain versioned and independent of output adapters.
- Learned knowledge must preserve provenance and versioning. Newly ingested external material must not silently change production behavior.
- Runtime inference must use an approved/pinned knowledge state; it must not learn directly from arbitrary web pages during a user request.
- Do not assume publicly visible internet tablature is automatically licensed for crawling, storage, redistribution, or training.

## Required workflow

When implementing a backlog item:

1. Pick the correct stable task ID (`PV-*`, `TI-*`, `GK-*`, or `SE-*`).
2. Check whether an existing task already owns the work before creating a new one.
3. Add or update tests before changing scoring/knowledge behavior.
4. Keep existing public JSON fields backward-compatible unless the task explicitly changes the schema.
5. Run `pytest -q`.
6. Update the relevant project docs/backlog.
7. Record evaluation evidence rather than claiming that a heuristic or learned profile is more accurate without measurements.

For learned guitar knowledge, use the controlled lifecycle documented in `LEARNING_PIPELINE.md`:

```text
eligible source
→ provenance/license gate
→ normalization + quality + deduplication
→ feature extraction / training
→ candidate knowledge
→ offline evaluation / shadow comparison
→ approved versioned snapshot
```

Production behavior must never be silently changed by newly ingested material.

## Current focus

Track identification has an explainable V0 and can improve incrementally.

The immediate prototype focus is still user-visible score/performance quality. In parallel, the playing-knowledge project should become the maintainable connection between phrase behavior/style and decisions such as hand position, movable shapes, string choice, chord voicing, articulation, and performance timing.

The larger `SE-*` learning/release infrastructure is a long-term enabler and must not block Prototype 0.1.