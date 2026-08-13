# FretPilot Roadmap

## Current focus

The first vertical slice is now runnable:

```text
MIDI
→ NormalizedTimeline
→ rhythm-grid analysis
→ phrase-level guitar fingering
→ basic articulation planning
→ JSON analysis
```

The next priority is **notation-quality rhythm**: duration spelling, ties, phrase boundaries, and measure coordinates. Those pieces should be stable before GP5 export is implemented.

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
- [x] track listing / CLI selection
- [x] note-on/note-off normalization
- [ ] malformed/hanging-note repair policy
- [ ] measure coordinate conversion
- [x] beat coordinate conversion
- [x] JSON debug dump
- [x] parser diagnostics

Acceptance test:

> A MIDI file can be imported and represented without losing its musical timing information.

**Status:** Core V0 implemented; representative real-world MIDI corpus still needed.

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
→ Select Track
→ Humanize Guitar
→ Review changes / warnings
→ Download GP5
→ Download Ample MIDI
```

- [x] CLI skeleton and JSON inspection
- [x] end-to-end analysis command
- [ ] API service
- [ ] simple web UI
- [ ] processing report
- [ ] low-confidence measure list
- [ ] downloadable GP5
- [ ] downloadable Ample MIDI

## Dataset / testing strategy

Before optimizing algorithms, maintain a small curated regression set covering:

- slow melodic lead
- fast scalar lead
- repeated riffs
- triplets
- syncopation
- noisy note lengths
- imperfect note-on timing
- large melodic leaps
- notes with multiple plausible fretboard positions
- articulation-friendly phrases
- phrases where articulation should remain minimal

Every engine change should be evaluated against this set.
