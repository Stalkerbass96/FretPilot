# FretPilot AI / Codex Handoff

Read `AGENTS.md` first. This file is the compact continuation point only.
Architecture lives in [`ARCHITECTURE.md`](ARCHITECTURE.md), product priority in
[`ROADMAP.md`](ROADMAP.md), and task status in the specialized backlogs.

## Last verified baseline

At this handoff, `main` includes the validated LLM shadow implementation and
was verified with:

```bash
.venv/bin/python -m pytest -q       # 204 passed
cd web && pnpm test                 # 11 passed
cd web && pnpm build                # type checks + production build passed
```

In Codex Desktop, load the bundled workspace dependencies first if `pnpm`
cannot find `node`; this is an execution-environment issue, not a project setup
alternative.

Run `git status -sb` and `git log -1 --oneline` before editing; do not assume a
development server from a prior task is still running.

## Product runtime

```text
MIDI → streams → guitar confidence → deterministic rewrite
→ section-aware analysis → Guitar IR
→ PDF / GP5 / PerformancePlan / VI report / Ample MIDI
```

`generate_prototype_package()` is the single product conversion pipeline.
Section-aware musical execution lives only in
`analysis/section_execution.py`. Compatibility modules must remain thin.

Current scope is standard-tuned six-string guitar. MIDI fidelity defaults to
`0.35`, favoring playable/coherent output while preserving rewrite provenance.
The pinned guitar-playing knowledge snapshot is `2026.08.2`.

## AI shadow: exact current state

The optional path is deliberately separate from conversion:

```text
deterministic rewrite baseline
→ bounded structured note context
→ OpenAI-compatible provider
→ deterministic proposal validation
→ ShadowRewriteReport (`applied: false`)
```

Implementation entry points:

```text
src/fretpilot/ai/models.py                         provider-neutral contracts
src/fretpilot/ai/context.py                        bounded/redacted context
src/fretpilot/ai/providers/openai_compatible.py    HTTP adapter
src/fretpilot/ai/validation.py                     hard validation and budgets
src/fretpilot/ai/shadow.py                         read-only orchestration
src/fretpilot/ai/config.py                         environment configuration
src/fretpilot/api/app.py                           status + shadow endpoints
web/src/AIShadowPanel.tsx                          consent/review UI
```

The model receives at most 256 structured notes by default, the source basename,
deterministic changes, policy budgets, and musical features. It does not receive
binary MIDI or a full local path. Accepted suggestions are still not applied to
MIDI, Guitar IR, GP5, or any other artifact.

Configuration is currently backend-only:

```text
FRETPILOT_LLM_BASE_URL
FRETPILOT_LLM_MODEL
FRETPILOT_LLM_API_KEY
FRETPILOT_LLM_PROVIDER_ID   optional
FRETPILOT_LLM_JSON_MODE     optional
```

The frontend only reads `/api/ai/status`, asks for external-processing consent,
and calls `/api/ai/shadow`. It has no provider-configuration editor yet.
`create_app()` currently captures the startup advisor; introduce a small
backend-owned state object instead of mutable module globals.

## Next requested increment (`SE-050`)

Unless the user changes direction, implement safe provider configuration from
the local frontend. Keep this first increment session-only in backend memory;
do not invent plaintext disk persistence. Preserve environment variables as the
startup fallback.

Acceptance boundary:

1. Backend exposes non-secret status plus explicit configure/test/clear actions.
2. API key is write-only: never returned, logged, placed in a URL, browser
   storage, report, job artifact, exception, or test snapshot.
3. Base URL validation remains HTTP(S)-only with no embedded credentials,
   query, or fragment.
4. Configuration changes replace the active advisor atomically for later
   requests; a failed connection test does not destroy the last working config.
5. The UI clearly distinguishes environment and session configuration, supports
   connection testing, and still requires per-analysis external-AI consent.
6. AI remains Shadow-only and cannot enter the canonical GP5/output pipeline.
7. Add API redaction/error tests and frontend configure/test/clear tests, then
   run the full baseline commands above.

If persistence across restarts is requested later, use an OS credential store
or another explicit secret backend; do not use `localStorage` or a repository
configuration file.

## Stable capabilities and known limits

Stable baseline includes logical MIDI streams, explainable guitar confidence,
provenance-safe rewrite, section-aware playing analysis, playable fingering,
canonical Guitar IR, GP5/PDF/PerformancePlan/VI/Ample outputs, FastAPI jobs, the
React review UI, and the approved generic Ample SC profile.

Evidence is still required for full-song score acceptance, real Ample plugin
behavior, calibrated detection/style profiles, and comparative LLM quality.
AI advice is read-only; generic VI control planning is also shadow-only; API
jobs are process-local, and the proposed first configuration increment should
be process-local as well.

## Resume rules

- Use the relevant `TI-*`, `GK-*`, `VI-*`, or `SE-*` backlog task ID.
- Preserve stable source-note identity and hard fretboard/file constraints.
- Keep provider/product controls out of Guitar IR and Guitar Playing Knowledge.
- Never claim improved musical quality or plugin behavior without real evidence.
- Update only the narrow authoritative document whose facts changed.
