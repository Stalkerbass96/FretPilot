# Track Identification Backlog

Use this file as the canonical task list for the track-identification module. Each task has a stable ID so commits, pull requests, tests, and AI handoffs can reference the same work item.

Status markers:

- `[ ]` not started
- `[~]` in progress
- `[x]` completed and verified
- `[!]` blocked; document the blocker beneath the item

## P0 — Measurement and stable foundations

### [ ] TI-001 — Define a labeled fixture manifest

Create a machine-readable manifest for MIDI fixtures and expected labels.

Required fields:

```text
fixture_id
source/path or generator
license/provenance
midi_type
expected physical-track count
expected InstrumentStream identities
expected guitar decisions
optional section/behavior labels
known ambiguities
```

Requirements:

- Prefer synthetic MIDI generated in tests.
- Public-domain or explicitly licensed real-world MIDI may be referenced separately.
- Do not commit copyrighted commercial MIDI without permission.
- Include both positive and hard-negative guitar examples.

Acceptance criteria:

- A documented manifest schema exists.
- At least 12 synthetic fixtures cover the matrix in `TEST_PLAN.md`.
- Fixtures can be regenerated deterministically.
- Tests fail when expected stream identity or guitar decision changes.

Likely files:

```text
tests/fixtures/track_identification/
tests/fixture_manifest.json
scripts/generate_detection_fixtures.py
```

### [ ] TI-002 — Build the evaluation harness

Implement repeatable evaluation for Layers 1–3.

Required outputs:

- guitar/non-guitar precision, recall, and F1;
- three-way decision confusion matrix;
- false-positive and false-negative fixture lists;
- per-metadata-condition breakdown;
- optional threshold sweep.

Acceptance criteria:

- One command evaluates the fixture manifest.
- Results are deterministic.
- CI runs a regression gate without requiring external downloads.
- A human-readable report is produced in JSON and Markdown or console form.

Do not modify classifier weights solely to improve a single fixture before this harness exists.

### [ ] TI-003 — Centralize detector configuration

Move weights, thresholds, keyword dictionaries, guitar-range assumptions, and decision labels into versioned configuration objects.

Acceptance criteria:

- No scoring weight or threshold is hidden inside classification flow code.
- Configuration serializes to a stable debug representation.
- Default behavior remains backward-compatible.
- Tests can run alternate configurations without monkey-patching module globals.

### [ ] TI-004 — Add public output schema/versioning

Add a schema version to guitar-detection JSON output and golden snapshot tests.

Acceptance criteria:

- `GuitarDetectionReport` exposes a schema version.
- Public field removals/renames require explicit migration notes.
- Golden snapshots cover one Type-0 and one Type-1 file.

## P1 — Harden InstrumentStream resolution

### [ ] TI-010 — Distinguish instrument program changes from articulation controls

Current resolver splits by every active program. Some files or plugins may use program changes for articulations.

Research and design requirements:

- inspect change duration and return-to-program patterns;
- support a policy/configuration layer rather than hard-coded vendor assumptions;
- preserve the raw program event timeline;
- never merge streams destructively without recording evidence.

Acceptance criteria:

- a synthetic articulation-program fixture does not fragment one guitar performance incorrectly;
- a true mid-track instrument change still creates distinguishable logical regions/streams;
- the resolution reason is explainable.

### [ ] TI-011 — Model bank select and vendor metadata

Preserve CC0/CC32 bank selection and attach it to program metadata where present.

Acceptance criteria:

- bank metadata appears in normalized events and stream summaries;
- unknown vendor mappings remain neutral evidence;
- General MIDI behavior remains unchanged.

### [ ] TI-012 — Represent source provenance and metadata quality

Add structured provenance to each Layer-1/2 evidence item.

Examples:

```text
track_name_exact_keyword
instrument_name_alias
GM_program_family
percussion_channel_rule
vendor_mapping
```

Acceptance criteria:

- confidence calculations can distinguish independent corroborating sources from duplicate metadata;
- reasons remain human-readable.

## P1 — Improve Layer 1 and Layer 2 evidence

### [ ] TI-020 — Externalize multilingual instrument aliases

Move track/instrument keywords to a versioned data file or registry.

Acceptance criteria:

- aliases support exact tokens, abbreviations, and negative compounds;
- `bass guitar` remains distinct from six-string guitar;
- tests cover English plus at least three additional language/notation variants;
- adding aliases does not require editing classifier flow code.

### [ ] TI-021 — Add metadata conflict semantics

Represent agreement and conflict explicitly instead of only averaging scores.

Examples:

- track name says guitar, program says piano;
- track name is generic, instrument name says guitar;
- program says guitar, note behavior strongly contradicts it.

Acceptance criteria:

- result includes conflict flags/codes;
- confidence decreases for unresolved conflicts;
- probability and confidence remain separate concepts.

## P1 — Improve Layer 3 guitar behavior evidence

### [ ] TI-030 — Add physically valid chord-voicing feasibility

Replace simple `max_onset_polyphony <= 6` logic with a guitar voicing feasibility test.

The first implementation may use constraint solving or bounded search over string/fret candidates.

Acceptance criteria:

- impossible six-note clusters are rejected even though note count is six;
- common open and movable chord shapes are accepted;
- max fret and tuning are configurable;
- tests include ambiguous keyboard voicings.

### [ ] TI-031 — Detect staggered strum gestures

Group near-simultaneous ascending or descending note attacks into chord gestures.

Acceptance criteria:

- configurable millisecond/beat window;
- direction and spread duration are exposed;
- grouped strums influence behavior features without modifying source notes;
- dense melodic runs are not routinely collapsed into strums.

### [ ] TI-032 — Add keyboard/synth hard-negative features

Investigate features that reduce common false positives:

- sustain-pedal-driven overlap;
- impossible hand-span/polyphony patterns;
- extremely wide register use;
- independent bass and treble voices;
- dense repeated block chords beyond guitar voicing feasibility.

Acceptance criteria:

- measurable false-positive reduction on the labeled corpus;
- no material recall regression without documentation.

### [ ] TI-033 — Add tuning and instrument configuration

Support explicit:

- standard and alternate tunings;
- capo;
- fret count;
- six-, seven-, and eight-string configurations.

Acceptance criteria:

- Layer 3 receives an instrument model rather than using one global assumption;
- output states which model produced the score;
- unknown tuning can be represented as unresolved rather than guessed silently.

### [ ] TI-034 — Add pitch-bend and harmonic evidence

Preserve/analyze pitch-bend contours and possible harmonic ranges where useful.

Acceptance criteria:

- bend events remain tied to channel/time;
- guitar-like bends may contribute evidence but never become a sole identity rule;
- non-guitar expressive controllers do not automatically produce a positive result.

## P0/P1 — Layer 4 section and behavior architecture

### [ ] TI-040 — Define section/phrase data model

Create a representation for time-bounded behavior classification.

Minimum fields:

```text
section_id
stream_id
start_tick/start_beat
end_tick/end_beat
boundary reasons/confidence
feature vector
behavior profile matches
```

Acceptance criteria:

- one stream can carry multiple ordered sections;
- section results serialize independently from guitar identity;
- no behavior profile is permanently attached to the full stream by default.

### [ ] TI-041 — Implement baseline windowed segmentation

Start with deterministic windows and feature-change boundaries.

Possible baseline:

- 2/4/8-measure windows where measure data exists;
- beat-based fallback;
- adjacent feature-distance threshold;
- merge short/similar neighboring regions.

Acceptance criteria:

- synthetic riff → strumming → solo fixture produces at least three stable regions;
- boundaries include reasons and confidence;
- segmentation remains deterministic.

### [ ] TI-042 — Add motif/repetition features

Implement rhythmic and pitch-interval motif similarity for riff/breakdown evidence.

Acceptance criteria:

- transposition-tolerant interval representation is considered;
- repeated riffs rank above unrelated melodic sequences;
- metrics are exposed for debugging.

### [ ] TI-043 — Add harmonic and chord-role features

Add chord recognition sufficient for:

- power chords;
- triads;
- seventh/extended chords;
- voice-leading density;
- repeated comping shapes.

Acceptance criteria:

- features feed the profile library through canonical names;
- jazz-comping and breakdown rules no longer depend mainly on crude polyphony/range metrics.

### [ ] TI-044 — Version and calibrate behavior profiles

Move profiles to a versioned external representation or strongly typed registry with migration notes.

Acceptance criteria:

- vocabulary, feature dependencies, thresholds, and maturity are auditable;
- profile evaluation has labeled fixtures and metrics;
- experimental profiles are clearly distinguished from production-ready profiles.

## P2 — Product integration

### [~] TI-050 — Define auto-selection policy

Partial implementation (2026-08-14): the local API and frontend use
`guitar-only-v1`, which selects only `likely_guitar`, filters possible/unlikely
streams from generation cards, groups same-track/channel Program fragments, and
marks sparse likely parts as optional. CLI unification, manual override, and
remembered choices remain open.

Document and implement policies for:

- one likely guitar;
- several likely guitars;
- only possible guitars;
- no candidates;
- user override and remembered choice.

Acceptance criteria:

- CLI and future API/UI share the same policy object;
- no silent selection in ambiguous cases;
- user-visible explanation identifies why confirmation is required.

### [~] TI-051 — Add review-friendly detection report

Partial implementation (2026-08-14): `/api/detect` and completed jobs expose a
compact grouped summary with track name, channel, programs, note count,
probability, confidence, recommendation, and top reasons. Layer-4 profiles,
metadata-conflict warnings, and unsupported-assumption warnings remain open.

Produce a compact product-facing summary in addition to the full debug JSON.

Acceptance criteria:

- stream name, channel, program, note count, probability, confidence, decision, and top reasons;
- top Layer-4 profiles shown only for likely/selected guitar streams;
- warnings for conflicts and unsupported assumptions.

### [ ] TI-052 — Add user correction feedback format

Define a local, privacy-conscious correction record:

```text
source fingerprint
selected stream ID
correct/incorrect identity label
correct behavior sections/labels
optional notes
schema version
```

Acceptance criteria:

- corrections can be exported for later dataset curation;
- no upload or remote collection is assumed;
- source MIDI content is not embedded by default.

## Completed baseline work

### [x] TI-BASE-001 — Preserve channel/program metadata

Implemented in `src/fretpilot/midi/`.

### [x] TI-BASE-002 — Resolve InstrumentStream objects

Implemented in `src/fretpilot/detection/streams.py`.

### [x] TI-BASE-003 — Implement explainable Layers 1–3 V0

Implemented in `src/fretpilot/detection/guitar_classifier.py`.

### [x] TI-BASE-004 — Implement experimental Layer-4 registry

Implemented in `src/fretpilot/knowledge/guitar_behaviors.py`.

### [x] TI-BASE-005 — Add stream-aware CLI selection

Implemented in `src/fretpilot/cli.py`.
