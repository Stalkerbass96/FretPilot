# PDF Score Output

FretPilot can render canonical Guitar IR directly as a landscape A4 PDF without Guitar Pro.

## Command

```bash
fretpilot-pdf song.mid \
  --stream-id t0:ch2:p27 \
  -o song.pdf
```

Optional layout controls:

```bash
fretpilot-pdf song.mid \
  --stream-id t0:ch2:p27 \
  --measures-per-system 4 \
  --systems-per-page 5 \
  -o song.pdf
```

When exactly one likely guitar stream exists, `--stream-id` may be omitted. When multiple guitar streams are detected, selection remains explicit.

## Current review-score contents

- landscape A4 pages;
- cover and project summary;
- six-line guitar TAB;
- measure numbers and beat guides;
- fret numbers from canonical Guitar IR;
- canonical harmony symbols such as `C#sus2` anchored from `IRHarmonyRegion`;
- exact written-duration labels with literal beat fallback for unsupported values rather than silent rounding;
- explicit rest spans decomposed into exact binary, dotted, and triplet rest values where possible;
- rhythmic stems, isolated flags, and meter-aware beam groups below TAB;
- dotted rhythm marks that preserve the beam level of the underlying binary value;
- triplet brackets for exact consecutive three-note tuplet groups;
- cross-measure tie marks;
- generic technique labels such as hammer-on, pull-off, slide, vibrato, let ring, palm mute, harmonic, and pitch raise/bend intent;
- warnings for notes without printable string/fret assignments.

Harmony, rests, stems/beams, dotted marks, and tuplets are rendering of canonical score/analysis data. The PDF exporter does not run a separate chord classifier and does not use performance timing to invent written rhythm.

## Deliberate limitations

The PDF renderer is still a review format rather than publication engraving. It does not yet include:

- five-line standard notation paired with TAB;
- multiple independent notation voices;
- chord diagrams;
- key signatures and key-aware enharmonic spelling;
- publication-quality noteheads/rest glyphs or full traditional engraving rules;
- advanced bend curves;
- automatic system breaking and measure-width allocation based on musical density;
- collision-aware placement for every possible combination of technique, harmony, and rhythm annotations.

PDF output consumes Guitar IR and must not contain plugin-specific Ample Guitar mappings. Score timing remains separate from source/performance timing.
