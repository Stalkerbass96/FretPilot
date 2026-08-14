# FretPilot Frontend Design System

> Status: `Quiet Studio 0.1` baseline, introduced 2026-08-13.

## Product direction

FretPilot is a musician-facing creation tool, not a generic analytics dashboard.
The frontend should make the first conversion simple, reveal deeper controls only
when they matter, and keep musical material visually dominant.

The baseline follows four principles:

1. **Quiet confidence** — warm neutral surfaces, restrained color, thin borders,
   and very light elevation.
2. **Musical focus** — score/TAB previews and decisions take priority over charts
   or decorative dashboard metrics.
3. **Simple first, powerful later** — the main path is file, intent, outputs;
   advanced controls remain secondary.
4. **Explainable states** — recommendations, warnings, progress, and local-engine
   status are visible without turning the page into an alert wall.

## Research synthesis

The system combines ideas rather than cloning one product:

- [Geist typography](https://vercel.com/geist/typography) for compact, explicit
  text roles and disciplined hierarchy.
- [Geist colors](https://vercel.com/geist/colors) for semantic separation of
  backgrounds, component surfaces, borders, and text/icon contrast.
- [Radix Themes color](https://www.radix-ui.com/themes/docs/theme/color) for
  stepped accent/neutral thinking and light-mode variants.
- [Radix Primitives](https://www.radix-ui.com/primitives/docs/overview/introduction)
  for accessible, unstyled interaction behavior that remains fully brandable.
- [shadcn/ui](https://ui.shadcn.com/docs) for open-code component ownership and
  a predictable composition model rather than an opaque component dependency.
- [Linear Method](https://linear.app/method/introduction) for purpose-built UI,
  clarity, and progressive complexity.
- [Atlassian foundations](https://atlassian.design/foundations) for treating
  tokens as the shared source of truth across color, spacing, type, border,
  radius, and elevation.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) for contrast, visible focus,
  reflow, keyboard navigation, and target-size requirements.

## Technical baseline

```text
web/
├── React 19 + TypeScript
├── Vite
├── Tailwind CSS 4
├── Radix UI interaction primitives
├── Lucide icons
└── Vitest + Testing Library
```

The Python engine remains the canonical source of musical decisions. The web
application is an independent client and must not duplicate fingering,
articulation, rewrite, or export policy in browser code.

Target integration boundary:

```text
browser File
→ future local/API upload endpoint
→ FretPilot prototype service
→ job/output manifest
→ review UI and downloads
```

## Core tokens

Tokens live in `web/src/styles.css` and are named by purpose rather than raw hue.

```text
canvas / canvas-deep       application background
surface / surface-soft     cards and quiet inset areas
ink / ink-soft             primary and supporting text
muted / faint              metadata and tertiary information
line / line-strong         separation and interactive boundaries
accent / accent-soft       primary actions and selected state
warm / warm-soft           review-needed state
```

The baseline uses 8, 12, 18, and 24px radii by role. Shadows never communicate
selection by themselves; selection also uses color and/or borders.

## Typography

- Display: an editorial serif stack for the product promise and major empty
  states. It should be rare.
- Interface: the platform's high-quality sans stack, including native Chinese
  fonts, for controls and dense information.
- Mono: source stream IDs, technical values, and version identifiers only.

## Accessibility contract

- All controls use native elements or Radix primitives.
- Focus indication is visible and does not rely on color alone.
- Interactive targets meet the WCAG 2.2 24px minimum; primary buttons and
  navigation targets are at least 32px.
- File selection exposes errors through an alert role.
- Drag-and-drop is always paired with a keyboard-operable file input.
- Motion is reduced under `prefers-reduced-motion`.
- Responsive layout reflows rather than scaling down desktop UI.

## Current scope

Implemented:

- responsive application shell and navigation;
- conversion workspace;
- MIDI file selection/drop state and validation;
- MIDI-fidelity preference;
- PDF, GP5, and Ample MIDI output selection;
- recent-project and project-library presentations;
- visible design-system reference page;
- foundational interaction tests.

Not yet implemented:

- Python API/server and real job execution;
- live progress/event streaming;
- score preview and measure-level correction UI;
- persistent project storage;
- routing, authentication, localization infrastructure;
- dark theme.
