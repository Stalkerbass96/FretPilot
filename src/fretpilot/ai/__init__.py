"""Optional, provider-neutral AI advice that cannot bypass engine validation."""

from fretpilot.ai.context import build_shadow_rewrite_request
from fretpilot.ai.models import (
    AIProviderIdentity,
    RewriteProposalDecision,
    ShadowRewritePolicy,
    ShadowRewriteReport,
    ShadowRewriteRequest,
)
from fretpilot.ai.shadow import generate_shadow_rewrite_report

__all__ = [
    "AIProviderIdentity",
    "RewriteProposalDecision",
    "ShadowRewritePolicy",
    "ShadowRewriteReport",
    "ShadowRewriteRequest",
    "build_shadow_rewrite_request",
    "generate_shadow_rewrite_report",
]
