"""Provider contract for optional musical reasoning services."""

from __future__ import annotations

from typing import Any, Protocol

from fretpilot.ai.models import AIProviderIdentity, ShadowRewriteRequest


class AIProviderError(RuntimeError):
    """A sanitized provider/configuration/protocol failure."""


class RewriteAdvisor(Protocol):
    @property
    def identity(self) -> AIProviderIdentity: ...

    def propose_rewrite(self, request: ShadowRewriteRequest) -> dict[str, Any]: ...
