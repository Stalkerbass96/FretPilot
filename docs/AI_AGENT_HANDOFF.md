# FretPilot AI / Codex Handoff

> Consolidated: 2026-08-14
>
> This is the authoritative short handoff for an AI coding agent. Read `AGENTS.md` first, then this file. Detailed task truth lives in the specialized backlogs.

## 1. Product goal

FretPilot converts imperfect or AI-generated MIDI into two guitar-aware outputs:

1. **human-readable guitar notation/TAB**;
2. **performance data for virtual guitar instruments**.

The engine preserves source MIDI truth, resolves logical instrument streams, identifies likely guitars, infers musical behavior over time, chooses guitarist-like fretboard/articulation decisions, builds canonical Guitar IR, then renders score and performance outputs.

Current scope is standard-tuned six-string guitar. Current implemented performance target is Ample Guitar SC 4.x, but the architecture must support multiple virtual-guitar products.

## 2. Current runtime path

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
→ weak/strong-boundary hand-position continuity baseline
→ per-section articulation
→ remap local indices to original source_note_index
→ merged GuitarTrackAnalysis
→ canonical Guitar IR + section/hand-position provenance
├──→ PDF/TAB preview
├──→ GP5
└──→ current Ample Guitar SC renderer
```

A target-neutral performance-intent layer now also exists as an API baseline:

```text
Guitar IR + PlayingContext.performance
→ Generic PerformancePlan
→ [future VI capability negotiation]
→ [future adapter consumption]
```

The current Ample renderer does **not** consume `PerformancePlan` yet; preserving existing Ample output is intentional until tests/integration are ready.

## 3. Important implemented capabilities

- MIDI Type 0 / Type 1 parsing;
- preservation of Track / Channel / Program / ticks / original timing;
- logical `InstrumentStream` resolution;
- explainable three-layer guitar identity ranking;
- separate experimental Layer-4 guitar behavior profiles;
- rhythm grid analysis and notation cleanup;
- score timing separated from source/performance timing;
- measure coordinates and cross-measure ties;
- standard six-string fretboard candidates;
- phrase-level fingering baseline;
- movable riff/arpeggio shape repair;
- simultaneous chord distinct-string solving;
- `PlayingContext`-aware fingering soft costs;
- hammer-on / pull-off / slide / vibrato inference;
- context-aware articulation confidence weighting;
- deterministic section segmentation;
- independent `PlayingContext` per section;
- section-aware fingering/articulation execution with global source-index remapping;
- stable `section_id`-keyed context overrides;
- explicit hand-position state baseline with weak-boundary carry / strong-boundary reset policy;
- Guitar IR v0.1 with section-context and hand-position provenance through the public builder;
- target-neutral `PerformancePlan` models/planner baseline;
- GP5 write + parse-back validation;
- PDF/TAB review renderer;
- Ample Guitar SC MIDI renderer;
- provider-neutral `VirtualGuitarInstrumentProfile` schema skeleton;
- multi-guitar one-command prototype package.

The latest code baseline for the new hand-position/performance modules passed the full existing CI suite. Recheck HEAD CI after making changes.

## 4. Current limitations / active cleanup

Do not mistake these for completed production features:

- Section behavior labels are hand-authored experimental rules, not calibrated truth.
- `GK-013` hand-position continuity is an **integrated baseline**, not a mature model. The current weak-boundary threshold is heuristic and still needs focused regressions and real-song/golden evaluation.
- `src/fretpilot/analysis/section_aware.py` still contains the older reset-only implementation. Package-level imports already use `section_execution.py`, but a direct import from the old module can observe stale behavior. **Replace the old module with a compatibility re-export as an early cleanup task.**
- Dedicated weak-boundary-carry / strong-boundary-reset tests are still pending.
- No true left-hand finger numbers, barre, stretch model, or thumb-over planning yet.
- Generic `PerformancePlan` exists, but it is not yet emitted by the prototype package and is not consumed by Ample/VI adapters.
- Dedicated neutral-vs-context `PerformancePlan` behavior tests are pending.
- PDF/TAB is still a review renderer, not musician-grade engraving.
- No true two-voice notation yet.
- Bend/vibrato performance rendering is incomplete.
- Ample is the only implemented virtual-guitar target.
- `VI-002` migration of Ample facts into the generic VI profile is still pending.
- Track identification is useful but intentionally not treated as finished.

## 5. Task families

```text
PV-*  prototype/output validation and musician-facing quality
TI-*  InstrumentStream / guitar-track identification
GK-*  guitarist-like playing knowledge, style, phrasing, fingering, articulation, performance intent
VI-*  virtual-guitar product knowledge, capabilities, adapters, compatibility
SE-*  evaluation, feedback, reproducibility, knowledge/model evolution governance
```

Authoritative task docs:

```text
docs/ROADMAP.md
docs/projects/track-identification/BACKLOG.md
docs/projects/guitar-playing-knowledge/BACKLOG.md
docs/projects/virtual-guitar-instruments/BACKLOG.md
docs/projects/system-evolution/BACKLOG.md
```

## 6. Architectural boundaries — do not violate

### Instrument identity vs playing behavior

```text
Layers 1–3 = is this likely guitar?
Layer 4 / PlayingContext = what guitar behavior/style is happening?
```

Layer 4 must not override instrument identity.

### Guitar knowledge vs plugin knowledge

```text
GK = how a real guitarist would likely play
VI = how a target software instrument must be controlled
```

Never put product keyswitches, CCs, MIDI control notes, latch/reset rules, or plugin limitations into Guitar Playing Knowledge or canonical Guitar IR.

### Hard constraints vs soft knowledge

Physical fretboard/playability and file-format validity are deterministic hard constraints. Style/role/knowledge/ML may rank valid alternatives but never bypass those constraints.

### Score vs performance

Score timing and source/performance timing are separate. Do not destroy source performance timing to make notation prettier.

### Runtime vs learning

Runtime uses approved/versioned musical knowledge and adapter profiles. Web/user data may feed a controlled offline candidate/evaluation/promotion loop later; runtime never silently self-modifies while processing a song.

## 7. Long-term knowledge assets

### TI — Instrument / Track Knowledge

Answers: **which logical stream is guitar?**

### GK — Guitar Playing Knowledge

Answers: **how would a real guitarist likely play this section?**

Composable dimensions remain separate:

```text
role: solo / riff / strumming / comping / ...
style: metal / rock / jazz / blues / ...
technique family: legato / arpeggio / sweep / fingerstyle / ...
```

### VI — Virtual Guitar Instrument Knowledge

Answers: **how must a specific plugin/version be controlled to realize canonical guitar intent?**

### SE — Evaluation / Learning Knowledge

Answers: **did a new heuristic/profile/model/adapter actually improve the system, and can it be reproduced or rolled back?**

## 8. Recommended next work for Codex

If the user gives no more specific task, continue existing work rather than rebuilding it.

### A. Small P0 cleanup + regressions

1. Replace `src/fretpilot/analysis/section_aware.py` with a compatibility re-export of `section_execution.py` so there is one execution truth.
2. Add focused tests for:
   - weak boundary carries prior hand position;
   - strong boundary resets;
   - replacements remain physically playable and simultaneous strings distinct;
   - `HandPositionState.section_id` aligns with section contexts;
   - public Guitar IR contains section contexts and hand-position provenance.
3. Add `PerformancePlan` tests proving:
   - neutral preferences preserve source timing/duration/velocity;
   - non-neutral section preferences produce deterministic target-neutral changes;
   - no VI/product control information exists in generic plan models.

### B. Finish `GK-005` product integration

Expose Generic PerformancePlan in prototype/report output before letting any VI adapter consume it.

Preferred transition:

```text
Guitar IR
→ Generic PerformancePlan
→ review/evaluation
→ VI capability negotiation
→ adapter
```

Do not change Ample MIDI output until neutral behavior and adapter handoff have regression coverage.

Primary files:

```text
src/fretpilot/performance/models.py
src/fretpilot/performance/planner.py
src/fretpilot/prototype.py
src/fretpilot/virtual_instruments/
```

### C. Continue `GK-013` evaluation / richer state

Current hand-position code is in:

```text
src/fretpilot/guitar/hand_position.py
src/fretpilot/analysis/section_execution.py
```

Next improvements should evaluate/tune the boundary threshold and entry-window policy using golden/real-song evidence, then evolve toward richer position/span/shape-transition state rather than adding arbitrary penalties.

Keep the existing Message-in-a-Bottle movable-arpeggio golden regression green.

### D. `PV-002` musician-readable PDF/TAB

Improve rhythmic stems/beams, musical spacing, rests/ties/slides/let-ring notation, section-aware phrase spacing, and visual golden fixtures. Do not alter music analysis solely to beautify engraving.

### E. `VI-002` Ample profile migration

Move current Ample product facts into the provider-neutral VI profile schema **without changing existing MIDI render output**. Add conformance/regression coverage before adding a second product.

## 9. Files to inspect first

### Current guitar-intelligence path

```text
src/fretpilot/analysis/guitar.py
src/fretpilot/analysis/sections.py
src/fretpilot/analysis/section_contexts.py
src/fretpilot/analysis/section_execution.py
src/fretpilot/analysis/section_aware.py   # stale compatibility issue; do not extend
src/fretpilot/knowledge/playing_contexts.py
src/fretpilot/guitar/fingering.py
src/fretpilot/guitar/hand_position.py
src/fretpilot/articulation/planner.py
```

### IR / performance

```text
src/fretpilot/ir/models.py
src/fretpilot/ir/builder.py
src/fretpilot/ir/project_builder.py
src/fretpilot/performance/models.py
src/fretpilot/performance/planner.py
src/fretpilot/prototype.py
```

### Virtual instruments

```text
src/fretpilot/virtual_instruments/models.py
src/fretpilot/exporters/ample_guitar/profiles.py
src/fretpilot/exporters/ample_guitar/renderer.py
docs/projects/virtual-guitar-instruments/
```

### Relevant tests

```text
tests/test_guitar_analysis.py
tests/test_section_segmentation.py
tests/test_section_aware_analysis.py
tests/test_guitar_fingering.py
tests/test_guitar_ir_builder.py
tests/test_prototype_package.py
tests/test_ample_guitar_renderer.py
```

## 10. Current prototype commands

Full package:

```bash
fretpilot prototype song.mid \
  --all-likely-guitars \
  -o output/
```

Current package includes analysis, Guitar IR, GP5 when supported, Ample MIDI, and processing report. Generic PerformancePlan is **not yet included**.

Section diagnostics:

```bash
fretpilot sections song.mid \
  --stream-id t0:ch2:p27
```

## 11. Required coding-agent workflow

For every nontrivial change:

1. Read `AGENTS.md`, this handoff, and the narrow relevant backlog.
2. Inspect current code/tests; code and green regressions are implementation truth.
3. Reuse stable task IDs.
4. Add/update regression tests before changing scoring, fingering, knowledge, or adapter mappings.
5. Preserve source timing and global `source_note_index` through local/section processing.
6. Preserve neutral/default behavior unless the task explicitly changes it.
7. Run the full suite / CI.
8. Update only the narrow authoritative docs that changed.
9. Do not claim improved accuracy or guitarist-likeness without evidence/golden review.
10. Do not broaden scope into track-identification perfection or web-learning infrastructure unless explicitly requested.

## 12. Priority summary

Immediate:

```text
single section-execution truth
+ focused GK-013/GK-005 regressions
+ expose Generic PerformancePlan for review
```

Then:

```text
musician-readable TAB/PDF
+ richer hand/shape knowledge
+ VI-002 Ample migration
```

Long term:

```text
versioned Guitar Playing Knowledge
+ versioned Virtual Instrument Knowledge
+ licensed/approved learning data
+ evaluation / candidate / promotion loop
```

The long-term learning system must not block useful Prototype 0.1 iteration.
