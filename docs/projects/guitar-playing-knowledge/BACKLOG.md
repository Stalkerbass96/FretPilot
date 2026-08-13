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

Status: **todo**

Pass an optional/derived PlayingContext through:

```text
analyze_guitar_track
→ optimize_fingering
→ plan_articulations
→ Guitar IR
→ performance renderer
```

Acceptance:

- neutral/default context preserves current output;
- explicit context appears in analysis/IR metadata;
- no output adapter directly invents style rules.

### GK-003 — replace hard-coded fingering weights with preference-aware costs

Status: **todo**

Acceptance:

- current movable-arpeggio regression remains green;
- `shape_reuse`, `same_string_legato`, `open_string_usage`, and `hand_position_stability` affect candidate ranking;
- physical fretboard constraints remain hard constraints.

### GK-004 — articulation planner consumes context

Status: **todo**

Acceptance:

- technique eligibility remains deterministic;
- context changes ranking/confidence, not physical validity;
- metal riff increases palm-mute/staccato priors;
- solo increases bend/vibrato/legato priors.

## P1 — phrase-level knowledge

### GK-010 — section/phrase segmentation

Segment a stream before style/role inference. Whole-track labels are insufficient.

### GK-011 — phrase-level behavior classification

Output multiple context distributions over time, for example:

```text
bars 1-8   riff + rock_arpeggio
bars 9-16  strumming + rock
bars 17-24 solo + rock
```

### GK-012 — shape memory

Represent reusable fretboard shape prototypes independent of absolute root fret.

Examples:

- sus2 arpeggio shape;
- power chord;
- octave shape;
- triad inversion;
- jazz shell voicing.

### GK-013 — hand-position state

Track hand center, span, shift boundaries, and phrase-level position plans rather than evaluating only note-to-note transitions.

### GK-014 — left-hand finger assignment

Add finger numbers, barre representation, stretch feasibility, and optional thumb-over techniques.

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
