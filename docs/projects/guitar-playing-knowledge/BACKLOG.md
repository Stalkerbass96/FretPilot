# Guitar Playing Knowledge Backlog

Stable task IDs use the `GK-` prefix.

## P0 — establish the knowledge interface

### GK-001 — PlayingContext model

Status: **implemented**

Acceptance:

- role, style, and technique dimensions remain separate;
- profiles compose into fingering/articulation/performance preferences;
- existing Layer-4 behavior matches can be bridged into PlayingContext;
- tests cover representative composed contexts.

### GK-002 — thread PlayingContext through analysis

Status: **in progress; section-aware execution baseline implemented**

Implemented flow:

```text
InstrumentStream
→ section segmentation
→ section behavior profiles
→ section PlayingContext
→ per-section optimize_fingering
→ per-section plan_articulations
→ remap local note indices to stream-wide source_note_index
→ merged GuitarTrackAnalysis
→ Guitar IR / prototype outputs
```

The one-command prototype package uses this section-aware path by default. Analysis/report files expose the section contexts used to drive execution.

Remaining work is now narrow:

- `GK-005`: make `PerformancePreferences` influence a generic performance plan before any virtual-instrument adapter;
- persist complete section/knowledge provenance as a stable Guitar IR contract;
- `GK-013`: replace unconditional section-boundary hand-position resets with explicit hand-position state.

Acceptance:

- neutral/default context preserves current output;
- explicit/derived context is traceable through analysis and IR/report provenance;
- no output adapter invents style rules;
- source timing and stream-wide note identity survive section-local processing.

### GK-003 — preference-aware fingering costs

Status: **implemented baseline**

Current preference-aware costs include:

- adjacent-string arpeggio bias;
- same-string legato bias;
- hand-position stability;
- movable-shape reuse;
- open-string preference/avoidance;
- compact chord/shape voicing;
- wide-interval position-shift willingness.

Acceptance:

- movable-arpeggio golden regression remains green;
- preferences affect candidate ranking among physically valid positions;
- physical fretboard constraints remain hard constraints.

Future learned/statistical ranking remains `GK-040+` work.

### GK-004 — articulation planner consumes context

Status: **implemented baseline**

Current behavior:

- deterministic physical/timing eligibility remains unchanged;
- `hammer_pull`, `slide`, and `vibrato` preferences confidence-weight only already-valid decisions;
- neutral preferences preserve historical confidence values;
- style-heavy techniques such as palm mute/staccato are not emitted merely because a profile prefers them; they still need deterministic/contextual eligibility evidence.

### GK-005 — generic Performance Plan consumes PerformancePreferences

Status: **not started — recommended next architecture task after/alongside GK-013**

Goal:

> Convert generic guitarist performance intent into a target-neutral plan before any virtual-instrument adapter translates it.

Target flow:

```text
Guitar IR + time-varying PlayingContext
→ generic PerformancePlan
→ target capability negotiation
→ Ample / future adapter
```

The generic plan may represent:

- timing looseness / tightening;
- velocity variation;
- accent intent;
- note overlap intent;
- pick/strum direction intent when available;
- expressive timing that belongs to guitarist behavior rather than one plugin.

Acceptance:

- `PerformancePreferences` measurably affect target-neutral intent;
- neutral preferences preserve source/performance behavior;
- no keyswitch, CC number, plugin MIDI note, latch/reset state, or vendor-specific behavior appears in the generic plan;
- Ample adapter behavior can consume the plan without changing canonical musical meaning;
- tests distinguish generic performance intent from VI-specific translation.

## P1 — phrase / fretboard-state knowledge

### GK-010 — section/phrase segmentation

Status: **implemented baseline**

Current deterministic baseline:

```text
InstrumentStream + time-signature map
→ non-overlapping measure windows
→ per-window behavior features
→ normalized feature distance
→ change-point boundaries
→ merge adjacent similar windows
→ GuitarSection records
```

Each section carries stream/section identity, measure/beat boundaries, feature snapshot, and boundary confidence/reason.

The baseline answers only **where behavior changes**; semantic interpretation remains GK-011.

### GK-011 — phrase-level behavior classification

Status: **implemented experimental baseline**

Current behavior:

- run the current Layer-4 behavior library independently for each `GuitarSection`;
- retain all behavior-profile matches for explainability;
- only matches above a configurable threshold contribute to `PlayingContext`;
- produce independent role/style/technique preference contexts per section.

Important limitation:

> Current behavior profiles remain hand-authored experimental rules. Section-level evaluation fixes the whole-track modeling mistake but does not make the labels calibrated truth.

### GK-012 — shape memory

Status: **not started**

Represent reusable fretboard shape prototypes independent of absolute root fret.

Examples:

- sus2 arpeggio shape;
- power chord;
- octave shape;
- triad inversion;
- jazz shell voicing.

### GK-013 — hand-position state

Status: **not started — highest-value current music-engine task**

Track hand center, span, shift boundaries, and phrase-level position plans rather than evaluating only note-to-note transitions.

Section-aware analysis currently treats each section boundary as a safe reset point. GK-013 should make this explicit and selective:

- estimate section-entry/exit hand state;
- carry hand-position state across weak boundaries;
- allow deliberate repositioning at strong phrase/style boundaries;
- record shift reason and cost;
- keep physical fretboard constraints deterministic;
- preserve current movable-arpeggio golden regression.

### GK-014 — left-hand finger assignment

Status: **not started**

Add finger numbers, barre representation, stretch feasibility, and optional thumb-over techniques.

### GK-015 — section-aware execution and merge

Status: **implemented baseline**

Current behavior:

- solve fingering and articulation independently with each section's PlayingContext;
- section boundaries currently act as phrase resets;
- remap local section note indices back to original stream-wide indices;
- preserve global source timing for Guitar IR and performance rendering;
- support stable `section_id`-keyed context overrides for future user corrections;
- one-command prototype generation uses this path and reports section contexts.

### GK-016 — source-note rationalization continuum

Status: **implemented deterministic baseline**

FretPilot now has an explainable rewrite stage between logical stream selection
and section-aware guitar analysis:

```text
InstrumentStream
→ confidence-gated note rewrite
→ rewritten InstrumentStream + source mapping + change log
→ section / fingering / articulation analysis
```

The public control is `midi_fidelity` in the inclusive range `0..1`:

- `1.0` is an exact note passthrough;
- lower values admit progressively lower-confidence musical repairs;
- the default `0.35` favors guitar reasonableness while remaining conservative.

The V0 deterministic baseline may:

- octave-shift pitches that lie outside the configured standard-guitar range;
- repair high-confidence isolated octave-register outliers;
- delete exact duplicate notes and short isolated spike notes;
- insert a missing note only inside a strongly evidenced repeated-pulse pattern.

Every edit records operation, before/after state, confidence, reason, stable
source-note identity, and MIDI/synthetic origin. Synthetic identities start
after the original note-index range. Rewrites run before fingering and
articulation so downstream intelligence sees the musically revised material.

Future work:

- harmony/key/chord-conditioned pitch alternatives rather than octave-only repair;
- motif-aware insertion/deletion across longer phrases;
- jointly score note edits, fingering, and articulation alternatives;
- human review controls and regression-corpus calibration for threshold values.

## P2 — expand style knowledge

### GK-020 — metal family

Planned reusable subprofiles include tight rhythm riff, breakdown, tremolo picking, metal lead/solo, and modern low-tuned riff.

### GK-021 — rock/pop family

Planned: open-chord rhythm, movable arpeggio, power-chord riff, melodic lead.

### GK-022 — jazz family

Planned: shell voicing, drop-2/drop-3 tendencies, comping voice leading, single-note jazz lead.

### GK-023 — blues family

Planned: pentatonic-box behavior, bend targets, vibrato patterns, double stops.

### GK-024 — funk family

Planned: muted sixteenth-note rhythm, partial chords, percussive articulation, tight position reuse.

### GK-025 — fingerstyle/acoustic family

Planned: bass/melody separation, alternating bass, open-string resonance, chord-melody voicing.

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

Learned data creates a candidate snapshot first; production remains pinned to the last approved snapshot.

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
