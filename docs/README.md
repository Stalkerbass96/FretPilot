# FretPilot Documentation Index

This page is the navigation entry point for product, architecture, and active development-project documentation.

## Start here

- [`../AGENTS.md`](../AGENTS.md) — mandatory contributor workflow and source-of-truth rules.
- [`AI_AGENT_HANDOFF.md`](AI_AGENT_HANDOFF.md) — compact current implementation handoff for AI agents/contributors.
- [`ROADMAP.md`](ROADMAP.md) — current product milestone, priority, and release gates.
- [`../README.md`](../README.md) — product overview, installation, and runnable commands.
- [`PRODUCT.md`](PRODUCT.md) — product definition and user scope.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — module boundaries and executable architecture.
- [`LONG_TERM_ARCHITECTURE.md`](LONG_TERM_ARCHITECTURE.md) — Runtime/Learning planes and long-term evolution constraints.
- [`MUSIC_IR.md`](MUSIC_IR.md) — canonical Guitar IR contract.

For a new AI agent: read `AGENTS.md` → `AI_AGENT_HANDOFF.md` → `ROADMAP.md`, then open only the specialized project docs for the task family being changed.

## Specialized task families

### SE — system evolution

Cross-module reproducibility, knowledge snapshots, evaluation identity, feedback loops, and learned-ranker governance:

- [`projects/system-evolution/README.md`](projects/system-evolution/README.md)
- [`projects/system-evolution/BACKLOG.md`](projects/system-evolution/BACKLOG.md)

### GK — guitar playing knowledge

Real-guitar style/behavior knowledge, fretboard execution, articulation, right-hand intent, harmony, and controlled future learning:

- [`projects/guitar-playing-knowledge/README.md`](projects/guitar-playing-knowledge/README.md)
- [`projects/guitar-playing-knowledge/BACKLOG.md`](projects/guitar-playing-knowledge/BACKLOG.md)
- [`projects/guitar-playing-knowledge/LEARNING_PIPELINE.md`](projects/guitar-playing-knowledge/LEARNING_PIPELINE.md)

### VI — virtual guitar instruments

Product/version-specific capabilities, control knowledge, compatibility, conformance, and future multi-product adapters:

- [`projects/virtual-guitar-instruments/README.md`](projects/virtual-guitar-instruments/README.md)
- [`projects/virtual-guitar-instruments/BACKLOG.md`](projects/virtual-guitar-instruments/BACKLOG.md)

Product controls remain downstream of canonical Guitar IR/Guitar Playing Knowledge.

### TI — track / instrument identification

Logical stream resolution, guitar identity evidence, calibration, and selection policy:

- [`projects/track-identification/README.md`](projects/track-identification/README.md)
- [`projects/track-identification/STATUS.md`](projects/track-identification/STATUS.md)
- [`projects/track-identification/BACKLOG.md`](projects/track-identification/BACKLOG.md)
- [`projects/track-identification/TEST_PLAN.md`](projects/track-identification/TEST_PLAN.md)
- [`GUITAR_DETECTION.md`](GUITAR_DETECTION.md)

## Task prefixes

```text
PV-*  prototype/output quality
TI-*  instrument-stream / guitar-track identification
GK-*  guitarist-like playing knowledge and learning
VI-*  virtual-guitar product knowledge/adapters
SE-*  reproducibility/evaluation/evolution governance
```

## Documentation ownership

Use each document for one purpose:

- **AGENTS.md** — contributor workflow, invariants, and where to find truth.
- **AI_AGENT_HANDOFF.md** — short current-state summary; do not duplicate whole backlogs here.
- **ROADMAP.md** — product milestone, active priorities, and release gates.
- **Project BACKLOG** — canonical task IDs **and their current status**, including implemented, partial, and pending work.
- **Project README/design docs** — boundaries and intended architecture.
- **STATUS** — module-specific implemented behavior where that project maintains one.
- **TEST_PLAN/evaluation docs** — evidence required before accuracy/quality claims.
- **Algorithm/format docs** — detailed current semantics where needed.

When code behavior changes, update the narrowest authoritative document. Do not copy the same implementation-status paragraph into multiple files.
