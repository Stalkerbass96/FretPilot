# FretPilot Documentation Index

This page is the navigation entry point for product, architecture, and active development-project documentation.

## Start here

- [`../README.md`](../README.md) — product overview, installation, and runnable CLI commands.
- [`../AGENTS.md`](../AGENTS.md) — required reading and workflow for AI agents and contributors.
- [`PRODUCT.md`](PRODUCT.md) — product definition, scope, and target user.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — module boundaries and pipeline architecture.
- [`ROADMAP.md`](ROADMAP.md) — overall implementation phases and current priorities.
- [`MUSIC_IR.md`](MUSIC_IR.md) — planned canonical Guitar IR.

## Active project: guitar playing knowledge

This project manages the maintainable bridge between style/behavior understanding and realistic guitar choices:

- [`projects/guitar-playing-knowledge/README.md`](projects/guitar-playing-knowledge/README.md) — project architecture, role/style/technique composition, and current scope.
- [`projects/guitar-playing-knowledge/BACKLOG.md`](projects/guitar-playing-knowledge/BACKLOG.md) — stable `GK-xxx` work items for style-aware fingering, articulation, phrase context, and learning infrastructure.
- [`projects/guitar-playing-knowledge/LEARNING_PIPELINE.md`](projects/guitar-playing-knowledge/LEARNING_PIPELINE.md) — controlled provenance, quality, feature extraction, evaluation, and knowledge-promotion workflow for future self-learning.

## Active project: track identification

The detailed instrument-stream and guitar-track identification work is managed as a separate project:

- [`projects/track-identification/README.md`](projects/track-identification/README.md) — project hub and stable concepts.
- [`projects/track-identification/STATUS.md`](projects/track-identification/STATUS.md) — implemented versus planned behavior.
- [`projects/track-identification/BACKLOG.md`](projects/track-identification/BACKLOG.md) — prioritized task IDs and acceptance criteria.
- [`projects/track-identification/TEST_PLAN.md`](projects/track-identification/TEST_PLAN.md) — fixture, regression, evaluation, and quality requirements.
- [`GUITAR_DETECTION.md`](GUITAR_DETECTION.md) — current layered detection algorithm.

## Documentation roles

Use documents for different purposes:

- **Product docs** explain why the feature exists and what users receive.
- **Architecture docs** define module boundaries and invariants.
- **Algorithm docs** define current behavior and scoring semantics.
- **Project STATUS** records what the code actually supports now.
- **Project BACKLOG** records work that has not been completed.
- **TEST_PLAN** defines evidence required before accuracy claims or scoring changes.

When code behavior changes, update the narrowest relevant document instead of duplicating the same details across every file.
