# Guitar Playing Knowledge — Research Sources

This file maps the evidence-backed knowledge distilled into `src/fretpilot/knowledge/`.

The runtime knowledge base stores factual summaries and derived soft priors only. It does not copy or redistribute source tablature examples.

## Current source families

### MIDI-to-rich-tablature / fingering research

- Bontempi, Manerba, D'Hooge, Canazza (2024), *From MIDI to Rich Tablatures: an Automatic Generative System incorporating Lead Guitarists' Fingering and Stylistic choices* — https://arxiv.org/abs/2407.09052
  - persistent fretting-hand position;
  - phrase-local optimization plus phrase transitions;
  - hand/string movement versus available IOI;
  - hand-spread and open-string/timbre tradeoffs;
  - hammer-on, pull-off, slide, bend and vibrato feasibility/priors;
  - middle-neck position as a weak empirical prior, not a hard rule.

- D'Hooge, Bigo, Déguernel, Martin (2024), *Guitar Chord Diagram Suggestion for Western Popular Music* — https://arxiv.org/abs/2407.14260
  - current chord should not be voiced independently;
  - previous chord/voicing context improves chord-diagram choice and texture continuity.

- FretboardFlow (ISMIR 2025) — https://ismir2025program.ismir.net/poster_266.html
  - expert chord transitions and voicing history are useful evidence for context-aware fretboard navigation.

### Jazz voicing research

- Kunjara (2025), *Drop 2 Voicing for Guitar* — https://so06.tci-thaijo.org/index.php/rmj/article/view/278341
  - drop-2 is a practical guitar voicing family;
  - voicing choice and voice leading belong together.

### Fender educational references

- Blues scale / movable positions — https://www.fender.com/articles/scales/blues-guitar-scale
- Palm muting — https://www.fender.com/articles/techniques/3-keys-to-ace-your-palm-muting
- Picking families (alternate, down, tremolo, sweep, fingerstyle, hybrid) — https://www.fender.com/articles/techniques/what-type-of-picker-are-you
- Travis picking — https://www.fender.com/articles/techniques/travis-picking-on-guitar
- R&B / Soul rhythm and voicing language — https://www.fender.com/articles/songs/r-and-b-soul-path

## Runtime knowledge added from this research pass

```text
src/fretpilot/knowledge/research_sources.py
src/fretpilot/knowledge/fretboard_research.py
src/fretpilot/knowledge/articulation_research.py
src/fretpilot/knowledge/style_blues.py
src/fretpilot/knowledge/jazz_priors.py
src/fretpilot/knowledge/metal_priors.py
src/fretpilot/knowledge/fingerstyle_priors.py
src/fretpilot/knowledge/country_priors.py
src/fretpilot/knowledge/punk_priors.py
src/fretpilot/knowledge/syncopated_rhythm_priors.py
src/fretpilot/knowledge/picking_research.py
src/fretpilot/knowledge/rock_pop_priors.py
src/fretpilot/knowledge/strategy_priors.py
```

The current priors cover:

- persistent hand-position planning;
- weak 5–12 fret preference for suitable lead material;
- IOI-aware shift/string-change cost;
- previous-voicing context and texture continuity;
- same-string legato and slide feasibility;
- long-note vibrato preference;
- high-string / duration / cliché bias for bends;
- blues lead and shuffle/rhythm tendencies;
- jazz voicing/voice-leading tendencies;
- metal rhythm tendencies;
- rock/pop rhythm, arpeggio and lead tendencies;
- fingerstyle alternating-bass / bass-treble separation tendencies;
- country/hybrid-picking tendencies;
- punk power-shape/downstroke tendencies;
- syncopated/percussive chord-rhythm tendencies for funk/R&B/soul-like material;
- alternate, downstroke, tremolo, sweep and hybrid picking families;
- one style/technique strategy registry for future score planning.

## Next knowledge expansion

Priority additions:

1. song-level style prior feeding section-level strategy;
2. chord-quality inference and reusable chord-shape vocabulary;
3. blues lead cliché detector and bend target model;
4. jazz shell/drop-2/drop-3 concrete voicing library;
5. metal lead/tremolo/sweep phrase detectors;
6. right-hand picking-intent inference from symbolic rhythm/string motion;
7. chord-shape transition prototypes for western popular music;
8. style-conditioned score spelling and Guitar Pro notation strategy;
9. source-weighted evaluation against open/licensed symbolic examples;
10. learned candidate rankers after deterministic/evidence-backed baselines stabilize.

All new rules should preserve source IDs and remain soft preferences unless the rule is a true physical/playability constraint.
