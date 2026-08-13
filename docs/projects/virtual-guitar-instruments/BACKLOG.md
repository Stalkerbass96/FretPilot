# Virtual Guitar Instrument Knowledge Backlog

Use the `VI-` prefix for product-specific virtual-guitar knowledge, generic adapter schemas, compatibility testing, and renderer behavior.

Status markers:

- `[ ]` not started
- `[~]` in progress
- `[x]` implemented/verified

## P0 — establish the adapter knowledge contract

### [~] VI-001 — Generic VirtualGuitarInstrumentProfile schema

Define a shared typed schema for virtual-guitar capabilities and control mappings.

Minimum concepts:

```text
profile_id
vendor
product
version_family
profile_schema_version
playable_range
supported_articulations
control bindings
state/latch semantics
preroll/overlap requirements
pitch-expression capabilities
string/position forcing capabilities
known limitations
provenance/evidence
maturity
```

Acceptance:

- the schema can represent the current Ample Guitar SC profile without losing information;
- raw keyswitch/CC numbers remain outside Guitar IR;
- unsupported and approximated capabilities are distinguishable;
- profile identity/version is serializable into output reports.

### [ ] VI-002 — Migrate Ample Guitar SC profile to the generic schema

Keep current rendering behavior green while moving static knowledge out of the Ample-only dataclass.

Acceptance:

- existing Ample parse-back tests remain green;
- the renderer consumes the generic profile or a thin Ample extension;
- current `ample-guitar-sc-v4` profile remains selectable;
- no musical intent changes are introduced by the migration.

### [x] VI-003 — Adapter registry

Create a registry/factory that resolves a requested virtual-guitar profile independently of the CLI command implementation.

Example target:

```text
get_virtual_guitar_profile("ample-guitar-sc-v4")
list_virtual_guitar_profiles()
```

Acceptance:

- profile lookup is provider-neutral;
- unknown profiles fail with an explicit available-profile list;
- profile metadata is available to API/UI without importing product-specific renderer internals.

### [ ] VI-004 — Capability negotiation

Before rendering, compare Guitar IR intent with target-product capabilities.

Required result categories:

```text
native
approximated
unsupported
requires_fallback
```

Acceptance:

- unsupported bends/vibrato/etc. are reported before output when possible;
- renderer does not silently discard important musical intent;
- the processing report lists capability fallbacks and unsupported events.

## P1 — rendering/state-machine quality

### [ ] VI-010 — Generic articulation control binding model

Support binding types such as:

```text
keyswitch
cc
velocity_range
program_change
note_overlap
pitch_bend
channel_policy
compound/state-machine action
```

Acceptance:

- one canonical articulation can require multiple ordered control actions;
- latch vs momentary state is explicit;
- reset semantics are explicit.

### [ ] VI-011 — Instrument state-machine interface

Some products require persistent articulation state, resets, or mutually exclusive controls.

Acceptance:

- state transitions are deterministic;
- hanging/stale articulation state can be detected in tests;
- renderers can expose a final-state validation report.

### [ ] VI-012 — Timing and legato calibration profile

Represent product/version-specific timing requirements:

- keyswitch preroll;
- hammer/pull overlap;
- legato slide overlap;
- release ordering;
- optional host/plugin latency compensation.

Acceptance:

- timing parameters are profile data where possible, not magic numbers in renderer flow;
- exact values carry provenance or test evidence.

### [ ] VI-013 — Pitch-expression capability model

Represent:

- pitch-bend range;
- monophonic/channel-wide bend limitations;
- per-note/MPE support where applicable;
- vibrato controller methods;
- polyphonic-bend fallback rules.

Acceptance:

- Guitar IR bend/vibrato intent can be validated against target capabilities;
- unsupported polyphonic expression is surfaced clearly.

### [ ] VI-014 — String/position forcing abstraction

Some virtual guitars can force strings, positions, or fretboard behavior.

Acceptance:

- the capability can be declared without assuming every product supports it;
- FretPilot fingering may be translated when supported;
- unsupported forcing does not alter canonical string/fret intent silently.

### [ ] VI-015 — Picking/strumming control abstraction

Represent optional product controls for:

- down/up picking;
- strum direction/spread;
- repeated-note alternation;
- sweep/rake controls;
- accents/ghost notes.

Acceptance:

- upstream `PerformancePlan` expresses musical intent;
- the adapter maps that intent to available product controls or reports approximation.

## P1 — validation and evidence

### [~] VI-020 — Profile provenance schema

Every nontrivial product mapping should record evidence such as:

```text
official_manual
vendor_midi_map
verified_plugin_test
user_report
inferred_behavior
```

Minimum metadata:

```text
source type
document/product version
retrieval/test date
evidence notes
verification status
```

Acceptance:

- official documented controls and inferred behavior are distinguishable;
- changing a mapping requires updating evidence/version metadata.

### [ ] VI-021 — Adapter conformance test suite

Define reusable tests every adapter/profile should run where applicable:

- output MIDI parses successfully;
- notes remain in supported range;
- state resets correctly;
- no hanging notes;
- keyswitch/control ordering is valid;
- legato overlap conditions are met;
- unsupported intent produces warnings;
- deterministic rendering from the same inputs.

### [ ] VI-022 — Manual plugin verification records

Create a structured record for DAW/plugin verification by product/version.

Example checks:

```text
articulation triggers
string forcing
legato behavior
bend behavior
vibrato behavior
release/hanging notes
host-specific quirks
```

Acceptance:

- verified behavior is tied to exact product/version/profile version;
- unverifiable assumptions remain marked experimental.

## P2 — multi-product support

### [ ] VI-030 — Add second virtual-guitar adapter

Choose the next product based on user demand and availability of reliable documentation/testing.

Acceptance:

- implementation uses the generic profile/capability contract;
- no Ample-specific assumptions are copied into shared code;
- at least one common Guitar IR fixture renders through both adapters for comparison.

### [ ] VI-031 — Add third adapter family

Target a meaningfully different control architecture so the abstraction is tested against more than two similar products.

### [ ] VI-032 — Product/version compatibility matrix

Maintain a matrix such as:

```text
profile
product/version
verified host(s)
articulation coverage
string forcing
bend/vibrato support
maturity
last verified
```

Acceptance:

- API/UI can expose adapter maturity and limitations;
- product upgrades can be tracked without silently treating versions as equivalent.

## P2 — knowledge evolution

### [ ] VI-040 — Adapter knowledge candidate lifecycle

Use a controlled lifecycle for new mappings or changed behavior:

```text
candidate
→ evidence review
→ automated conformance tests
→ plugin/manual verification where required
→ approved profile version
```

Acceptance:

- newly discovered web/manual information never changes production mappings immediately;
- runtime only loads approved adapter profiles by default.

### [ ] VI-041 — Calibration dataset

Collect reproducible calibration cases for timing, velocity, overlap, and expression behavior.

Examples:

- minimum legato overlap that reliably triggers;
- safe keyswitch lead time;
- velocity ranges producing intended articulations;
- bend curve response;
- repeated-note behavior.

Acceptance:

- results identify plugin/product version and host/test setup;
- calibration affects only adapter knowledge, not canonical guitar-playing knowledge.

### [ ] VI-042 — Learned expressive adapter tuning

After enough verified data exists, allow learned/optimized parameters for expressive rendering, such as:

- overlap amount;
- velocity scaling;
- strum spread;
- accent translation;
- fallback selection among several supported articulations.

Hard protocol/control mappings remain source-backed/versioned facts.

Acceptance:

- learned parameters are versioned separately from official control mappings;
- candidate vs approved separation follows the System Evolution lifecycle;
- deterministic fallback remains available.

## P3 — product integration

### [ ] VI-050 — Generic export command/API target selection

Long-term interface example:

```bash
fretpilot export-performance song.mid \
  --instrument-profile ample-guitar-sc-v4
```

The current Ample-specific command may remain as a convenience alias.

Acceptance:

- API/UI can list supported targets from the registry;
- output package records exact profile/version;
- renderer warnings are product-specific but returned through a common report schema.

### [ ] VI-051 — User calibration/override profile

Allow users to override safe adapter parameters for their local setup without modifying canonical profiles.

Examples:

- keyswitch preroll adjustment;
- overlap adjustment;
- velocity scaling;
- host latency compensation.

Acceptance:

- overrides are separated from official profile knowledge;
- reports record active overrides;
- unsafe/invalid control changes are validated.

## Guardrails

- Never put vendor-specific keyswitch/CC numbers into Guitar IR.
- Never make Guitar Playing Knowledge depend on one plugin's limitations.
- Official control mappings and learned expressive preferences are different knowledge types.
- Version product profiles by product/version family and verification state.
- A new plugin version is not assumed compatible until verified.
- Runtime does not crawl vendor/internet pages to discover mappings during export.
- Unsupported musical intent must be reported, approximated explicitly, or preserved for another target; never silently discarded when material.
