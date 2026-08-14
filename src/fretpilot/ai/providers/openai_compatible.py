"""OpenAI-compatible chat-completions adapter for third-party LLM APIs."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlsplit

import httpx

from fretpilot.ai.models import AIProviderIdentity, ShadowRewriteRequest
from fretpilot.ai.providers.base import AIProviderError


_SYSTEM_PROMPT = """You are a guitar MIDI rewrite advisor.
Return one JSON object only, with keys `summary` and `decisions`.
Each decision must contain source_note_index, operation, confidence, reason,
and target_pitch when operation is transpose. Use only operations allowed by
the policy. Do not invent note indices, exceed edit budgets, or claim that any
proposal was applied. Prefer no decision over a weak decision."""


def _validated_base_url(value: str) -> tuple[str, str]:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("LLM base URL must be an absolute HTTP(S) URL.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(
            "LLM base URL must not contain credentials, query parameters, or fragments."
        )
    base_url = value.rstrip("/")
    return base_url, f"{parsed.scheme}://{parsed.netloc}"


def _json_content(value: Any) -> dict[str, Any]:
    if not isinstance(value, str):
        raise AIProviderError("LLM response content was not a JSON string.")
    text = value.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIProviderError("LLM response did not contain valid JSON.") from exc
    if not isinstance(payload, dict):
        raise AIProviderError("LLM response JSON must be an object.")
    return payload


class OpenAICompatibleRewriteAdvisor:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        provider_id: str = "openai-compatible",
        timeout_seconds: float = 60.0,
        json_mode: bool = True,
        client: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("LLM API key cannot be empty.")
        if not model.strip():
            raise ValueError("LLM model cannot be empty.")
        self._base_url, endpoint_origin = _validated_base_url(base_url)
        self._api_key = api_key
        self._json_mode = json_mode
        self._client = client
        self._timeout_seconds = timeout_seconds
        self._identity = AIProviderIdentity(
            provider_id=provider_id,
            model=model.strip(),
            endpoint_origin=endpoint_origin,
        )

    @property
    def identity(self) -> AIProviderIdentity:
        return self._identity

    def propose_rewrite(self, request: ShadowRewriteRequest) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.identity.model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        request.to_provider_payload(),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                },
            ],
        }
        if self._json_mode:
            body["response_format"] = {"type": "json_object"}

        try:
            if self._client is None:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    response = client.post(
                        f"{self._base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self._api_key}"},
                        json=body,
                    )
            else:
                response = self._client.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=body,
                )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            raise AIProviderError(
                f"LLM provider returned HTTP {exc.response.status_code}."
            ) from exc
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise AIProviderError("LLM provider request or response failed.") from exc
        return _json_content(content)
