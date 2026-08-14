# FretPilot Architecture

FretPilot turns imperfect MIDI into guitar-aware score and performance
artifacts. Hard physical/file constraints are deterministic; versioned
knowledge only ranks valid musical choices.

## One runtime path

```text
MIDI
→ NormalizedTimeline
→ logical InstrumentStream resolution
→ guitar detection and selection
→ adjustable note rationalization
→ section/context analysis
→ fingering, articulation, picking, harmony
→ GuitarTrackAnalysis
→ canonical Guitar IR
├─→ PDF/TAB
├─→ GP5
├─→ Generic PerformancePlan
├─→ VI capability report
└─→ Ample Guitar SC MIDI
```

`generate_prototype_package()` is the product-level conversion pipeline. The
CLI and API call it directly. Performance and VI sidecars are generated inside
that pipeline, so console, `python -m fretpilot`, and API execution share the
same behavior.

The web path adds delivery concerns only:

```text
React UI → FastAPI → bounded JobManager → generate_prototype_package()
```

The API owns uploads, job state, output selection, isolation, and downloads. It
does not own musical policy.

## Canonical contracts

| Contract | Purpose |
|---|---|
| `NormalizedTimeline` | Loss-minimized MIDI source truth |
| `InstrumentStream` | Logical track/channel/program stream |
| `GuitarTrackAnalysis` | Guitar decisions before output formatting |
| `GuitarProjectIR` | Shared score/performance musical intent |
| `GuitarPerformancePlan` | Target-neutral performance realization |
| `VirtualGuitarInstrumentProfile` | Product/version capability and control knowledge |

Score timing and source/performance timing are separate. Product-specific
keyswitches, CCs, latch state, and approximations never enter Guitar IR.

## Module ownership

| Module | Owns | Must not own |
|---|---|---|
| `midi` | parsing, metadata, source timing | musical repair |
| `detection` | logical streams, guitar identity confidence | playing-style decisions |
| `rewrite` | explicit add/delete/transpose repairs and provenance | hidden source mutation |
| `analysis` | sections, context, pipeline orchestration | output formatting |
| `rhythm` | notation grids and score timing | performance timing replacement |
| `guitar` | fretboard feasibility and fingering | plugin controls |
| `knowledge` | versioned guitarist behavior/preferences | vendor mappings |
| `articulation`, `picking`, `harmony` | target-neutral musical intent | renderer policy |
| `ir` | canonical project/event representation | target-specific state |
| `performance` | target-neutral timing/velocity/overlap intent | keyswitch scheduling |
| `virtual_instruments` | product-neutral VI contracts and negotiation | source analysis |
| `exporters` | GP5, PDF, and Ample realization | re-inferring musical intent |
| `api` | jobs, uploads, artifact delivery | duplicated engine logic |
| `web` | presentation and user workflow | Python musical policy |

## Implementation truths

- Section-aware execution lives in
  `src/fretpilot/analysis/section_execution.py`.
- `src/fretpilot/analysis/__init__.py` exports it without wrapping behavior.
- `src/fretpilot/analysis/section_aware.py` is import compatibility only.
- Prototype orchestration lives in `src/fretpilot/prototype.py`.
- `entrypoint.py` and `prototype_performance_cli.py` are compatibility shims;
  they do not add conversion behavior.
- Behavior profile contracts belong to `knowledge`; detection may consume them,
  but knowledge does not import detection.

## Runtime knowledge

Runtime uses approved, pinned snapshots. Guitar IR, reports, manifests, and API
jobs record the snapshot version; section contexts also record the exact entry
IDs used. Candidate or lesson-derived knowledge does not affect production
until it is evaluated and promoted.

```text
TI / Layers 1–3 = which stream is guitar?
GK / Layer 4    = how is this section likely played?
VI              = how can a product realize the intent?
SE              = how are evidence and promotion governed?
```

## Current infrastructure limits

- API job state is process-local and in memory.
- PDF is a review renderer, not publication engraving.
- Ample Guitar SC is the only runtime virtual-guitar target.
- The generic VI control plan is still checked in shadow mode against the
  proven Ample scheduler.
- Behavior/style profiles are deterministic baselines, not calibrated truth.

Long-term learning architecture is documented in
[`LONG_TERM_ARCHITECTURE.md`](LONG_TERM_ARCHITECTURE.md). Current priorities are
in [`ROADMAP.md`](ROADMAP.md); task details remain in the `TI-*`, `GK-*`,
`VI-*`, and `SE-*` project backlogs.
