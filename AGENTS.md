# FretPilot AI Contributor Guide

This file is the entry point for AI agents and new contributors.

## Before changing code

Read `README.md` first, then read the project documentation that matches the module you are changing.

### Track identification work

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

### Guitar-playing knowledge / fingering / articulation work

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

## Non-negotiable design rules

- A physical MIDI track is not necessarily an instrument.
- Preserve physical track, MIDI channel, active program, source ticks, and original notes.
- Resolve logical `InstrumentStream` objects before guitar analysis.
- Layers 1–3 answer whether a stream is probably guitar.
- Layer 4 answers what guitar behavior a region resembles; it must not override instrument identity.
- `role`, `style`, and `technique family` are separate dimensions and may be composed (for example `solo + metal`).
- Guitar-playing knowledge is a soft prior. Physical fretboard/playability constraints remain hard constraints.
- Do not scatter genre-specific magic numbers across fingering, articulation, and exporters; add or update a versioned knowledge profile instead.
- Track names and General MIDI programs are evidence, not absolute truth.
- Classification must remain explainable: expose per-layer scores, reasons, and raw metrics.
- Do not silently auto-select when multiple likely guitar streams exist.
- Do not let plugin-specific Ample Guitar mappings leak into detection or canonical musical intent.
- Do not introduce an LLM dependency into deterministic import, stream resolution, or baseline classification.
- Learned knowledge must preserve provenance and versioning. Newly ingested external material must not silently change production behavior.
- Do not assume publicly visible internet tablature is automatically licensed for crawling, storage, redistribution, or training.

## Required workflow

When implementing a backlog item:

1. Pick a stable project task ID (`TI-xxx` or `GK-xxx`).
2. Add or update tests before changing scoring/knowledge behavior.
3. Keep existing public JSON fields backward-compatible unless the task explicitly changes the schema.
4. Run `pytest -q`.
5. Update the relevant project docs/backlog.
6. Record evaluation evidence rather than claiming that a heuristic or learned profile is more accurate without measurements.

For learned guitar knowledge, use the controlled lifecycle documented in `LEARNING_PIPELINE.md`:

```text
eligible source
→ provenance/license gate
→ normalization + feature extraction
→ candidate knowledge
→ offline evaluation
→ approved versioned snapshot
```

Runtime inference must use an approved snapshot; it must not learn directly from arbitrary web pages during a user request.

## Current focus

Track identification has an explainable V0 and can improve incrementally.

The output prototype now has a more important parallel focus: make MIDI become guitarist-like notation/performance. The playing-knowledge project should provide the maintainable connection between phrase behavior/style and decisions such as hand position, movable shapes, string choice, chord voicing, articulation, and performance timing.
