# Guitar harmony labeling baseline

FretPilot harmony labels are target-neutral musical analysis. They are derived before GP5/PDF formatting and are stored in canonical Guitar IR.

## Implemented path

```text
final section-aware string/fret choices
→ conservative HarmonyPlan
→ IRHarmonyRegion
→ Guitar IR JSON
→ GP5 chord text / prototype report
```

Single-context analysis uses the same base planner. Section-aware analysis runs harmony independently inside each `SectionContextAnalysis` region and remaps local note indices back to source-wide indices, so a chord is never inferred by joining notes across a section boundary.

## Current evidence rules

### Simultaneous source chord

A simultaneous source onset may receive a harmony label when its pitch-class set exactly matches a supported template. Two-note power chords are allowed only when the source bass is the inferred root; ambiguous inverted fifth dyads stay unspecified.

### Sequential guitar arpeggio

A sequential label requires all of the following:

- at least three notes;
- unique increasing source onsets;
- the cell spans no more than 1.5 beats;
- the final fingering follows a monotonic adjacent-string path;
- the pitch-class set exactly matches a supported harmony template.

Four-note sequential cells are accepted when they contain four distinct pitch classes, or when a three-note harmony closes by repeating the opening pitch class one octave higher. A repeated interior tone cannot make the first note of the next phrase get absorbed into the previous chord cell.

## Supported templates

Current exact templates include:

- major / minor triads;
- sus2 / sus4;
- diminished triads;
- major-7 / dominant-7 / minor-7;
- root-position two-note power chords.

Inversions of three-or-more-note chords use slash notation such as `C/E`. Current pitch spelling is sharp-oriented (`C#`, `D#`, `F#`, `G#`, `A#`); key-aware enharmonic spelling remains future work.

## Message in a Bottle regression

The supplied reference pattern is a golden harmony fixture. The movable cells must identify, in order, as:

```text
C#sus2
Asus2
Bsus2
F#sus2
```

The harmony test is intentionally separate from fingering-ranking tests where possible: a harmony regression should test chord interpretation, not accidentally fail because another valid string/fret ranking changed.

## Guitar IR

`GuitarTrackIR.harmony_regions` stores typed `IRHarmonyRegion` records with:

- start beat;
- symbol;
- root pitch class;
- quality;
- confidence;
- source note indices;
- explanation/reason.

The JSON loader round-trips these records and remains backward-compatible with older IR that has no harmony regions.

## Output adapters

GP5 currently renders the harmony symbol as text on the first exported score beat corresponding to the region. It does not invent a chord diagram or rolled-chord timing.

Prototype reports expose harmony decision count, symbols, and quality counts for quick real-MIDI evaluation.

## Guardrails

- No language model is required for the baseline harmony decision.
- Exact source pitches and final physical guitar fingering remain primary evidence.
- A style label does not create a chord symbol.
- Ambiguous dyads and cross-section combinations remain unspecified.
- Output adapters consume `IRHarmonyRegion`; they do not run their own chord classifier.
- Future statistical/key-aware models may rank spellings or ambiguous candidates, but may not bypass deterministic pitch-set validation.
