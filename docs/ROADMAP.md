# FretPilot Roadmap

> Current milestone: **Prototype 0.1 — musician-reviewable guitar score + virtual-guitar performance package**
>
> This file tracks product priority and release gates. Task-level detail belongs in the `TI-*`, `GK-*`, `VI-*`, and `SE-*` backlogs.

## Current vertical slice

```text
MIDI
→ NormalizedTimeline + source timing + pitch-wheel/range evidence
→ InstrumentStream resolution
→ Layers 1–3 guitar identity
→ selected guitar stream
→ adjustable MIDI-fidelity note rationalization
→ rhythm / notation analysis
→ section segmentation
→ per-section behavior/style evidence
→ per-section PlayingContext
→ fingering + hand-position / voicing continuity
→ fretting-digit assignment
→ articulation / source-backed pitch movement
→ right-hand pick / strum / sweep / tremolo intent
→ conservative harmony regions
→ GuitarTrackAnalysis
→ canonical Guitar IR + pinned knowledge provenance
├──→ GP5
├──→ PDF/TAB
├──→ Generic PerformancePlan sidecar
├──→ VI capability diagnostics
└──→ Ample Guitar SC 4.x MIDI
```

The score and performance paths share canonical musical intent, but adapter-specific keyswitch/CC/state data remains outside Guitar IR.

## What is already baseline-complete

### Input / guitar execution

- MIDI Type 0 / Type 1 import and logical `InstrumentStream` resolution;
- layered guitar candidate ranking and explicit multi-guitar selection;
- local guitar-only confidence preflight that groups same-track/channel program
  fragments and filters low-confidence streams from generation;
- provenance-safe note rationalization with adjustable MIDI fidelity;
- score timing separated from source/performance timing;
- section-aware `PlayingContext`;
- six-string fretboard candidates and hard playability constraints;
- movable riff/arpeggio repair and chord-voicing continuity;
- explicit hand-position state with weak-boundary carry / strong-boundary reset;
- deterministic 1–4 fretting digits;
- hammer/pull, slide, vibrato, contextual palm mute/staccato;
- source-backed positive pitch-raise intent from declared MIDI wheel range;
- down/up pick, strum, observed rolled strum, tremolo, and sweep baselines;
- conservative harmony labeling;
- safe second-voice preservation for unequal same-onset chord releases when the
  sustained string remains free;
- canonical Guitar IR provenance for section, hand position, fretting, right hand, harmony, and articulation parameters.

### Score outputs

GP5 baseline includes string/fret mapping, rests/durations, ties, fretting
digits, supported articulations, pick direction, observed rolled-strum
`BeatStroke`, conservative pitch curves, harmony labels, the safe two-voice
chord-release case, and write/parse-back validation.

PDF/TAB baseline includes six-line TAB, harmony labels, exact rests,
stems/flags/beams, dotted marks, triplet brackets, ties, density-aware system
breaking, over-density warnings, separate V1/V2 rhythm lanes, and
collision-aware technique labels.

### Performance / virtual instruments

- target-neutral Generic PerformancePlan with timing/velocity/accent/overlap intent;
- ordinary `fretpilot prototype` PerformancePlan sidecars;
- provider-neutral `VirtualGuitarInstrumentProfile`;
- approved static profile registry;
- migrated `ample-guitar-sc-v4` generic profile;
- capability negotiation and capability-report sidecars;
- pre-render `report_only` / `warn` / `strict` policy;
- public Ample export uses generic profile truth through a thin compatibility view while retaining the proven legacy scheduler;
- shadow generic control planning has regression coverage against legacy Ample keyswitch/legato behavior.
- pinned guitar-playing snapshot `2026.08.2` is recorded in Guitar IR,
  reports, manifests, and API jobs;
- the local FastAPI/React product shell provides preflight, conversion, download,
  and read-only knowledge review;
- Ample Metal Eclipse 4.1 is present only in the review catalog; Ample Guitar SC
  remains the runtime renderer.

Track identification remains an incremental `TI-*` project and is not the main Prototype 0.1 blocker.

## Active Prototype 0.1 work

### 1. Musician-facing score validation

The engine can generate complete GP5/PDF/TAB review material. The next step is real-song acceptance rather than adding more debug notation.

Priority fixes from real review should target:

- incorrect string/fret/shape decisions;
- phrase or hand-position discontinuity;
- wrong/missing articulation or harmony labels;
- mixed-density horizontal allocation;
- general voice separation beyond the safe chord-release case;
- paired standard staff + TAB when the TAB baseline is stable enough.

Acceptance:

> At least one full real guitar stream reads like a usable first-draft guitar part, not a debugging visualization.

### 2. VI-004 — generic control handoff

The generic VI profile, negotiation layer, preflight policy, and shadow control plan exist. The production Ample MIDI scheduler is intentionally still the regression-proven legacy scheduler.

Next transition:

```text
canonical Guitar IR / PerformancePlan
→ capability negotiation
→ generic ControlAction plan
→ shadow/parity comparison
→ adapter consumption only when output-neutral coverage stays green
```

Do not switch schedulers merely for architectural neatness.

### 3. Real Ample plugin verification

Automated MIDI parse-back is not the same as plugin verification. At least one generated Ample MIDI must be played through the actual Ample Guitar SC 4.x plugin/DAW and recorded as structured verification evidence.

### 4. Guitar-knowledge refinement

The biggest structural GK gap is `GK-012` reusable root-independent shape memory. Hand-position and fretting-digit baselines should then be refined with barre/stretch/thumb/explicit shift semantics and real-song evidence rather than rebuilt.

### 5. Reproducibility/documentation closeout

Before Prototype 0.1 external testing:

- README/current commands must match implementation;
- authoritative handoff/backlogs must not contradict one another;
- unsupported target capabilities must remain explicit;
- extend existing knowledge provenance into full engine/config/model identity
  and selectable approved snapshots under `SE-*`.

## One-command validation package

```bash
fretpilot prototype song.mid \
  --all-likely-guitars \
  -o output/
```

Per selected stream the package produces analysis JSON, rewrite provenance,
Guitar IR JSON, PDF, GP5 when supported, Ample MIDI, and a processing report.
The prototype post-hook also produces PerformancePlan and VI-capability
sidecars/indexes.

## Prototype 0.1 release gates

Prototype 0.1 is ready for external hands-on testing when:

1. full CI is green;
2. one real multi-guitar MIDI generates complete review packages;
3. at least one full guitar score/TAB has been visually reviewed and accepted as a usable first draft;
4. at least one generated Ample MIDI has been played through the actual plugin/DAW;
5. unsupported cases produce explicit warnings/errors rather than silent corruption;
6. README, handoff, roadmap, and specialized backlog statuses match the implementation.

Multi-product support, full TI calibration, large-scale learning infrastructure, and learned rankers are **not** Prototype 0.1 blockers.

## After Prototype 0.1

Near-term candidates:

- `GK-012` reusable shape memory and advanced left-hand contracts;
- calibrated style-family expansion;
- TI labeled fixtures/evaluation/config versioning;
- reusable VI adapter conformance suite and second virtual-guitar target;
- SE reproducibility manifest and golden-review registry.

Long-term:

```text
stable deterministic engine
+ approved/versioned Guitar Playing Knowledge
+ approved/versioned Virtual Instrument Knowledge
+ golden/user correction evidence
+ controlled candidate → evaluation → promotion loop
+ optional learned rankers that never bypass hard constraints
```

Runtime must remain reproducible. New web/user/learned evidence never silently changes production behavior.
