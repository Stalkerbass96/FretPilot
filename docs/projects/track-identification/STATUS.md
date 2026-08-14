# Track Identification Status

Last reviewed against repository `main`: 2026-08-14.

This document distinguishes implemented behavior from planned behavior. Update it whenever a backlog item changes module capabilities.

## Implemented baseline

### MIDI metadata preservation

Implemented in `src/fretpilot/midi/`:

- physical MIDI track index and track name;
- optional MIDI `instrument_name`;
- MIDI channel on every normalized note;
- program-change events;
- program active at note-on stored on each normalized note;
- General MIDI program name and family helpers;
- source ticks and derived beat coordinates;
- parser diagnostics for unmatched, zero-length, and unclosed notes.

The importer does not quantize or repair musical timing.

### InstrumentStream resolution

Implemented in `src/fretpilot/detection/streams.py`:

- notes are grouped by physical track, MIDI channel, and active program;
- Type-0 and Type-1 files use the same logical representation;
- stream IDs use `t{track}:ch{channel}:p{program}`;
- each stream can be exposed as a `NormalizedTrack` for existing downstream engines.

Current limitation: any program change fragments a channel into another stream, even when a plugin/exporter uses program changes as articulation controls.

### Layers 1–3 guitar identity classification

Implemented in `src/fretpilot/detection/guitar_classifier.py`.

Layer 1 currently uses track-name keywords.

Layer 2 currently uses:

- General MIDI percussion channel exclusion;
- General MIDI program family;
- optional `instrument_name` keywords.

Layer 3 currently extracts:

- note count and pitch range;
- standard six-string 0–24 fret playable-pitch ratio;
- onset count;
- maximum and mean onset polyphony;
- monophonic-onset ratio;
- 2–6 note chord-onset ratio;
- adjacent interval within one octave ratio;
- repeated-pitch ratio;
- low-register ratio;
- short-note ratio.

The current combined identity score is:

```text
30% Layer 1
35% Layer 2
35% Layer 3
```

Current thresholds:

```text
>= 0.75  likely_guitar
>= 0.62  possible_guitar
<  0.62  unlikely_guitar
```

These numbers are uncalibrated V0 heuristics. They must not be described as statistically accurate until the evaluation backlog is completed.

### Layer 4 behavior library

Implemented in `src/fretpilot/knowledge/guitar_behaviors.py`:

- versioned profile registry (`LIBRARY_VERSION = "0.1"`);
- inspectable weighted feature rules;
- profile match output with score, status, matched features, and missing features;
- experimental profiles for solo, riff, strumming, breakdown, and jazz comping.

The identity classifier still reports whole-stream profile matches for debugging.
The production prototype additionally uses `src/fretpilot/analysis/sections.py`
and `section_contexts.py` to:

- create deterministic measure-window regions;
- split/merge regions by behavior-feature distance;
- run the experimental profile library per section;
- derive an independent `PlayingContext` for each section.

Current limitation: labels and boundaries are deterministic experimental rules,
not calibrated truth. They do not yet understand harmony, strum timing,
physical chord voicings, palm muting, or reliable genre context.

### CLI integration

Implemented in `src/fretpilot/cli.py`:

```bash
fretpilot tracks song.mid
fretpilot tracks song.mid -o tracks.json
fretpilot rhythm song.mid --stream-id STREAM_ID
fretpilot fingering song.mid --stream-id STREAM_ID
fretpilot analyze song.mid --stream-id STREAM_ID
```

Selection behavior:

- one likely guitar stream: downstream analysis may select it automatically;
- no likely guitar stream: command asks the user to inspect candidates;
- multiple likely guitar streams: command requires explicit `--stream-id`;
- `--track` remains as a legacy physical-track selector.

### Guitar-only product preflight

Implemented across `src/fretpilot/detection/review.py`, `src/fretpilot/api/`,
and `web/src/`:

- `POST /api/detect` accepts a MIDI upload and returns a compact review summary;
- only `likely_guitar` streams enter the generated candidate list;
- `possible_guitar` and `unlikely_guitar` streams are hidden from candidate cards
  and reported as filtered counts;
- each candidate includes probability, decision confidence, note count, channel,
  recommendation, and concise reasons;
- fragments sharing the same physical track and channel are grouped into one
  product-facing guitar part while retaining their individual stream IDs;
- short high-confidence parts are marked `optional`, but remain selected under
  the current policy;
- completed conversion results use the same grouping and evidence metadata.

The frontend does not yet provide manual inclusion/exclusion controls. This is
therefore a guitar-only V0 policy, not completion of the full user-override
requirements in `TI-050`.

### Automated tests

Current detection coverage in `tests/test_guitar_detection.py` includes:

- Type-0 MIDI split into channel/program streams;
- guitar versus bass versus General MIDI drums;
- positive track-name evidence conflicting with a non-guitar program;
- proof that Layer-4 profiles are separate from the guitar identity decision.

API and frontend tests additionally cover:

- grouping multiple Program fragments into one review card;
- filtering a non-guitar stream from the candidate list;
- confidence/recommendation rendering and the `/api/detect` upload contract;
- propagation of detection metadata into completed conversion jobs.

Section tests additionally cover deterministic riff → strumming → solo
segmentation, adjacent-window merging, per-section contexts, and stream-wide
source-note remapping.

GitHub Actions runs `pytest -q` on pushes to `main` and pull requests.

## Known limitations

### Data and evaluation

- No committed labeled real-world corpus.
- No precision, recall, F1, confusion matrix, calibration curve, or source-level error report.
- No golden JSON snapshots for public output stability.
- The manually tested `The_Police_-_Message_in_a_Bottle.mid` file is not committed and must not be assumed available to another AI agent.
- The manually tested `Led_Zeppelin_-_Stairway_to_Heaven.mid` file is not committed
  and must not be assumed available to another AI agent. On 2026-08-14 the V0
  policy resolved 15 logical streams into 7 displayed guitar parts: 8 likely
  stream fragments, 1 possible stream filtered, and 6 unlikely streams filtered.
  This is a regression observation, not calibration evidence.

### Layer 1 metadata

- Keyword list is hard-coded.
- Localization coverage is minimal.
- No tokenization or alias configuration file.
- Negative words can be ambiguous in compound track names.

### Layer 2 metadata

- General MIDI assumptions may not hold for vendor-specific mappings.
- Program changes used for articulations may create false stream splits.
- Bank-select and drum-kit metadata are not modeled.
- No provenance/quality score for metadata sources.

### Layer 3 note behavior

- Standard tuning and 24 frets are hard-coded through the current guitar model.
- Pitch-class behavior alone cannot reliably distinguish guitar from playable piano/synth parts.
- Chord feasibility checks only onset size, not actual string/fret voicing.
- Staggered strums are not grouped into a chord gesture.
- Sustain-pedal and overlapping keyboard voices are not treated specially.
- Pitch bend, capo, alternate tuning, seven/eight-string guitar, harmonics, and transposed MIDI are not represented.
- Feature values are whole-stream aggregates and may hide section changes.

### Layer 4 behavior/style

- Whole-stream matches remain in identity/debug reports; runtime execution is
  section-aware.
- Section boundaries and profiles are uncalibrated deterministic baselines.
- No beat-level/free-form phrase model beyond deterministic measure-window
  change points.
- No repeated-motif similarity.
- No chord recognition or harmonic vocabulary.
- No strum direction/timing features.
- No power-chord or breakdown-specific voicing model.
- No role/style labeled corpus.

## Current code map

```text
src/fretpilot/midi/models.py
    NormalizedNote, NormalizedTrack, ProgramEvent, NormalizedTimeline

src/fretpilot/midi/parser.py
    load_midi(); preserves track/channel/program/timing metadata

src/fretpilot/midi/gm.py
    General MIDI program names and families

src/fretpilot/detection/models.py
    InstrumentStream, feature/result/report data models

src/fretpilot/detection/streams.py
    resolve_instrument_streams()

src/fretpilot/detection/guitar_classifier.py
    Layers 1–3, feature extraction, probability/confidence, report ranking

src/fretpilot/detection/review.py
    Guitar-only selection policy and product-facing grouped candidate summaries

src/fretpilot/analysis/sections.py, src/fretpilot/analysis/section_contexts.py
    Section model, deterministic segmentation, and per-section behavior context

src/fretpilot/api/app.py, src/fretpilot/api/jobs.py
    Upload preflight and detection metadata in conversion jobs

web/src/App.tsx
    Candidate confidence, recommendations, filtered counts, and grouped results

src/fretpilot/knowledge/guitar_behaviors.py
    Layer-4 profile registry and matching

src/fretpilot/cli.py
    `tracks` command and stream selection for downstream analysis

tests/test_midi_parser.py
tests/test_guitar_detection.py
```

## Do not claim yet

Until backed by the evaluation plan, do not claim that FretPilot:

- identifies guitar tracks with a particular accuracy percentage;
- reliably identifies genre;
- distinguishes guitar from piano or synth in all metadata-free MIDI;
- detects solo, riff, strumming, breakdown, or jazz at production quality;
- understands physical polyphonic guitar voicings;
- supports alternate tunings or extended-range guitars.

## Next recommended task

Implement `TI-001` and `TI-002` from `BACKLOG.md`: define the labeled fixture manifest and evaluation harness before changing weights or adding more profile rules.
