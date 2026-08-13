# FretPilot Product Definition

## 1. Product statement

FretPilot converts imperfect MIDI into **guitar-aware notation** and **performance-ready MIDI**.

The initial user problem is simple:

> I have a MIDI guitar part extracted or generated from an AI music source. It contains useful musical information, but the rhythm is messy, the fingering is not guitar-realistic, and it has no meaningful guitar articulations. I want a clean Guitar Pro score and a convincing Ample Guitar performance without manually rebuilding the part.

FretPilot solves the gap between **generic MIDI** and **guitar performance intent**.

---

## 2. Target user

Primary users for V0.1:

- songwriters using Suno or other AI music generators
- guitarists who want editable tabs from generated MIDI
- producers using virtual guitars
- arrangers who want a fast starting point rather than manual transcription

The first version is not intended to replace a professional engraver or guitarist in every edge case. It should produce a strong, editable first result.

---

## 3. V0.1 scope

### Input

- Standard MIDI File (`.mid`)
- one selected guitar track at a time
- initial focus: monophonic or mostly monophonic lead/riff material
- 6-string guitar
- standard tuning by default: E2 A2 D3 G3 B3 E4

### Output

FretPilot produces two related outputs:

1. **Score output**
   - Guitar Pro-compatible file
   - initial implementation target: `.gp5`
   - readable rhythm
   - string/fret assignments
   - guitar articulations where supported

2. **Performance output**
   - Standard MIDI File tailored for Ample Guitar
   - note timing and velocity suitable for playback
   - keyswitch/control events for supported articulations
   - performance humanization that does not damage score readability

### Core capabilities

V0.1 must support:

- MIDI parsing and normalization
- tempo and time-signature preservation/detection where possible
- phrase-aware rhythm quantization and repair
- detection of suspicious note lengths / overlaps / gaps
- playable string and fret assignment
- position continuity optimization
- basic guitar articulation inference
- score/performance separation
- GP5 export
- Ample Guitar MIDI export

---

## 4. Explicit non-goals for V0.1

Do not expand scope before the core pipeline is reliable.

V0.1 does **not** need to support:

- full-band arrangement
- bass, piano, strings, or drums
- audio-to-MIDI transcription
- audio stem separation
- tablature OCR
- every alternate tuning
- 7/8-string guitars
- full chord-comping optimization
- automatic tone/amp preset generation
- direct DAW plugin hosting
- model training from scratch
- fully autonomous LLM-based MIDI rewriting

These may be revisited after the guitar pipeline is validated.

---

## 5. Core product workflow

```text
1. Import MIDI
2. Select guitar track
3. Analyze musical structure
4. Repair rhythm
5. Build candidate guitar fingerings
6. Optimize fingering across phrases
7. Infer articulation candidates
8. Validate playability and consistency
9. Build canonical FretPilot Guitar IR
10. Render score representation
11. Render Ample Guitar performance representation
12. Export GP5 + MIDI
```

The user should eventually experience this as one action, for example **Humanize Guitar**, while advanced settings remain optional.

---

## 6. Product logic

### 6.1 MIDI normalization

The parser converts raw MIDI events into a clean note timeline.

Responsibilities:

- merge note-on/note-off events
- normalize PPQ/ticks to musical time
- preserve tempo changes
- preserve time signatures
- detect malformed or hanging notes
- resolve tiny accidental overlaps
- group notes into measures and provisional phrases

Output: normalized note events, not yet guitar-specific.

### 6.2 Musical analysis

The analysis layer derives context required by later decisions.

Possible features:

- estimated key / scale context
- beat strength
- measure position
- local tempo context
- phrase boundaries
- melodic direction
- repeated motif detection
- chord context when available or inferable
- role classification such as lead, riff, arpeggio

Not every feature must ship in the first implementation, but the architecture should leave room for them.

### 6.3 Rhythm repair

Rhythm repair is **not simply nearest-grid quantization**.

It should choose a musically plausible symbolic rhythm while preserving intentional feel.

Candidate grid values may include:

- quarter notes
- eighth notes
- sixteenth notes
- triplets
- dotted values
- ties
- selected syncopated combinations

A rhythm candidate should be scored using factors such as:

- timing distance from the original MIDI
- consistency with neighboring notes
- beat/meter fit
- phrase consistency
- complexity penalty
- repeated-pattern consistency

The engine should expose confidence and preserve the original timing separately for performance rendering.

### 6.4 Guitar fingering

A MIDI pitch can map to multiple string/fret positions. FretPilot must treat fingering as an optimization problem across a phrase rather than choosing each note independently.

Candidate positions must satisfy:

- pitch correctness
- tuning constraints
- fret range
- string availability

The optimizer should prefer:

- playable hand movement
- position continuity
- sensible string changes
- avoiding unnecessary large fret jumps
- preserving same-string motion when it enables meaningful guitar techniques
- idiomatic fretboard regions

Future versions may support player profiles such as beginner, standard, shred/lead, or acoustic.

### 6.5 Articulation planning

The articulation engine adds technique only when musically and physically plausible.

Initial candidate set:

- normal picked note
- hammer-on
- pull-off
- slide / legato slide
- vibrato
- palm mute
- natural harmonic where strongly implied and playable

Later candidates:

- bend
- pre-bend
- release
- tapping
- dead note
- pinch harmonic
- tremolo picking

Articulation decisions should combine deterministic constraints with contextual scoring.

Examples:

- hammer-on/pull-off requires a compatible fingering relationship
- slide generally requires a same-string path
- vibrato is more likely on sustained or phrase-ending notes
- palm mute is more likely on repeated low-string rhythmic figures than on lyrical lead notes

### 6.6 AI-assisted interpretation

LLMs such as ChatGPT or DeepSeek are optional reasoning providers, not core runtime dependencies.

Good use cases:

- classify phrase intent
- choose between similarly plausible articulation plans
- infer stylistic intent from a compact symbolic phrase description
- explain low-confidence decisions to the user

Bad use cases:

- directly editing binary MIDI
- calculating exact MIDI timing
- enforcing fretboard constraints
- determining file-format correctness
- acting as the sole source of articulation decisions

All AI responses must be parsed into a strict structured schema and validated by deterministic rules before use.

---

## 7. Two-output model

FretPilot explicitly separates notation from playback.

### Score representation

Optimized for:

- readability
- clean note values
- sensible ties
- stable fingering
- clear articulations
- Guitar Pro editing

### Performance representation

Optimized for:

- convincing playback
- microtiming
- velocity shaping
- note overlaps required by sampled-instrument legato
- keyswitches
- plugin-specific articulation controls

The performance output may deliberately differ from the score timing. This is expected behavior.

---

## 8. Success criteria for V0.1

The first version is successful if a user can take a generated lead/riff MIDI and, with minimal manual work, obtain:

- a clearly improved readable guitar tab
- physically plausible fingering
- noticeably more natural articulation
- an Ample Guitar MIDI that sounds better than the raw source
- deterministic, reproducible exports

A useful internal test metric is not only "is the MIDI valid?" but also:

- How many manual edits does a guitarist need after export?
- How often are fingerings impossible or awkward?
- How often does rhythm repair change an intentional rhythm incorrectly?
- How often do added articulations improve rather than degrade playback?

---

## 9. Proposed user-facing V0.1 flow

```text
Upload MIDI
   ↓
Choose track
   ↓
Choose guitar profile
   - Electric Lead
   - Electric Rhythm (later)
   - Acoustic (later)
   ↓
Humanize Guitar
   ↓
Review summary
   - rhythm corrections
   - fingering changes
   - articulations added
   - low-confidence measures
   ↓
Export
   - Guitar Pro (.gp5)
   - Ample Guitar MIDI (.mid)
```

The UI should eventually highlight low-confidence decisions so users can inspect only the places that actually need attention.

---

## 10. Product moat

FretPilot's durable value should come from its accumulated instrument intelligence rather than dependence on a specific AI provider.

The core asset is:

```text
Generic MIDI
    ↓
Musical intent
    ↓
Guitar technique / fingering
    ↓
Canonical Guitar IR
    ↓
Score + instrument-specific performance adapters
```

This architecture later allows new exporters and virtual instruments without redesigning the musical reasoning layer.
