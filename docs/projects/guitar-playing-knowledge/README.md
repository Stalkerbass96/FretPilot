# Guitar Playing Knowledge Project

## Goal

Build a versioned, explainable knowledge layer that converts symbolic MIDI into guitar choices a real guitarist is likely to make.

This project sits between behavior/style understanding and downstream rendering:

```text
MIDI / InstrumentStream
        ↓
behavior + section analysis
        ↓
PlayingContext
(role + style + technique family)
        ↓
Guitar Playing Knowledge
        ├── fingering / hand position preferences
        ├── articulation preferences
        ├── chord / voicing preferences
        └── performance preferences
        ↓
Guitar IR
        ├── score/PDF/GP5
        └── Ample performance MIDI
```

## Important distinction

Do not flatten musical concepts into one label.

- `solo`, `riff`, `strumming`, `comping` are **roles/behaviors**.
- `metal`, `jazz`, `rock`, `blues`, `funk` are **styles**.
- `sweep`, `alternate-picking`, `fingerstyle`, `legato`, `arpeggio` are **technique families**.

They are composable. A phrase may be:

```text
role: solo 0.88
style: metal 0.92
technique: legato 0.64
```

The merged PlayingContext becomes a set of soft preferences for downstream algorithms.

## Current implementation

The repository currently has two related knowledge layers:

1. `knowledge/guitar_behaviors.py`
   - Layer-4 behavior matching used by stream analysis.
   - Experimental whole-stream profiles: solo, riff, strumming, breakdown, jazz comping.

2. `knowledge/playing_contexts.py`
   - Composable role/style/technique profiles.
   - Produces `FingeringPreferences`, `ArticulationPreferences`, and `PerformancePreferences`.
   - Bridges current behavior matches into the new PlayingContext model.

Initial playing profiles include:

- solo
- riff
- strumming
- metal
- jazz
- rock_arpeggio

These values are hand-authored V0 priors, not claims of learned statistical truth.

## Knowledge should influence choices, not violate physics

Knowledge profiles are soft priors. Deterministic constraints remain authoritative:

- a note must exist on the configured tuning/fretboard;
- simultaneous chord notes cannot occupy the same string;
- impossible hand stretches may be rejected;
- requested articulations must be physically/renderably valid;
- output formats remain validated independently.

For example, a metal profile may prefer low-register pedal tones and palm mute, but it cannot force an impossible fingering.

## Fingering knowledge targets

The knowledge layer should eventually express at least:

- hand-position stability;
- position-shift cost by phrase context;
- adjacent-string arpeggio preference;
- movable-shape reuse;
- same-string legato preference;
- open-string preference/avoidance;
- power-chord and octave-shape preference;
- chord compactness and voice-leading;
- string-crossing ergonomics;
- left-hand finger assignment;
- barre preference;
- stretch limits and thumb-over behavior;
- style-specific tuning assumptions.

## Articulation knowledge targets

Examples:

### Solo / lead

Usually higher priors for:

- bends;
- vibrato;
- hammer-on / pull-off;
- legato slide;
- expressive position choices.

### Metal riff

Usually higher priors for:

- low-register pedal tones;
- palm mute;
- repeated power shapes;
- stable hand positions;
- tighter timing and accent patterns;
- controlled note length and staccato behavior.

### Jazz

Usually higher priors for:

- economical voice leading;
- compact or drop voicings;
- reduced reliance on open strings;
- chord extensions;
- phrase-aware chromatic movement.

These are tendencies, not absolute rules.

## Long-term learning objective

The knowledge base should become partially data-derived rather than permanently hand-tuned.

The system should learn statistical guitar habits from high-quality, legally usable symbolic guitar sources and convert them into versioned derived knowledge rather than blindly copying source tablature.

See [LEARNING_PIPELINE.md](LEARNING_PIPELINE.md).

## Non-goals for the prototype

Do not block the V0.1 product on:

- perfect style classification;
- internet crawling;
- a trained neural fingering model;
- every genre and tuning;
- exact left-hand finger numbers;
- reproducing a published reference tab exactly.

The current goal is a stable interface so every future improvement can enter through the knowledge layer instead of adding isolated special cases throughout the codebase.
