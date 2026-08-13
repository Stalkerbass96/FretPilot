# Guitar Playing Knowledge Backlog

Stable task IDs use the `GK-` prefix.

This backlog is the task-level source of truth for guitarist-like behavior. Keep plugin/product control facts in `VI-*`, not here.

## P0 — knowledge interface and runtime flow

### GK-001 — PlayingContext model

Status: **implemented**

Role, style, and technique-family dimensions remain separate and composable. Profiles merge into fingering, articulation, and performance preferences. Existing Layer-4 behavior matches can be bridged into `PlayingContext`.

### GK-002 — thread PlayingContext through analysis

Status: **in progress; fingering/articulation/IR path implemented**

Implemented flow:

```text
InstrumentStream
→ section segmentation
→ section behavior profiles
→ section PlayingContext
→ per-section fingering
→ hand-position continuity baseline
→ per-section articulation
→ remap to stream-wide source_note_index
→ GuitarTrackAnalysis
→ Guitar IR provenance
```

The one-command prototype uses the section-aware path by default.

Remaining:

- finish `GK-005` product-path integration;
- add stronger regression/golden evidence for hand-position continuity;
- keep knowledge/version provenance explicit as schemas evolve.

Acceptance:

- neutral/default context preserves existing behavior;
- explicit/derived context remains traceable through analysis and Guitar IR;
- no output adapter invents style rules;
- source timing and stable source-note identity survive section-local processing.

### GK-003 — preference-aware fingering costs

Status: **implemented baseline**

Current preferences affect valid-candidate ranking for adjacent-string arpeggios, same-string legato, hand-position stability, shape reuse, open strings, compact voicing, low-register bias, and wide-interval position shifts.

Physical fretboard constraints remain hard constraints. Learned/statistical ranking remains `GK-040+`.

### GK-004 — articulation planner consumes context

Status: **implemented baseline**

Context confidence-weights already-valid hammer/pull, slide, and vibrato decisions. It does not invent techniques merely because a style prefers them. Palm mute, bend, staccato, etc. still require their own eligibility evidence.

### GK-005 — generic Performance Plan consumes PerformancePreferences

Status: **API/planner baseline implemented; product integration and dedicated tests pending**

Current code:

```text
src/fretpilot/performance/models.py
src/fretpilot/performance/planner.py
```

Implemented target-neutral intent includes:

- source and target timing;
- timing tightening/loosening intent;
- source and target velocity;
- deterministic velocity variation/evening;
- metric accent strength;
- note-overlap intent;
- section/PlayingContext provenance;
- reasons/deltas for explainability.

Neutral preferences are designed to preserve source timing, duration, and velocity. No keyswitch, CC, vendor MIDI note, latch/reset state, or product mapping belongs in this plan.

Still pending:

- dedicated neutral-vs-context regression tests;
- expose the plan in prototype/report output;
- define the stable handoff from `PerformancePlan` to `VI-*` capability negotiation;
- only after the above, let Ample/future adapters consume the generic plan without changing canonical musical meaning.

Target flow:

```text
Guitar IR + time-varying PlayingContext
→ Generic PerformancePlan
→ VI capability negotiation
→ Ample / future virtual-guitar adapter
```

## P1 — phrase / fretboard-state knowledge

### GK-010 — section/phrase segmentation

Status: **implemented baseline**

Current deterministic baseline:

```text
InstrumentStream + time-signature map
→ measure windows
→ behavior features
→ normalized feature distance
→ change boundaries
→ merge adjacent similar windows
→ GuitarSection
```

Sections now retain both a bounded `boundary_confidence` and an unbounded normalized `boundary_strength`. The latter lets downstream planners distinguish a boundary that barely crossed the split threshold from a much stronger musical change.

Segmentation answers **where behavior changes**; semantic interpretation remains GK-011.

### GK-011 — phrase-level behavior classification

Status: **implemented experimental baseline**

The current Layer-4 behavior library runs independently per `GuitarSection`. All matches remain available for diagnostics; only sufficiently strong matches contribute to that section's `PlayingContext`.

Important limitation: current profiles are hand-authored experimental rules, not calibrated musical truth.

### GK-012 — shape memory

Status: **not started**

Represent reusable fretboard shape prototypes independent of absolute root fret, including sus2 arpeggios, power chords, octave shapes, triad inversions, and jazz shell voicings.

The Message-in-a-Bottle movable sus2/arpeggio regression remains an important golden reference for this work.

### GK-013 — hand-position state

Status: **integrated baseline; focused regression/evaluation still pending**

Current code:

```text
src/fretpilot/guitar/hand_position.py
src/fretpilot/analysis/section_execution.py
```

Implemented baseline:

- explicit `HandPositionState` per executed section;
- section entry/exit fret center;
- min/max fret span summary;
- previous-section exit position;
- shift amount and transition cost/reason;
- weak-boundary carry versus strong-boundary reset;
- default carry threshold currently uses normalized `boundary_strength <= 1.35`;
- a short section-entry repair window re-ranks only canonical playable fretboard candidates;
- simultaneous notes still require distinct strings;
- open strings do not incorrectly force the fretting-hand center to fret zero;
- analysis exposes `hand_positions` and the public section-aware API uses this execution path;
- Guitar IR public builder now persists hand-position provenance.

Still pending before calling GK-013 mature:

- dedicated weak-boundary-carry / strong-boundary-reset tests;
- real-song and golden-tab evaluation of the 1.35 threshold and entry-window policy;
- richer hand-center/span state beyond the current summary/entry repair;
- context/shape-aware transition scoring;
- remove the duplicate legacy implementation in `src/fretpilot/analysis/section_aware.py` or replace it with a compatibility re-export. **Package-level APIs already use `section_execution.py`; direct imports from the old module can still observe legacy reset-only behavior.**

Physical/playability constraints remain deterministic.

### GK-014 — left-hand finger assignment

Status: **not started**

Add finger numbers, barre representation, stretch feasibility, and optional thumb-over techniques. Do not conflate string/fret position with true left-hand fingering.

### GK-015 — section-aware execution and merge

Status: **implemented baseline**

Current behavior:

- solve fingering/articulation with each section's `PlayingContext`;
- selectively carry hand-position state across weak section boundaries;
- remap section-local note indices back to original stream-wide indices;
- preserve global source timing;
- support stable `section_id`-keyed context overrides for future user corrections;
- one-command prototype generation uses the package-level section-aware path.

## P2 — expand style knowledge

### GK-020 — metal family

Status: **planned**

Reusable subprofiles: tight rhythm riff, breakdown, tremolo picking, metal lead/solo, modern low-tuned riff.

### GK-021 — rock/pop family

Status: **planned**

Open-chord rhythm, movable arpeggio, power-chord riff, melodic lead.

### GK-022 — jazz family

Status: **planned**

Shell voicing, drop-2/drop-3 tendencies, comping voice leading, single-note jazz lead.

### GK-023 — blues family

Status: **planned**

Pentatonic-box behavior, bend targets, vibrato patterns, double stops.

### GK-024 — funk family

Status: **planned**

Muted sixteenth-note rhythm, partial chords, percussive articulation, tight position reuse.

### GK-025 — fingerstyle/acoustic family

Status: **planned**

Bass/melody separation, alternating bass, open-string resonance, chord-melody voicing.

## P3 — learning infrastructure

### GK-030 — source provenance schema

Define source/license/permission/quality metadata for every learning batch.

### GK-031 — symbolic tab normalizer

Normalize eligible GP/MusicXML/other symbolic sources into an internal learning representation.

### GK-032 — knowledge feature extractor

Extract aggregate fretboard, phrase, articulation, and style-conditioned statistics.

### GK-033 — deduplication and source-family weighting

Prevent copied/derived tabs from dominating learned priors.

### GK-034 — quality estimator

Score structural validity, fretboard validity, notation consistency, metadata quality, and source confidence.

### GK-035 — knowledge snapshot format

Version learned profiles separately from application code.

### GK-036 — candidate/evaluation/promotion workflow

Learned data creates a candidate snapshot first; production stays pinned to the last approved snapshot.

## P4 — learned fingering ranker

### GK-040 — regression evaluation corpus

Metrics should include exact string/fret agreement, shape-family agreement, average hand shift, fret-span cost, impossible fingering rate, and phrase-level path score.

### GK-041 — statistical candidate ranker

Start with interpretable learned weights before sequence models.

### GK-042 — sequence-level fretboard model

Rank complete phrase fingering paths while deterministic constraints prune impossible candidates.

### GK-043 — knowledge retrieval

Retrieve similar approved shape/phrase prototypes to inform ranking without storing arbitrary internet content in runtime profiles.

## Guardrails

- Do not silently change production knowledge from newly ingested data.
- Do not treat one published tab as canonical truth.
- Do not ingest or redistribute internet content without an appropriate legal basis.
- Preserve source provenance and knowledge-version reproducibility.
- Keep physical/playability validation deterministic.
- Learned models rank candidates; they do not bypass hard guitar constraints.
- Keep Guitar Playing Knowledge separate from target virtual-instrument control knowledge (`VI-*`).
