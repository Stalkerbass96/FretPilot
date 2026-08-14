# Virtual Guitar Instrument Knowledge Backlog

Use the `VI-` prefix for product-specific virtual-guitar knowledge, generic adapter contracts, compatibility testing, and renderer behavior.

```text
[x] implemented/verified baseline
[~] in progress
[ ] not started
```

## P0 — adapter knowledge contract

| Task | Status | Current contract |
|---|---|---|
| VI-001 Generic VirtualGuitarInstrumentProfile | [x] | provider-neutral capability/profile schema |
| VI-002 migrate Ample Guitar SC facts | [x] | generic profile is the public static truth; thin compatibility view preserves legacy scheduler output |
| VI-003 adapter/profile registry | [x] | deterministic approved-profile lookup by `profile_id` |
| VI-004 capability negotiation / handoff | [~] | negotiation, reports, preflight policy, and shadow control planning exist; production scheduler handoff remains |

### VI-001 — generic profile schema

The shared schema represents:

```text
profile identity/version
playable range/channel
capability support level
ordered generic ControlAction records
fallback intent
preroll/overlap/reset timing
pitch-expression flags
string/position forcing flags
limitations
provenance/evidence
maturity
```

Raw keyswitch/CC/state facts remain outside Guitar IR and Guitar Playing Knowledge.

### VI-002 — Ample Guitar SC 4.x migration

**Implemented/verified baseline.** `AMPLE_GUITAR_SC_V4_PROFILE` carries the regression-backed Ample facts currently used by FretPilot. Public `export_ample_sc_midi` now selects the generic profile by default, runs provider-neutral capability preflight, normalizes profile data through a deliberately thin renderer view, and delegates event scheduling to the proven legacy renderer.

Regression coverage protects:

- playable range/channel/profile identity;
- keyswitch mappings;
- preroll/overlap/keyswitch-length values;
- reset semantics;
- explicit keyswitch release value and reset offset;
- default generic path vs explicit generic/legacy overrides;
- legacy MIDI event/tick neutrality for the covered fixtures.

Remaining cleanup is non-blocking: duplicate legacy profile structures may be reduced only when compatibility and external callers remain safe. Do not remove the legacy scheduler merely to make the architecture look cleaner.

### VI-003 — approved profile registry

Implemented:

```text
list_profiles()
get_profile("ample-guitar-sc-v4")
```

The runtime registry is deterministic and local. It never crawls vendor pages or auto-loads candidate mappings.

### VI-004 — capability negotiation and adapter handoff

Implemented baseline:

```text
canonical intent
→ CapabilityResolution
   native / approximated / unsupported / requires_fallback
→ CapabilityReport
→ pre-render policy
   report_only / warn / strict
→ shadow VirtualInstrumentControlPlan
```

Additional implemented behavior:

- undeclared intents resolve explicitly as unsupported;
- fallback cycles fail instead of looping;
- capability reports inventory Guitar IR articulation/right-hand requirements and optional Generic PerformancePlan timing/duration/velocity requirements;
- tied fragments are deduplicated by source-note identity;
- normal `fretpilot prototype` writes per-stream `*.vi-capabilities.json` plus top-level `vi-capabilities.json`;
- current Ample limitations such as pick/strum/sweep/tremolo, vibrato/pitch raise, and Generic PerformancePlan adjustments are explicit;
- public Ample rendering runs capability preflight before the legacy scheduler;
- shadow generic control planning compiles approved `ControlAction` records and is regression-compared with legacy keyswitch/legato scheduling.

Current shadow parity includes exact keyswitch note-on/release semantics, reset `+1 tick` behavior, preroll, and linked-note overlap for the covered Ample fixture.

Still pending before VI-004 is complete:

- let the production adapter consume the generic control plan instead of only shadow-comparing it;
- preserve exact legacy output during that handoff;
- connect selected Generic PerformancePlan target timing/duration/velocity intents only when the target profile declares a safe realization;
- expose a stable capability/preflight summary in the broader product API/report contract where useful.

Do not switch production scheduling until parity coverage is strong enough.

## P1 — rendering / state-machine quality

| Task | Status | Remaining focus |
|---|---|---|
| VI-010 generic ControlAction binding model | [~] | CC, velocity ranges, program change, pitch bend, channel policy, richer state metadata |
| VI-011 instrument state-machine interface | [ ] | persistent/latching state, resets, final-state validation |
| VI-012 timing/legato calibration profile | [~] | broader measured provenance and optional host/plugin latency |
| VI-013 pitch-expression capability model | [~] | channel-wide policy, vibrato methods, polyphonic fallback, verified target mapping |
| VI-014 string/position forcing abstraction | [ ] | target-neutral forcing capability + safe unsupported behavior |
| VI-015 picking/strumming control abstraction | [~] | product realization for canonical pick/strum/sweep/tremolo intent |

### VI-010 — ControlAction baseline

Current generic actions already cover keyswitches, linked note overlap, timing anchors, duration, explicit release values, and relative tick offsets. One canonical capability may require multiple ordered actions.

Still needed as actual products require them:

```text
cc
velocity_range
program_change
pitch_bend
channel_policy
persistent/latching state metadata
```

### VI-012 — timing calibration

The Ample profile currently stores repository-regression-backed keyswitch length, preroll, legato overlap, release semantics, and reset timing. Future calibration must keep exact product/version/host evidence rather than turning measurements into unexplained magic numbers.

### VI-013 — pitch expression

The generic schema can declare pitch-expression capability and bend range. Current Ample legacy handoff explicitly reports canonical `pitch_raise`/vibrato realization as unsupported. Add target mappings only with reliable evidence/plugin validation.

### VI-015 — picking/strumming

Canonical Guitar IR already carries right-hand motion/direction and techniques such as `rolled_strum`, `tremolo`, and `sweep`. Capability negotiation can report those requirements. Current Ample baseline does not realize them through product-specific controls yet.

## P1 — validation / evidence

| Task | Status | Remaining focus |
|---|---|---|
| VI-020 profile provenance | [~] | expand evidence categories and verified vendor/plugin references |
| VI-021 reusable adapter conformance suite | [~] | turn current Ample parity/negotiation tests into reusable cross-adapter fixtures |
| VI-022 manual plugin verification records | [ ] | real DAW/plugin evidence tied to exact product/version |

### VI-020 — provenance

`AdapterEvidence` distinguishes source type, reference, status, and notes. The Ample migration deliberately uses repository-regression evidence and does **not** claim official vendor verification.

Future evidence types may include:

```text
official_manual
vendor_midi_map
verified_plugin_test
user_report
inferred_behavior
```

### VI-021 — conformance

Current tests already cover substantial Ample behavior: parseability, profile parity, event order, legato overlap, capability negotiation, preflight policy, and generic shadow-plan parity. The remaining task is to define a reusable suite every future adapter can run.

Expected shared checks:

- supported note range;
- no hanging notes;
- deterministic rendering;
- valid control ordering/reset/final state;
- required overlap/timing;
- explicit unsupported warnings/errors;
- output-neutral profile/control-plan handoff where applicable.

### VI-022 — real plugin verification

Prototype 0.1 still needs at least one structured verification record from actual Ample Guitar SC 4.x playback in a DAW/plugin host.

Record:

```text
profile/product/version
host/setup
articulation triggers
legato behavior
release/hanging notes
bend/vibrato behavior
known host quirks
verification date/result
```

Automated MIDI parse-back is necessary but not equivalent to plugin verification.

## P2 — multi-product support

| Task | Status |
|---|---|
| VI-030 second virtual-guitar adapter | [ ] |
| VI-031 third/different adapter family | [ ] |
| VI-032 product/version compatibility matrix | [ ] |

Do not add a second product until the generic contract is sufficiently proven by Ample conformance and the new adapter has reliable documentation/testing access.

## P2 — adapter knowledge evolution

| Task | Status |
|---|---|
| VI-040 adapter candidate lifecycle | [ ] |
| VI-041 calibration dataset | [ ] |
| VI-042 learned expressive adapter tuning | [ ] |

Target lifecycle:

```text
candidate mapping/calibration
→ evidence review
→ automated conformance
→ plugin/manual verification where needed
→ approved versioned profile
```

New web/manual/user evidence never changes production mappings automatically.

## Boundary rules

- Guitar IR expresses canonical musical intent, not product controls.
- Guitar Playing Knowledge (`GK-*`) describes real-guitar choices, not plugin behavior.
- Adapter approximations/unsupported cases must be explicit.
- Product facts require provenance and version identity.
- Preserve the proven legacy output while migrating architecture; architecture cleanup is not a license to change musical behavior.
