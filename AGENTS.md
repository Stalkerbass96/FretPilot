# FretPilot AI Contributor Guide

This file is the mandatory entry point for Codex, AI agents, and new contributors.

## Read order

Before a nontrivial change, read:

1. [`docs/AI_AGENT_HANDOFF.md`](docs/AI_AGENT_HANDOFF.md) — short current implementation handoff;
2. [`docs/ROADMAP.md`](docs/ROADMAP.md) — product milestone, release gates, and current priority;
3. the specialized backlog for the task family being changed.

Do not reconstruct architecture or priorities from old chat history when repository documents already define them.

## Task-family source of truth

```text
PV-*  prototype/output quality              docs/ROADMAP.md
TI-*  stream / guitar-track identification  docs/projects/track-identification/BACKLOG.md
GK-*  guitarist-like playing knowledge      docs/projects/guitar-playing-knowledge/BACKLOG.md
VI-*  virtual-guitar adapters/knowledge      docs/projects/virtual-guitar-instruments/BACKLOG.md
SE-*  reproducibility/evaluation/evolution   docs/projects/system-evolution/BACKLOG.md
```

Supporting design docs live beside those backlogs. The backlog owns task status; `ROADMAP.md` owns product priority; `AI_AGENT_HANDOFF.md` owns the compact current-state summary.

## Module map

### TI — instrument / stream identity

Read the TI project docs and inspect:

```text
src/fretpilot/midi/
src/fretpilot/detection/
```

### GK — guitar playing knowledge and execution

Read the GK project docs and inspect:

```text
src/fretpilot/knowledge/
src/fretpilot/guitar/
src/fretpilot/articulation/
src/fretpilot/picking/
src/fretpilot/harmony/
src/fretpilot/analysis/
```

The canonical section-aware execution logic lives in `src/fretpilot/analysis/section_execution.py`. `section_aware.py` is compatibility-only; do not create a second execution truth there.

### Score / IR / performance

```text
src/fretpilot/ir/
src/fretpilot/exporters/guitar_pro/
src/fretpilot/exporters/pdf_score/
src/fretpilot/performance/
src/fretpilot/prototype.py
src/fretpilot/entrypoint.py
```

### VI — target virtual instruments

```text
src/fretpilot/virtual_instruments/
src/fretpilot/exporters/ample_guitar/
```

Critical distinction:

```text
GK = how a real guitarist would likely play
VI = how a target software instrument realizes canonical intent
```

### SE — evaluation / reproducibility / knowledge evolution

Read `docs/LONG_TERM_ARCHITECTURE.md` and the SE project docs. Use `SE-*` only for cross-project infrastructure/governance; do not duplicate work already owned by TI/GK/VI.

## Non-negotiable design rules

- A physical MIDI Track is not necessarily one instrument; resolve logical `InstrumentStream` objects first.
- Preserve source Track, Channel, Program, ticks, original timing, and stable source-note identity.
- Layers 1–3 estimate guitar identity; Layer 4 / `PlayingContext` describes role/style/technique.
- `role`, `style`, and `technique family` remain separate, composable dimensions.
- Guitar Playing Knowledge is a soft prior; physical fretboard/playability and file-format constraints are hard constraints.
- Learned/AI systems may rank valid alternatives but never create physically invalid ones.
- Section-local processing must remap correctly to stream-wide `source_note_index`.
- Score timing and source/performance timing remain separate.
- Canonical Guitar IR is adapter-independent and versioned.
- Product keyswitch/CC/state mappings never belong in Guitar IR or Guitar Playing Knowledge.
- Unsupported target capabilities must be explicit; never silently drop material intent.
- Multiple likely guitar streams must not be silently collapsed into one.
- Runtime uses approved/pinned knowledge and adapter profiles; new evidence never silently mutates production behavior.
- Public tablature/vendor material is not automatically licensed for crawling, redistribution, or training.

## Required workflow

For a nontrivial task:

1. read the handoff, roadmap, and narrow specialized backlog;
2. inspect current code/tests — code plus green regressions are implementation truth;
3. reuse the stable task ID where possible;
4. add/update regression coverage before changing musical scoring, fingering, knowledge, or adapter mappings;
5. preserve backward-compatible output unless the task explicitly changes a public contract;
6. run full CI;
7. update only the narrow authoritative document whose status/contract changed;
8. record evidence before claiming improved accuracy, guitarist-likeness, or verified plugin behavior.

Learning/promotion must follow:

```text
eligible evidence/data
→ provenance/license/verification gate
→ candidate knowledge/profile/model
→ evaluation/conformance/shadow comparison
→ approval
→ versioned production state
```

Runtime must never learn directly from arbitrary web pages while processing a song.

## Default priority

If the user has not specified a task, follow `docs/ROADMAP.md`. Prototype 0.1 currently prioritizes:

```text
keep CI/output parity green
→ real-song GP5/TAB musician review
→ real Ample plugin verification
→ VI-004 output-neutral generic control handoff
→ GK-012 / advanced left-hand refinement
→ release/documentation closeout
```

Do not expand distant crawling/training or multi-product work ahead of those release gates unless explicitly requested.
