# FretPilot Roadmap

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

- [ ] MIDI parser
- [ ] tempo map
- [ ] time-signature map
- [ ] track listing / selection
- [ ] note-on/note-off normalization
- [ ] malformed/hanging-note cleanup
- [ ] beat + measure coordinate conversion
- [ ] JSON debug dump

Acceptance test:

> A MIDI file can be imported and represented without losing its musical timing information.

## Phase 2 — Rhythm repair

Goal: generate a readable symbolic rhythm while preserving source performance timing.

- [ ] candidate quantization grids
- [ ] note-start scoring
- [ ] note-duration scoring
- [ ] ties
- [ ] phrase consistency
- [ ] triplet detection
- [ ] confidence values
- [ ] before/after diagnostics

Acceptance test:

> Typical generated/extracted guitar MIDI becomes materially easier to read without flattening intentional rhythm.

## Phase 3 — Guitar fingering engine

Goal: assign physically plausible strings/frets at phrase level.

- [ ] standard-tuning fretboard model
- [ ] pitch → string/fret candidate generator
- [ ] configurable max fret
- [ ] transition cost model
- [ ] dynamic-programming / graph optimizer
- [ ] same-string preference where musically justified
- [ ] impossible-note diagnostics

Acceptance test:

> Monophonic lead/riff MIDI exports with no impossible fingerings and substantially fewer awkward jumps than naive lowest-fret assignment.

## Phase 4 — Basic articulation engine

Goal: add useful guitar technique without over-articulating.

Initial set:

- [ ] pick
- [ ] hammer-on
- [ ] pull-off
- [ ] slide
- [ ] legato slide
- [ ] vibrato
- [ ] palm mute
- [ ] natural harmonic

Acceptance test:

> Added articulations are physically valid and improve a majority of reference phrases in blind listening/review.

## Phase 5 — Guitar Pro exporter

Goal: produce an editable readable score.

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

- [ ] API/CLI first
- [ ] simple web UI
- [ ] processing report
- [ ] low-confidence measure list
- [ ] downloadable outputs

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
