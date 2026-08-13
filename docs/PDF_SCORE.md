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

## V0.1 contents

- landscape A4 pages;
- cover and project summary;
- six-line guitar TAB;
- measure numbers and beat guides;
- fret numbers from Guitar IR;
- written-duration labels;
- cross-measure tie marks;
- generic technique labels such as hammer-on, pull-off, slide, vibrato, let ring, palm mute, and harmonic;
- warnings for notes without printable string/fret assignments.

## Deliberate limitations

The first PDF renderer is a review format rather than publication engraving. It does not yet include:

- five-line standard notation;
- beams, stems, or conventional rhythmic noteheads;
- multiple independent notation voices;
- chord diagrams;
- key signatures and enharmonic spelling;
- advanced bend curves;
- automatic line breaking based on musical density.

PDF output consumes Guitar IR and must not contain plugin-specific Ample Guitar mappings. Score timing remains separate from source/performance timing.
