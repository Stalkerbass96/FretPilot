# FretPilot Roadmap

> Current milestone: **Prototype 0.1 — musician-reviewable score + virtual-guitar performance output**
>
> Codex/AI agents: read `AGENTS.md` and `docs/AI_AGENT_HANDOFF.md` first. This file tracks product priority; task details live in the `TI-*`, `GK-*`, `VI-*`, and `SE-*` backlogs.

## Current implemented vertical slice

```text
MIDI
→ NormalizedTimeline
→ InstrumentStream resolution
→ Layers 1–3 guitar identity
→ selected guitar stream
→ rhythm / notation analysis
→ section segmentation
→ per-section behavior profiles
→ per-section PlayingContext
→ per-section fingering
→ hand-position continuity baseline
→ per-section articulation
→ global source-note remap
→ GuitarTrackAnalysis
→ canonical Guitar IR + section/hand-position provenance
├──→ PDF/TAB review output
├──→ GP5
└──→ current Ample Guitar SC 4.x renderer
```

A separate target-neutral performance-intent baseline now exists:

```text
Guitar IR + PlayingContext.performance
→ Generic PerformancePlan
→ future VI capability negotiation
→ future adapter consumption
```

The existing Ample renderer still uses the established source-performance path. Do not silently switch it to `PerformancePlan` until neutral behavior and adapter handoff have regression coverage.

Track identification remains an incremental `TI-*` project and is **not** the main prototype blocker.

## Task families

```text
PV-*  immediate prototype/output quality
TI-*  InstrumentStream / guitar-track identification
GK-*  guitarist-like playing knowledge, style, phrasing, fingering, performance intent
VI-*  virtual-guitar instrument knowledge and adapters
SE-*  evaluation, feedback, reproducibility, knowledge evolution
```

## Current status

### Input / stream selection

- [x] MIDI Type 0 / Type 1 import
- [x] preserve Track / Channel / active Program / ticks / source timing
- [x] logical `InstrumentStream` resolution
- [x] layered guitar candidate ranking
- [x] explicit stream selection and multiple-guitar ambiguity handling
- [ ] measured/calibrated track-identification evaluation (`TI-*`)

### Musical understanding / guitar execution

- [x] rhythm-grid analysis and basic notation cleanup
- [x] source/performance timing separate from score timing
- [x] measure coordinates and cross-measure ties
- [x] standard six-string fretboard candidates
- [x] movable riff/arpeggio shape repair baseline
- [x] simultaneous chord distinct-string solving
- [x] `PlayingContext` model with separate role/style/technique dimensions
- [x] context-aware fingering soft costs
- [x] hammer-on / pull-off / slide / vibrato inference
- [x] context-aware articulation confidence weighting
- [x] deterministic section segmentation baseline
- [x] independent `PlayingContext` per section
- [x] section-aware execution and global source-note remap
- [x] explicit hand-position state baseline (`GK-013`)
- [x] weak-boundary carry / strong-boundary reset baseline
- [ ] focused GK-013 regression/golden evaluation and threshold tuning
- [ ] reusable shape-memory model (`GK-012`)
- [ ] true left-hand finger/barre/stretch assignment (`GK-014`)
- [ ] bend/palm-mute/pick-direction/strum-intent expansion

### Guitar IR

- [x] schema version 0.1
- [x] tempo/time-signature maps
- [x] score and source-performance timing
- [x] string/fret and generic articulations
- [x] transformation/change log
- [x] section-context provenance through public builder
- [x] hand-position provenance through public builder
- [ ] formal knowledge/config/runtime version manifest (`SE-*`)
- [ ] richer voice/phrase/left-hand contracts as needed

### Generic Performance Plan (`GK-005`)

- [x] target-neutral plan models
- [x] target-neutral planner API
- [x] section/context provenance
- [x] timing, velocity, metric accent, and overlap intent baseline
- [x] standalone `fretpilot-performance-plan` CLI
- [ ] dedicated neutral-vs-context behavior regressions
- [ ] include plan in one-command prototype/report package
- [ ] stable capability-negotiation handoff into `VI-*`
- [ ] let adapters consume the plan only after regression coverage

### PDF / TAB

- [x] direct landscape PDF/TAB renderer
- [x] six-line TAB with string/fret decisions
- [ ] musician-grade rhythmic stems/beams
- [ ] proportional spacing by rhythmic density
- [ ] better rests/ties/slides/let-ring notation
- [ ] dotted/tuplet visual quality
- [ ] multi-voice TAB
- [ ] standard staff + TAB pairing
- [ ] visual golden regression samples

### GP5

- [x] PyGuitarPro adapter
- [x] rests and duration decomposition
- [x] string/fret mapping
- [x] ties and supported articulations
- [x] write + parse-back validation
- [ ] real Guitar Pro visual review
- [ ] true two-voice notation
- [ ] safer partial let-ring representation inside chords

### Ample Guitar SC 4.x

- [x] working versioned legacy profile
- [x] source timing/velocity rendering
- [x] Sustain state
- [x] Hammer/Pull and Legato Slide controls/overlap
- [x] selected additional articulation mappings
- [x] tempo/time-signature output
- [x] parse-back event-order regression
- [ ] manual DAW/plugin verification
- [ ] vibrato rendering
- [ ] bend curves
- [ ] pick-direction/accent shaping

### Virtual Guitar Instrument architecture (`VI-*`)

- [x] provider-neutral `VirtualGuitarInstrumentProfile` schema skeleton
- [x] VI project/backlog and knowledge boundaries
- [ ] `VI-002` migrate existing Ample product facts to generic profile without changing output
- [ ] adapter registry (`VI-003`)
- [ ] capability negotiation (`VI-004`)
- [ ] common conformance tests
- [ ] second virtual-guitar product after Ample baseline is verified

## Active prototype work

### PV-002 — musician-readable score/TAB

Use real-song review by measure/stream. Prioritize rhythmic readability, spacing, rests/ties, phrase layout, hand-position plausibility, and visual golden samples.

Acceptance:

> At least one full real guitar stream reads like a usable first-draft TAB rather than a debugging visualization.

### GK-013 — hand-position baseline validation

The runtime baseline is integrated. Current remaining work is evidence and refinement, not rebuilding the module.

Immediate acceptance work:

- weak boundary can preserve a useful previous hand center;
- strong boundary can deliberately reset/reposition;
- no repair bypasses physical fretboard constraints;
- simultaneous notes remain on distinct strings;
- Message-in-a-Bottle movable-arpeggio regression remains green;
- threshold/entry-window changes are justified by fixtures or real-song review.

Compatibility cleanup:

> Package-level section-aware APIs use `src/fretpilot/analysis/section_execution.py`. The older `section_aware.py` still contains legacy reset-only code and should be replaced with a thin compatibility re-export.

### GK-005 — performance intent validation/integration

Use the standalone command to inspect generic intent without changing any plugin output:

```bash
fretpilot-performance-plan song.mid \
  --stream-id t0:ch2:p27 \
  -o performance-plan.json
```

Next:

1. add dedicated neutral/context regression tests;
2. include `.performance-plan.json` or equivalent summary in prototype output;
3. define capability negotiation with `VI-*`;
4. then adapt Ample while proving legacy-neutral output stability.

### VI-002 — Ample knowledge migration

Move existing Ample facts from exporter-specific profile structures into the provider-neutral VI schema. Do not alter MIDI behavior as part of the migration. Verified vendor/plugin facts and learned calibration preferences must remain distinguishable.

## One-command validation package

Current command:

```bash
fretpilot prototype song.mid \
  --all-likely-guitars \
  -o output/
```

Per selected stream it currently produces analysis JSON, Guitar IR JSON, GP5 when supported, Ample MIDI, and processing report. Generic PerformancePlan is available through its standalone CLI but is not yet part of this package.

## Prototype 0.1 release definition

Prototype 0.1 is ready for external hands-on testing when:

1. full CI is green;
2. one real multi-guitar MIDI can generate complete review packages;
3. at least one full score/TAB has been visually reviewed and is musician-readable enough for first-draft use;
4. at least one generated Ample MIDI has been played through the actual plugin/DAW;
5. unsupported cases produce explicit warnings rather than silent corruption;
6. README commands and current architecture match the implementation.

Multi-product support and large-scale self-learning are **not** Prototype 0.1 blockers.

## Long-term direction

```text
stable deterministic engine
+ versioned Guitar Playing Knowledge
+ versioned Virtual Instrument Knowledge
+ golden/user correction data
+ controlled candidate → evaluation → promotion loop
```

Runtime must remain reproducible. New web/user/learned knowledge does not silently change production behavior.
