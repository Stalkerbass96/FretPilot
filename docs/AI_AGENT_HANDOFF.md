# FretPilot AI / Codex Handoff

> Consolidated: 2026-08-14
>
> This is the authoritative short handoff for an AI coding agent. Read `AGENTS.md` first, then this file. Detailed design lives in the specialized project docs linked below.

## 1. Product goal

FretPilot converts imperfect or AI-generated MIDI into two guitar-aware outputs:

1. **human-readable guitar notation/TAB**;
2. **performance MIDI for virtual guitar instruments**.

The engine must preserve source MIDI truth, infer/select guitar streams, infer musical behavior over time, choose guitarist-like string/fret/articulation decisions, build a canonical Guitar IR, then render score and performance outputs.

Current target scope is standard-tuned 6-string guitar. Current performance target is Ample Guitar SC 4.x, but the architecture must support more guitar instruments later.

## 2. Current runtime path — implemented baseline

```text
MIDI
→ NormalizedTimeline
→ InstrumentStream resolution
→ layered guitar detection
→ selected guitar stream
→ confidence-gated source-note rewrite (`midi_fidelity`, default 0.35)
→ rhythm / notation analysis
→ section segmentation
→ per-section behavior profiles
→ per-section PlayingContext
→ per-section fingering
→ per-section articulation
→ remap local indices to original source_note_index
→ merged GuitarTrackAnalysis
→ canonical Guitar IR
├──→ PDF/TAB preview
├──→ GP5
└──→ performance adapter
       └── Ample Guitar SC 4.x today
```

The one-command prototype package now uses the **section-aware path by default**.

## 3. Important current capabilities

Implemented and covered by tests/CI:

- MIDI Type 0 / Type 1 parsing;
- preservation of physical Track / Channel / Program / original ticks and timing;
- logical `InstrumentStream` resolution;
- three-layer guitar identity ranking;
- guitar-only product preflight with confidence, recommendations, low-confidence
  filtering, and same-track/channel Program-fragment grouping;
- separate experimental Layer-4 guitar behavior profiles;
- adjustable MIDI-fidelity vs guitar-reasonableness note rewriting, with stable
  source mapping and an explainable per-edit report;
- rhythm grid analysis and basic notation repair;
- measure coordinates and cross-measure ties;
- source/performance timing kept separate from score timing;
- standard six-string fretboard candidate generation;
- phrase-level fingering baseline;
- movable riff/arpeggio shape repair;
- simultaneous chord distinct-string solving;
- context-aware fingering soft costs;
- hammer-on / pull-off / slide / vibrato inference;
- context-aware articulation confidence weighting;
- section segmentation using measure windows + behavior feature change distance;
- independent `PlayingContext` per section;
- section-aware fingering/articulation execution and global note-index remapping;
- explicit section entry/exit hand-position state, weak-boundary continuity,
  strong-boundary resets, and explainable shift records;
- stable `section_id`-keyed context override hook for future user corrections;
- canonical Guitar IR v0.2 with project-level knowledge provenance;
- GP5 write + parse-back validation;
- safe unequal-chord voice separation and two-voice GP5 output;
- Ample Guitar SC MIDI renderer;
- PDF/TAB renderer supports independent V1/V2 rhythm rows and voice-aware
  pagination, but engraving quality is not yet musician-grade;
- generic `VirtualGuitarInstrumentProfile` schema skeleton;
- pinned versioned Knowledge Snapshot/registry with profile provenance;
- candidate reusable shape-library representation;
- knowledge snapshot and used-entry IDs in Guitar IR/reports;
- multi-guitar one-command prototype package including PDF review output.
- responsive React/TypeScript frontend and `Quiet Studio 0.1` design-system
  baseline with local file/output preferences, a read-only knowledge review
  console, and browser-validated layouts.

The last code-level product regression for section-aware prototype packaging passed CI. Always verify current HEAD CI before merging new changes.

## 4. Current known limitations

Do not mistake these for implemented features:

- Section behavior labels are still hand-authored experimental rules, not calibrated truth.
- Section boundaries use explicit strength to choose hand-position carry or reset.
- Hand-position state is a deterministic baseline and still needs calibration
  against reviewed real-song fingerings.
- No left-hand finger numbers / barre / thumb-over planning.
- `PerformancePreferences` exist in PlayingContext but do not yet drive a generic performance plan.
- Knowledge snapshot and used profile IDs are persisted, but stable
  region-to-individual-decision provenance is not yet complete.
- PDF/TAB is still primarily a review renderer, not Guitar Pro / Songsterr-quality engraving.
- Two-voice notation currently covers safe unequal chord releases in GP5 and
  PDF/TAB; general contrapuntal voice separation remains incomplete.
- Bend/vibrato performance rendering is incomplete.
- Ample is the only implemented virtual-guitar target.
- Track identification is useful but intentionally not treated as finished.
- The frontend cannot yet override the automatic guitar-only selection; short
  likely parts are labeled optional but remain selected.
- The frontend is connected to a local Python job API, but project/job metadata
  is not yet persistent across server restarts.

## 5. Task families

Use existing prefixes rather than creating duplicate work:

```text
PV-*  prototype/output validation and immediate musician-facing quality
TI-*  InstrumentStream / guitar-track identification
GK-*  guitarist-like playing knowledge, style, phrasing, fingering, articulation
VI-*  virtual-guitar product knowledge, capabilities, adapters, compatibility
SE-*  evaluation, feedback, reproducibility, knowledge/model evolution governance
```

Detailed backlogs:

```text
docs/ROADMAP.md

docs/projects/track-identification/BACKLOG.md
docs/projects/guitar-playing-knowledge/BACKLOG.md
docs/projects/virtual-guitar-instruments/BACKLOG.md
docs/projects/system-evolution/BACKLOG.md
```

## 6. Core architectural boundaries — do not violate

### Instrument identity vs playing behavior

```text
Layers 1–3 = is this likely guitar?
Layer 4 / PlayingContext = what kind of guitar behavior/style is happening?
```

Layer 4 must not override instrument identity.

### Guitar knowledge vs plugin knowledge

```text
GK = how a real guitarist would likely play
VI = how a target software instrument must be controlled
```

Do not put Ample keyswitches, CCs, state-machine rules, or product limitations into Guitar Playing Knowledge or canonical Guitar IR.

### Hard constraints vs soft knowledge

Physical fretboard/playability/file-format validity are hard deterministic constraints.

Style/role/knowledge/ML systems may rank valid alternatives but must not bypass physical constraints.

### Score vs performance

Score timing and source/performance timing are separate representations. Do not destroy original performance timing to make notation cleaner.

### Runtime vs learning

Runtime uses approved/versioned knowledge and adapter profiles. Internet/user data may feed an offline candidate/evaluation/promotion loop later; runtime must not silently self-modify while processing a song.

## 7. Canonical long-term knowledge domains

### TI — Instrument / Track Knowledge

Answers: **which logical stream is guitar?**

### GK — Guitar Playing Knowledge

Answers: **how would a real guitarist likely play this section?**

Composable dimensions stay separate:

```text
role: solo / riff / strumming / comping / ...
style: metal / rock / jazz / blues / ...
technique family: legato / arpeggio / sweep / fingerstyle / ...
```

### VI — Virtual Guitar Instrument Knowledge

Answers: **how must a particular plugin/version be controlled to realize canonical guitar intent?**

### SE — Evaluation / Learning Knowledge

Answers: **did a new heuristic/profile/model/adapter actually improve the system, and can it be reproduced/rolled back?**

## 8. Recommended next work for Codex

If the user does not specify another task, prefer one of these in order.

### A. `PV-002` — musician-readable PDF/TAB

The renderer exists but output is not yet comparable to normal playable TAB.

Focus on:

- rhythmic stems/beams;
- proportional musical spacing;
- rests/ties/slides/let-ring notation;
- readable measure/system layout;
- section-aware phrase spacing;
- visual golden fixtures.

Do not solve engraving by changing musical analysis merely to make the page prettier.

### B. `GK-013` — Hand-position calibration

**The state/transition baseline is implemented. Calibrate it before expanding
the model.**

Current behavior already estimates section entry/exit hand state, carries state
across weak boundaries, resets at strong boundaries, and records transition
cost/reason. Remaining work is reviewed-song calibration, reusable shape state,
and future finger/barre state.

Primary files:

```text
src/fretpilot/analysis/section_aware.py
src/fretpilot/guitar/fingering.py
src/fretpilot/guitar/models.py
src/fretpilot/knowledge/playing_contexts.py
tests/test_section_aware_analysis.py
```

### C. Generic Performance Plan — finish `GK-002` through `GK-005`

`PerformancePreferences` currently exist but do not affect a canonical performance-intent layer.

Target flow:

```text
Guitar IR / section PlayingContext
→ generic PerformancePlan
→ target capability negotiation
→ Ample / future adapter
```

The generic plan may describe timing feel, accent, overlap, pick/strum intent, etc. Product-specific keyswitch/CC translation stays in `VI-*`.

Do not let Ample-specific behavior define the generic model.

### D. `VI-002` — migrate Ample profile to generic VI schema

Preserve current Ample output exactly while moving static product knowledge into the provider-neutral profile schema. Add conformance tests before adding a second product.

## 9. Files to inspect first

### Section-aware playing path

```text
src/fretpilot/analysis/guitar.py
src/fretpilot/analysis/sections.py
src/fretpilot/analysis/section_contexts.py
src/fretpilot/analysis/section_aware.py
src/fretpilot/knowledge/playing_contexts.py
src/fretpilot/guitar/fingering.py
src/fretpilot/articulation/planner.py
src/fretpilot/ir/models.py
src/fretpilot/ir/builder.py
src/fretpilot/prototype.py
```

### Tests most relevant to the current music-intelligence path

```text
tests/test_guitar_analysis.py
tests/test_section_segmentation.py
tests/test_section_aware_analysis.py
tests/test_guitar_fingering.py
tests/test_guitar_ir_builder.py
tests/test_prototype_package.py
```

### Product / architecture docs

```text
docs/ROADMAP.md
docs/LONG_TERM_ARCHITECTURE.md
docs/projects/guitar-playing-knowledge/BACKLOG.md
docs/projects/virtual-guitar-instruments/BACKLOG.md
```

## 10. Current prototype command

```bash
fretpilot prototype song.mid \
  --all-likely-guitars \
  -o output/
```

Each selected stream receives analysis, Guitar IR, PDF and GP5 when supported,
Ample MIDI, and a processing report. Analysis/report include section-context
summaries and independent output status.

For section diagnostics:

```bash
fretpilot sections song.mid \
  --stream-id t0:ch2:p27
```

## 11. Required coding-agent workflow

For every nontrivial change:

1. Read `AGENTS.md`, this handoff, and the narrow relevant backlog.
2. Inspect current code/tests before assuming docs are exact implementation truth.
3. Reuse a stable task ID where possible.
4. Add/update regression tests before changing scoring, fingering, knowledge, or adapter mappings.
5. Preserve source timing and global `source_note_index` identity through section/local processing.
6. Preserve neutral/default behavior unless the task explicitly changes it.
7. Run the full test suite / CI.
8. Update only the narrow authoritative docs that changed.
9. Do not claim improved accuracy or guitarist-likeness without evidence/golden review.
10. Do not broaden scope into track-identification perfection or web-learning infrastructure unless explicitly requested.

## 12. Product priority summary

Short term:

```text
better musician-readable output
+ better guitarist-like execution
+ useful human review/correction
```

Medium term:

```text
hand/shape knowledge
+ generic performance intent
+ multi-plugin adapter architecture
```

Long term:

```text
versioned Guitar Playing Knowledge
+ versioned Virtual Instrument Knowledge
+ licensed/approved learning data
+ evaluation / candidate / promotion loop
```

The long-term learning system must not block useful Prototype 0.1 iteration.
