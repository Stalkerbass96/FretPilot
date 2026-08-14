# FretPilot Roadmap

> Current milestone: **Prototype 0.1 — musician-reviewable score + virtual-guitar performance output**
>
> Codex/AI agents: read `AGENTS.md` and `docs/AI_AGENT_HANDOFF.md` first. This file tracks product priority; task details live in the `TI-*`, `GK-*`, `VI-*`, and `SE-*` backlogs.

## Current implemented vertical slice

```text
MIDI
→ NormalizedTimeline + pitch-wheel/range evidence
→ InstrumentStream resolution
→ Layers 1–3 guitar identity
→ selected guitar stream
→ rhythm / notation analysis
→ section segmentation
→ per-section behavior profiles
→ per-section PlayingContext
→ section-aware fingering + hand-position continuity
→ fretting-digit assignment
→ articulation / pitch-raise evidence
→ right-hand pick / strum / sweep / tremolo planning
→ conservative harmony regions
→ global source-note remap
→ GuitarTrackAnalysis
→ canonical Guitar IR + section/hand-position/right-hand/harmony provenance
├──→ PDF/TAB review output
├──→ GP5
└──→ current Ample Guitar SC 4.x renderer
```

A target-neutral performance-intent path is also part of the prototype workflow:

```text
Guitar IR + PlayingContext.performance
→ Generic PerformancePlan
→ .performance-plan.json sidecar / report summary
→ future VI capability negotiation
→ future adapter consumption
```

The existing Ample renderer still uses the established source-performance path. Do not silently switch it to `PerformancePlan` until capability negotiation and adapter handoff have regression coverage.

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
- [x] package-level pitch-wheel + declared range preservation
- [ ] measured/calibrated track-identification evaluation (`TI-*`)

### Musical understanding / guitar execution

- [x] rhythm-grid analysis and notation cleanup baseline
- [x] source/performance timing separate from score timing
- [x] measure coordinates and cross-measure ties
- [x] standard six-string fretboard candidates
- [x] movable riff/arpeggio shape repair baseline
- [x] simultaneous chord distinct-string solving
- [x] `PlayingContext` model with separate role/style/technique dimensions
- [x] context-aware fingering soft costs
- [x] hammer-on / pull-off / slide / vibrato inference
- [x] explicit monophonic pitch-raise evidence from declared MIDI wheel range
- [x] context-aware articulation confidence weighting
- [x] deterministic section segmentation baseline
- [x] independent `PlayingContext` per section
- [x] section-aware execution and global source-note remap
- [x] explicit hand-position state baseline (`GK-013`)
- [x] weak-boundary carry / strong-boundary reset baseline
- [x] focused GK-013 weak/strong-boundary regressions
- [x] 1–4 fretting-digit assignment baseline (`GK-014`)
- [x] right-hand downstroke / alternate / tremolo / sweep / strum planning baseline
- [x] observed micro-timed `rolled_strum` evidence baseline
- [x] conservative simultaneous/sequential harmony labeling baseline
- [ ] reusable shape-memory model (`GK-012`)
- [ ] advanced left-hand contracts: barre / stretch / thumb / explicit shift fingering semantics
- [ ] broader deterministic palm-mute/bend technique evidence beyond currently explicit source signals

### Guitar IR

- [x] schema version 0.1
- [x] tempo/time-signature maps
- [x] score and source-performance timing
- [x] string/fret and generic articulations
- [x] articulation parameters for source-backed pitch movement
- [x] fretting digit
- [x] generic right-hand intent + technique provenance
- [x] typed harmony regions
- [x] transformation/change log
- [x] section-context provenance through public builder
- [x] hand-position provenance through public builder
- [x] JSON round-trip coverage for newer guitar fields
- [ ] formal knowledge/config/runtime version manifest (`SE-*`)
- [ ] richer voice/phrase/barre contracts as needed

### Generic Performance Plan (`GK-005`)

- [x] target-neutral plan models
- [x] target-neutral planner API
- [x] section/context provenance
- [x] timing, velocity, metric accent, and overlap intent baseline
- [x] neutral-vs-context behavior regressions
- [x] standalone `fretpilot-performance-plan` CLI
- [x] one-command prototype sidecars and report integration
- [ ] stable capability-negotiation handoff into `VI-*`
- [ ] let adapters consume the plan only after regression coverage

### PDF / TAB

- [x] direct landscape PDF/TAB renderer
- [x] six-line TAB with string/fret decisions
- [x] canonical harmony symbols above TAB
- [x] explicit exact rest-span baseline
- [x] deterministic rhythmic stems / isolated flags / meter-aware beams
- [x] dotted rhythm marks
- [x] exact triplet grouping + bracket/number baseline
- [x] density-aware system breaking with minimum onset-gap planning
- [x] explicit warning when one measure exceeds full-system density capacity
- [x] cross-measure tie marks
- [x] layout-level visual golden previews for harmony/rhythm/density
- [ ] variable-width measure allocation inside a mixed-density system
- [ ] collision-aware annotation placement beyond current fixed lanes
- [ ] multi-voice TAB
- [ ] standard staff + TAB pairing
- [ ] publication-quality traditional rest/notehead engraving

### GP5

- [x] PyGuitarPro adapter
- [x] rests and duration decomposition
- [x] string/fret mapping
- [x] fretting-digit mapping
- [x] pick-stroke direction
- [x] observed rolled-strum `BeatStroke` mapping
- [x] source-backed integer-semitone pitch-raise curve mapping with conservative fractional fallback
- [x] harmony text labels
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
- [ ] generic PerformancePlan / pick-direction / accent handoff after VI capability negotiation

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

Use real-song review by measure/stream. The current PDF now has harmony labels, exact rests, rhythm stems/beams, dotted/triplet marks, and density-aware line breaking. The next score-quality work is visual collision refinement, mixed-density width allocation, phrase/system layout, and then paired standard staff + TAB.

Acceptance:

> At least one full real guitar stream reads like a usable first-draft TAB rather than a debugging visualization.

### GK-013 / GK-014 — left-hand refinement

The hand-position and 1–4 fretting-digit baselines are integrated and regression-covered. Remaining work is evidence-driven refinement rather than rebuilding them:

- reusable shape memory across phrase/context regions;
- barre / stretch / thumb / explicit position-shift semantics;
- no repair bypasses physical fretboard constraints;
- simultaneous notes remain on distinct strings;
- Message-in-a-Bottle movable-arpeggio regression remains green.

### GK-005 — performance intent → VI handoff

The plan now appears in normal prototype packages. Next:

1. define stable capability negotiation with `VI-*`;
2. migrate Ample knowledge into the provider-neutral VI schema without output changes;
3. let adapters consume generic plan intents only with legacy-neutral regression coverage.

### VI-002 — Ample knowledge migration

Move existing Ample facts from exporter-specific profile structures into the provider-neutral VI schema. Do not alter MIDI behavior as part of the migration. Verified vendor/plugin facts and learned calibration preferences must remain distinguishable.

## One-command validation package

Current command:

```bash
fretpilot prototype song.mid \
  --all-likely-guitars \
  -o output/
```

Per selected stream it produces analysis JSON, Guitar IR JSON, GP5 when supported, Ample MIDI, processing report, and Generic PerformancePlan sidecars/report enrichment.

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
