# Learning Pipeline

## Purpose

Define how FretPilot may eventually learn guitar-playing knowledge from external symbolic sources without turning the runtime system into an uncontrolled crawler or treating one tablature source as ground truth.

## Core principle

The product should learn **derived guitar behavior statistics and reusable musical patterns**, not merely copy source tabs.

Knowledge promotion must be reproducible, versioned, attributable, and evaluated before it affects production fingering/articulation decisions.

## Source eligibility

Only ingest sources that are legally and technically appropriate for the intended use, such as:

- public-domain material;
- permissively licensed symbolic guitar datasets;
- material explicitly licensed/permissioned for analysis/training;
- first-party/user-contributed material where the required rights are available.

Do not assume that content being visible on the public internet grants permission to crawl, store, redistribute, or train on it. Source terms and licenses must be recorded.

## Proposed stages

```text
Source registry
    ↓
license / permission gate
    ↓
quality scoring
    ↓
download / import
    ↓
format normalization
    ↓
deduplication
    ↓
section + role + style annotation
    ↓
guitar feature extraction
    ↓
source-level derived records
    ↓
aggregate statistics / learned candidate
    ↓
offline evaluation
    ↓
knowledge proposal
    ↓
review + promotion
    ↓
versioned production knowledge snapshot
```

## Source registry

Every source batch should carry provenance metadata, for example:

```json
{
  "source_id": "dataset-example-v1",
  "source_type": "licensed_dataset",
  "license": "SPDX-or-project-specific-license",
  "source_url": "recorded-outside-runtime-profile",
  "retrieved_at": "ISO-8601",
  "ingestion_version": "0.1",
  "allowed_uses": ["analysis", "derived_statistics"],
  "redistribution_allowed": false
}
```

The exact schema will evolve, but provenance must never be optional for learned knowledge.

## Quality scoring

A source tab is not automatically high quality because it exists.

Candidate quality features can include:

- complete tuning information;
- valid fret/string assignments;
- low impossible-chord rate;
- consistent meter and duration notation;
- repeated sections that use stable shapes;
- articulation syntax consistency;
- agreement between pitch and TAB position;
- confidence/reputation metadata supplied by the licensed dataset;
- duplicate/near-duplicate agreement across independent sources when legally available.

Low-quality material may remain useful for robustness tests but should not dominate knowledge learning.

## What to extract

Prefer compact derived features such as:

### Fretboard behavior

- pitch → string/fret conditional distributions;
- hand-position center and shift distribution;
- position-shift distance by phrase boundary;
- adjacent-string transition matrix;
- open-string usage by context;
- fret-span distribution;
- chord shape classes;
- power-chord / octave-shape frequencies;
- repeated movable-shape statistics.

### Phrase behavior

- role labels: solo, riff, strumming, comping, arpeggio, breakdown;
- phrase-length distributions;
- motif repetition;
- register usage;
- density and onset-polyphony;
- rhythmic motif statistics.

### Articulation behavior

- hammer/pull probability by interval and timing;
- slide probability by string/fret distance;
- bend/vibrato prevalence by role/style;
- palm-mute density;
- let-ring behavior;
- staccato/note-length distributions.

### Style-conditioned behavior

Examples:

```text
P(string transition | pitch interval, role=solo, style=metal)
P(palm mute | role=riff, style=metal, register=low)
P(open string | role=strumming, style=rock)
P(position shift | phrase boundary, role=solo)
P(chord shape class | style=jazz, chord function=dominant)
```

## Learned knowledge artifacts

Raw sources and production knowledge should be separate.

A promoted artifact should contain derived information such as:

```json
{
  "knowledge_version": "2027.03.0",
  "profile": "metal_riff",
  "sample_count": 18234,
  "source_batch_count": 7,
  "features": {
    "shape_reuse": 1.42,
    "palm_mute": 1.61,
    "low_register_bias": 1.38
  },
  "evaluation": {
    "held_out_score": 0.84
  }
}
```

Runtime code should load these compact knowledge snapshots rather than fetching internet tabs on demand.

## Candidate promotion

No learned update should immediately overwrite production values.

Use a proposal lifecycle:

```text
candidate
→ evaluation
→ shadow comparison
→ approved
→ versioned release
```

Required checks should eventually include:

- held-out source evaluation;
- regression corpus performance;
- impossible-fingering rate;
- hand-shift cost;
- shape consistency;
- reference-tab similarity where a licensed reference exists;
- human guitar-player review on selected examples.

## Online/self-learning boundary

"Self learning" should mean the system can automate discovery, extraction, aggregation, and proposal generation under controlled policies.

It should **not** mean production behavior silently changes whenever the crawler sees a new webpage.

Recommended separation:

```text
Runtime inference
    uses approved Knowledge Snapshot

Offline learning worker
    discovers/ingests eligible material
    extracts features
    proposes Knowledge Candidate

Evaluation/promotion gate
    decides whether candidate becomes a new snapshot
```

This preserves reproducibility: the same FretPilot version plus the same knowledge snapshot should produce the same result.

## Future model path

The deterministic preference model can later coexist with learned models:

1. statistical priors from tab corpora;
2. gradient-boosted/ranking model for candidate fingerings;
3. sequence model for phrase-level fretboard paths;
4. retrieval of similar approved shape prototypes;
5. LLM/music model as an advisor for ambiguous style/phrase context.

Hard fretboard constraints and output validation remain deterministic even if the ranker becomes learned.
