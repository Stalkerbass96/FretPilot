# Virtual Guitar Instrument Knowledge Project

## Goal

Build a versioned adapter-knowledge layer that converts canonical FretPilot performance intent into reliable control data for multiple virtual guitar instruments.

This project answers a different question from Guitar Playing Knowledge:

- `GK-*` asks: **How would a real guitarist likely play this phrase?**
- `VI-*` asks: **How must a specific virtual guitar instrument be controlled to reproduce that intent?**

The boundary is strict. Product-specific keyswitches, CC numbers, velocity conventions, legato overlap requirements, string-forcing controls, engine quirks, and version-specific mappings must not leak into Guitar IR or generic guitar-playing knowledge.

## Architectural position

```text
InstrumentStream
      ↓
Musical / Guitar Intelligence
      ↓
PlayingContext
      ↓
Guitar Playing Knowledge
      ↓
Canonical Guitar IR
(score intent + performance intent)
      ↓
Virtual Guitar Capability Resolver
      ↓
Virtual Guitar Instrument Profile
      ↓
Adapter Planner / State Machine
      ↓
Plugin-specific MIDI / CC / keyswitch / automation
```

The same Guitar IR should be renderable through different adapters without changing the upstream musical interpretation.

## Knowledge categories

A virtual-guitar profile may eventually describe:

### Identity and compatibility

- vendor/product identity;
- product/version family;
- profile schema/version;
- supported instrument type and tuning assumptions;
- minimum/maximum playable pitch;
- supported host/control modes;
- known compatibility restrictions.

### Articulation capability

For each canonical articulation or performance intent:

- supported / unsupported / approximated;
- keyswitch mapping;
- CC mapping;
- velocity-switch mapping;
- program-change mapping when applicable;
- required preroll;
- state duration/latching behavior;
- reset behavior;
- mutually exclusive states;
- fallback strategy.

Examples of canonical intents include:

```text
sustain
palm_mute
hammer_on
pull_off
legato_slide
slide_in
slide_out
bend
vibrato
harmonic
staccato
let_ring
```

### Fretboard / string control

Where the product supports it:

- string forcing;
- fret/position forcing;
- hand-position constraints;
- open-string forcing/avoidance;
- chord/voicing hints;
- capo/tuning control;
- extended-range behavior.

### Picking and rhythm control

Where available:

- down/up pick control;
- alternate-picking rules;
- strum direction;
- strum spread;
- rake/sweep control;
- repeated-note behavior;
- round-robin/repetition handling;
- accent and ghost-note control.

### Legato and timing semantics

- required note overlap for hammer/pull/slide;
- minimum/maximum overlap windows;
- keyswitch lead time;
- note-off ordering;
- engine latency compensation;
- release-tail behavior;
- hanging-note prevention;
- state-reset requirements.

### Pitch expression

- pitch-bend range;
- bend curve strategy;
- vibrato control strategy;
- channel-wide vs per-note limitations;
- MPE/per-note controller capability when applicable;
- polyphonic bend restrictions.

### Dynamics and tone-state control

- velocity interpretation;
- dynamic CCs;
- mute depth;
- articulation-dependent velocity ranges;
- tone/pickup controls when musically relevant;
- humanization limits that should be handled by the adapter rather than the upstream performance plan.

## Current implementation

The first product-specific implementation is currently under:

```text
src/fretpilot/exporters/ample_guitar/
```

It already contains a versioned Ample Guitar SC profile and renderer. This is the prototype reference implementation, not the final generic architecture.

The long-term direction is:

```text
Canonical VirtualGuitarInstrumentProfile schema
              ↓
        Adapter Registry
        ├── Ample profile(s)
        ├── future product profile(s)
        └── future product profile(s)
              ↓
product-specific renderer/state machine only where necessary
```

Do not prematurely force every product into identical behavior. The shared schema should express common capabilities, while adapters may still contain product-specific state-machine logic.

## What should evolve

This knowledge is versioned and can improve over time.

Good sources of evolution include:

- official vendor manuals and articulation maps;
- official MIDI/control documentation;
- reproducible plugin-version tests;
- user-confirmed compatibility reports;
- DAW round-trip tests;
- listening/behavior regression tests;
- explicitly recorded calibration results;
- new product/version support.

Different kinds of knowledge have different trust levels:

```text
official documentation
    → authoritative mapping evidence

reproducible automated/manual test
    → verified behavior evidence

user report
    → candidate evidence until reproduced

learned rendering preference
    → candidate expressive prior, never a replacement for documented controls
```

## Self-evolution boundary

This module may evolve, but it must not silently rewrite product mappings from arbitrary internet content.

Use a controlled lifecycle:

```text
new manual / product version / calibration result
        ↓
Adapter Knowledge Candidate
        ↓
compatibility + rendering tests
        ↓
review
        ↓
approved versioned instrument profile
        ↓
runtime adapter registry
```

For expressive decisions, future learned data may tune preferences such as overlap, accent scaling, or articulation fallback quality. Hard control mappings and plugin protocol requirements remain versioned, source-backed facts.

## Core invariants

- Guitar IR stores musical intent, not vendor-specific control numbers.
- Guitar Playing Knowledge models guitarist behavior, not plugin behavior.
- Instrument profiles are versioned by product/version family.
- Unsupported articulations must be explicit; adapters must not silently fake exact support.
- Adapter output must be reproducible from engine + IR + instrument-profile versions.
- New product versions must not silently inherit old mappings unless compatibility is verified.
- Runtime should use approved profiles, not scrape vendor/web pages during a render request.

## Task ownership

Use `VI-*` for virtual-guitar product knowledge, adapter schemas, compatibility tests, and renderer behavior.

Use:

- `GK-*` for real-guitar playing knowledge;
- `SE-*` for cross-project snapshot/provenance/evaluation infrastructure;
- `PV-*` for immediate prototype validation;
- `TI-*` for instrument-stream/guitar identity detection.
