# FretPilot Guitar IR

## Purpose

Guitar IR is FretPilot's canonical representation between musical reasoning and output adapters.

It is:

- independent of Guitar Pro;
- independent of Ample Guitar;
- JSON serializable;
- deterministic;
- explicit about score timing versus source/performance timing;
- extensible through a schema version.

Implemented code:

```text
src/fretpilot/ir/models.py
src/fretpilot/ir/builder.py
```

CLI:

```bash
fretpilot build-ir song.mid --stream-id t0:ch2:p27 -o guitar-ir.json
```

## Current schema

Top-level shape:

```json
{
  "schema_version": "0.1",
  "title": "song",
  "source": "song.mid",
  "tempo_map": [],
  "time_signatures": [],
  "tracks": [],
  "changes": [],
  "warnings": []
}
```

## Guitar track

```json
{
  "id": "guitar-1",
  "name": "Lead Guitar · CH3 · Electric Guitar (clean)",
  "source_stream_id": "t0:ch2:p27",
  "role": "unknown",
  "tuning": [40, 45, 50, 55, 59, 64],
  "fret_count": 24,
  "measures": []
}
```

Tuning values are MIDI pitches from string 6 to string 1.

## Measure

```json
{
  "number": 1,
  "start_beat": 0.0,
  "duration_beats": 4.0,
  "numerator": 4,
  "denominator": 4,
  "events": []
}
```

The V0.1 builder supports time-signature maps and emits a warning when a time-signature change truncates a nominal measure.

## Note event

```json
{
  "id": "n-00001",
  "source_note_index": 0,
  "pitch": 69,
  "score": {
    "start_beat": 1.5,
    "duration_beats": 0.5,
    "measure_number": 1,
    "beat_in_measure": 1.5,
    "voice": 1,
    "tie_in": false,
    "tie_out": false
  },
  "performance": {
    "source_start_beat": 1.487,
    "source_duration_beats": 0.493,
    "velocity": 92
  },
  "fingering": {
    "string": 2,
    "fret": 10
  },
  "articulations": [
    {
      "type": "slide",
      "confidence": 0.89,
      "reason": "Connected notes remain on the same string.",
      "source_note_id": "n-00000"
    }
  ],
  "confidence": {
    "rhythm": 0.96,
    "fingering": 1.0,
    "articulation": 0.89
  }
}
```

## Ties and measure splitting

A note crossing a barline becomes multiple score events with the same `source_note_index` and source performance timing.

Example:

```text
n-00012-1  tie_out=true
n-00012-2  tie_in=true
```

This keeps the score writable in notation formats without losing the fact that the original MIDI contained one continuous note.

## Transformation log

Rhythm changes remain inspectable:

```json
{
  "id": "chg-onset-00001",
  "stage": "rhythm_onset",
  "source_note_index": 0,
  "before": {"start_beat": 1.487},
  "after": {"start_beat": 1.5},
  "confidence": 0.96,
  "reason": "snap_to_eighth_grid"
}
```

Current stages:

```text
rhythm_onset
rhythm_duration
rhythm_overlap
voice_assignment
```

## Core articulation vocabulary

Current deterministic output:

- `hammer_on`
- `pull_off`
- `slide`
- `vibrato`

Planned canonical vocabulary:

- `pick`
- `legato_slide`
- `palm_mute`
- `natural_harmonic`
- `bend`
- `pre_bend`
- `bend_release`
- `tapping`
- `dead_note`
- `pinch_harmonic`
- `tremolo_pick`

The IR stores musical intent. It must never store Ample Guitar keyswitch note numbers.

## Current V0.1 limitations

- up to two voices for safe unequal chord releases;
- general contrapuntal voice separation is not yet implemented;
- duration spelling uses the selected rhythm grid;
- no explicit rest events yet;
- no dotted-note or tuplet spelling objects yet;
- no phrase/section objects yet;
- role defaults to `unknown`;
- fingering confidence is currently binary playable/unplayable;
- note fragments repeat the original source performance timing;
- no chord grouping or chord-diagram representation yet.

## Next adapters

The next prototype milestone is:

```text
Guitar IR
→ minimal GP5 exporter
→ open and inspect in Guitar Pro
```

After GP5 round-trip validation:

```text
Guitar IR
→ Ample Guitar performance MIDI adapter
```

## Key invariant

> Score timing and performance timing are separate data.

Score timing should be clean and writable. Performance timing may retain microtiming, overlaps, velocity shaping, and later instrument-specific rendering behavior.
