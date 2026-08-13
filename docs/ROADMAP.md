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

## Task families and long-term architecture

FretPilot uses stable task prefixes:

```text
PV-*  prototype/output validation and immediate product quality
TI-*  instrument-stream / guitar-track identification
GK-*  guitar-playing knowledge, style, phrasing, and learning
SE-*  cross-project self-evolution infrastructure and governance
```

Long-term architecture and self-evolution are documented separately so they do not block Prototype 0.1:

- `docs/LONG_TERM_ARCHITECTURE.md`
- `docs/projects/system-evolution/README.md`
- `docs/projects/system-evolution/BACKLOG.md`
- `docs/projects/guitar-playing-knowledge/LEARNING_PIPELINE.md`

The core long-term rule is:

> Runtime uses deterministic constraints plus approved/versioned knowledge. New external data, user corrections, or learned models enter production only through offline evaluation and promotion.

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
- [x] movable riff/arpeggio shape repair baseline
- [x] hammer-on, pull-off, slide, and vibrato inference
- [x] ringing-overlap normalization
- [x] unequal same-onset chord-duration normalization
- [x] `let_ring` intent and transformation log
- [x] initial composable `PlayingContext` knowledge model
- [ ] thread `PlayingContext` through fingering/articulation (`GK-002` onward)
- [ ] phrase/section-aware context

### Guitar IR

- [x] schema version `0.1`
- [x] tempo and time-signature maps
- [x] measures and score events
- [x] source/performance timing
- [x] string/fret assignment
- [x] generic articulation vocabulary
- [x] confidence and warnings
- [x] CLI `fretpilot build-ir`
- [ ] context/knowledge provenance metadata (`SE-011`)

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

### PDF / TAB preview

- [x] direct PDF renderer exists for review without Guitar Pro
- [x] six-line TAB output
- [ ] musician-readable rhythmic engraving
- [ ] better phrase-aware spacing and beaming
- [ ] rest/tie/slide/bend notation quality
- [ ] multi-voice TAB rendering
- [ ] visual golden regression samples

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

### PV-002 — Score/TAB visual review

Review generated GP5/PDF output and record issues by measure/stream rather than changing heuristics from memory.

Review:

- measure alignment;
- rests;
- note values;
- ties;
- string/fret choices;
- chord grouping;
- let-ring markings;
- rhythmic readability;
- hand-position plausibility;
- excessive articulations;
- unreadable measures.

Acceptance:

> At least one complete real guitar stream is readable as an editable first draft or reviewable PDF/TAB draft.

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
- score/PDF/GP5 warnings;
- Ample warnings;
- low-confidence measures;
- runtime/knowledge version provenance when available.

Acceptance:

> A user can understand what FretPilot changed and where manual review is needed.

### PV-005 — Batch command

Add/use a command such as:

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

### Guitar performance and knowledge

- [ ] `PlayingContext`-aware fingering costs (`GK-003`)
- [ ] hand-position state (`GK-013`)
- [ ] shape memory (`GK-012`)
- [ ] left-hand finger assignment (`GK-014`)
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

Continue through the dedicated `TI-*` backlog without blocking output validation:

- labeled regression corpus;
- precision/recall/F1 evaluation;
- centralized configuration;
- alternate tunings and extended-range guitars;
- section-level behavior profiles;
- user override and correction data.

### Self-evolution infrastructure

Continue through `SE-*` and `GK-*` only after the prototype interfaces provide useful real data:

- runtime reproducibility manifest (`SE-002`);
- shared evaluation identity (`SE-003`);
- correction/golden-review registry (`SE-020/SE-021`);
- knowledge snapshot format/pinning (`GK-035`, `SE-030`);
- candidate vs production lifecycle (`GK-036`, `SE-031`);
- shadow comparison (`SE-032`);
- learned fingering ranker (`GK-041/GK-042`);
- optional model registry/integration (`SE-050/SE-051`).

## Release definition: Prototype 0.1

Prototype 0.1 is ready for external hands-on testing when:

1. the full CLI pipeline is green in CI;
2. one real multi-track MIDI can generate output packages for all likely guitars;
3. at least one generated score/TAB output has been visually reviewed;
4. at least one generated Ample SC MIDI has been played through the plugin;
5. known unsupported cases appear as warnings rather than silent corruption;
6. the README contains exact reproducible commands.

The long-term learning system is explicitly **not** a Prototype 0.1 release requirement.