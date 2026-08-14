# Guitar Playing Knowledge Backlog

Stable task IDs use the `GK-` prefix. This file is the task-status source of truth for **how a real guitarist would likely play**. Product/plugin controls belong in `VI-*`.

Status language:

```text
implemented           contract is present and regression-covered
implemented baseline  useful deterministic baseline; calibration/richer semantics remain
partial                some priors/mechanisms exist; family/task is not complete
not started            no first-class implementation yet
```

## P0 — knowledge interface / runtime flow

| Task | Status | Current contract |
|---|---|---|
| GK-001 PlayingContext | implemented | separate composable role/style/technique-family dimensions |
| GK-002 thread context through analysis | implemented baseline | section context reaches fingering, articulation, right hand, Guitar IR, PerformancePlan |
| GK-003 preference-aware fingering | implemented baseline | soft ranking only; hard fretboard constraints stay authoritative |
| GK-004 context-aware articulation | implemented baseline | hammer/pull, slide, vibrato, contextual palm mute/staccato, source-backed pitch movement |
| GK-005 Generic PerformancePlan | implemented product baseline | target-neutral timing/duration/velocity/accent/overlap intent + normal prototype sidecars |

### GK-002 — remaining

The normal runtime is:

```text
InstrumentStream
→ section segmentation
→ behavior/style evidence
→ PlayingContext
→ fingering + hand-position / voicing continuity
→ fretting digit
→ articulation / pitch movement
→ right-hand PickingPlan
→ global source_note_index remap
→ GuitarTrackAnalysis
→ Guitar IR provenance
```

Remaining is mostly cross-project provenance/versioning under `SE-*`; do not rebuild context threading.

### GK-005 — remaining

`fretpilot prototype` now emits per-stream `.performance-plan.json` sidecars plus `performance-plans.json`. VI capability negotiation exists and can inventory PerformancePlan requirements, but production Ample rendering still uses source performance timing/velocity/duration.

Next contract:

```text
Guitar IR + PlayingContext.performance
→ Generic PerformancePlan
→ VI capability negotiation
→ target adapter consumption only with output-neutral regression coverage
```

No vendor keyswitch/CC/state belongs in PerformancePlan.

## P1 — phrase / fretboard / technique state

| Task | Status | Current contract / remaining gap |
|---|---|---|
| GK-010 section/phrase segmentation | implemented baseline | deterministic measure/feature-change boundaries; calibration remains |
| GK-011 behavior classification | implemented experimental baseline | solo/riff/strum/heavy/jazz-comping/arpeggio vocabulary; rules are not calibrated truth |
| GK-012 reusable shape memory | **not started** | needs root-independent reusable shape prototypes |
| GK-013 hand-position state | implemented baseline | weak-boundary carry / strong-boundary reset; real-song threshold/state calibration remains |
| GK-014 fretting-digit assignment | implemented baseline | deterministic 1–4 digits; barre/stretch/thumb/chord-wide solving remain |
| GK-015 section-aware execution/merge | implemented baseline | one canonical execution path with global source-note remap and context overrides |
| GK-016 right-hand intent | implemented baseline | down/up pick, strum, observed rolled strum, tremolo, sweep; hybrid/calibration remain |
| GK-017 pitch-wheel gesture preservation | implemented positive-raise baseline | explicit-range monophonic raises; downward/pre-bend/richer curves remain |
| GK-018 harmony regions | implemented conservative baseline | simultaneous/sequential chord labels and inversions; richer harmonic semantics remain |

### GK-012 — reusable shape memory

This is the biggest structural GK gap.

Existing local repair can reuse movable riff/arpeggio shapes and chord-voicing continuity, but there is no first-class shape prototype independent of absolute root fret.

Initial shape families should include:

```text
sus2 arpeggio
power chord
octave shape
triad inversion
jazz shell voicing
```

The Message-in-a-Bottle movable sus2 pattern remains a primary golden reference.

### GK-013 — hand-position refinement

Implemented:

- explicit per-section `HandPositionState`;
- entry/exit fret center and min/max span;
- previous-section exit / shift amount / transition reason;
- weak-boundary carry and strong-boundary reset;
- entry repair only among canonical playable candidates;
- distinct-string chord constraints preserved;
- Guitar IR provenance and focused weak/strong regressions.

Remaining:

- real-song/golden calibration of the current boundary threshold and entry window;
- richer hand-center/span/shape-transition state;
- explicit position-shift semantics coordinated with GK-012/GK-014.

### GK-014 — advanced left-hand contracts

Current `fretting_digit` is deterministic 1–4 and persisted in Guitar IR/GP5. Open or ambiguous cases abstain rather than force impossible fingering.

Remaining:

```text
first-class barre
stretch feasibility
thumb-over/thumb-fretting
richer chord-wide digit solving
explicit shift fingering semantics
```

### GK-016 — right-hand intent

Current deterministic baseline recognizes:

- tight low-register riff figures → repeated downstrokes;
- slower single-note/arpeggio material → alternate picking;
- rapid repeated same-pitch runs → tremolo + alternating direction;
- fast monotonic adjacent-string runs → sweep intent;
- chord onsets in strumming context → strum motion/direction;
- real staggered overlapping chord onsets → `rolled_strum` evidence.

Research/style priors only adjust confidence after timing/fingering evidence passes. Do not invent rolled timing for simultaneous chords.

Remaining: hybrid-picking inference and real-song threshold calibration.

### GK-017 — pitch movement

Package-level MIDI loading preserves raw pitch-wheel and RPN 0/0 range events. `pitch_raise` is emitted only when range and note ownership are unambiguous. Guitar IR stores semitone amount and curve timing; GP5 maps safe integer-semitone curves and conservatively falls back for fractional cases.

Remaining: downward gestures, pre-bend/pre-raise semantics, richer multi-point curves. Target-specific pitch realization belongs in VI.

### GK-018 — harmony regions

Current conservative analysis labels simultaneous chords and strong sequential broken-chord cells, respects section boundaries, supports common qualities/inversions, and persists typed harmony regions into Guitar IR. GP5/PDF consume the canonical labels rather than re-inferring harmony.

Remaining: richer extensions/alterations, phrase-level harmonic context, and stronger ambiguity handling.

## P2 — style-family knowledge

All style families below are **partial baselines**, not calibrated musical truth.

| Task | Current useful priors | Major remaining work |
|---|---|---|
| GK-020 metal | low-register stability, PM/staccato evidence, downstroke/tremolo | calibrated rhythm/breakdown/lead/low-tuned subprofiles |
| GK-021 rock/pop | movable arpeggio/shape reuse/open-string policy | open-chord, power-chord, melodic-lead subprofiles |
| GK-022 jazz | compact voicing, open-string avoidance, voice-leading proxies | shell/drop-2/drop-3 and richer comping semantics |
| GK-023 blues | box-position/expressive priors + explicit source pitch raises | pentatonic-box semantics, double stops, target-aware bends/vibrato |
| GK-024 funk | short/percussive/staccato priors | muted 16ths, partial chords, ghost/percussive-note model |
| GK-025 fingerstyle/acoustic | alternating-bass/open-string/let-ring/voice-separation priors | bass/melody separation, alternating thumb, chord-melody planner |

Runtime style priors remain soft rankings. A song/section style label never bypasses physical fretboard constraints.

## P3 — controlled learning infrastructure

These are not Prototype 0.1 blockers.

| Task | Status |
|---|---|
| GK-030 source provenance schema | not started as full learning-batch contract |
| GK-031 symbolic tab normalizer | not started |
| GK-032 knowledge feature extractor | not started |
| GK-033 dedup/source-family weighting | not started |
| GK-034 quality estimator | not started |
| GK-035 versioned Knowledge Snapshot format | baseline implemented: packaged 2026.08.2 registry, source/rule separation, runtime provenance; candidate release tooling pending |
| GK-036 candidate/evaluation/promotion workflow | not started |

Target lifecycle:

```text
eligible/licensed evidence
→ provenance + quality + dedup
→ normalized derived features
→ candidate knowledge snapshot
→ offline evaluation / shadow comparison
→ approval
→ pinned production snapshot
```

Runtime does not crawl arbitrary pages or mutate production knowledge while processing a song.

## P4 — learned ranking

| Task | Status |
|---|---|
| GK-040 regression evaluation corpus | not started |
| GK-041 interpretable statistical candidate ranker | not started |
| GK-042 sequence-level fretboard path model | not started |
| GK-043 approved shape/phrase retrieval | not started |

Expected metrics include string/fret agreement, shape-family agreement, fretting-digit agreement where known, average hand shift, fret-span cost, impossible-fingering rate, and phrase-level path score.

Learned systems rank deterministic valid candidates; they never create impossible fretboard positions.

## Guardrails

- Do not treat one published tab as canonical truth.
- Do not ingest/redistribute material without an appropriate legal basis.
- Preserve source provenance and knowledge-version reproducibility.
- Keep physical/playability validation deterministic.
- Keep Guitar Playing Knowledge separate from target virtual-instrument control knowledge (`VI-*`).
- Newly discovered evidence creates candidate knowledge; it does not silently replace production behavior.
