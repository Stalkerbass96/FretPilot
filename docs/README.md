# FretPilot Documentation Index

This page is the navigation entry point for product, architecture, and active development-project documentation.

## Start here

- [`AI_AGENT_HANDOFF.md`](AI_AGENT_HANDOFF.md) — **fast handoff for AI agents: current state, task map, boundaries, and recommended next work**.
- [`../AGENTS.md`](../AGENTS.md) — mandatory contributor workflow and non-negotiable design rules.
- [`../README.md`](../README.md) — product overview, installation, and runnable CLI commands.
- [`PRODUCT.md`](PRODUCT.md) — product definition, scope, and target user.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — current module boundaries and executable architecture.
- [`LONG_TERM_ARCHITECTURE.md`](LONG_TERM_ARCHITECTURE.md) — stable vs evolvable modules, Runtime/Learning planes, knowledge assets, and self-evolution architecture.
- [`KNOWLEDGE_BASE.md`](KNOWLEDGE_BASE.md) — unified knowledge-entry, snapshot, provenance, lifecycle, and runtime traceability contract.
- [`ROADMAP.md`](ROADMAP.md) — prototype phases and current product priorities.
- [`MUSIC_IR.md`](MUSIC_IR.md) — canonical Guitar IR contract.
- [`FRONTEND_DESIGN_SYSTEM.md`](FRONTEND_DESIGN_SYSTEM.md) — product frontend
  principles, technical baseline, tokens, accessibility, and current scope.

For a new AI agent, read `AI_AGENT_HANDOFF.md` first. Only enter the detailed project documents for the task family being changed.

## Umbrella project: system evolution

Use this project for cross-module reproducibility, knowledge snapshots, evaluation identity, feedback loops, and learned-ranker integration:

- [`projects/system-evolution/README.md`](projects/system-evolution/README.md) — project boundary and Runtime/Learning overview.
- [`projects/system-evolution/BACKLOG.md`](projects/system-evolution/BACKLOG.md) — stable `SE-xxx` tasks.

Do not duplicate specialized work here when it already belongs to `TI-*`, `GK-*`, or `VI-*`.

## Active project: guitar playing knowledge

This project manages the maintainable bridge between style/behavior understanding and realistic guitar choices:

- [`projects/guitar-playing-knowledge/README.md`](projects/guitar-playing-knowledge/README.md) — project architecture, role/style/technique composition, and current scope.
- [`projects/guitar-playing-knowledge/BACKLOG.md`](projects/guitar-playing-knowledge/BACKLOG.md) — stable `GK-xxx` work items for style-aware fingering, articulation, phrase context, and learning infrastructure.
- [`projects/guitar-playing-knowledge/LEARNING_PIPELINE.md`](projects/guitar-playing-knowledge/LEARNING_PIPELINE.md) — controlled provenance, quality, feature extraction, evaluation, and knowledge-promotion workflow for future self-learning.

## Active project: virtual guitar instrument knowledge

This project owns product/version-specific virtual-guitar capability and adapter knowledge:

- [`projects/virtual-guitar-instruments/README.md`](projects/virtual-guitar-instruments/README.md) — boundary between real-guitar playing knowledge and software-instrument control knowledge.
- [`VIRTUAL_INSTRUMENT_KNOWLEDGE_BASE.md`](VIRTUAL_INSTRUMENT_KNOWLEDGE_BASE.md) — versioned product-profile schema, evidence levels, and the initial Ample Metal Eclipse 4.1 knowledge asset.
- [`projects/virtual-guitar-instruments/BACKLOG.md`](projects/virtual-guitar-instruments/BACKLOG.md) — stable `VI-xxx` tasks for profile schemas, capability negotiation, adapter state machines, compatibility, calibration, and future multi-product support.

Current Ample Guitar support is the first implementation example. The registry now contains a documented Ample Metal Eclipse 4.1 profile; future adapters must consume canonical Guitar IR without leaking product-specific keyswitch/CC behavior upstream.

## Active project: track identification

The detailed instrument-stream and guitar-track identification work is managed as a separate project:

- [`projects/track-identification/README.md`](projects/track-identification/README.md) — project hub and stable concepts.
- [`projects/track-identification/STATUS.md`](projects/track-identification/STATUS.md) — implemented versus planned behavior.
- [`projects/track-identification/BACKLOG.md`](projects/track-identification/BACKLOG.md) — prioritized `TI-xxx` task IDs and acceptance criteria.
- [`projects/track-identification/TEST_PLAN.md`](projects/track-identification/TEST_PLAN.md) — fixture, regression, evaluation, and quality requirements.
- [`GUITAR_DETECTION.md`](GUITAR_DETECTION.md) — current layered detection algorithm.

## Task prefixes

```text
PV-*  prototype/output validation and immediate product quality
TI-*  instrument-stream / guitar-track identification
GK-*  guitar-playing knowledge, style, phrasing, and learning
VI-*  virtual-guitar product knowledge, adapters, and compatibility
SE-*  cross-project evolution infrastructure and governance
```

## Documentation roles

Use documents for different purposes:

- **AI Agent Handoff** summarizes current state and routes work to the correct project.
- **Product docs** explain why the feature exists and what users receive.
- **Architecture docs** define module boundaries and invariants.
- **Long-term architecture** defines stable/evolvable boundaries and learning governance.
- **Algorithm docs** define current behavior and scoring semantics.
- **Project STATUS** records what the code actually supports now.
- **Project BACKLOG** records work that has not been completed.
- **TEST_PLAN/evaluation docs** define evidence required before accuracy claims or knowledge promotion.

When code behavior changes, update the narrowest relevant document instead of duplicating the same details across every file.
