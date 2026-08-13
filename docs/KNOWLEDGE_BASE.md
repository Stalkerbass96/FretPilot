# FretPilot Knowledge Base

> Current built-in snapshot: `2026.08.1`

## Purpose

The knowledge base is FretPilot's versioned, explainable source of soft musical
preferences and reusable knowledge assets. It is not one opaque model and it
does not replace deterministic parsing, fretboard physics, or output-format
validation.

```text
approved pinned KnowledgeSnapshot
        ↓
KnowledgeRegistry
        ↓
context/profile/shape queries
        ↓
valid candidates ranked by musical preference
        ↓
Guitar IR + exact knowledge provenance
```

The Runtime Plane never crawls, learns, or promotes knowledge while converting
a song. Candidate creation and promotion belong to the offline Learning Plane.

## Knowledge domains

The common entry schema can represent several independent domains:

| Domain | Question | Canonical owner |
|---|---|---|
| Instrument identity | Which logical stream is guitar? | `TI-*` |
| Musical structure | What role/phrase/section is occurring? | shared `TI-*` / `GK-*` |
| Guitar playing | How would a real guitarist likely play it? | `GK-*` |
| Guitar shapes | Which movable shape or voicing can be reused? | `GK-012` |
| Virtual instrument | How does a plugin realize canonical intent? | `VI-*` |
| Evaluation/corrections | Did a candidate improve the result? | `SE-*` |

Virtual-instrument profiles keep their provider-neutral models and an
independently pinned snapshot under `src/fretpilot/virtual_instruments/`.
Vendor keyswitches and CC mappings must never enter Guitar Playing Knowledge.
See [`VIRTUAL_INSTRUMENT_KNOWLEDGE_BASE.md`](VIRTUAL_INSTRUMENT_KNOWLEDGE_BASE.md)
for the profile contract and initial Ample Metal Eclipse asset.

## Common contract

Every `KnowledgeEntry` contains:

```text
knowledge_id
domain + kind
schema_version + knowledge_version
lifecycle status
scope
payload
provenance
evaluation identity
```

Lifecycle status is explicit:

```text
candidate → evaluated → approved → deprecated
```

An approved entry may still describe musically experimental priors. Governance
status answers whether the pinned runtime may load it; `payload.maturity`
describes how mature the musical interpretation is.

## Current built-in asset

`src/fretpilot/knowledge/assets/knowledge-2026.08.1.json` currently contains:

- the six existing Playing Profiles (`solo`, `riff`, `strumming`, `metal`,
  `jazz`, `rock_arpeggio`) as approved runtime entries;
- candidate shape prototypes for power chord, octave, suspended-second
  arpeggio, and compact triad inversion.
- 71 candidate abstractions derived from the user-provided *Total Rock Guitar*
  reference, covering all 22 lessons across execution rules, rhythm rules,
  phrase patterns, harmonic contexts, and additional shape families.

The reference-derived candidates store concise rules in original wording,
lesson-level provenance, allowed-use notes, engine targets, hard constraints,
soft preferences, and exceptions. They do not contain song transcriptions,
continuous TAB, page images, or audio. See
[`projects/guitar-playing-knowledge/TRG_SOURCE_REVIEW.md`](projects/guitar-playing-knowledge/TRG_SOURCE_REVIEW.md).

Shape coordinates increment `string_offset` toward higher-pitched strings;
`fret_offset` is relative to the anchor fret. `interval_semitones` remains an
independent musical validation value so a later matcher can reject shapes that
do not fit the active tuning or cross the standard G–B tuning boundary badly.

Playing Profile behavior is unchanged from the previous hand-authored Python
constants. All candidates are queryable and visible in the review console but
intentionally do not affect runtime decisions until focused evaluation and
integration are complete.

## Runtime provenance

Every section `PlayingContext` records:

```text
knowledge_version
knowledge_entry_ids
```

The builder aggregates those references into Guitar IR. Prototype processing
reports and `manifest.json` record the same pinned snapshot. This makes a result
traceable even after knowledge values evolve.

## Adding or changing knowledge

1. Add or modify an entry in a new candidate snapshot; never overwrite the
   currently approved asset in place after release.
2. Record source type, reference, rights/license where applicable, and notes.
3. Add focused regression or evaluation fixtures.
4. Compare the candidate with the pinned production snapshot.
5. Approve and release a new snapshot version only after review.
6. Update the runtime pin and document known improvements/regressions.

Internet visibility is not a license. External symbolic data requires an
explicit provenance and allowed-use decision before ingestion.

## Current limitations

- Runtime uses one built-in pinned snapshot; selecting an external approved
  snapshot is still pending.
- Shape prototypes are represented but not yet consumed by fingering.
- Behavior profiles have not yet migrated into this common asset envelope.
- Virtual-instrument profiles intentionally use a separately pinned snapshot;
  a shared release manifest across both snapshot families is still pending.
- No user-correction or promotion UI exists yet.
- Knowledge release reports and shadow-comparison tooling remain future work.
