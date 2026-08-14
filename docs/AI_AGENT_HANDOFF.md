# FretPilot AI / Codex Handoff

Read `AGENTS.md` first. This file contains only current operational context;
architecture and priorities live in [`ARCHITECTURE.md`](ARCHITECTURE.md) and
[`ROADMAP.md`](ROADMAP.md).

## Current product

FretPilot converts imperfect MIDI into:

1. musician-reviewable guitar score/TAB;
2. target-neutral performance intent;
3. Ample Guitar SC 4.x control MIDI and explicit capability diagnostics.

Current scope is standard-tuned six-string guitar. The default MIDI-fidelity
value is `0.35`, intentionally favoring playable, coherent output while keeping
every rewrite in provenance.

## Runtime

```text
MIDI → streams → guitar confidence → rewrite → section-aware analysis
→ Guitar IR → PDF / GP5 / PerformancePlan / VI report / Ample MIDI
```

An optional OpenAI-compatible AI shadow path can inspect bounded structured
note context and return validated rewrite advice. It never applies edits or
changes the canonical conversion path.

`generate_prototype_package()` is the single product conversion pipeline.
Section-aware musical execution lives only in
`analysis/section_execution.py`. Compatibility modules must remain thin.

The built-in guitar-playing snapshot is `2026.08.2`. Runtime artifacts record
the snapshot and relevant entry IDs.

## Stable baseline

- Type 0/1 MIDI parsing and logical track/channel/program streams;
- explainable guitar confidence and multi-guitar selection;
- provenance-safe note rationalization;
- section-aware role/style/technique contexts;
- playable fingering, hand-position continuity, fretting digits;
- articulation, right-hand intent, and conservative harmony;
- canonical Guitar IR with separate score and performance timing;
- GP5, PDF/TAB, PerformancePlan, VI report, and Ample MIDI outputs;
- FastAPI conversion jobs and React review UI;
- provider-neutral AI shadow contracts, OpenAI-compatible adapter, CLI/API,
  consent gate, and frontend review panel;
- approved Ample SC generic profile with legacy-scheduler parity checks.

## Known limits

- track confidence and style profiles are not fully calibrated;
- reusable root-independent shape memory (`GK-012`) is not implemented;
- barre/stretch/thumb and arbitrary multi-voice notation remain incomplete;
- PDF/TAB still needs full-song musician acceptance;
- generic VI control planning remains shadow-only;
- Ample timing/picking realization and plugin verification remain incomplete;
- API jobs are not persistent.
- AI advice has not yet passed real-song comparative evaluation and remains
  read-only.

## Current priority

1. Keep regressions and adapter parity green.
2. Review full real-song GP5/PDF output and fix musician-facing errors.
3. Verify generated MIDI in the real Ample Guitar SC plugin/DAW.
4. Move generic VI control planning toward production only after parity.
5. Implement `GK-012` and evidence-driven left-hand refinements.

Do not expand into crawling, online learning, learned rankers, or another VI
product unless explicitly requested.

## Code map

```text
src/fretpilot/midi/                 source normalization
src/fretpilot/detection/            guitar identity
src/fretpilot/rewrite/              explicit note repair
src/fretpilot/analysis/             section-aware orchestration
src/fretpilot/guitar/               fretboard and fingering
src/fretpilot/knowledge/            approved guitarist knowledge
src/fretpilot/ir/                   canonical contract
src/fretpilot/performance/          target-neutral performance plan
src/fretpilot/virtual_instruments/  VI contracts and negotiation
src/fretpilot/exporters/            PDF, GP5, Ample
src/fretpilot/prototype.py          product conversion pipeline
src/fretpilot/api/                  local service boundary
web/                                presentation only
```

## Workflow

For nontrivial changes:

1. read the narrow relevant backlog;
2. inspect code and tests before editing;
3. add regression coverage for changed contracts;
4. preserve source identity, hard constraints, and explicit unsupported states;
5. run the full backend suite and frontend test/build;
6. update only authoritative documents whose facts changed.

Never claim improved musical quality or verified plugin behavior without real
evidence.
