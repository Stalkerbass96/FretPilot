# FretPilot AI / Codex Handoff

> Consolidated: 2026-08-14
>
> Read `AGENTS.md` first. This file is the short current-state handoff. Product priority lives in `docs/ROADMAP.md`; task-level truth lives in the specialized `TI-*`, `GK-*`, `VI-*`, and `SE-*` backlogs.

## Product goal

FretPilot converts imperfect or AI-generated MIDI into two guitar-aware outputs:

1. musician-reviewable guitar notation/TAB;
2. target-neutral performance intent that can be realized by virtual-guitar adapters.

Current instrument scope is standard-tuned six-string guitar. Current implemented virtual-guitar target is Ample Guitar SC 4.x.

## Current runtime path

```text
MIDI
→ NormalizedTimeline + source timing + pitch-wheel/range evidence
→ logical InstrumentStream resolution
→ Layers 1–3 guitar identity
→ selected guitar stream
→ rhythm / notation analysis
→ deterministic section segmentation
→ per-section behavior + style evidence
→ per-section PlayingContext
→ fingering + hand-position / voicing continuity
→ 1–4 fretting-digit assignment
→ articulation + source-backed pitch movement
→ right-hand pick / strum / sweep / tremolo planning
→ conservative harmony regions
→ global source_note_index remap
→ GuitarTrackAnalysis
→ canonical Guitar IR
├──→ GP5
├──→ PDF/TAB review output
├──→ Generic PerformancePlan sidecar
├──→ VI capability diagnostics
└──→ Ample Guitar SC MIDI
```

The normal `fretpilot prototype` command writes PerformancePlan and VI capability sidecars after the canonical prototype package is generated.

## Current implemented baseline

### Guitar execution / Guitar IR

- score timing and source/performance timing remain separate;
- standard six-string fretboard candidates and hard playability constraints;
- section-aware `PlayingContext` with separate role/style/technique-family dimensions;
- movable riff/arpeggio repair and chord-voicing continuity;
- explicit hand-position state with weak-boundary carry / strong-boundary reset;
- deterministic 1–4 `fretting_digit` assignment;
- hammer/pull, slide, vibrato, contextual palm mute/staccato, and source-backed positive pitch-raise intent;
- right-hand down/up pick, strum, observed rolled strum, tremolo, and sweep baselines;
- conservative simultaneous/sequential harmony regions;
- canonical Guitar IR persists section, hand-position, fretting, right-hand, harmony, and articulation provenance.

### Score outputs

GP5 currently supports the implemented string/fret path, rests/durations, ties, fretting digits, supported articulations, pick direction, observed rolled-strum `BeatStroke`, integer-semitone pitch curves with conservative fractional fallback, and harmony labels.

PDF/TAB currently has six-line TAB, harmony labels, exact rests, stems/flags/beams, dotted marks, triplet brackets, ties, density-aware system breaking, and explicit over-density warnings. It remains a review renderer, not publication-grade engraving.

### Performance / VI

`Generic PerformancePlan` contains target-neutral timing, duration/overlap, velocity, metric-accent, and section/context intent. Neutral preferences preserve source timing/duration/velocity.

The provider-neutral VI layer now includes:

- `VirtualGuitarInstrumentProfile`;
- approved static profile registry;
- migrated `ample-guitar-sc-v4` generic profile;
- capability negotiation and capability reports;
- `report_only` / `warn` / `strict` pre-render capability policies;
- a shadow `VirtualInstrumentControlPlan` that compiles generic `ControlAction` records for comparison with the proven legacy scheduler.

Public Ample export uses the generic profile as the static knowledge source, normalizes it through a thin compatibility view, runs capability preflight, then delegates MIDI scheduling to the existing legacy renderer. Output-neutral profile-handoff and shadow-control parity regressions protect the transition.

## Important limitations

Do not mistake these for finished production features:

- behavior/style profiles are hand-authored baselines, not calibrated musical truth;
- `GK-012` reusable root-independent shape memory is not implemented yet;
- hand-position/fretting baselines still lack first-class barre, stretch, thumb, and richer explicit shift semantics;
- pitch-wheel interpretation currently covers conservative positive raises, not the full bend/pre-bend/downward gesture space;
- no true multi-voice TAB/GP5 notation yet;
- PDF/TAB still needs collision-aware layout, mixed-density variable measure widths, paired standard staff + TAB, and real-song musician acceptance;
- Ample MIDI still does not consume Generic PerformancePlan target timing/velocity/duration or canonical pick/strum intent;
- vibrato/pitch-raise rendering in the Ample adapter remains unsupported;
- the generic shadow control plan is not yet the production MIDI scheduler;
- Ample is the only implemented virtual-guitar target;
- track identification is useful but is not yet measured/calibrated as a finished classifier;
- runtime knowledge is versioned in code, but the formal reproducibility/knowledge-snapshot manifest remains `SE-*` work.

## Architectural boundaries

```text
TI / Layers 1–3  = which logical stream is guitar?
GK / Layer 4     = how would a guitarist likely play this section?
VI               = how does a specific virtual instrument realize canonical intent?
SE               = how are evaluation, provenance, corrections, and knowledge evolution governed?
```

Non-negotiable rules:

- physical fretboard/file constraints are hard; knowledge/ML only ranks valid alternatives;
- Layer 4 behavior never overrides instrument identity;
- product keyswitches/CC/state never belong in Guitar IR or Guitar Playing Knowledge;
- source timing and stable `source_note_index` survive section-local processing;
- score timing and performance timing remain separate;
- unsupported target capabilities must be explicit, never silently discarded;
- runtime uses approved/pinned knowledge; web/user/learned evidence does not silently mutate production behavior.

## Current product priority

Prototype 0.1 is in validation/quality convergence rather than architecture bootstrap.

Priority order unless the user says otherwise:

1. keep full CI green and preserve output-neutral adapter parity;
2. perform full real-song GP5/TAB review and fix musician-facing score issues;
3. perform real Ample Guitar SC DAW/plugin verification and record evidence;
4. finish VI-004 by moving from shadow generic control planning toward adapter consumption only when parity remains green;
5. implement `GK-012` reusable shape memory and evidence-driven advanced left-hand semantics;
6. close Prototype 0.1 documentation/reproducibility gaps.

Do not divert Prototype 0.1 into large-scale crawling, online learning, learned rankers, or multi-product expansion unless explicitly requested.

## Files to inspect first

### Guitar-intelligence path

```text
src/fretpilot/analysis/sections.py
src/fretpilot/analysis/section_contexts.py
src/fretpilot/analysis/section_execution.py
src/fretpilot/knowledge/
src/fretpilot/guitar/
src/fretpilot/articulation/
src/fretpilot/picking/
src/fretpilot/harmony/
```

`src/fretpilot/analysis/section_aware.py` is compatibility-only; do not create a second execution implementation there.

### IR / score / performance

```text
src/fretpilot/ir/
src/fretpilot/exporters/guitar_pro/
src/fretpilot/exporters/pdf_score/
src/fretpilot/performance/
src/fretpilot/prototype.py
src/fretpilot/entrypoint.py
```

### Virtual instruments

```text
src/fretpilot/virtual_instruments/
src/fretpilot/exporters/ample_guitar/
```

## Current commands

One-command validation package:

```bash
fretpilot prototype song.mid \
  --all-likely-guitars \
  -o output/
```

The package contains per-stream analysis, Guitar IR, GP5 when supported, Ample MIDI, processing reports, plus PerformancePlan and VI-capability sidecars/indexes.

Useful focused commands:

```bash
fretpilot inspect song.mid
fretpilot sections song.mid --stream-id t0:ch2:p27
fretpilot-pdf song.mid --stream-id t0:ch2:p27 -o score.pdf
fretpilot-performance-plan song.mid --stream-id t0:ch2:p27 -o performance-plan.json
```

## Required coding workflow

For every nontrivial change:

1. read this handoff and the narrow relevant backlog;
2. inspect current code/tests; code + green regressions are implementation truth;
3. reuse stable task IDs;
4. add/update regression coverage before changing musical scoring or adapter mappings;
5. preserve canonical/source identities and neutral behavior unless intentionally changed;
6. run full CI;
7. update only the narrow authoritative docs that changed;
8. do not claim improved guitarist-likeness or verified plugin behavior without evidence.
