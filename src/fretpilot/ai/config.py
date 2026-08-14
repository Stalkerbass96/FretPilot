"""Environment-backed configuration for the optional LLM advisor."""

from __future__ import annotations

import os
from typing import Mapping

from fretpilot.ai.providers import OpenAICompatibleRewriteAdvisor, RewriteAdvisor


def advisor_from_environment(
    environment: Mapping[str, str] | None = None,
) -> tuple[RewriteAdvisor | None, str | None]:
    values = os.environ if environment is None else environment
    base_url = values.get("FRETPILOT_LLM_BASE_URL", "").strip()
    model = values.get("FRETPILOT_LLM_MODEL", "").strip()
    api_key = values.get("FRETPILOT_LLM_API_KEY", "")
    configured = [bool(base_url), bool(model), bool(api_key)]
    if not any(configured):
        return None, None
    if not all(configured):
        return None, (
            "AI configuration requires FRETPILOT_LLM_BASE_URL, "
            "FRETPILOT_LLM_MODEL, and FRETPILOT_LLM_API_KEY."
        )
    try:
        return (
            OpenAICompatibleRewriteAdvisor(
                base_url=base_url,
                api_key=api_key,
                model=model,
                provider_id=values.get(
                    "FRETPILOT_LLM_PROVIDER_ID",
                    "openai-compatible",
                ),
                json_mode=values.get("FRETPILOT_LLM_JSON_MODE", "true").lower()
                not in {"0", "false", "no"},
            ),
            None,
        )
    except ValueError as exc:
        return None, str(exc)
