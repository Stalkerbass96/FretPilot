# FretPilot Roadmap

## Current focus

The current vertical slice is now:

```text
MIDI
→ NormalizedTimeline with program metadata
→ InstrumentStream resolution
→ layered guitar detection
→ selected guitar stream
→ rhythm-grid analysis
→ phrase-level guitar fingering
→ basic articulation planning
→ JSON analysis
```

The next priority is **phrase/section segmentation**. One guitar stream may contain riff, strumming, solo, and breakdown sections, so the behavior library must classify musical regions rather than permanently labeling a whole channel. Notation-quality duration spelling, ties, and measure coordinates follow immediately after that.

## Phase 0 — Product definition

Goal: lock product boundaries before implementation.

- [x] define V0.1 target user and problem
- [x] define score vs performance outputs
- [x] define architecture boundaries
- [x] define canonical Guitar IR direction
- [ ] collect 10–20 representative MIDI test files
- [ ] define objective/subjective evaluation rubric

## Phase 1 — MIDI foundation

Goal: load real-world MIDI reliably and produce normalized timelines.

- [x] MIDI parser
- [x] tempo map
- [x] time-signature map
- [x] physical track listing
- [x] preserve MIDI channel
- [x] preserve program changes and program active at note-on
- [x] preserve optional instrument name
- [x] note-on/note-off normalization
- [ ] malformed/hanging-note repair policy
- [ ] measure coordinate conversion
- [x] beat coordinate conversion
- [x] JSON debug dump
- [x] parser diagnostics

Acceptance test:

> A MIDI file can be imported without losing physical track, channel, program, or musical timing information.

**Status:** Core V0 implemented; representative real-world MIDI corpus still needed.

## Phase 1.5 — Instrument stream resolution and guitar detection

Goal: find guitar material reliably even when MIDI metadata is missing or wrong.

- [x] resolve logical streams by physical track + channel + active program
- [x] Layer 1 track-name keyword evidence
- [x] Layer 2 channel/program/instrument-name evidence
- [x] Layer 3 deterministic note-behavior evidence
- [x] separate probability, confidence, per-layer reasons, and raw metrics
- [x] exclude General MIDI percussion channel
- [x] rank multiple guitar candidates
- [x] require explicit selection when multiple likely guitars exist
- [x] route rhythm/fingering/analysis through `--stream-id`
- [ ] labeled instrument-detection regression corpus
- [ ] precision/recall evaluation and threshold calibration
- [ ] stronger physical chord-voicing feasibility
- [ ] alternate-tuning-aware behavior analysis
- [ ] support program changes that represent intentional articulations rather than instrument changes

Acceptance test:

> Type-0 and Type-1 MIDI files produce correctly separated logical streams, and likely guitar streams rank above bass, drums, and unrelated instruments without blindly trusting metadata.

**Status:** Explainable three-layer V0 implemented.

## Phase 1.6 — Guitar behavior and style knowledge library

Goal: describe the role and performance behavior of guitar sections after guitar identity is established.

Initial profiles:

- [x] Solo / Lead
- [x] Riff
- [x] Strumming / Chord Rhythm
- [x] Breakdown / Heavy Low Riff
- [x] Jazz Comping

Infrastructure:

- [x] versioned rule/profile registry
- [x] keep Layer 4 separate from instrument identity
- [x] expose matched and missing features
- [ ] phrase/section segmentation
- [ ] repeated-pattern similarity
- [ ] strum timing and direction features
- [ ] power-chord and chord-extension features
- [ ] palm-mute and accent likelihood
- [ ] tonal/scale vocabulary
- [ ] labeled role/style corpus
- [ ] profile calibration and learned ranking model

Acceptance test:

> A single guitar stream can be segmented and labeled with changing roles such as riff → strumming → solo, with explanations and confidence per region.

**Status:** Whole-stream experimental profile registry implemented; section-level classification is next.

## Phase 2 — Rhythm repair

Goal: generate a readable symbolic rhythm while preserving source performance timing.

- [x] candidate quantization grids
- [x] note-start scoring
- [ ] note-duration scoring / spelling
- [ ] rests and ties
- [ ] phrase segmentation and phrase consistency
- [x] basic triplet detection
- [x] per-note confidence values
- [x] source/target onset deltas
- [ ] swing interpretation
- [ ] mixed-grid / tuplet handling

Acceptance test:

> Typical generated/extracted guitar MIDI becomes materially easier to read without flattening intentional rhythm.

**Status:** Onset-repair V0 implemented. Duration and phrase logic are the next core task.

## Phase 3 — Guitar fingering engine

Goal: assign physically plausible strings/frets at phrase level.

- [x] standard-tuning fretboard model
- [x] pitch → string/fret candidate generator
- [x] configurable max fret
- [x] transition cost model
- [x] dynamic-programming optimizer
- [x] lead/riff same-string preference where musically justified
- [x] impossible-note diagnostics
- [ ] polyphonic/chord fingering constraints
- [ ] alternate tunings

Acceptance test:

> Monophonic lead/riff MIDI exports with no impossible fingerings and substantially fewer awkward jumps than naive lowest-fret assignment.

**Status:** Monophonic lead/riff V0 implemented.

## Phase 4 — Basic articulation engine

Goal: add useful guitar technique without over-articulating.

Initial set:

- [ ] explicit pick/stroke planning
- [x] hammer-on
- [x] pull-off
- [x] slide
- [ ] legato slide distinction
- [x] vibrato
- [ ] palm mute
- [ ] natural harmonic
- [ ] bend

Additional work:

- [x] keep articulation vocabulary independent from plugin keyswitches
- [ ] phrase/style context
- [ ] confidence calibration
- [ ] optional AI ranking of ambiguous candidates

Acceptance test:

> Added articulations are physically valid and improve a majority of reference phrases in blind listening/review.

**Status:** Conservative deterministic V0 implemented for hammer-on, pull-off, slide, and vibrato.

## Phase 5 — Guitar IR builder + Guitar Pro exporter

Goal: produce an editable readable score from the canonical representation.

- [ ] build current analysis results into Guitar IR schema v0.1
- [ ] transformation/change log
- [ ] GP5 library evaluation / integration
- [ ] measures / voices
- [ ] notes / rests / ties
- [ ] string + fret
- [ ] basic articulations
- [ ] tempo / time signature
- [ ] round-trip test in Guitar Pro

Acceptance test:

> Export opens cleanly in Guitar Pro and matches the canonical score representation.

## Phase 6 — Ample Guitar adapter

Goal: turn Guitar IR into convincing Ample-compatible MIDI.

- [ ] choose first supported Ample Guitar product/version
- [ ] document articulation mapping
- [ ] keyswitch mapping
- [ ] velocity rules
- [ ] overlap / legato rules
- [ ] performance timing renderer
- [ ] reference DAW test project

Acceptance test:

> FretPilot-rendered MIDI sounds clearly more guitar-like than raw source MIDI using the supported Ample setup.

## Phase 7 — AI-assisted ambiguity resolution

Goal: use an external reasoning model only where it adds measurable value.

- [ ] provider interface
- [ ] structured phrase context schema
- [ ] strict structured output
- [ ] deterministic validation
- [ ] fallback with AI disabled
- [ ] compare AI-assisted decisions against rule-only baseline

Potential providers:

- OpenAI
- DeepSeek
- others via adapter

Acceptance test:

> AI improves selected ambiguous cases without making core processing dependent on provider availability.

## Phase 8 — MVP application

Goal: expose the pipeline as a simple product.

Initial user flow:

```text
Upload MIDI
→ Detect instrument streams
→ Select guitar stream
→ Humanize Guitar
→ Review changes / warnings
→ Download GP5
→ Download Ample MIDI
```

- [x] CLI skeleton and JSON inspection
- [x] layered stream detection command
- [x] stream-aware end-to-end analysis command
- [ ] API service
- [ ] simple web UI
- [ ] processing report
- [ ] low-confidence measure list
- [ ] downloadable GP5
- [ ] downloadable Ample MIDI

## Dataset / testing strategy

Before optimizing algorithms, maintain a curated regression set covering:

Instrument identity:

- type-0 full arrangement with many channels
- type-1 one-instrument-per-track arrangement
- correct guitar metadata
- incorrect guitar metadata
- missing program metadata
- bass guitar vs six-string guitar
- piano/synth parts that are guitar-playable
- drums and percussion

Guitar behavior:

- slow melodic lead
- fast scalar lead
- repeated riffs
- strummed chords
- power-chord breakdowns
- jazz comping
- sections that change role
- triplets and syncopation
- noisy note lengths and imperfect note-on timing
- large melodic leaps
- articulation-friendly phrases
- phrases where articulation should remain minimal

Every engine change should be evaluated against this set.
