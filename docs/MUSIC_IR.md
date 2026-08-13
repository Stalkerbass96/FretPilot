# FretPilot Guitar IR

## Purpose

The Guitar IR is FretPilot's canonical intermediate representation between musical reasoning and output adapters.

It must be:

- independent of Guitar Pro
- independent of Ample Guitar
- serializable
- deterministic
- rich enough to describe notation and performance intent
- extensible without breaking old files

## Top-level shape

```json
{
  "schema_version": "0.1",
  "project": {
    "title": "Untitled",
    "source": "midi"
  },
  "tempo_map": [],
  "time_signatures": [],
  "tracks": []
}
```

## Guitar track

```json
{
  "id": "guitar-1",
  "role": "lead",
  "tuning": [40, 45, 50, 55, 59, 64],
  "fret_count": 24,
  "phrases": []
}
```

Tuning values are MIDI pitches from string 6 to string 1 by convention.

## Phrase

```json
{
  "id": "phrase-001",
  "start_beat": 0.0,
  "end_beat": 4.0,
  "role": "melodic_lead",
  "confidence": 0.92,
  "events": []
}
```

## Note event

```json
{
  "id": "n-001",
  "pitch": 69,
  "score": {
    "start_beat": 1.5,
    "duration_beats": 0.5,
    "voice": 1,
    "tie_in": false,
    "tie_out": false
  },
  "performance": {
    "source_start_beat": 1.487,
    "source_duration_beats": 0.493,
    "start_offset_ms": -8,
    "duration_scale": 1.03,
    "velocity": 92
  },
  "fingering": {
    "string": 2,
    "fret": 10,
    "position": 9,
    "finger": null
  },
  "articulations": [
    {
      "type": "slide",
      "direction": "up",
      "target_note_id": "n-002",
      "confidence": 0.89
    }
  ],
  "confidence": {
    "rhythm": 0.96,
    "fingering": 0.91,
    "articulation": 0.89
  }
}
```

## Core articulation vocabulary

Initial generic articulation types:

- `pick`
- `hammer_on`
- `pull_off`
- `slide`
- `legato_slide`
- `vibrato`
- `palm_mute`
- `natural_harmonic`

Future candidates:

- `bend`
- `pre_bend`
- `bend_release`
- `tapping`
- `dead_note`
- `pinch_harmonic`
- `tremolo_pick`

The IR stores musical intent. It must not store plugin-specific keyswitch note numbers.

## Change log / transformation record

A processed project may carry transformations so the UI can explain changes:

```json
{
  "changes": [
    {
      "id": "chg-001",
      "stage": "rhythm",
      "event_ids": ["n-001"],
      "before": {"start_beat": 1.487},
      "after": {"start_beat": 1.5},
      "confidence": 0.96,
      "reason": "phrase_consistent_16th_quantization"
    }
  ]
}
```

## Key rule

Score timing and performance timing are separate on purpose.

The score should be clean and readable. The performance may contain microtiming, overlaps, duration changes, velocity shaping, and instrument-specific rendering behavior.
