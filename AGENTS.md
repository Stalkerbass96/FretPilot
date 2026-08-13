# FretPilot AI Contributor Guide

This file is the entry point for AI agents and new contributors.

## Before changing code

Read these files in order:

1. [`README.md`](README.md) — product summary and runnable commands.
2. [`docs/projects/track-identification/README.md`](docs/projects/track-identification/README.md) — current project entry point for instrument-stream and guitar-track identification.
3. [`docs/projects/track-identification/STATUS.md`](docs/projects/track-identification/STATUS.md) — what is implemented versus planned.
4. [`docs/projects/track-identification/BACKLOG.md`](docs/projects/track-identification/BACKLOG.md) — prioritized work items and acceptance criteria.
5. [`docs/projects/track-identification/TEST_PLAN.md`](docs/projects/track-identification/TEST_PLAN.md) — regression and evaluation requirements.
6. [`docs/GUITAR_DETECTION.md`](docs/GUITAR_DETECTION.md) — detailed algorithm design.

Then inspect the relevant implementation and tests:

```text
src/fretpilot/midi/
src/fretpilot/detection/
src/fretpilot/knowledge/
src/fretpilot/cli.py
tests/test_midi_parser.py
tests/test_guitar_detection.py
```

## Non-negotiable design rules

- A physical MIDI track is not necessarily an instrument.
- Preserve physical track, MIDI channel, active program, source ticks, and original notes.
- Resolve logical `InstrumentStream` objects before guitar analysis.
- Layers 1–3 answer whether a stream is probably guitar.
- Layer 4 answers what guitar behavior a region resembles; it must not override instrument identity.
- Track names and General MIDI programs are evidence, not absolute truth.
- Classification must remain explainable: expose per-layer scores, reasons, and raw metrics.
- Do not silently auto-select when multiple likely guitar streams exist.
- Do not let plugin-specific Ample Guitar mappings leak into detection or canonical musical intent.
- Do not introduce an LLM dependency into deterministic import, stream resolution, or baseline classification.

## Required workflow for this module

When implementing a backlog item:

1. Pick one task ID from `BACKLOG.md`.
2. Add or update tests before changing scoring behavior.
3. Keep existing public JSON fields backward-compatible unless the task explicitly changes the schema.
4. Run `pytest -q`.
5. Update `STATUS.md` and the selected task in `BACKLOG.md`.
6. Update `GUITAR_DETECTION.md` when algorithm semantics, weights, thresholds, features, or invariants change.
7. Record evaluation evidence rather than claiming that a heuristic is more accurate without measurements.

## Current focus

The detection module has an explainable V0 implementation. The next major work is not adding more arbitrary thresholds. It is building a labeled regression/evaluation corpus, hardening Layers 1–3, and adding section-level segmentation so Layer 4 can classify changing guitar behavior within one stream.
