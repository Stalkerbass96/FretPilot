# Total Rock Guitar Source Review

## Scope

The user-provided 94-page scan of Troy Stetina's *Total Rock Guitar* was
reviewed lesson by lesson as an editorial guitar-playing reference. Snapshot
`2026.08.2` records 71 independently worded candidate abstractions covering all
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
`src/fretpilot/knowledge/assets/knowledge-2026.08.2.json`.

## Source-independent representation

The book is registered once as `source.book.total_rock_guitar` in the snapshot
source registry. Each supported semantic rule references that ID through
`provenance.source_ids`. No lesson, page, title, or book-specific field appears
inside a musical payload.

Future books or datasets should be registered once and linked to existing
semantic entries. A new source is not a reason to duplicate a musical rule.

## Rights and transformation boundary

The snapshot stores only concise, derived musical concepts in new wording. It
does not embed or redistribute:

- full songs or continuous TAB;
- page images;
- audio or backing tracks;
- exercise sequences that reconstruct the source notation.

Rights and allowed-use metadata live on the shared source record rather than
being repeated 71 times. Any broader redistribution or training use requires a
separate rights decision.

## Runtime boundary

All 71 entries are `candidate` and `untested`. They are returned by the API and
shown in the human-review console, but no new consumer is wired into fingering,
articulation, rewrite, or performance generation yet. Existing approved Playing
Profiles remain the only approved playing knowledge used by the current runtime.

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
