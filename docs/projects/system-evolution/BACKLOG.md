# System Evolution Backlog

Use the `SE-` prefix only for cross-project infrastructure or governance. If a task is clearly owned by track identification or guitar-playing knowledge, use the canonical `TI-*` or `GK-*` task instead.

Status markers:

- `[ ]` not started
- `[~]` in progress
- `[x]` implemented/verified

## P0 — architecture and reproducibility

### [x] SE-001 — Define Runtime Plane vs Learning Plane

Established in `docs/LONG_TERM_ARCHITECTURE.md`.

Acceptance:

- stable/deterministic and evolvable modules are explicitly separated;
- runtime does not directly learn from arbitrary internet pages;
- learning requires candidate/evaluation/promotion stages;
- project ownership between `PV-*`, `TI-*`, `GK-*`, and `SE-*` is documented.

### [ ] SE-002 — Runtime reproducibility manifest

Define a common version/provenance record attached to analysis and output packages.

Minimum fields should include:

```text
engine_version
configuration_version
Guitar_IR_schema_version
knowledge_snapshot_version
optional model/provider/version
source fingerprint
```

Acceptance:

- prototype report contains this record;
- output adapters do not invent their own incompatible version metadata;
- a result can state which approved knowledge snapshot influenced it.

Likely dependencies:

- current Guitar IR metadata;
- `GK-035` knowledge snapshot format.

### [ ] SE-003 — Shared evaluation artifact identity

Define how benchmark/evaluation results identify:

```text
engine version
knowledge snapshot
configuration
fixture/golden-corpus version
metric set
```

Acceptance:

- two evaluation reports can be compared without guessing which knowledge/configuration produced them;
- track-identification and fingering benchmarks can use the same top-level identity envelope.

Canonical subproject work remains `TI-001/TI-002` and `GK-040`.

## P1 — shared musical-context contracts

### [ ] SE-010 — Shared Phrase/Section context contract

Coordinate the data contract used by:

- track behavior classification;
- rhythm decisions;
- style/role inference;
- `PlayingContext`;
- Guitar IR;
- review UI.

This task does not implement segmentation itself. Segmentation remains owned by `TI-040/TI-041` and `GK-010/GK-011`.

Acceptance:

- one region can expose boundaries, confidence, role/style/technique evidence, and change reasons;
- downstream modules consume the same region identity instead of recomputing incompatible sections;
- whole-track classification remains available as a fallback only.

### [ ] SE-011 — Context provenance in Guitar IR

Record enough context metadata in Guitar IR to explain why a fingering/articulation/performance decision was made.

Acceptance:

- the IR can reference `PlayingContext`/region IDs;
- knowledge snapshot version is preserved;
- renderer-specific mappings remain outside the canonical intent model.

Primary implementation dependency: `GK-002`.

## P1 — feedback and review loop

### [ ] SE-020 — Common user-correction envelope

Define a privacy-conscious correction envelope that can carry module-specific corrections without embedding full source files by default.

Examples:

```text
source fingerprint
stream/region/event ID
correction type
old decision
user-selected decision
engine/knowledge version
optional note
```

Canonical module-specific payloads remain owned by tasks such as `TI-052` and future `GK-*` correction tasks.

Acceptance:

- corrections are exportable as structured records;
- runtime production knowledge does not mutate immediately;
- a later curation pipeline can associate corrections with the exact engine/knowledge version.

### [ ] SE-021 — Golden-review registry

Create a registry for human-reviewed real-song cases that records issues by stream, region/measure, and category.

Example categories:

- wrong track;
- wrong rhythm spelling;
- wrong string/fret path;
- implausible hand position;
- wrong articulation;
- unreadable notation;
- performance mismatch.

Acceptance:

- reviews can become regression/evaluation evidence;
- copyrighted source content is not duplicated unnecessarily in the registry;
- reference provenance/permissions are recorded.

## P2 — approved knowledge snapshots

### [ ] SE-030 — Knowledge Snapshot loader/pinning

Create a runtime mechanism that loads an explicitly selected approved knowledge snapshot.

Acceptance:

- no implicit "latest from the internet" behavior;
- missing/incompatible snapshots fail clearly or use a documented built-in fallback;
- snapshot version appears in reports and Guitar IR metadata.

Canonical knowledge format work: `GK-035`.

### [ ] SE-031 — Candidate vs production snapshot separation

Implement storage/naming semantics that prevent candidate learning artifacts from replacing production knowledge automatically.

Lifecycle:

```text
candidate
→ evaluated
→ shadow-tested
→ approved
→ production snapshot
```

Canonical learning work: `GK-036`.

### [ ] SE-032 — Shadow comparison runner

Given the same evaluation corpus, compare current production knowledge against a candidate snapshot.

Required comparisons should eventually include:

- track identity metrics where relevant;
- fingering/shape metrics;
- impossible-fingering rate;
- hand-shift cost;
- articulation changes;
- notation regressions;
- human-review deltas where available.

Acceptance:

- candidate improvements and regressions are visible before promotion;
- promotion can never be justified by one cherry-picked song.

## P2 — source and learning governance

### [ ] SE-040 — Unified source registry contract

Define the shared source/provenance identity used by learning datasets and golden evaluation material.

Minimum concepts:

```text
source_id
license/permission
allowed uses
retrieval/import date
source family
quality metadata
content fingerprint
```

Detailed guitar-learning ingestion remains owned by `GK-030` onward.

### [ ] SE-041 — Cross-source dedup identity

Define stable fingerprints/near-duplicate identities so one copied tab or MIDI does not dominate datasets across multiple websites or collections.

Detailed weighting/learning implementation remains `GK-033`.

## P3 — learned-ranker integration

### [ ] SE-050 — Learned-ranker adapter contract

Define a provider-neutral runtime interface for optional learned ranking.

The contract should accept deterministic candidates and return ranked/scored alternatives with model/version metadata.

Acceptance:

- deterministic candidate generation remains authoritative;
- learned rankers cannot introduce physically impossible positions;
- no specific ML framework leaks into Guitar IR;
- disabling the ranker preserves a deterministic fallback.

Canonical guitar ranker development remains `GK-041/GK-042`.

### [ ] SE-051 — Model registry and compatibility metadata

Track optional learned/advisor model identity, supported knowledge schema, feature schema, and evaluation status.

Acceptance:

- reports identify the exact optional model used;
- incompatible model/feature/snapshot combinations fail explicitly;
- the engine can run without any learned model.

## P3 — product learning loop

### [ ] SE-060 — Correction-to-curation pipeline

Build the offline path from exported user corrections to a curated evaluation/training pool.

Acceptance:

- corrections require review/quality gates before becoming training evidence;
- rights/provenance are retained;
- correction frequency alone does not automatically change production knowledge.

### [ ] SE-061 — Knowledge release report

Every promoted knowledge snapshot should eventually include a machine-readable and human-readable release report:

```text
new snapshot version
source batches included
changed profiles/features
benchmark deltas
known regressions
approval status
```

This report becomes the audit trail for FretPilot's self-evolution.

## Explicit non-goals for Prototype 0.1

Do not block the current prototype on:

- internet crawling;
- automated model training;
- full knowledge snapshot service;
- online learning;
- a generalized model registry;
- automatic production promotion.

The prototype only needs interfaces that keep those future capabilities possible without architectural rewrites.