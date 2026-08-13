# FretPilot Long-Term Architecture

## Purpose

This document is the stable, high-level map for how FretPilot should grow without turning the codebase into a collection of unrelated heuristics.

The central design rule is:

> Keep physical constraints, file correctness, and canonical data contracts deterministic; allow musical preferences, classification, ranking, style knowledge, and adapter knowledge to improve through versioned evidence and evaluated learning.

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
        ├── Score adapters
        │     ├── PDF / TAB
        │     ├── GP5
        │     └── future MusicXML / score formats
        │
        └── Performance intent
              ↓
        Virtual Guitar Instrument Knowledge
        capability resolver + versioned product profile
              ↓
        Virtual Instrument Adapter
              ├── Ample Guitar
              └── future virtual guitar products
```

### Runtime invariant

Every result should be reproducible from a version tuple such as:

```text
engine_version
configuration_version
Guitar_IR_schema_version
playing_knowledge_snapshot_version
virtual_instrument_profile_version
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
| Score/file adapters | PDF/GP5/MusicXML formatting and serialization | **Stable/validated** |
| Virtual-guitar instrument knowledge | Product/version capabilities, control mappings, timing/state requirements | **Versioned/evolvable adapter knowledge** |
| Virtual-guitar renderer | Deterministic translation of IR intent through an approved product profile | **Stable/validated per profile** |
| Product UI/API | upload, selection, preview, correction, download | Engineering layer |
| Evaluation | golden material, metrics, human review | **Continuously growing** |
| Learning system | source registry, extraction, training, promotion | **Self-evolution infrastructure** |

The learned/evolvable layers may rank valid alternatives, but they must not bypass hard physical or file-format constraints.

Virtual-instrument adapter knowledge is special: documented MIDI/control mappings are source-backed facts, while expressive calibration such as overlap or accent translation may improve experimentally. These two knowledge types must not be conflated.

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

A downstream virtual-instrument adapter then asks a separate question: which of those canonical intents can this exact product/version render natively, approximately, or not at all?

---

## 4. Long-term knowledge assets

FretPilot should accumulate several different kinds of knowledge rather than one opaque model.

### 4.1 Instrument identification knowledge

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

### 4.4 Virtual-guitar instrument knowledge

This knowledge describes how a specific software instrument realizes canonical performance intent.

Examples:

- product/version identity and playable range;
- keyswitch, CC, velocity, program, pitch-bend, or compound control mappings;
- supported / approximated / unsupported articulations;
- latch/reset/state-machine behavior;
- keyswitch preroll and note-overlap requirements;
- string/position forcing capability;
- picking/strum control capability;
- bend/vibrato/per-note-expression capability;
- known product/version limitations;
- host/plugin verification evidence;
- expressive calibration parameters.

Canonical project: `docs/projects/virtual-guitar-instruments/` (`VI-*`).

Important distinction:

```text
Guitar Playing Knowledge
= how a real guitarist is likely to play

Virtual Guitar Instrument Knowledge
= how a target software instrument must be controlled
```

The latter must never redefine upstream musical intent just because one plugin cannot express it perfectly.

### 4.5 Evaluation knowledge

Examples:

- labeled synthetic fixtures;
- legally usable reference tabs;
- real-song golden reviews;
- user corrections;
- human guitarist ratings;
- plugin/product conformance and calibration records;
- regression history by engine/knowledge/profile version.

Evaluation is the gate between "a new idea" and "better production behavior".

---

## 5. Learning Plane

```text
Public-domain / permissively licensed / permissioned symbolic sources
Official/permissioned virtual-instrument documentation
Verified plugin calibration results
User corrections with appropriate rights
Golden evaluation material
        ↓
Source Registry
        ↓
License / Permission / Provenance Gate
        ↓
Quality / Evidence Scoring
        ↓
Normalization
        ↓
Deduplication / source-family weighting
        ↓
Feature or Capability Extraction
        ↓
Derived Statistics / Model Training / Adapter Knowledge Candidate
        ↓
Offline Evaluation
        ↓
Shadow Comparison against production
        ↓
Promotion Gate
        ↓
Approved Knowledge Snapshot / Approved Instrument Profile
        ↓
Runtime Plane
```

### Learning policy

"Self learning" means automation may discover eligible sources, normalize them, derive features, train/rank candidates, generate a proposed knowledge snapshot, or generate an adapter-profile candidate.

It does **not** mean:

```text
new webpage appears
→ production behavior silently changes
```

New material first creates a candidate. Production remains pinned to the last approved snapshot/profile.

See:

- `projects/guitar-playing-knowledge/LEARNING_PIPELINE.md` for guitarist/style learning;
- `projects/virtual-guitar-instruments/README.md` for adapter-knowledge evolution.

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

For virtual instruments, the pattern is different:

```text
Canonical Guitar IR performance intent
        ↓
Target profile capability negotiation
        ↓
native / approximated / unsupported classification
        ↓
Deterministic product adapter/state machine
        ↓
validated MIDI/control output
```

A learned model may later tune expressive adapter parameters, but it cannot invent undocumented control protocols or bypass capability validation.

---

## 7. Knowledge Snapshot and Adapter Profile contracts

Application code and knowledge should eventually be independently versioned.

Conceptually, guitarist/style knowledge may use a snapshot such as:

```json
{
  "snapshot_version": "2027.03.0",
  "schema_version": "1",
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

Virtual-instrument knowledge is separately versioned, for example:

```json
{
  "profile_id": "vendor-product-vX",
  "product_version_family": "X.x",
  "profile_schema_version": "1",
  "verification_status": "approved",
  "capabilities": {},
  "evidence": []
}
```

Runtime outputs should record both the musical knowledge snapshot and exact target instrument profile that influenced the result.

---

## 8. Project/task ownership

Use stable prefixes so future AI contributors know which backlog owns a change.

```text
PV-*  Prototype/output validation and near-term product quality
TI-*  InstrumentStream and guitar-track identification
GK-*  Guitar-playing/style/phrase knowledge and learning algorithms
VI-*  Virtual-guitar product knowledge, capabilities, adapter schemas, and compatibility
SE-*  Cross-project system-evolution infrastructure and governance
```

Do not create a duplicate `SE-*` task if the work already belongs clearly to `TI-*`, `GK-*`, or `VI-*`.

Project hubs:

- `docs/projects/track-identification/`
- `docs/projects/guitar-playing-knowledge/`
- `docs/projects/virtual-guitar-instruments/`
- `docs/projects/system-evolution/`

---

## 9. Long-term product loop

The eventual product learning loop should be:

```text
User imports MIDI
      ↓
FretPilot generates score/performance
      ↓
User reviews and optionally corrects musical decisions or adapter behavior
      ↓
Correction / verification record
      ↓
Curated evaluation/training/calibration pool
      ↓
Offline learning + evaluation
      ↓
Approved Knowledge Snapshot / Instrument Profile
      ↓
Future FretPilot versions improve
```

User corrections should never immediately mutate the current song's global production model or an official adapter mapping. They are evidence for a later curated release.

---

## 10. Near-term priority

The existence of this long-term architecture must not block the prototype.

Near-term work remains:

1. make PDF/TAB and score output readable;
2. thread `PlayingContext` into fingering/articulation (`GK-002` onward);
3. add phrase/section context;
4. keep Ample working while introducing the generic virtual-instrument profile contract (`VI-001/VI-002`);
5. create review/correction data contracts;
6. continue track identification incrementally;
7. only then expand the larger offline learning and multi-product infrastructure.

The goal now is to preserve the right interfaces so future musical learning and future virtual-guitar adapters can improve independently without requiring a rewrite.