# Virtual Guitar Instrument Knowledge Backlog

Use the `VI-` prefix for product-specific virtual-guitar knowledge, generic adapter schemas, compatibility testing, and renderer behavior.

Status markers:

- `[ ]` not started
- `[~]` in progress
- `[x]` implemented/verified

## P0 — establish the adapter knowledge contract

### [x] VI-001 — Generic VirtualGuitarInstrumentProfile schema

A shared typed schema now represents provider-neutral virtual-guitar capabilities and control mappings.

Implemented concepts include:

```text
profile_id
vendor
product
version_family
profile_schema_version
playable_range
articulation capabilities
ordered generic ControlAction records
fallback intent
preroll/overlap timing parameters
pitch-expression capability flags
string/position forcing flags
known limitations
provenance/evidence
maturity
```

Current guarantees:

- raw keyswitch/control facts remain outside Guitar IR;
- `native`, `approximated`, `unsupported`, and `requires_fallback` are distinguishable;
- capabilities may require multiple ordered generic actions;
- profile identity/version and evidence are serializable into diagnostics.

### [~] VI-002 — Migrate Ample Guitar SC profile to the generic schema

**Implemented baseline:** `AMPLE_GUITAR_SC_V4_PROFILE` now mirrors the regression-covered legacy `ample-guitar-sc-v4` facts in the generic schema, including playable range, channel, keyswitch values, timing/overlap values, reset semantics, limitations, and repository-regression evidence. Dedicated parity tests ensure the migrated data remains identical to the current legacy profile.

**Still pending before completion:**

- make the legacy Ample renderer consume the generic profile (or a deliberately thin compatibility view);
- prove legacy MIDI event ordering/output remains regression-neutral after that handoff;
- remove duplicate static profile truth only after renderer parity is established.

Acceptance:

- existing Ample parse-back tests remain green;
- the renderer consumes the generic profile or a thin Ample extension;
- current `ample-guitar-sc-v4` profile remains selectable;
- no musical intent changes are introduced by the migration.

### [x] VI-003 — Adapter registry

A deterministic approved-profile registry now resolves `profile_id` independently of CLI/product renderer code.

Implemented behavior:

```text
list_profiles()
get_profile("ample-guitar-sc-v4")
```

- registry snapshot is immutable at runtime;
- duplicate ids fail during module initialization;
- unknown ids fail with the available profile list;
- runtime registry never crawls vendor pages or loads unapproved candidate knowledge.

### [~] VI-004 — Capability negotiation

**Implemented baseline:** provider-neutral negotiation resolves one canonical intent to an explicit `CapabilityResolution` with:

```text
native
approximated
unsupported
requires_fallback → deterministic fallback chain
```

Additional implemented pieces:

- missing declarations remain explicitly unsupported;
- fallback cycles raise instead of looping;
- `CapabilityReport` inventories actual Guitar IR articulation/right-hand requirements and optional Generic PerformancePlan timing/duration/velocity requirements;
- tied score fragments are deduplicated by source-note identity;
- ordinary `fretpilot prototype` writes per-stream `*.vi-capabilities.json` plus top-level `vi-capabilities.json` diagnostics against the approved `ample-guitar-sc-v4` profile;
- current legacy handoff limitations such as pick direction, sweep/tremolo/rolled strum, vibrato/pitch raise, and Generic PerformancePlan adjustments are explicit rather than silently omitted.

**Still pending before completion:**

- run negotiation before target rendering rather than only as a read-only prototype diagnostic;
- connect resolved capabilities to adapter handoff with output-neutral regression coverage;
- decide policy for whether particular unsupported intents warn, approximate, or block a target render;
- surface the same summary in the canonical processing report/API contract where appropriate.

## P1 — rendering/state-machine quality

### [~] VI-010 — Generic articulation control binding model

The generic `ControlAction` baseline already supports compound capability mappings and is used by the migrated Ample profile for keyswitch and note-overlap actions.

Still needed:

```text
cc
velocity_range
program_change
pitch_bend
channel_policy
richer compound/state-machine action metadata
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

### [~] VI-012 — Timing and legato calibration profile

The migrated Ample generic profile already stores its current regression-backed keyswitch length, preroll, and legato overlap parameters. Broader calibration/provenance remains pending.

Represent product/version-specific timing requirements:

- keyswitch preroll;
- hammer/pull overlap;
- legato slide overlap;
- release ordering;
- optional host/plugin latency compensation.

Acceptance:

- timing parameters are profile data where possible, not magic numbers in renderer flow;
- exact values carry provenance or test evidence.

### [~] VI-013 — Pitch-expression capability model

The generic profile already declares per-note pitch-expression support and optional bend range, and the current Ample migrated profile explicitly reports canonical `pitch_raise` as unsupported by the legacy adapter handoff.

Still needed:

- channel-wide bend policy;
- vibrato controller methods;
- polyphonic-bend fallback rules;
- verified adapter mappings when reliable product evidence is available.

### [ ] VI-014 — String/position forcing abstraction

Some virtual guitars can force strings, positions, or fretboard behavior.

Acceptance:

- the capability can be declared without assuming every product supports it;
- FretPilot fingering may be translated when supported;
- unsupported forcing does not alter canonical string/fret intent silently.

### [~] VI-015 — Picking/strumming control abstraction

Canonical Guitar IR now carries right-hand `motion`, `direction`, and techniques such as `rolled_strum`, `tremolo`, and `sweep`. Capability diagnostics translate those into provider-neutral requirements such as `pick_down`, `strum_up`, and technique intents.

The current Ample migrated baseline explicitly reports these as unsupported by the legacy handoff; product-specific control realization remains pending.

Acceptance:

- upstream Guitar IR / PerformancePlan expresses musical intent;
- the adapter maps that intent to available product controls or reports approximation.

## P1 — validation and evidence

### [~] VI-020 — Profile provenance schema

`AdapterEvidence` now separates source type, reference, status, and notes. The Ample migration intentionally uses `repository_regression` evidence and does **not** claim official vendor provenance.

Still needed for future mappings:

```text
official_manual
vendor_midi_map
verified_plugin_test
user_report
inferred_behavior
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

Existing Ample profile-parity and negotiation tests are building blocks, but a reusable cross-adapter suite is still pending.

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
- expression curves.

Only approved/versioned parameter snapshots may reach normal runtime.
