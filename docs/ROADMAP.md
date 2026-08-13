# FretPilot Roadmap

> Current milestone: **Prototype 0.1 — musician-reviewable score + virtual-guitar performance output**
>
> For an AI/Codex handoff, read `docs/AI_AGENT_HANDOFF.md` first. This roadmap tracks product priority; specialized `TI-*`, `GK-*`, `VI-*`, and `SE-*` details live in their project backlogs.

## Current implemented vertical slice

```text
MIDI
→ NormalizedTimeline
→ InstrumentStream resolution
→ layered guitar detection
→ selected guitar stream
→ rhythm / notation repair
→ section segmentation
→ per-section behavior profiles
→ per-section PlayingContext
→ per-section fingering + articulation
→ stream-wide GuitarTrackAnalysis
→ Guitar IR
├──→ PDF/TAB review output
├──→ GP5
└──→ Ample Guitar SC 4.x performance MIDI
```

The one-command prototype package uses the section-aware analysis path.

Track identification remains an incremental `TI-*` project and is **not** the main prototype blocker.

## Task families

```text
PV-*  immediate prototype/output quality
TI-*  InstrumentStream / guitar-track identification
GK-*  guitarist-like playing knowledge, style, phrasing, fingering
VI-*  virtual-guitar instrument knowledge and adapters
SE-*  evaluation, feedback, reproducibility, knowledge evolution
```

Long-term architecture:

- `docs/LONG_TERM_ARCHITECTURE.md`
- `docs/projects/guitar-playing-knowledge/`
- `docs/projects/track-identification/`
- `docs/projects/virtual-guitar-instruments/`
- `docs/projects/system-evolution/`

## Prototype status

### Input / stream selection

- [x] Standard MIDI import
- [x] MIDI Type 0 and Type 1
- [x] physical Track / Channel / active Program preservation
- [x] logical `InstrumentStream` resolution
- [x] layered guitar candidate ranking
- [x] explicit `--stream-id`
- [x] multiple-guitar ambiguity handling
- [ ] labeled corpus + Precision/Recall/F1 calibration (`TI-*`)

### Musical understanding / guitar execution

- [x] onset-grid analysis
- [x] basic duration spelling
- [x] score timing separate from source/performance timing
- [x] measure coordinates and cross-measure ties
- [x] standard six-string fingering
- [x] movable riff/arpeggio shape repair baseline
- [x] simultaneous chord distinct-string solving
- [x] hammer-on / pull-off / slide / vibrato inference
- [x] ringing-overlap normalization + `let_ring`
- [x] composable `PlayingContext`
- [x] context-aware fingering soft costs (`GK-003` baseline)
- [x] context-aware articulation confidence (`GK-004` baseline)
- [x] measure-aware section segmentation (`GK-010` baseline)
- [x] section behavior → PlayingContext (`GK-011` experimental baseline)
- [x] per-section fingering/articulation execution + global note-index remapping (`GK-015` baseline)
- [ ] explicit hand-position state and cross-section continuity (`GK-013`)
- [ ] reusable explicit shape-memory layer (`GK-012`)
- [ ] left-hand finger/barre assignment (`GK-014`)
- [ ] generic Performance Plan consumes `PerformancePreferences` (`GK-005` / remaining `GK-002`)

### Guitar IR

- [x] schema version `0.1`
- [x] tempo / time-signature maps
- [x] measures and score events
- [x] source/performance timing
- [x] string/fret assignment
- [x] generic articulation vocabulary
- [x] confidence / warnings / transformation log
- [x] section-context field reserved in track IR
- [ ] persist complete section/knowledge provenance as a stable IR contract
- [ ] generic performance-intent representation
- [ ] true multi-voice notation representation

### PDF / TAB

- [x] direct PDF renderer exists
- [x] six-line TAB review output
- [x] basic rhythm row with note heads, stems, beams, dots, and triplet marks
- [ ] musician-grade rhythmic grouping and collision avoidance
- [ ] proportional musical spacing
- [ ] high-quality rests/ties/slides/let-ring presentation
- [ ] section/phrase-aware system layout
- [ ] multi-voice TAB
- [ ] visual golden regression fixtures

### Guitar Pro 5

- [x] GP5 exporter
- [x] generated rests
- [x] duration decomposition
- [x] string/fret mapping
- [x] ties
- [x] supported basic articulations
- [x] write + parse-back automated validation
- [ ] hands-on Guitar Pro visual review
- [ ] real-song golden score review
- [ ] true two-voice output

### Ample Guitar SC 4.x

- [x] working performance-MIDI renderer
- [x] source timing / velocity preservation
- [x] sustain state
- [x] Hammer/Pull keyswitch behavior
- [x] Legato Slide keyswitch behavior
- [x] required legato overlap
- [x] selected generic articulation mappings when present in IR
- [x] parse-back event-order tests
- [ ] manual DAW/plugin listening validation
- [ ] bend curves
- [ ] vibrato rendering
- [ ] generic performance preferences before adapter translation

### Virtual-guitar adapter architecture

- [x] `VI-*` project boundary
- [x] provider-neutral `VirtualGuitarInstrumentProfile` skeleton
- [ ] migrate Ample static knowledge into generic profile (`VI-002`)
- [ ] adapter registry (`VI-003`)
- [ ] capability negotiation: native / approximated / unsupported (`VI-004`)
- [ ] common conformance suite (`VI-021`)
- [ ] second target after Ample is validated (`VI-030`)

## Active priority

### 1. `PV-002` — musician-readable score/TAB

The current renderer is useful for debugging but not yet a normal playable TAB experience.

Focus on:

- rhythmic engraving;
- spacing by musical time;
- rests/ties/slides/let-ring;
- readable systems/measures;
- visual golden fixtures.

Acceptance:

> At least one complete real guitar stream is comfortable to review as a first-draft TAB without Guitar Pro.

### 2. `GK-013` — hand-position state

Current section-aware execution treats each section as an independent phrase reset.

Add explicit hand-position planning so:

- weak boundaries can carry hand position;
- strong musical/style boundaries can justify a deliberate shift;
- shift cost/reason is explainable;
- physical fretboard constraints remain deterministic.

Acceptance:

> Section-aware context changes musical decisions without creating arbitrary or excessive position jumps at boundaries.

### 3. Finish `GK-002` via generic Performance Plan (`GK-005`)

Target architecture:

```text
section PlayingContext + canonical guitar intent
→ generic PerformancePlan
→ VI capability negotiation
→ target adapter
```

`PerformancePreferences` must affect generic musical intent before Ample-specific translation.

### 4. Human review / correction data

Implement the first small review/correction record path (`SE-020/021`) after the output is useful enough to review.

Important examples:

- wrong guitar stream;
- wrong section boundary;
- wrong role/style context;
- bad string/fret choice;
- bad articulation;
- unreadable notation measure.

These records become future evaluation assets, not direct runtime self-learning.

### 5. `VI-002` — generalize Ample knowledge

Preserve current Ample output while moving static product facts into the generic VI profile schema. Do not put plugin facts in Guitar IR or GK.

## Existing prototype package

```bash
fretpilot prototype song.mid \
  --all-likely-guitars \
  -o output/
```

Per stream, the package contains analysis JSON, Guitar IR JSON, GP5 when supported, Ample MIDI, and a processing report. Analysis/report include section-context summaries.

Section diagnostics:

```bash
fretpilot sections song.mid \
  --stream-id t0:ch2:p27
```

## Prototype 0.1 release definition

Prototype 0.1 is ready for external hands-on testing when:

1. full CI is green;
2. a real multi-track MIDI can generate packages for likely guitar streams;
3. at least one complete PDF/TAB or GP5 score has been visually reviewed;
4. at least one Ample MIDI has been played through the actual plugin;
5. unsupported cases generate warnings instead of silent corruption;
6. README commands remain reproducible.

Perfect Track identification, multi-product virtual-guitar support, and autonomous learning are explicitly **not** Prototype 0.1 blockers.

## Long-term evolution rule

```text
eligible evidence / corrections / licensed data
→ candidate knowledge/profile/model
→ evaluation / conformance / shadow comparison
→ approval
→ versioned production state
```

Runtime never silently learns from arbitrary internet content while processing a song.
