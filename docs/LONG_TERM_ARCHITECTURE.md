# FretPilot Long-Term Architecture

## Purpose

This document is the stable, high-level map for how FretPilot should grow without turning the codebase into a collection of unrelated heuristics.

The central design rule is:

> Keep physical constraints, file correctness, and canonical data contracts deterministic; allow musical preferences, classification, ranking, and style knowledge to improve through versioned knowledge and evaluated learning.

FretPilot therefore has two planes:

1. **Runtime Plane** — deterministic/reproducible processing used for a user's song.
2. **Learning Plane** — offline ingestion, evaluation, and knowledge/model promotion.

The Runtime Plane must never silently learn from arbitrary internet pages during a user request.

---

## 1. Runtime Plane

```text
MIDI / AI MIDI / DAW MIDI
        ↓
Input Foundation
NormalizedTimeline
        ↓
Instrument Intelligence
InstrumentStream resolution
Layers 1–3 guitar identity evidence
        ↓
Musical Understanding
measure / phrase / section / motif / harmony
        ↓
Behavior Context
role + style + technique-family evidence
        ↓
PlayingContext
        ↓
Guitar Intelligence
fingering / hand position / shapes / voicings
articulation / performance planning
        ↓
Canonical Guitar IR
        ├── Score outputs: PDF / GP5 / future MusicXML
        └── Performance outputs: Ample MIDI / future virtual guitars
```

### Runtime invariant

Every result should be reproducible from a version tuple such as:

```text
engine_version
configuration_version
Guitar_IR_schema_version
knowledge_snapshot_version
optional_model_provider + model_version
```

The same source plus the same version tuple should produce the same result, apart from explicitly documented nondeterministic providers.

---

## 2. Stable Engine vs Evolvable Intelligence

Not every FretPilot module should learn.

| Area | Long-term responsibility | Evolution policy |
|---|---|---|
| MIDI/Input Foundation | SMF parsing, ticks, tempo, controllers, diagnostics | **Stable/deterministic** |
| InstrumentStream resolver | Track/channel/program preservation and logical stream construction | Mostly deterministic; policies can improve |
| Guitar identity classifier | Guitar/non-guitar evidence and candidate ranking | **Evolvable** through labeled data |
| Phrase/Section analysis | Boundaries, motifs, harmony, musical role | **Evolvable** |
| Rhythm/notation | Quantization, duration spelling, rests, ties, voices | Hybrid: hard notation rules + learned preferences |
| Fretboard constraints | String/fret existence, tuning, chord feasibility, stretch limits | **Stable/deterministic** |
| Fingering ranking | Which valid path a guitarist is likely to choose | **Core evolvable intelligence** |
| Style/role knowledge | solo/riff/strumming + metal/rock/jazz/etc. | **Core evolvable knowledge** |
| Articulation ranking | hammer/pull/slide/bend/vibrato/palm mute, etc. | **Evolvable**, with deterministic eligibility |
| Performance feel | timing, velocity, accents, note overlap, strum spread | **Evolvable** |
| Guitar IR | Canonical musical contract | **Stable and schema-versioned** |
| File/output adapters | PDF/GP5/MusicXML/Ample mappings | **Stable/validated** |
| Product UI/API | upload, selection, preview, correction, download | Engineering layer |
| Evaluation | golden material, metrics, human review | **Continuously growing** |
| Learning system | source registry, extraction, training, promotion | **Self-evolution infrastructure** |

The learned/evolvable layers may rank valid alternatives, but they must not bypass hard physical or file-format constraints.

---

## 3. Musical context is compositional

Do not flatten musical knowledge into one genre label.

A phrase can independently carry:

```text
role:
  solo = 0.90

style:
  metal = 0.85

technique_family:
  legato = 0.65
```

These dimensions compose into `PlayingContext`.

Examples:

```text
metal + riff
→ low-register bias
→ shape reuse
→ palm mute / staccato priors
→ tighter performance timing

metal + solo
→ position-aware lead fingering
→ legato / bend / vibrato priors
→ lower open-string preference

jazz + comping
→ voice-leading-aware voicings
→ compact shapes
→ lower open-string preference
→ phrase-aware position stability
```

These are soft priors, never absolute rules.

---

## 4. Long-term knowledge assets

FretPilot should accumulate several different kinds of knowledge rather than one opaque model.

### 4.1 Instrument knowledge

Examples:

- metadata reliability;
- guitar vs keyboard/synth behavior;
- tuning and range priors;
- strum gestures;
- bend/controller evidence;
- user corrections to stream identity.

Canonical project: `docs/projects/track-identification/` (`TI-*`).

### 4.2 Phrase and musical-structure knowledge

Examples:

- section boundaries;
- motif repetition;
- riff vs solo vs comping;
- harmonic role;
- phrase-length and density patterns.

This knowledge is shared by track behavior analysis and guitar-playing knowledge.

### 4.3 Guitar-playing knowledge

Examples:

- pitch → string/fret conditional distributions;
- hand-position centers and shift boundaries;
- adjacent-string transition patterns;
- movable shape reuse;
- open-string usage;
- chord/voicing families;
- left-hand finger assignment;
- articulation likelihood by context;
- performance timing/accent tendencies.

Canonical project: `docs/projects/guitar-playing-knowledge/` (`GK-*`).

### 4.4 Evaluation knowledge

Examples:

- labeled synthetic fixtures;
- legally usable reference tabs;
- real-song golden reviews;
- user corrections;
- human guitarist ratings;
- regression history by engine/knowledge version.

Evaluation is the gate between "a new idea" and "better production behavior".

---

## 5. Learning Plane

```text
Public-domain / permissively licensed / permissioned symbolic sources
User corrections with appropriate rights
Golden evaluation material
        ↓
Source Registry
        ↓
License / Permission / Provenance Gate
        ↓
Quality Scoring
        ↓
Normalization
        ↓
Deduplication / source-family weighting
        ↓
Phrase + role + style annotation
        ↓
Feature Extraction
        ↓
Derived Statistics / Model Training
        ↓
Knowledge Candidate
        ↓
Offline Evaluation
        ↓
Shadow Comparison against production
        ↓
Promotion Gate
        ↓
Approved Knowledge Snapshot
        ↓
Runtime Plane
```

### Learning policy

"Self learning" means automation may discover eligible sources, normalize them, derive features, train/rank candidates, and generate a proposed snapshot.

It does **not** mean:

```text
new webpage appears
→ production behavior silently changes
```

New material first creates a candidate. Production remains pinned to the last approved snapshot.

See `projects/guitar-playing-knowledge/LEARNING_PIPELINE.md` for the detailed source/learning policy.

---

## 6. Candidate-generation and ranking architecture

For problems such as fingering, the long-term pattern should be:

```text
MIDI phrase
   ↓
Deterministic candidate generator
   ↓
Hard guitar constraints prune impossible candidates
   ↓
Knowledge / statistical / learned ranker
   ↓
Best valid phrase path
   ↓
Deterministic validation
```

This is preferable to asking a generative model to invent a fingering with no constraint system.

Possible ranking evolution:

1. hand-authored deterministic costs;
2. profile-conditioned costs from `PlayingContext`;
3. learned statistical weights;
4. phrase-level ranking model;
5. retrieval of similar approved shape prototypes;
6. optional sequence/music model advisor.

The hard constraint layer remains deterministic at every stage.

---

## 7. Knowledge Snapshot contract

Application code and knowledge should eventually be independently versioned.

Conceptually:

```json
{
  "snapshot_version": "2027.03.0",
  "schema_version": "1",
  "source_batches": 7,
  "profiles": {
    "metal_riff": {},
    "rock_arpeggio": {},
    "jazz_comping": {}
  },
  "evaluation": {
    "benchmark_version": "2027.02",
    "status": "approved"
  }
}
```

Runtime outputs should record which knowledge snapshot influenced the result.

---

## 8. Project/task ownership

Use stable prefixes so future AI contributors know which backlog owns a change.

```text
PV-*  Prototype/output validation and near-term product quality
TI-*  InstrumentStream and guitar-track identification
GK-*  Guitar-playing/style/phrase knowledge and learning algorithms
SE-*  Cross-project system-evolution infrastructure and governance
```

Do not create a duplicate `SE-*` task if the work already belongs clearly to `TI-*` or `GK-*`.

The system-evolution umbrella lives under:

`docs/projects/system-evolution/`

---

## 9. Long-term product loop

The eventual product learning loop should be:

```text
User imports MIDI
      ↓
FretPilot generates score/performance
      ↓
User reviews and optionally corrects
      ↓
Correction record
      ↓
Curated evaluation/training pool
      ↓
Offline learning + evaluation
      ↓
Approved Knowledge Snapshot
      ↓
Future FretPilot versions improve
```

User corrections should never immediately mutate the current song's global production model. They are evidence for a later curated knowledge release.

---

## 10. Near-term priority

The existence of this long-term architecture must not block the prototype.

Near-term work remains:

1. make PDF/TAB and score output readable;
2. thread `PlayingContext` into fingering/articulation (`GK-002` onward);
3. add phrase/section context;
4. create review/correction data contracts;
5. continue track identification incrementally;
6. only then build the larger offline learning infrastructure.

The goal now is to preserve the right interfaces so future learning can improve the engine without requiring a rewrite.