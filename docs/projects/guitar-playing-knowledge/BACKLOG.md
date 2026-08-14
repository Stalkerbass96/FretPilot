# Guitar Playing Knowledge Backlog

Stable task IDs use the `GK-` prefix.

This backlog is the task-level source of truth for guitarist-like behavior. Keep plugin/product control facts in `VI-*`, not here.

## P0 — knowledge interface and runtime flow

### GK-001 — PlayingContext model

Status: **implemented**

Role, style, and technique-family dimensions remain separate and composable. Profiles merge into fingering, articulation, performance, and downstream score-strategy preferences. Existing Layer-4 behavior matches can be bridged into `PlayingContext`.

### GK-002 — thread PlayingContext through analysis

Status: **implemented baseline; VI handoff still pending**

Current flow:

```text
InstrumentStream
→ section segmentation
→ section behavior/style evidence
→ section PlayingContext
→ final fingering + hand-position/voicing continuity
→ fretting-digit assignment
→ articulation + explicit pitch-wheel gesture interpretation
→ right-hand PickingPlan
→ stream-wide source_note_index remap
→ GuitarTrackAnalysis
→ Guitar IR provenance/strategy/right-hand/fretting metadata
```

The normal prototype uses the public section-aware analysis path. A separate one-command product entry, `fretpilot-prototype-performance`, additionally writes target-neutral PerformancePlan JSON sidecars.

Remaining:

- define the stable `PerformancePlan → VI-*` capability-negotiation handoff;
- merge PerformancePlan sidecars into the ordinary prototype command/manifest after the sidecar format stabilizes;
- keep knowledge/version provenance explicit as schemas evolve.

Acceptance:

- neutral/default context preserves deterministic baseline behavior;
- explicit/derived context remains traceable through analysis and Guitar IR;
- context overrides affect left-hand, articulation, and right-hand planning consistently;
- no output adapter invents style rules;
- source timing and stable source-note identity survive section-local processing.

### GK-003 — preference-aware fingering costs

Status: **implemented baseline**

Current preferences affect valid-candidate ranking for adjacent-string arpeggios, same-string legato, hand-position stability, shape reuse, open strings, compact voicing, low-register bias, and wide-interval position shifts.

Physical fretboard constraints remain hard constraints. Learned/statistical ranking remains `GK-040+`.

### GK-004 — articulation planner consumes context

Status: **implemented baseline**

Current deterministic/context-aware articulation includes:

- hammer-on / pull-off;
- slide;
- vibrato;
- contextual staccato;
- contextual palm mute;
- explicit-range, monophonic MIDI pitch-wheel `pitch_raise` gestures with semitone and curve-timing parameters.

Style/context can confidence-weight eligible techniques, but does not invent them. Pitch-wheel interpretation requires an explicit RPN range and an unambiguous monophonic source stream; missing range or overlapping notes abstain.

The GP5 adapter maps `pitch_raise` parameters to a Guitar Pro pitch curve only after the target-neutral musical decision exists in Guitar IR.

### GK-005 — generic Performance Plan consumes PerformancePreferences

Status: **implemented product baseline; VI consumption pending**

Current code:

```text
src/fretpilot/performance/models.py
src/fretpilot/performance/planner.py
src/fretpilot/performance/json_export.py
src/fretpilot/prototype_performance_cli.py
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

Neutral preferences preserve source timing, duration, and velocity. Dedicated neutral/context regressions lock this contract and verify that canonical Guitar IR is not mutated by PerformancePlan construction.

Product entry:

```text
fretpilot-prototype-performance INPUT.mid OUTPUT_DIR
```

This generates the normal prototype package plus per-stream `.performance-plan.json` sidecars and a `performance-plans.json` index. The normal `fretpilot prototype` command is intentionally unchanged for backward compatibility while the sidecar format stabilizes.

Still pending:

- define the stable handoff from `PerformancePlan` to `VI-*` capability negotiation;
- merge the sidecar/status into the ordinary prototype manifest;
- only after that, let Ample/future adapters consume the generic plan without changing canonical musical meaning.

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

Sections retain both bounded `boundary_confidence` and unbounded normalized `boundary_strength`. Segmentation answers **where behavior changes**; semantic interpretation remains GK-011.

### GK-011 — phrase-level behavior classification

Status: **implemented experimental baseline**

The current Layer-4 behavior library runs independently per `GuitarSection`. All matches remain available for diagnostics; only sufficiently strong matches contribute to the section `PlayingContext`.

Current behavior vocabulary includes solo/lead, riff, strumming, breakdown/heavy-low behavior, jazz comping, and an arpeggio baseline used by the section-aware guitar path.

Important limitation: current profiles are hand-authored experimental rules, not calibrated musical truth.

### GK-012 — shape memory

Status: **not started as a first-class reusable shape model**

Existing fingering already contains local movable-arpeggio/riff-shape reuse and chord-voicing continuity, but there is not yet a versioned reusable shape-prototype representation independent of absolute root fret.

Future shape memory should include sus2 arpeggios, power chords, octave shapes, triad inversions, and jazz shell voicings. The Message-in-a-Bottle movable sus2 regression remains an important golden reference.

### GK-013 — hand-position state

Status: **implemented baseline; real-song calibration pending**

Current code:

```text
src/fretpilot/guitar/hand_position.py
src/fretpilot/analysis/section_execution.py
```

Implemented:

- explicit `HandPositionState` per executed section;
- section entry/exit fret center;
- min/max fret span summary;
- previous-section exit position;
- shift amount and transition cost/reason;
- weak-boundary carry versus strong-boundary reset;
- default carry threshold currently uses normalized `boundary_strength <= 1.35`;
- short section-entry repair re-ranks only canonical playable candidates;
- simultaneous notes still require distinct strings;
- open strings do not force the fretting-hand center to fret zero;
- Guitar IR persists hand-position provenance;
- focused regressions prove that a weak boundary changes the real final fingering to a carried position, while a strong boundary allows a local reset.

The old duplicate `analysis/section_aware.py` implementation has been removed in favor of a compatibility re-export; the canonical execution logic lives in `section_execution.py`.

Still pending before calling GK-013 mature:

- real-song and golden-tab evaluation of the `1.35` threshold and entry-window policy;
- richer hand-center/span state beyond the current summary/entry repair;
- context/shape-aware transition scoring.

### GK-014 — fretting-digit assignment

Status: **implemented baseline**

Implemented:

- deterministic 1–4 `fretting_digit` assignment after final string/fret selection;
- open strings and unplayable/ambiguous cases remain unspecified;
- clear movable-shape resets restart the local digit anchor;
- simultaneous shapes with excessive span remain unspecified rather than forcing impossible digits;
- Message-in-a-Bottle-style movable sus2 regression reuses the expected digit family;
- `fretting_digit` is persisted in canonical `IRFingering`;
- Guitar IR JSON round-trip preserves the digit;
- GP5 maps 1/2/3/4 to index/middle/annular/little and has parse-back coverage;
- GP5 prefers the persisted IR digit and only derives a fallback for older/manual IR.

Still pending:

- first-class barre representation;
- explicit stretch-feasibility model beyond conservative abstention;
- optional thumb-over/thumb-fretting techniques;
- richer chord-wide digit solving for difficult voicings.

### GK-015 — section-aware execution and merge

Status: **implemented baseline**

Current behavior:

- solve fingering/articulation with each section's `PlayingContext`;
- selectively carry hand-position state across weak section boundaries;
- apply chord/voicing strategy after final position carry;
- assign fretting digits after final string/fret choices;
- remap section-local note indices back to original stream-wide indices;
- preserve global source timing;
- support stable `section_id`-keyed context overrides;
- public section-aware analysis also builds right-hand PickingPlan using the same context override;
- normal one-command prototype generation uses this public section-aware path.

### GK-016 — right-hand picking/strum intent

Status: **implemented baseline**

Target-neutral `PickingPlan` currently recognizes only when deterministic evidence is strong enough:

- tight low-register metal/riff figures → repeated downstrokes;
- slower arpeggio/single-note passages → alternate down/up picking;
- very rapid repeated same-pitch runs → `tremolo` technique plus alternate directions;
- fast monotonic adjacent-string arpeggio runs → `sweep` technique plus one-direction motion;
- chord onsets in strumming context → chord-level strum motion/direction.

`PICKING_RESEARCH` is consumed only as a confidence prior after timing/fingering evidence passes. Neutral/no-context analysis does not invent picking direction.

Guitar IR persists motion, direction, confidence, reason, and optional `tremolo`/`sweep` technique provenance. GP5 currently writes safe beat-level pick direction. It deliberately does not add a GP tremolo subdivision effect when source MIDI already contains explicit repeated notes, and it does not invent rolled-strum timing for simultaneous chord onsets.

Pending:

- infer rolled-strum timing only from real staggered-onset evidence;
- add hybrid-picking inference only when bass/treble separation and string-skip evidence are strong;
- real-song threshold calibration.

### GK-017 — explicit pitch-wheel gesture preservation

Status: **implemented positive-raise baseline**

Package-level MIDI loading preserves raw pitch-wheel events and RPN 0/0 wheel-range events. The guitar analysis path emits `pitch_raise` only when:

- the wheel range is explicitly declared;
- the selected stream is monophonic at the gesture peak;
- the gesture is a meaningful positive raise;
- source timing can be attached to one note unambiguously.

The analysis/IR keeps semitone amount, wheel range, peak timing, return timing, and whether the wheel returned to center. GP5 maps this to a parse-back-tested pitch curve.

Pending:

- negative/downward gestures;
- pre-raise/pre-bend interpretation;
- richer multi-point wheel-curve preservation;
- product/profile-specific policies in VI adapters, not in Guitar IR.

## P2 — expand style knowledge

### GK-020 — metal family

Status: **partial baseline; family expansion planned**

Already available mechanisms include low-register riff priors, palm mute/staccato evidence, downstroke intent, rapid repeated-note tremolo picking, and position/shape stability. Still planned: more calibrated subprofiles for tight rhythm, breakdowns, metal lead/solo, and modern low-tuned riffing.

### GK-021 — rock/pop family

Status: **partial baseline; family expansion planned**

Current style priors and arpeggio behavior already influence movable arpeggios, shape reuse, open-string policy, and right-hand alternate/sweep decisions. More calibrated open-chord, power-chord, and melodic-lead subprofiles remain planned.

### GK-022 — jazz family

Status: **partial baseline; family expansion planned**

Existing priors influence compact voicing, open-string avoidance, hand-position/voice-leading proxy costs, and chord-voicing continuity. Shell/drop-2/drop-3 knowledge and richer comping semantics remain planned.

### GK-023 — blues family

Status: **partial baseline; family expansion planned**

Existing priors cover box-position/expressive lead tendencies. Explicit MIDI pitch-wheel raises can now become target-neutral pitch-raise intent and GP5 curves. Pentatonic-box semantics, target-aware expressive patterns, double stops, and richer vibrato remain planned.

### GK-024 — funk family

Status: **partial baseline; family expansion planned**

Current style inference and articulation preferences can support short/percussive material and staccato evidence. Dedicated muted-sixteenth, partial-chord, and percussive-ghost-note modeling remains planned.

### GK-025 — fingerstyle/acoustic family

Status: **partial priors; deeper planner work planned**

Current knowledge includes alternating-bass, voice-separation, open-string, let-ring, and overlap priors. Dedicated bass/melody voice separation, alternating-thumb execution, and chord-melody planning remain pending.

## P3 — learning infrastructure

### GK-030 — source provenance schema

Define source/license/permission/quality metadata for every learning batch.

### GK-031 — symbolic tab normalizer

Normalize eligible GP/MusicXML/other symbolic sources into an internal learning representation.

### GK-032 — knowledge feature extractor

Extract aggregate fretboard, phrase, articulation, right-hand, and style-conditioned statistics.

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

Metrics should include exact string/fret agreement, shape-family agreement, fretting-digit agreement where known, average hand shift, fret-span cost, impossible fingering rate, and phrase-level path score.

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
