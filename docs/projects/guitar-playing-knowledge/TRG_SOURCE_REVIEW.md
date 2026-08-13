# Total Rock Guitar Source Review

## Scope

The user-provided 94-page scan of Troy Stetina's *Total Rock Guitar* was
reviewed lesson by lesson as an editorial guitar-playing reference. Snapshot
`2026.08.1` records 71 independently worded candidate abstractions covering all
22 lessons.

The source is not treated as a statistical dataset or ground-truth TAB corpus.
It contributes explainable editorial priors only.

## Candidate inventory

| Kind | Count | Intended use |
|---|---:|---|
| `execution_rule` | 20 | Physical technique, muting, bends, harmonics, legato and picking actions |
| `rhythm_rule` | 12 | Subdivision, accent, shuffle, rests and picking-motion continuity |
| `phrase_pattern` | 8 | Riff, pedal-tone, repetition, question/answer and arrangement organization |
| `harmonic_context` | 22 | Tonality, scale color, chord function and pitch-rewrite protection |
| `shape_family` | 9 | Reusable dyad, chord, inversion and partial-shape families |

The complete machine-readable inventory lives in
`src/fretpilot/knowledge/assets/knowledge-2026.08.1.json`.

## Coverage by lesson family

- Lessons 1–4: movable dyads and power chords, slides, rests, muting, rolling
  string changes, legato, palm mute and arpeggiation.
- Lessons 5–8: pentatonic language, bends, vibrato, barre/open chords, blues
  comping, accents, alternate picking, continuous strumming and major harmony.
- Lessons 9–12: expressive bend types, modal and pentatonic color, riff
  transposition, Blues Scale, rhythmic displacement and sixteenth offbeats.
- Lessons 13–17: minor harmony, diatonic harmonization, natural and pinch
  harmonics, fret-hand mute, scale-position connectivity, rakes, rapid licks,
  rests and question/answer phrasing.
- Lessons 18–22: Roman-numeral transposition, partial triads, pedal-tone metal
  riffing, minor/modal/hybrid scales, chromatic passing tones, Half-time,
  Shuffle, sliding octaves, picking-strategy alternatives, tritone motion,
  tremolo picking and three-note-per-string runs.

## Rights and transformation boundary

The snapshot stores only concise, derived musical concepts in new wording. It
does not embed or redistribute:

- full songs or continuous TAB;
- page images;
- audio or backing tracks;
- exercise sequences that reconstruct the source notation.

Every source-derived entry records `user_provided_reference` provenance and an
allowed-use note. Any broader redistribution or training use requires a
separate rights decision.

## Runtime boundary

All 71 entries are `candidate` and `untested`. They are returned by the API and
shown in the human-review console, but no new consumer is wired into fingering,
articulation, rewrite, or performance generation yet. Existing approved Playing
Profiles remain the only source-derived knowledge used by the current runtime.

Promotion path:

```text
candidate abstraction
→ original synthetic fixture
→ rule-level regression
→ real-song shadow comparison
→ human guitar-player review
→ evaluated entry
→ explicit consumer integration
→ approved snapshot
```
