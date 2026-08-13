# Virtual Instrument Adaptation Knowledge Base

> Built-in snapshot: `2026.08.0`

## Purpose and boundary

This knowledge base answers one question: **how does a particular software
instrument and version realize canonical guitar-performance intent?** It is
separate from Guitar Playing Knowledge, which decides what a guitarist should
play.

```text
Guitar Playing Knowledge              Virtual Instrument Knowledge
------------------------              ----------------------------
choose hammer-on intent      Guitar IR      map it to F0 + overlap
choose string/fret intent      --->         map it to string forcing
choose vibrato intent                       map it to CC1 behavior
```

Vendor keyswitches, CC numbers, velocity switches and plugin state never enter
Guitar IR. A new instrument profile can therefore replace the target renderer
without changing the upstream musical decision.

## Versioned structure

The packaged JSON asset contains one immutable snapshot and one or more
profiles:

```text
VirtualInstrumentKnowledgeSnapshot
├── snapshot_version + schema_version + lifecycle status
└── profiles[]
    └── VirtualGuitarInstrumentProfile
        ├── identity and product/version compatibility
        ├── playable range, tuning and sample modes
        ├── articulation capabilities[]
        │   └── ordered ControlAction[]
        ├── non-articulation controls[]
        ├── velocity layers[]
        ├── timing/calibration parameters
        ├── limitations
        └── evidence[]
```

Each `ControlAction` stores the raw MIDI number as the executable value and may
also retain the vendor note name as `display_label`. This is intentional:
octave labels differ between vendors and DAWs, while raw MIDI note numbers do
not.

Capability support is one of:

```text
native | approximated | unsupported | requires_fallback
```

Evidence status is independent:

```text
official   official product page/manual statement
verified   reproducible plugin/host test
candidate  report or inference awaiting reproduction
```

Profile maturity also stays independent. `official_documented` means that the
control map is source-backed; `plugin_unverified` means FretPilot has not yet
confirmed the behavior in the actual plugin. Documentation evidence must not
silently become a playback-verification claim.

## Initial profile: Ample Metal Eclipse 4.1

The first snapshot contains `ample-metal-eclipse-v4.1`, covering:

- product identity, ESP Eclipse I source instrument, bridge-pickup library,
  plugin formats and Mono/Stereo DI modes;
- raw playable range MIDI 36–84 (vendor labels C1–C5);
- Sustain/Pop, Natural Harmonic, Palm Mute, Slide In/Out, Legato Slide,
  Hammer-On/Pull-Off, Tap and Pinch Harmonic mappings;
- articulation-specific playable subranges and automatic-reset semantics;
- all documented Sustain velocity layers;
- string assignment, position assignment, position mode, open-string priority,
  auto-legato, vibrato, note repeater and performance-effect controls;
- per-string two-semitone down-tuning capability;
- explicit limitations for values that still need plugin calibration.

Sources are embedded in the profile as evidence records:

- official product page: `https://www.amplesound.net/en/pro-pd.asp?id=16`
- official main-panel manual: `https://amplesound.net/en/Main_Panel_Manual-AME.pdf`

The profile does **not** invent a keyswitch lead time or a tick-based legato
overlap. The manual requires ordering/overlap, but an exact timing value belongs
in a future verified calibration record.

## Runtime interface

Python callers use the provider-neutral registry:

```python
from fretpilot.virtual_instruments import get_builtin_virtual_instrument_registry

registry = get_builtin_virtual_instrument_registry()
profile = registry.require("ample-metal-eclipse-v4.1")
hammer_on = profile.capability("hammer_on")
string_assignment = profile.control("string_assignment")
```

The local product API exposes compact UI metadata at:

```text
GET /api/virtual-instruments
```

This listing does not yet make Eclipse the default export target. The current
Ample Guitar SC renderer remains unchanged until the generic adapter planner and
plugin conformance checks are complete.

## Adding another instrument

1. Create a new profile ID containing product and version family.
2. Record raw MIDI numbers plus vendor display labels.
3. Add official evidence separately from plugin-test evidence.
4. Mark absent support explicitly only when evidence supports that conclusion.
5. Add registry/model tests and product-specific conformance fixtures.
6. Verify in the exact plugin version and host, then update
   `verification_status` in a new snapshot rather than rewriting the released
   asset.

## Next verification work

- Load AME 4.1 in a supported host and verify every keyswitch audibly.
- Calibrate safe keyswitch preroll and minimum legato-overlap windows.
- Test whether string and position forcing match FretPilot's selected fingering.
- Verify CC1 vibrato, velocity-127 setting behavior and state reset/no-hanging
  notes.
- Add an Eclipse renderer target only after those checks are represented as
  reproducible evidence.
