"""Format Guitar IR section provenance as concise Guitar Pro markers."""

from __future__ import annotations

from typing import Any, Mapping


def _strongest(scores: object, minimum: float) -> str | None:
    if not isinstance(scores, Mapping):
        return None
    candidates = [
        (str(name), float(score))
        for name, score in scores.items()
        if isinstance(score, (int, float)) and float(score) >= minimum
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[1])[0]


def section_marker_titles(
    section_contexts: list[dict[str, Any]],
) -> dict[int, str]:
    """Return start-measure -> concise strategy label."""

    result: dict[int, str] = {}
    for number, raw in enumerate(section_contexts, start=1):
        start_measure = raw.get("start_measure")
        if not isinstance(start_measure, int):
            continue
        context = raw.get("playing_context", {})
        if not isinstance(context, Mapping):
            context = {}
        style = _strongest(context.get("style_scores"), 0.45)
        technique = _strongest(context.get("technique_scores"), 0.50)
        role = _strongest(context.get("role_scores"), 0.50)
        if technique == "rock_arpeggio":
            technique = "arpeggio"

        parts = [f"S{number:02d}"]
        if style:
            parts.append(style)
        if technique:
            parts.append(technique)
        elif role:
            parts.append(role)
        result[start_measure] = " · ".join(parts)
    return result
