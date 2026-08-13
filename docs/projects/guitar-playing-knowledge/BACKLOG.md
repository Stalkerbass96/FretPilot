# Guitar Playing Knowledge Backlog

Stable task IDs use the `GK-` prefix.

## P0 — establish the knowledge interface

### GK-001 — PlayingContext model

Status: **implemented**

Acceptance:

- role, style, and technique dimensions remain separate;
- profiles compose into fingering/articulation/performance preferences;
- existing Layer-4 behavior matches can be bridged into PlayingContext;
- tests cover solo+metal, breakdown→metal riff, and jazz comping.

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

The one-command prototype package now uses this section-aware path by default.
Its analysis/report files expose the section contexts used to drive execution.

Still pending:

- make `PerformancePreferences` influence a generic performance plan before any virtual-instrument adapter;
- persist full section-context provenance directly into Guitar IR rather than only analysis/report metadata;
- decide when selected section boundaries should carry hand-position state across the boundary instead of resetting it.

Acceptance:

- neutral/default context preserves current output;
- explicit context appears in analysis/IR metadata;
- no output adapter directly invents style rules.

### GK-003 — replace hard-coded fingering weights with preference-aware costs

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

- current movable-arpeggio regression remains green;
- `shape_reuse`, `same_string_legato`, `open_string_usage`, and `hand_position_stability` affect candidate ranking;
- physical fretboard constraints remain hard constraints.

Future learned/statistical ranking remains `GK-040+` work.

### GK-004 — articulation planner consumes context

Status: **implemented baseline**

Current behavior:

- deterministic physical/timing eligibility remains unchanged;
- `hammer_pull`, `slide`, and `vibrato` preferences confidence-weight only already-valid articulation decisions;
- neutral preferences preserve historical confidence values exactly;
- style-heavy techniques such as palm mute/staccato are **not** emitted merely because a style profile prefers them; they need their own eligibility/context features first.

Acceptance:

- technique eligibility remains deterministic;
- context changes ranking/confidence, not physical validity;
- metal/riff profiles carry palm-mute/staccato priors for future eligible decisions;
- solo profiles carry stronger bend/vibrato/legato priors.

## P1 — phrase-level knowledge

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
→ stable GuitarSection records
```

Each section carries:

- stream/section identity;
- measure and beat boundaries;
- feature snapshot;
- boundary confidence and reason.

The baseline deliberately answers only **where behavior changes**; semantic labels remain GK-011.

### GK-011 — phrase-level behavior classification

Status: **implemented experimental baseline**

Current behavior:

- run the existing experimental Layer-4 behavior library independently for each `GuitarSection`;
- retain all behavior-profile matches for explainability;
- only matches above a configurable minimum score contribute to `PlayingContext`;
- produce independent role/style/technique preference contexts per section.

Example target shape now supported by the data flow:

```text
bars 1-8   riff context
bars 9-16  strumming context
bars 17-24 solo context
```

Important limitation:

> Current behavior profiles remain hand-authored experimental rules. Section-level evaluation fixes the whole-track modeling mistake, but does not make the labels musically calibrated yet.

### GK-012 — shape memory

Represent reusable fretboard shape prototypes independent of absolute root fret.

Examples:

- sus2 arpeggio shape;
- power chord;
- octave shape;
- triad inversion;
- jazz shell voicing.

### GK-013 — hand-position state

**Next execution priority.**

Track hand center, span, shift boundaries, and phrase-level position plans rather than evaluating only note-to-note transitions.

Section-aware analysis currently treats each detected section boundary as a safe reset point. GK-013 should make that explicit and selective:

- carry hand-position state across weak boundaries;
- allow deliberate repositioning at strong phrase/style boundaries;
- record the shift reason and cost;
- keep physical fretboard constraints deterministic.

### GK-014 — left-hand finger assignment

Add finger numbers, barre representation, stretch feasibility, and optional thumb-over techniques.

### GK-015 — section-aware execution and merge

Status: **implemented baseline**

Current behavior:

- solve fingering and articulation independently with each section's PlayingContext;
- section boundaries act as phrase resets;
- remap local section note indices back to original stream-wide indices;
- preserve global source timing for Guitar IR and performance rendering;
- support stable `section_id`-keyed context overrides for future user corrections;
- one-command prototype generation uses this path and reports section contexts.

## P2 — expand style knowledge

### GK-020 — metal family

Split broad metal priors into reusable subprofiles such as:

- tight rhythm riff;
- breakdown;
- tremolo picking;
- metal lead/solo;
- modern low-tuned riff.

### GK-021 — rock/pop family

- open-chord rhythm;
- movable arpeggio;
- power-chord riff;
- melodic lead.

### GK-022 — jazz family

- shell voicing;
- drop-2/drop-3 tendencies;
- comping voice leading;
- single-note jazz lead.

### GK-023 — blues family

- pentatonic box behavior;
- bend targets;
- vibrato patterns;
- double stops.

### GK-024 — funk family

- muted sixteenth-note rhythm;
- partial chords;
- percussive articulation;
- tight position reuse.

### GK-025 — fingerstyle/acoustic family

- bass/melody separation;
- alternating bass;
- open-string resonance;
- chord-melody voicing.

## P3 — learning infrastructure

### GK-030 — source provenance schema

Define source/license/permission/quality metadata for every learning batch.

### GK-031 — symbolic tab normalizer

Normalize eligible GP/MusicXML/other symbolic sources into an internal learning representation.

### GK-032 — knowledge feature extractor

Extract aggregate fretboard, phrase, articulation, and style-conditioned statistics.

### GK-033 — deduplication and source-family weighting

Prevent one copied tab from appearing hundreds of times and dominating learned priors.

### GK-034 — quality estimator

Score structural validity, fretboard validity, notation consistency, metadata quality, and source confidence.

### GK-035 — knowledge snapshot format

Version compact learned profiles separately from application code.

### GK-036 — candidate/evaluation/promotion workflow

Learned data creates a candidate snapshot first; production remains pinned to the last approved snapshot.

## P4 — learned fingering ranker

### GK-040 — regression evaluation corpus

Create train/dev/test splits with legally usable reference fingerings.

Metrics should include:

- exact string/fret agreement;
- shape-family agreement;
- average hand shift;
- fret-span cost;
- impossible fingering rate;
- phrase-level path score.

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
