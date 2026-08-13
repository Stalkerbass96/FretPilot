# System Evolution Project

## Goal

Provide the cross-project architecture and governance needed for FretPilot to improve over time without making runtime behavior irreproducible.

This is an **umbrella project**, not a replacement for the specialized backlogs.

Canonical subprojects remain:

- `TI-*` — track/instrument identification;
- `GK-*` — guitar-playing knowledge, style, phrasing, and learning;
- `PV-*` — prototype/output validation.

Use `SE-*` only for work that crosses these project boundaries or defines shared infrastructure.

## Core architecture

Read [`../../LONG_TERM_ARCHITECTURE.md`](../../LONG_TERM_ARCHITECTURE.md) first.

The system is intentionally divided into:

```text
Runtime Plane
  deterministic engine
  + approved versioned knowledge
  + optional pinned learned/advisor model

Learning Plane
  eligible sources / corrections / golden material
  → provenance + quality + dedup
  → feature extraction / training
  → candidate
  → evaluation
  → approved snapshot
```

The Runtime Plane must not silently learn from arbitrary internet material.

## Stable vs evolvable boundary

### Stable/deterministic core

- MIDI parsing and source preservation;
- physical fretboard constraints;
- output-format validation;
- canonical Guitar IR schema/versioning;
- reproducibility metadata;
- hard safety/validity rules.

### Evolvable intelligence

- guitar identity ranking;
- phrase/section analysis;
- role/style/technique inference;
- fingering candidate ranking;
- voicing/shape preference;
- articulation preference;
- performance feel;
- statistical/learned knowledge.

Learned intelligence ranks valid alternatives; it does not bypass hard constraints.

## Knowledge assets

Long term, FretPilot should treat these as independent versioned assets where practical:

```text
Engine
Configuration
Guitar IR schema
Instrument-detection knowledge
Guitar-playing knowledge
Evaluation benchmark
Optional learned ranker/model
```

A runtime result should eventually record enough version metadata to reproduce how it was produced.

## Related project documents

### Track identification

- `../track-identification/README.md`
- `../track-identification/BACKLOG.md`
- `../track-identification/TEST_PLAN.md`

### Guitar-playing knowledge

- `../guitar-playing-knowledge/README.md`
- `../guitar-playing-knowledge/BACKLOG.md`
- `../guitar-playing-knowledge/LEARNING_PIPELINE.md`

## Current status

The architectural direction is established. The larger self-evolution system is **not** a prototype blocker.

The immediate engineering focus remains score/output usability and connecting `PlayingContext` into current musical decisions.

See [`BACKLOG.md`](BACKLOG.md) for cross-project `SE-*` tasks.