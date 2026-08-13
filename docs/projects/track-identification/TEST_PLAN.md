# Track Identification Test Plan

This document defines the minimum evidence required before changing detection weights, thresholds, feature semantics, or behavior-profile maturity.

## Test layers

### 1. Unit tests

Validate isolated rules and data models.

Required areas:

- General MIDI program name/family mapping;
- track/instrument keyword matching;
- percussion-channel handling;
- feature extraction from synthetic note sequences;
- score combination and decision thresholds;
- confidence behavior under agreement and conflict;
- behavior-profile rule evaluation;
- serialization and schema versioning.

### 2. Stream-resolution tests

Validate physical Track, Channel, and Program handling.

Required cases:

1. Type-0 file with guitar, bass, drums, and piano on separate channels.
2. Type-1 file with one instrument per physical track.
3. One physical track containing two melodic channels with the same program.
4. One channel with a true mid-song instrument program change.
5. One channel with program changes used as articulation controls.
6. Missing program metadata.
7. Program change occurring after some notes.
8. Empty tracks and metadata-only tracks.
9. General MIDI channel 10 percussion.
10. Multiple drum/percussion tracks outside channel 10 with explicit metadata.

Each test must assert:

- physical track count;
- logical stream count;
- stream IDs;
- channel/program provenance;
- note ownership;
- no lost or duplicated notes.

## Synthetic identity fixture matrix

The committed CI corpus should contain deterministic synthetic fixtures covering at least:

| Fixture class | Metadata | Note behavior | Expected result |
|---|---|---|---|
| Clear lead guitar | Track + GM guitar agree | Monophonic, playable | likely guitar |
| Clear rhythm guitar | Track + GM guitar agree | Guitar-feasible chords | likely guitar |
| Guitar without metadata | None/unknown | Strong guitar behavior | possible or likely, based on calibrated policy |
| Misnamed piano as guitar | Track says guitar | Piano program + keyboard behavior | conflict; not silently likely |
| Guitar program with impossible notes | GM guitar | Strongly impossible range/polyphony | conflict; lower confidence |
| Bass guitar | Bass naming/program | Bass behavior | unlikely six-string guitar |
| Drums | Drum channel | Percussion notes | unlikely guitar |
| Guitar-playable piano arpeggio | Piano program | Guitar-playable notes | hard negative |
| Wide synth pad | Synth program | Dense/wide polyphony | unlikely guitar |
| Mixed Type-0 arrangement | Several channels | Mixed | correct ranked streams |
| Multiple guitars | Several guitar streams | Different roles | multiple likely; require selection |
| Missing/incorrect metadata | Conflicting | Ambiguous | possible guitar with reasons |

## Layer-4 behavior fixture matrix

Behavior tests must eventually operate on time-bounded sections, not only whole streams.

Required section classes:

- slow melodic solo;
- fast scalar solo;
- repeated single-note riff;
- power-chord riff;
- muted pedal-tone riff;
- down-strummed chord rhythm;
- alternating strum direction;
- arpeggiated chord texture;
- breakdown/heavy low riff;
- jazz comping with seventh/extended chords;
- clean chordal pop accompaniment;
- mixed stream: riff → strumming → solo;
- ambiguous section that should produce low confidence.

## Evaluation metrics

### Layers 1–3 identity

Report at minimum:

- binary guitar/non-guitar precision;
- binary recall;
- binary F1;
- three-way confusion matrix for `likely_guitar`, `possible_guitar`, and `unlikely_guitar`;
- false positives and false negatives by fixture ID;
- performance grouped by metadata condition:
  - correct metadata;
  - no metadata;
  - misleading metadata;
  - conflicting metadata;
- performance grouped by instrument class:
  - guitar;
  - bass;
  - drums;
  - piano/keyboard;
  - synth;
  - other pitched instruments.

Accuracy alone is insufficient because class balance may be artificial.

### Layer 4 behavior

Once section labels exist, report:

- per-profile precision, recall, and F1;
- macro and weighted F1;
- confusion matrix;
- section-boundary precision/recall within a documented tolerance;
- multi-label metrics when one section legitimately has multiple behaviors;
- coverage and abstention rate for low-confidence classifications.

## Threshold/calibration procedure

1. Keep a fixed development set and a held-out regression set.
2. Sweep identity thresholds only through the evaluation harness.
3. Record the metric tradeoff and selected rationale.
4. Avoid tuning on one named commercial song.
5. Prefer an explicit `possible_guitar` or abstention state over confident false positives.
6. Version threshold/config changes and update golden outputs.

## Golden output tests

Maintain stable JSON snapshots for:

- a Type-0 mixed arrangement;
- a Type-1 multi-track arrangement;
- conflicting metadata;
- missing metadata;
- multiple likely guitars;
- no likely guitar;
- one mixed-behavior guitar stream after section segmentation exists.

Golden snapshots should cover the public structure, not floating-point values that are intentionally unstable. Round numeric outputs consistently.

## Property/invariant tests

Useful invariants:

- stream resolution neither loses nor duplicates completed notes;
- the same input and configuration produce identical output;
- changing a track name does not alter Layer-3 metrics;
- changing a program does not alter Layer-3 note features;
- Layer-4 profile results never alter Layers 1–3 guitar probability;
- drum-channel classification remains negative regardless of pitch values;
- all probabilities/confidences stay within `[0, 1]`;
- candidate ranking is deterministic under ties;
- source MIDI objects are not mutated by classification.

## Real-world validation

Real-world files are valuable but must be handled carefully.

- Do not commit commercial copyrighted MIDI without permission.
- Store only fixture manifests, expected summaries, or hashes where licensing is unclear.
- Use public-domain, Creative Commons, or explicitly licensed files for reproducible external validation.
- Maintain source provenance and license notes.
- A file used manually in a chat or local test is not part of the regression corpus until it is represented in the manifest.

The previously inspected `The_Police_-_Message_in_a_Bottle.mid` is a useful manual Type-0 case but is not present in the repository and must not be used as a CI dependency.

## Commands and CI gates

Current baseline:

```bash
pytest -q
```

Planned evaluation command, name subject to implementation:

```bash
python -m fretpilot.evaluation.track_identification \
  --manifest tests/fixture_manifest.json \
  --output build/track-identification-report.json
```

Before merging a scoring change:

1. Unit and regression tests pass.
2. Evaluation report is generated.
3. Metric changes are summarized.
4. False-positive and false-negative changes are reviewed.
5. `STATUS.md`, `BACKLOG.md`, and `GUITAR_DETECTION.md` are updated where applicable.

## Minimum quality gate before production claims

No production accuracy claim should be made until:

- at least 100 independently labeled instrument streams are evaluated;
- hard negatives include keyboard/synth parts that are physically guitar-playable;
- more than one MIDI exporter/source is represented;
- the held-out set is not used for threshold tuning;
- confidence/abstention behavior is measured;
- results can be regenerated from a documented command and versioned configuration.
