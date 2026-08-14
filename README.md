# FretPilot

**MIDI-to-guitar notation and virtual-guitar performance engine.**

FretPilot turns raw, imperfect, or AI-generated MIDI into guitar-aware musical data that is both **reviewable by a guitarist** and **usable by virtual-guitar adapters**.

Current Prototype 0.1 scope:

- input: MIDI Type 0 / Type 1;
- instrument: standard-tuned six-string guitar, 0–24 frets;
- score outputs: Guitar Pro 5 (`.gp5`) and PDF/TAB review output;
- performance target: Ample Guitar SC 4.x MIDI;
- canonical layer: versioned Guitar IR shared by score/performance paths.

## Current pipeline

```text
MIDI
→ normalized source timeline
→ logical Track/Channel/Program InstrumentStreams
→ layered guitar candidate ranking
→ selected guitar stream
→ adjustable MIDI-fidelity note rationalization
→ rhythm / notation analysis
→ section segmentation
→ per-section behavior/style PlayingContext
→ fingering + hand-position / voicing continuity
→ 1–4 fretting digits
→ articulation + source-backed pitch movement
→ right-hand pick / strum / sweep / tremolo intent
→ conservative harmony regions
→ canonical Guitar IR + pinned knowledge provenance
├──→ GP5
├──→ PDF/TAB
├──→ Generic PerformancePlan
├──→ VI capability diagnostics
└──→ Ample Guitar SC MIDI
```

FretPilot keeps **score timing** separate from **source/performance timing**. Notation may be cleaned without destroying the original performance timing used by playback/performance planning.

## Design rules

- **Deterministic engine first.** Physical playability, source identity, timing, file validity, and adapter state remain deterministic.
- **Knowledge is a soft prior.** Style/role/technique knowledge ranks valid guitar choices but never bypasses fretboard constraints.
- **Metadata is evidence, not truth.** Track names and General MIDI programs help identify guitars but are not absolute labels.
- **One canonical Guitar IR.** Score and performance adapters consume the same musical intent.
- **Guitar knowledge and plugin knowledge are separate.** Vendor keyswitches/CC/state never enter Guitar Playing Knowledge or Guitar IR.
- **Unsupported target behavior is explicit.** Adapters warn, approximate deliberately, or block; they do not silently discard material intent.

## Install

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## One-command prototype package

Generate all likely guitar streams:

```bash
fretpilot prototype song.mid \
  --all-likely-guitars \
  -o output/
```

Or select one logical stream explicitly:

```bash
fretpilot prototype song.mid \
  --stream-id t0:ch2:p27 \
  -o output/
```

A successful package contains per-stream analysis, rewrite provenance, Guitar
IR, PDF, GP5 when supported, Ample MIDI, a processing report, Generic
PerformancePlan, and VI capability sidecars. All entry points use this same
prototype pipeline.

Representative layout:

```text
output/
├── manifest.json
├── performance-plans.json
├── vi-capabilities.json
├── t0_ch2_p27/
│   ├── t0_ch2_p27.analysis.json
│   ├── t0_ch2_p27.rewrite.json
│   ├── t0_ch2_p27.guitar-ir.json
│   ├── t0_ch2_p27.pdf
│   ├── t0_ch2_p27.gp5
│   ├── t0_ch2_p27.ample-sc.mid
│   ├── t0_ch2_p27.report.json
│   ├── t0_ch2_p27.performance-plan.json
│   └── t0_ch2_p27.vi-capabilities.json
└── ...
```

Unsupported outputs are recorded explicitly rather than causing unrelated outputs for the same stream to disappear.

The note-rationalization balance is adjustable from 0.0 (prefer a playable,
musically coherent result) to 1.0 (preserve MIDI notes). The default is 0.35,
deliberately favoring reasonableness while every delete, transpose, or insert
remains explicit in rewrite and Guitar IR provenance. For example:

    fretpilot prototype song.mid --midi-fidelity 0.35 -o output/

High-confidence repairs include guitar-range octave correction, exact duplicate
removal, isolated spike repair, repeated-pulse completion, and minimum deletion
for near-simultaneous chords that cannot fit six distinct strings.

## Optional AI shadow advice

FretPilot can call an OpenAI-compatible third-party API for read-only MIDI
rewrite suggestions. The model receives a bounded structured note context, not
the binary MIDI or the source's full local path. Every suggestion is checked
against fidelity budgets, stable note IDs, pitch-shift limits, and the physical
fretboard. Shadow suggestions are never applied to GP5 or other outputs.

Configure the local API/CLI process through environment variables:

```bash
export FRETPILOT_LLM_BASE_URL="https://provider.example/v1"
export FRETPILOT_LLM_MODEL="provider-model-id"
export FRETPILOT_LLM_API_KEY="..."
```

Generate a report directly:

```bash
fretpilot ai-shadow song.mid \
  --stream-id t0:ch2:p27 \
  --midi-fidelity 0.35 \
  -o shadow-advice.json
```

The frontend exposes the same capability under **高级设置 → AI 智能增强**.
It requires explicit consent before sending structured context externally.
The panel currently reports backend configuration status; provider URL, model,
and API key are still configured on the backend through environment variables.

## Useful focused commands

Inspect streams:

```bash
fretpilot inspect song.mid
fretpilot tracks song.mid -o tracks.json
```

Analyze/build canonical data:

```bash
fretpilot analyze song.mid --stream-id t0:ch2:p27 -o analysis.json
fretpilot build-ir song.mid --stream-id t0:ch2:p27 -o guitar-ir.json
fretpilot sections song.mid --stream-id t0:ch2:p27
```

Export score/performance artifacts:

```bash
fretpilot export-gp5 song.mid --stream-id t0:ch2:p27 -o song.gp5
fretpilot-pdf song.mid --stream-id t0:ch2:p27 -o song.pdf
fretpilot export-ample-sc song.mid --stream-id t0:ch2:p27 -o song-ample-sc.mid
fretpilot-performance-plan song.mid --stream-id t0:ch2:p27 -o performance-plan.json
```

## Guitar execution baseline

Current deterministic/context-aware guitar decisions include:

- six-string string/fret candidates and distinct-string chord solving;
- movable riff/arpeggio repair and chord-voicing continuity;
- section-aware hand-position carry/reset;
- 1–4 fretting digits;
- hammer-on / pull-off / slide / vibrato;
- contextual palm mute / staccato;
- explicit-range monophonic MIDI pitch raises;
- down/up picking, strum, observed rolled strum, tremolo, and sweep baselines;
- conservative simultaneous/sequential harmony labels.

Role/style/technique evidence is section-aware and remains a soft ranking prior. The current profiles are useful baselines, not calibrated ground truth.

## Guitar IR V0.1

Canonical Guitar IR includes, among other fields:

- tempo/time-signature maps;
- measure/beat coordinates;
- cleaned score onset/duration;
- original source onset/duration/velocity;
- stable source-note identity;
- string/fret and fretting digit;
- generic articulations and pitch-movement parameters;
- right-hand intent;
- typed harmony regions;
- section/context and hand-position provenance;
- ties and transformation/change records.

Product-specific keyswitch/CC/state data is intentionally excluded.

## GP5 baseline

Current GP5 support includes:

- rests and duration decomposition;
- string/fret and fretting-digit mapping;
- ties;
- supported articulations;
- pick direction;
- observed rolled-strum `BeatStroke`;
- source-backed integer-semitone pitch curves with conservative fallback for unsupported fractional representation;
- harmony labels;
- write + parse-back validation.
- conservative second-voice preservation for same-onset chord members with
  clearly different releases when the sustained string is not reused.

Still pending: real Guitar Pro visual acceptance across full songs, general
voice separation for arbitrary overlapping material, and richer partial
let-ring representation inside chords.

## PDF/TAB baseline

The review renderer currently includes:

- landscape six-line TAB;
- harmony symbols;
- exact rests;
- stems, isolated flags, and meter-aware beams;
- dotted marks and triplet brackets;
- cross-measure ties;
- density-aware system breaking and over-density warnings.
- independent V1/V2 rhythm lanes for the conservative chord-release case;
- collision-aware technique-label lanes with explicit condensation warnings.

It is not publication-grade engraving yet. Mixed-density variable measure
widths, general voice separation, and paired standard staff + TAB remain future
score-quality work.

## Ample Guitar SC 4.x baseline

Approved profile id:

```text
ample-guitar-sc-v4
```

Current renderer preserves source timing/velocity and supports the regression-covered Sustain, Hammer/Pull, Legato Slide, Natural Harmonic, Palm Mute, and Slide In/Out control paths.

The provider-neutral VI layer now owns the approved static profile/capability knowledge. Public Ample export runs capability preflight and normalizes the generic profile through a thin compatibility view before delegating event scheduling to the proven legacy scheduler.

Canonical pick/strum intent, Generic PerformancePlan target adjustments, vibrato, and pitch-raise curves are currently reported as unsupported by the legacy Ample handoff rather than silently approximated.

See [`docs/AMPLE_GUITAR_SC.md`](docs/AMPLE_GUITAR_SC.md) for low-level current MIDI mapping details.

## Track identification

FretPilot resolves logical `InstrumentStream` objects before guitar analysis and combines:

1. track-name evidence;
2. channel/program/instrument metadata;
3. note behavior / guitar plausibility;
4. a separate section/behavior layer for how selected guitar material is being played.

Track identification is useful but not yet a calibrated finished classifier. Multiple likely guitar streams are not silently collapsed into one.

The local frontend now runs a guitar-only preflight when a MIDI is selected. It
shows probability, decision confidence, reasons, and a recommendation for each
high-confidence guitar part; possible and unlikely streams are excluded from
generation cards and summarized as a filtered count. Program fragments on the
same physical track and channel are displayed as one guitar part.

## Local frontend and API

Start the local engine with `fretpilot-api`. In a second terminal, run
`pnpm install` and `pnpm dev` from `web/`.

The browser is a client of the Python engine; it does not duplicate musical
policy. It provides guitar-only detection preflight, MIDI-fidelity and output
controls, conversion/download states, and read-only review of the pinned
guitar-playing and virtual-instrument knowledge catalogs. Ample Metal Eclipse
4.1 is catalogued for review only; the verified runtime export target remains
`ample-guitar-sc-v4`.

## Tests

```bash
pytest -q
```

GitHub Actions covers the main deterministic contracts, including MIDI stream resolution, rhythm/fingering behavior, section-aware execution, hand-position/fretting regressions, Guitar IR round trips, GP5 parse-back, PDF layout helpers, Ample event ordering/profile parity, VI capability negotiation/preflight, and generic shadow-control parity.

## Documentation source of truth

For contributors/agents:

```text
AGENTS.md                                  entry point / workflow rules
docs/AI_AGENT_HANDOFF.md                   short current-state handoff
docs/ROADMAP.md                            product milestone / release gates
docs/projects/*/BACKLOG.md                 task-level status by TI/GK/VI/SE family
```

Do not use old chat history as the authoritative project state when these repository documents exist.

## Prototype 0.1 status

The architecture and main deterministic vertical slice are in place. Prototype 0.1 is now primarily a **validation and quality-convergence** milestone.

Before external hands-on testing, FretPilot still needs:

- full real-song GP5/TAB musician review and acceptance;
- at least one real Ample Guitar SC DAW/plugin verification record;
- continued output-neutral VI handoff coverage;
- explicit handling of unsupported cases;
- documentation/reproducibility closeout.

Large-scale online learning, learned rankers, and multiple virtual-guitar products are deliberately not Prototype 0.1 blockers.
