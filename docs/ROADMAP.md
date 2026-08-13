# FretPilot Roadmap

## Current milestone

FretPilot now has a complete CLI prototype path for both target outputs:

```text
MIDI
→ NormalizedTimeline
→ InstrumentStream resolution
→ layered guitar detection
→ selected guitar stream
→ rhythm repair suggestions
→ fingering
→ articulation planning
→ Guitar IR
├──→ Guitar Pro 5 export
└──→ Ample Guitar SC 4.x performance MIDI
```

Track identification remains an incremental project under:

```text
docs/projects/track-identification/
GitHub Issue #1
```

It is no longer the main blocker. The active priority is **prototype validation and output quality**.

## Prototype status

### Input and stream selection

- [x] Standard MIDI import
- [x] Type 0 and Type 1 support
- [x] physical Track / Channel / active Program preservation
- [x] logical `InstrumentStream` resolution
- [x] three-layer guitar candidate ranking
- [x] explicit `--stream-id` selection
- [x] multiple-guitar ambiguity handling

### Musical processing

- [x] onset-grid analysis
- [x] basic duration grid spelling
- [x] source timing kept separate from score timing
- [x] measure coordinates
- [x] cross-measure ties
- [x] standard six-string fingering
- [x] hammer-on, pull-off, slide, and vibrato inference
- [x] ringing-overlap normalization
- [x] unequal same-onset chord-duration normalization
- [x] `let_ring` intent and transformation log

### Guitar IR

- [x] schema version `0.1`
- [x] tempo and time-signature maps
- [x] measures and score events
- [x] source/performance timing
- [x] string/fret assignment
- [x] generic articulation vocabulary
- [x] confidence and warnings
- [x] CLI `fretpilot build-ir`

### Guitar Pro 5

- [x] PyGuitarPro dependency
- [x] Guitar IR adapter
- [x] generated rests
- [x] straight, dotted, and triplet duration decomposition
- [x] string/fret mapping
- [x] ties
- [x] single-note let ring
- [x] hammer-on / pull-off
- [x] slide
- [x] vibrato
- [x] `.gp5` writing
- [x] automated write-and-parse round trip
- [x] CLI `fretpilot export-gp5`
- [ ] visual inspection in Guitar Pro
- [ ] real-song golden output review
- [ ] safe representation for partial let-ring markings inside chords
- [ ] true two-voice notation

### Ample Guitar SC 4.x

- [x] versioned `ample-guitar-sc-v4` profile
- [x] documented raw-MIDI keyswitch mapping
- [x] original source timing and velocity rendering
- [x] Sustain state
- [x] Hammer-On / Pull-Off keyswitch
- [x] Legato Slide keyswitch
- [x] required legato note overlap
- [x] Natural Harmonic / Palm Mute / Slide In-Out mapping when present in IR
- [x] tempo and time-signature tracks
- [x] MIDI parse-back event-order test
- [x] CLI `fretpilot export-ample-sc`
- [ ] manual DAW test with Ample Guitar SC 4.x
- [ ] vibrato rendering
- [ ] bend curves
- [ ] pick direction and accent shaping

## Active Phase — Prototype validation

The next work should be completed in this order.

### PV-001 — Real output package

For one selected real MIDI file and each likely guitar stream, generate:

```text
<stream-id>.analysis.json
<stream-id>.guitar-ir.json
<stream-id>.gp5
<stream-id>.ample-sc.mid
<stream-id>.report.json
```

The report must include warnings, unsupported features, note counts, changes, and confidence summaries.

Acceptance:

> A user can inspect every candidate guitar part without manually reconstructing CLI commands.

### PV-002 — Guitar Pro visual review

Open generated `.gp5` files in Guitar Pro and review:

- measure alignment;
- rests;
- note values;
- ties;
- string/fret choices;
- chord grouping;
- let-ring markings;
- excessive articulations;
- unreadable measures.

Record issues by measure and stream ID instead of changing heuristics from memory.

Acceptance:

> At least one complete real guitar stream is readable as an editable first draft.

### PV-003 — Ample SC listening review

Load generated MIDI into a DAW with Ample Guitar SC 4.x and review:

- note range and octave;
- Sustain state;
- Hammer/Pull triggering;
- Legato Slide triggering;
- note overlap;
- hanging notes;
- timing against the original MIDI;
- excessive or missing legato.

Acceptance:

> The exported MIDI plays from beginning to end without broken keyswitch state or hanging notes, and selected legato passages trigger correctly.

### PV-004 — Processing report

Add a single machine-readable and human-readable report containing:

- selected stream metadata;
- guitar probability and evidence;
- rhythm grid;
- repaired onset/duration counts;
- let-ring conversions;
- unplayable notes;
- articulation counts;
- GP5 warnings;
- Ample warnings;
- low-confidence measures.

Acceptance:

> A user can understand what FretPilot changed and where manual review is needed.

### PV-005 — Batch command

Add a command such as:

```bash
fretpilot prototype song.mid --all-likely-guitars -o output-directory
```

It should generate the complete output package for all likely guitar streams.

Acceptance:

> The test MIDI with several guitar candidates can be processed in one command.

## Quality work after validation

### Notation quality

- [ ] true two-voice separation
- [ ] sustained bass plus upper melody
- [ ] chord-voicing feasibility
- [ ] explicit tuplets and dotted-note spelling in Guitar IR
- [ ] swing interpretation
- [ ] phrase/section segmentation
- [ ] section-dependent quantization grids

### Guitar performance

- [ ] bend detection and rendering
- [ ] vibrato controller/keyswitch strategy
- [ ] palm-mute inference
- [ ] pick-direction planning
- [ ] accent and velocity shaping
- [ ] strum timing and direction
- [ ] position/string forcing for supported Ample products

### Product application

- [ ] processing service/API
- [ ] upload UI
- [ ] guitar-stream selection UI
- [ ] score/change preview
- [ ] downloadable output package
- [ ] user correction capture

### Track identification

Continue through the dedicated backlog without blocking output validation:

- labeled regression corpus;
- precision/recall/F1 evaluation;
- centralized configuration;
- alternate tunings and extended-range guitars;
- section-level behavior profiles;
- user override and correction data.

## Release definition: Prototype 0.1

Prototype 0.1 is ready for external hands-on testing when:

1. the full CLI pipeline is green in CI;
2. one real multi-track MIDI can generate output packages for all likely guitars;
3. at least one generated GP5 has been opened and visually reviewed;
4. at least one generated Ample SC MIDI has been played through the plugin;
5. known unsupported cases appear as warnings rather than silent corruption;
6. the README contains exact reproducible commands.
