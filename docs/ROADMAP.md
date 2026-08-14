# FretPilot Roadmap

Current milestone: **Prototype 0.1 — musician-reviewable guitar score and
virtual-guitar performance package**.

Task-level truth stays in the `TI-*`, `GK-*`, `VI-*`, and `SE-*` backlogs. This
file contains only product priority and release gates.

## Baseline complete

- MIDI Type 0/1 parsing and logical instrument streams;
- guitar-only confidence, review recommendations, and multi-guitar selection;
- adjustable, provenance-safe note rationalization;
- section-aware context, fingering, hand position, fretting digits,
  articulations, right-hand intent, and conservative harmony;
- canonical Guitar IR with separate score and performance timing;
- GP5, PDF/TAB, Generic PerformancePlan, VI capability report, and Ample Guitar
  SC MIDI generation from one prototype pipeline;
- pinned guitar-playing knowledge snapshot and artifact provenance;
- FastAPI/React conversion and knowledge-review shell;
- approved generic Ample SC profile, negotiation policy, and shadow control-plan
  parity coverage.

## Active work

### 1. Full-song score acceptance

Review real guitar streams in Guitar Pro and PDF. Fix, in order:

1. impossible or unnatural string/fret/shape decisions;
2. broken phrase or hand-position continuity;
3. incorrect articulation, right-hand, or harmony intent;
4. mixed-density layout and multi-voice notation;
5. paired standard staff + TAB after the TAB baseline is stable.

Acceptance: one full guitar stream is usable as a first-draft part rather than
a debugging visualization.

### 2. Real Ample verification

Play at least one generated MIDI through Ample Guitar SC 4.x in a real DAW and
record structured evidence. MIDI parse-back alone is insufficient.

### 3. Generic VI control handoff (`VI-004`)

```text
Guitar IR / PerformancePlan
→ capability negotiation
→ generic ControlAction plan
→ parity comparison
→ production adapter consumption
```

Do not replace the proven scheduler until output-neutral parity stays green.

### 4. Guitar knowledge refinement

Implement reusable root-independent shape memory (`GK-012`), then refine
barre/stretch/thumb/shift semantics using real-song evidence.

### 5. Reproducibility

Extend knowledge provenance into full engine/config/model identity and
selectable approved snapshots under `SE-*`.

## One-command validation

```bash
fretpilot prototype song.mid --all-likely-guitars -o output/
```

Each selected stream produces rewrite provenance, analysis, Guitar IR, PDF,
GP5 when supported, Ample MIDI, PerformancePlan, VI capability report, and a
processing report. Top-level indexes summarize sidecars.

## Prototype 0.1 release gates

1. Backend and frontend CI are green.
2. One real multi-guitar MIDI produces complete packages.
3. One full GP5/PDF guitar part passes musician review.
4. One Ample MIDI is verified in the real plugin/DAW.
5. Unsupported cases are explicit rather than silently degraded.
6. README, handoff, roadmap, and specialized backlog statuses agree.

Multi-product support, full track-classifier calibration, large-scale learning,
and learned rankers are not Prototype 0.1 blockers.
